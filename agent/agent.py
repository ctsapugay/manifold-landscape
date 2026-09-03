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

    def to_dict(self) -> dict:
        return {
            "answer": self.answer, "scene": self.scene, "area": self.area,
            "quantities": self.quantities, "directives": self.directives,
            "trace": self.trace, "grounded_in": self.grounded_in,
            "grounding": self.grounding, "walkthrough": self.walkthrough,
            "declined": self.declined, "model_derived": self.model_derived,
            "brain": self.brain,
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

    def run(self, text: str) -> AgentResult:
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
                            "area": tracer.last_solve.area}

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
            declined=out.declined, model_derived=out.model_derived, brain=self.brain.kind)


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
