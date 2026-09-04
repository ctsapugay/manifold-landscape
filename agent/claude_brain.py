"""The Claude brain — the real product's agent.

Claude interprets the user's request and drives the deterministic tools through the Anthropic
tool-use loop. The mathematics is done entirely by the tools; Claude decides *which* tools to
call and *in what order*, reads back the verified results, and composes the explanation from
them. The ``anthropic`` package is imported lazily (only here, only when this brain is built),
so the rest of the system — and every offline check — never needs it or the network.

The message history lives on the brain across turns, so tutoring is genuinely multi-turn
(criterion G6): a follow-up question is answered in the context of everything already
computed. A ``client`` can be injected for testing, which is how the loop's message-threading
is exercised without a key or a network call.
"""

from __future__ import annotations

import json
import os

from .brain import Brain, OrchestrationResult

_DEFAULT_MODEL = "claude-sonnet-4-6"

_SYSTEM = """\
You are Manifold Landscape, an AI tutor for the geometry of continuous mathematics. You help
a user build intuition across five areas: scalar fields & surfaces, gradients & optimization
landscapes, vector fields, linear algebra as geometry, and dynamical systems (ODEs).

Hard rules:
- You do NOT do arithmetic or symbolic mathematics yourself. For EVERY mathematical result,
  call a tool. The tools return values that are independently verified; you must rely on them.
- Never state a numeric or symbolic value that a tool did not return. If you genuinely must
  offer an unverified value, prefix it with "(model-derived, unverified)". Prefer to call a
  tool instead.
- Interpret the request however it is posed — a typed equation, a word problem, or an open
  conceptual request ("show me an example of chaos"). For a conceptual request, choose a
  canonical illustrative example and solve it with the appropriate tool.
- Call exactly ONE solve_ tool for a problem. In particular, a "minimize" / "gradient
  descent" / "optimization" request goes to solve_optimization (it returns the descent path
  and the minimum) — do NOT also call solve_scalar_field, or the wrong visualization (a bare
  surface instead of the descent) will be shown.
- Never state a number the tools did not return — not only computed values, but also
  geometric constants you reason out yourself (an angle like 60°, a count, a coordinate), AND
  numbers you get by doing arithmetic on the returned values (a ratio of two eigenvalues, a
  product, a difference, a percentage). Cite the returned numbers as they are, or express a
  relationship qualitatively ("thousands of times stiffer", "about twice as steep") without a
  computed figure. If such a figure genuinely helps, prefix it "(model-derived, unverified)";
  prefer words. Model-derived numbers are a rare last resort. (Note: a Hessian's condition
  number, when useful, is returned to you as a verified value — use that rather than dividing
  the eigenvalues yourself.)
- After solving, explain the geometry plainly and concisely, grounded in the returned values.
- Ground QUALITATIVE claims too — a direction ("stretched along (1,1)"), a comparison ("this
  basin is deeper", "the y-wall is steeper"), a sign — in the verified values the tools
  returned (each quantity's value is given to you). Do not assert a direction or comparison you
  cannot read off those values; if the value you'd need was not computed, say what would settle
  it rather than guessing.
- When a specific feature would aid understanding (e.g. the user asks "where is the
  minimum?", "which direction is stretched most?", "animate the trajectory"), call the right
  tool to drive the view — focus_view to point at a feature, animate_motion to play a
  trajectory/descent, run_simulation for a sweep — so the explanation is shown, not just told.
- If a request is outside the five areas, say so briefly and offer the nearest in-scope idea.
  Do not fabricate an answer.
- Your reply is shown in a compact UI card, so write PLAIN PROSE: no Markdown (no #, *, -,
  backticks, tables) and no LaTeX ($…$, \\frac, \\dot). Write math inline in plain notation
  (x^2, ẋ = 10(y − x), ∇f, 8/3, λ).
Keep answers to two or three sentences unless asked for more."""


