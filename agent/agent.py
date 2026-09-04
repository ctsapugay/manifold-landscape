"""The agent — the transport-agnostic orchestration loop.

The agent owns a session: the current problem (so follow-up questions and view moves have
something to act on) and, for the Claude brain, the running message history (so tutoring is
multi-turn, criterion G6). Each turn it hands the request to its brain, which drives the
tools through a shared ``Tracer``; the tracer records every call (name, input, provenance,
whether it verified) into the inspectable trace (G3, G7). Afterwards the grounding gate
checks the answer's numbers against the verified state (G1) and labels anything model-derived.

``build_agent()`` picks the brain: the real Claude brain when a key is configured, else the
deterministic offline brain — the same object either way, so nothing downstream cares which
is driving.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from . import grounding
from .brain import Brain, OrchestrationResult
from .tools import ToolRegistry, ToolResult
from .trace import AgentTrace, ToolCall


# The domain each area is drawn over when the descriptor does not name one — the base the
# expandable-bounds control (G20) scales from. Linear-algebra is intentionally absent: its unit
# circle/sphere is not a domain, so it is not rescalable.
_DEFAULT_DOMAIN = {
    "scalar-fields": ((-3.0, 3.0), (-3.0, 3.0)),
    "optimization": ((-3.0, 3.0), (-3.0, 3.0)),
    "vector-fields": ((-2.0, 2.0), (-2.0, 2.0)),
}


def _base_domain(desc: dict):
    """The domain a solve started from, as a tuple of (lo, hi) per axis — or None if the area
    is not domain-based."""
    if desc.get("domain"):
        return tuple(tuple(float(c) for c in p) for p in desc["domain"])
    area = desc.get("area")
    if area == "dynamical-systems":
        return tuple((-3.0, 3.0) for _ in desc.get("vars", ["x", "y"]))
    return _DEFAULT_DOMAIN.get(area)


class Tracer:
    """Runs tools on the brain's behalf and records every call into the trace."""

    def __init__(self, registry: ToolRegistry, ctx: dict, brain_kind: str, request: str):
        self.registry = registry
        self.ctx = ctx
        self.trace = AgentTrace(brain=brain_kind, request=request)
        self.last_solve: ToolResult | None = None

    def call(self, name: str, tool_input: dict) -> ToolResult:
        res = self.registry.run(name, tool_input, self.ctx)
        self.trace.record(ToolCall(
            index=len(self.trace.calls), tool=name, input=dict(tool_input or {}),
            ok=res.ok, summary=res.summary, area=res.area,
            provenance=[p for p in res.provenance if p], produced=res.produced,
            verified=res.all_verified, error=res.error))
        if res.ok and res.scene is not None:
            self.ctx["current_scene"] = res.scene
            self.last_solve = res
        return res


@dataclass
class AgentResult:
    answer: str
    scene: dict | None = None
    area: str = ""
    quantities: list[dict] = field(default_factory=list)
    directives: list[dict] = field(default_factory=list)
    trace: dict = field(default_factory=dict)
    grounded_in: list[str] = field(default_factory=list)
    grounding: dict = field(default_factory=dict)
    walkthrough: list[dict] = field(default_factory=list)
    declined: bool = False
    model_derived: bool = False
    brain: str = ""
    descriptor: dict | None = None   # the problem descriptor, so a session can be re-opened (G21)

    def to_dict(self) -> dict:
        return {
            "answer": self.answer, "scene": self.scene, "area": self.area,
            "quantities": self.quantities, "directives": self.directives,
            "trace": self.trace, "grounded_in": self.grounded_in,
            "grounding": self.grounding, "walkthrough": self.walkthrough,
            "declined": self.declined, "model_derived": self.model_derived,
            "brain": self.brain, "descriptor": self.descriptor,
        }


