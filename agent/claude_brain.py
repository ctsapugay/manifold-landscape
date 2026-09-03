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
- After solving, explain the geometry plainly and concisely, grounded in the returned values.
- When a specific feature would aid understanding (e.g. the user asks "where is the
  minimum?"), call focus_view to drive the 3-D view to it.
- If a request is outside the five areas, say so briefly and offer the nearest in-scope idea.
  Do not fabricate an answer.
- Your reply is shown in a compact UI card, so write PLAIN PROSE: no Markdown (no #, *, -,
  backticks, tables) and no LaTeX ($…$, \\frac, \\dot). Write math inline in plain notation
  (x^2, ẋ = 10(y − x), ∇f, 8/3, λ).
Keep answers to two or three sentences unless asked for more."""


def _tool_result_payload(res) -> dict:
    """A compact, model-facing summary of a tool result (no bulky geometry arrays)."""
    if not res.ok:
        return {"ok": False, "error": res.error}
    payload = {
        "ok": True, "area": res.area,
        "quantities": [
            {"name": q.get("name"), "display": q.get("display"),
             "provenance": q.get("provenance"),
             "verified": q.get("verification", {}).get("passed")}
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
        self.messages.append({"role": "user", "content": text})
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
        declined = tracer.last_solve is None and not any(c.ok for c in tracer.trace.calls)
        return OrchestrationResult(
            answer=final_text or "I wasn't able to produce an answer.",
            scene=scene, area=area, quantities=quantities, directives=directives,
            walkthrough=(scene or {}).get("steps", []) if scene else [],
            declined=declined)