def _compact(value, _depth=0):
    """A model-facing form of a verified value: keep scalars/short lists, summarise long
    point arrays (trajectories, descent paths) so the model gets the KEY verified facts —
    eigenvector directions, critical-point coordinates, equilibria, divergence/curl, basin
    counts — without the bulky geometry. This is what lets the model ground directional and
    comparative claims in verified data instead of guessing (C-VERIFIED-MATH)."""
    if isinstance(value, bool) or value is None or isinstance(value, (int, float, str)):
        return value
    if isinstance(value, dict):
        if _depth >= 4:
            return "…"
        return {k: _compact(v, _depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        # a long list of points/rows is a sampled curve — summarise it, don't dump it
        if len(value) > 8 and all(isinstance(x, (list, tuple, int, float)) for x in value):
            first, last = _compact(value[0], _depth + 1), _compact(value[-1], _depth + 1)
            return {"n": len(value), "first": first, "last": last}
        return [_compact(v, _depth + 1) for v in value[:8]]
    return str(value)


def _tool_result_payload(res) -> dict:
    """A compact, model-facing summary of a tool result. Includes each verified quantity's
    KEY values (compacted) so the model can explain the geometry accurately — directions,
    coordinates, comparisons — grounded in verified data rather than inventing it."""
    if not res.ok:
        return {"ok": False, "error": res.error}
    payload = {
        "ok": True, "area": res.area,
        "quantities": [
            {"name": q.get("name"), "display": q.get("display"),
             "provenance": q.get("provenance"),
             "verified": q.get("verification", {}).get("passed"),
             "value": _compact(q.get("value"))}
            for q in res.quantities
        ],
    }
    if res.scene is not None:
        payload["scene_built"] = True
    if res.directive is not None:
        payload["view"] = res.directive
    return payload


class ClaudeBrain(Brain):
    kind = "claude"

    def __init__(self, registry, client=None, model: str | None = None, max_steps: int = 6):
        self.registry = registry
        self.model = model or os.environ.get("MANIFOLD_MODEL", _DEFAULT_MODEL)
        self.max_steps = max_steps
        self.messages: list[dict] = []
        self._client = client  # injectable for tests; else built lazily

    def reset(self) -> None:
        self.messages = []

    def answer_step(self, text: str, step: dict, ctx: dict, tracer) -> OrchestrationResult:
        """Answer a per-step follow-up with the live agent (criterion G17), in the running
        conversation. The step and its verified values are handed to Claude as context so the
        answer addresses THAT step and is grounded in the computed state; the grounding gate
        downstream labels anything not tool-verified. Multi-turn: it threads into ``messages``,
        so the chat is one continuous conversation (G16)."""
        step = step or {}
        quantities = (ctx.get("current_scene") or {}).get("quantities", [])
        facts = "; ".join(f"{q.get('name')} = {q.get('display')}" for q in quantities
                          if q.get("display"))
        aug = text
        if step.get("title"):
            about = f', which concerns {step.get("quantity")}' if step.get("quantity") else ""
            aug = (f'[Context: the user is looking at the walkthrough step "{step["title"]}"{about}. '
                   f'Answer their question about THIS step, grounded ONLY in these verified '
                   f'values — {facts or "(the current problem\'s verified results)"} — and do not '
                   f'introduce any number a tool did not produce. The problem is ALREADY solved '
                   f'and its visualization is on screen: do NOT call any solve_ tool (that would '
                   f'recompute the scene and disturb the walkthrough); at most call focus_view to '
                   f'point at a feature of the current problem.]\n\n{text}')
        out = self.orchestrate(aug, ctx, tracer)
        # a follow-up answered from context calls no tools and solves nothing — that is not a
        # decline. It is declined only if no answer text came back at all.
        out.declined = not bool(out.answer and out.answer.strip())
        return out

    # --- client ----------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            import anthropic  # lazy: only when actually calling the API
            # Identity-linked API keys must name the workspace the request acts in; a
            # standard key ignores the header. Set ANTHROPIC_WORKSPACE_ID in .env if your
            # key needs it (the API returns a 400 telling you so otherwise).
            wsid = (os.environ.get("ANTHROPIC_WORKSPACE_ID") or "").strip()
            if wsid:
                self._client = anthropic.Anthropic(
                    default_headers={"anthropic-workspace-id": wsid})
            else:
                self._client = anthropic.Anthropic()
        return self._client

    # --- the loop --------------------------------------------------------------

    def orchestrate(self, text: str, ctx: dict, tracer) -> OrchestrationResult:
        client = self._get_client()
        # On the first turn, give the model the deterministic reader's tool suggestion as a
        # HINT — it keeps the live agent from choosing the wrong solver (e.g. treating a
        # "minimize" as a plain surface). The model still orchestrates; this only steers the
        # first tool choice toward the deterministic read. Follow-ups are left unhinted.
        user_content = text
        if not self.messages:
            try:
                from .intake import interpret
                interp = interpret(text, has_current=bool(ctx.get("current_scene")))
                if interp.action in ("solve", "simulate", "animate") and interp.tool:
                    user_content = (f"[interpreter hint: this reads as {interp.note or interp.tool}; "
                                    f"prefer the {interp.tool} tool. Use your own judgement if the "
                                    f"request clearly means something else.]\n\n{text}")
            except Exception:
                pass
        self.messages.append({"role": "user", "content": user_content})
        directives: list[dict] = []
        final_text = ""
        interpretation = ""

        for _ in range(self.max_steps):
            resp = client.messages.create(
                model=self.model, max_tokens=2048, system=_SYSTEM,
                tools=self.registry.schemas(), messages=self.messages,
            )
            # preserve the full assistant turn (incl. any thinking blocks) in history
            self.messages.append({"role": "assistant", "content": resp.content})

            tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
            texts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
            if texts:
                final_text = "\n".join(t for t in texts if t).strip() or final_text
                if not interpretation:
                    interpretation = final_text[:160]

            if getattr(resp, "stop_reason", None) != "tool_use" or not tool_uses:
                break

            results_content = []
            for tu in tool_uses:
                res = tracer.call(tu.name, tu.input or {})
                if res.ok and res.directive:
                    directives.append(res.directive)
                results_content.append({
                    "type": "tool_result", "tool_use_id": tu.id,
                    "content": json.dumps(_tool_result_payload(res)),
                    "is_error": not res.ok,
                })
            self.messages.append({"role": "user", "content": results_content})

        tracer.trace.interpretation = interpretation or "Claude-orchestrated"
        scene = tracer.last_solve.scene if tracer.last_solve else ctx.get("current_scene")
        area = tracer.last_solve.area if tracer.last_solve else ctx.get("area", "")
        quantities = (tracer.last_solve.scene.get("quantities", [])
                      if tracer.last_solve else (ctx.get("current_scene") or {}).get("quantities", []))
        # A turn is a decline only if nothing came back at all: no answer text, no solve, and
        # no successful tool call. A follow-up answered from context (real text, no tool) is a
        # valid answer, not a decline.
        declined = (not (final_text and final_text.strip())
                    and tracer.last_solve is None
                    and not any(c.ok for c in tracer.trace.calls))
        return OrchestrationResult(
            answer=final_text or "I wasn't able to produce an answer.",
            scene=scene, area=area, quantities=quantities, directives=directives,
            walkthrough=((scene or {}).get("lesson") or (scene or {}).get("steps", [])) if scene else [],
            declined=declined)