class Agent:
    def __init__(self, brain: Brain, registry: ToolRegistry | None = None):
        self.brain = brain
        self.registry = registry or ToolRegistry()
        self.current: dict | None = None  # {descriptor, scene, area}

    def reset(self) -> None:
        self.current = None
        if hasattr(self.brain, "reset"):
            self.brain.reset()

    def answer_step(self, text: str, step: dict) -> AgentResult:
        """Answer a follow-up question aimed at ONE walkthrough step (criteria G13, G17).

        The answer is produced by the **agent's brain**: the live Claude brain answers it in the
        running conversation, grounded in the step's verified state (G17); the offline brain
        composes it deterministically from the grounded Explainer, biased to the step's own
        quantity. Either way the grounding gate labels any figure that is not tool-verified. It
        does NOT touch ``self.current``, so the user never loses their place in the walkthrough."""
        desc = (self.current or {}).get("descriptor")
        if not desc:
            return AgentResult(answer="Solve a problem first, then I can answer questions "
                               "about a step.", declined=True, brain=self.brain.kind)
        step = step or {}
        scene = (self.current or {}).get("scene") or {}
        ctx = {"current_scene": scene, "current_descriptor": desc,
               "area": (self.current or {}).get("area", "")}
        tracer = Tracer(self.registry, ctx, self.brain.kind, text)
        try:
            if hasattr(self.brain, "answer_step"):
                out = self.brain.answer_step(text, step, ctx, tracer)
            else:  # pragma: no cover - every brain defines it
                out = OrchestrationResult(answer="I can't answer that right now.", declined=True)
        except Exception as exc:
            return AgentResult(answer=f"I couldn't ground that against the step "
                               f"({type(exc).__name__}).", declined=True, brain=self.brain.kind)

        directives = list(out.directives)
        tgt = step.get("focus_target")
        if (isinstance(tgt, (list, tuple)) and len(tgt) == 3
                and not any(d.get("type") == "focus" for d in directives)):
            directives.append({"type": "focus", "target": [float(c) for c in tgt],
                               "highlight_layer": None, "label": step.get("focus") or ""})

        quantities = out.quantities or scene.get("quantities", [])
        g = grounding.check(out.answer, quantities, extra_text=text)
        model_derived = out.model_derived
        if not g["grounded"] and quantities:
            model_derived = True
        # Attach the trace so the tool-call view reflects a follow-up truthfully (G25): a
        # follow-up that drove the view (a focus_view call) shows that call; one answered
        # purely from context shows an empty call list, which the UI renders as
        # "answered from the current problem" rather than a blank/broken panel.
        tracer.trace.model_derived = model_derived
        return AgentResult(
            answer=out.answer, scene=None, area=desc.get("area", ""), quantities=[],
            directives=directives, trace=tracer.trace.to_dict(),
            grounded_in=out.grounded_in, grounding=g,
            walkthrough=[], declined=out.declined, model_derived=model_derived,
            brain=self.brain.kind)

    def rescale(self, factor: float) -> AgentResult | None:
        """Re-solve the current problem over its domain scaled by ``factor`` (criterion G20).

        Returns ``None`` when there is no current problem, or when the current area is not drawn
        over a domain (linear-algebra's unit circle/sphere is fixed) — the frontend gates the
        control on that. The recomputed scene is verified exactly like any other solve, so the
        expanded picture stays tool-computed and verified (C-VERIFIED-MATH)."""
        from web.problems import solve_descriptor
        cur = self.current or {}
        desc = cur.get("descriptor")
        if not desc or desc.get("area") == "linear-algebra":
            return None
        base = cur.get("base_domain") or _base_domain(desc)
        if not base:
            return None
        factor = max(0.5, min(4.0, float(factor)))

        def expand(lo, hi):
            c = (lo + hi) / 2.0
            half = (hi - lo) / 2.0 * factor
            return [c - half, c + half]

        new_domain = [expand(float(lo), float(hi)) for (lo, hi) in base]
        new_desc = dict(desc)
        new_desc["domain"] = new_domain
        scene = solve_descriptor(new_desc)
        self.current = {"descriptor": new_desc, "scene": scene,
                        "area": scene.get("area", ""), "base_domain": base}
        return AgentResult(
            answer="", scene=scene, area=scene.get("area", ""),
            quantities=scene.get("quantities", []),
            walkthrough=scene.get("lesson") or scene.get("steps", []),
            brain=self.brain.kind, descriptor=new_desc)

    def run(self, text: str) -> AgentResult:
        # Deterministic scope guard (both brains): a request the deterministic reader knows is
        # outside the five areas — a PDE/heat/wave equation, an integral, probability, primes,
        # weather — is declined here, so the live model can never be tempted to bluff one into a
        # tool (G2, C-VERIFIED-MATH). Only fires on a confident out-of-scope read; anything
        # parseable still goes to the brain to interpret and orchestrate freely.
        from .intake import interpret as _interpret
        pre = _interpret(text, has_current=bool((self.current or {}).get("scene")))
        if pre.action == "decline" and pre.out_of_scope:
            trace = AgentTrace(brain=self.brain.kind, request=text)
            trace.interpretation = "out of scope — declined without inventing an answer"
            msg = pre.reason + ((" " + pre.suggestion) if pre.suggestion else "")
            return AgentResult(answer=msg, declined=True, trace=trace.to_dict(),
                               brain=self.brain.kind)

        ctx = {
            "current_scene": (self.current or {}).get("scene"),
            "current_descriptor": (self.current or {}).get("descriptor"),
            "area": (self.current or {}).get("area", ""),
        }
        tracer = Tracer(self.registry, ctx, self.brain.kind, text)
        try:
            out: OrchestrationResult = self.brain.orchestrate(text, ctx, tracer)
        except Exception as exc:  # a brain failure must never crash the flow (G8)
            out = OrchestrationResult(
                answer=f"Something went wrong interpreting that ({type(exc).__name__}). "
                       "Please try rephrasing.", declined=True)

        # A successful solve becomes the session's current problem.
        if tracer.last_solve is not None:
            self.current = {"descriptor": tracer.last_solve.descriptor,
                            "scene": tracer.last_solve.scene,
                            "area": tracer.last_solve.area,
                            "base_domain": _base_domain(tracer.last_solve.descriptor or {})}

        # the request plus any expressions the user posed are legitimate number sources
        extra = text
        if tracer.last_solve is not None and tracer.last_solve.descriptor:
            extra += " " + " ".join(str(v) for v in tracer.last_solve.descriptor.values()
                                    if isinstance(v, (str, int, float)))
        g = grounding.check(out.answer, out.quantities, extra_text=extra)
        if not g["grounded"] and out.quantities:
            # numbers with no verified source get an honest label rather than silent trust
            out.model_derived = True
            out.answer += ("\n\n(Note: some figures above are model-derived and not "
                           "tool-verified.)")
        tracer.trace.model_derived = out.model_derived

        return AgentResult(
            answer=out.answer, scene=out.scene, area=out.area, quantities=out.quantities,
            directives=out.directives, trace=tracer.trace.to_dict(),
            grounded_in=out.grounded_in, grounding=g, walkthrough=out.walkthrough,
            declined=out.declined, model_derived=out.model_derived, brain=self.brain.kind,
            descriptor=(self.current or {}).get("descriptor"))

    def restore(self, descriptor: dict) -> AgentResult | None:
        """Re-establish a saved session (G21): re-solve its descriptor so the session's
        visualization comes back and the server-side agent knows the current problem again, so
        follow-up questions still work. Deterministic and local — no model call. Returns the
        rebuilt scene, or ``None`` if the descriptor cannot be solved."""
        from web.problems import solve_descriptor
        if not descriptor:
            return None
        try:
            scene = solve_descriptor(descriptor)
        except Exception:
            return None
        self.current = {"descriptor": descriptor, "scene": scene,
                        "area": scene.get("area", ""),
                        "base_domain": _base_domain(descriptor)}
        if hasattr(self.brain, "reset"):
            self.brain.reset()  # a re-opened session starts a fresh conversation history
        return AgentResult(
            answer="", scene=scene, area=scene.get("area", ""),
            quantities=scene.get("quantities", []),
            walkthrough=scene.get("lesson") or scene.get("steps", []),
            brain=self.brain.kind, descriptor=descriptor)


def _claude_available() -> bool:
    if not (os.environ.get("ANTHROPIC_API_KEY") or "").strip():
        return False
    try:
        import anthropic  # noqa: F401
    except Exception:
        return False
    return True


def build_agent(force: str | None = None, registry: ToolRegistry | None = None) -> Agent:
    """Construct an agent with the right brain.

    ``force`` = 'claude' or 'offline' selects explicitly (used by tests); otherwise the
    Claude brain is used when a key and the SDK are present, and the deterministic offline
    brain otherwise (a graceful degradation, not an error).
    """
    registry = registry or ToolRegistry()
    want_claude = force == "claude" or (force is None and _claude_available())
    if want_claude:
        from .claude_brain import ClaudeBrain
        return Agent(ClaudeBrain(registry), registry)
    from .offline_brain import OfflineBrain
    return Agent(OfflineBrain(), registry)
