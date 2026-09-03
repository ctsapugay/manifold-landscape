"""The deterministic brain: interpret the request, plan the tool calls, answer from the
verified state.

This is a genuine interpret → orchestrate loop, not a fixed pipeline: different inputs drive
different tool sequences (a matrix → ``solve_linear_algebra``; 'show me chaos' →
``solve_dynamical_system``; 'where is the minimum?' → a grounded answer plus a ``focus_view``
move). It is what runs when no Claude key is present, and what the offline checks exercise —
so the agent's machinery is provable without the network (C-LOCAL).

Answers are composed by the ``Explainer`` from the problem's *verified* quantities, so every
value stated is one a tool produced (C-VERIFIED-MATH, C-GROUNDED-EXPLANATION).
"""

from __future__ import annotations

from engine.explain import Explainer
from engine.notation import to_notation
from web.problems import solution_for

from .brain import Brain, OrchestrationResult
from .intake import interpret

# a natural "headline" question per area, used to summarize a freshly solved problem
_SEED = {
    "scalar-fields": "what are the critical points?",
    "optimization": "where is the minimum?",
    "vector-fields": "what are the divergence and curl?",
    "linear-algebra": "describe the transformation",
    "dynamical-systems": "what are the equilibria and their stability?",
}


class OfflineBrain(Brain):
    kind = "offline"

    def orchestrate(self, text: str, ctx: dict, tracer) -> OrchestrationResult:
        interp = interpret(text, has_current=bool(ctx.get("current_scene")))
        tracer.trace.interpretation = interp.note or interp.action

        if interp.action == "decline":
            msg = interp.reason
            if interp.suggestion:
                msg += " " + interp.suggestion
            return OrchestrationResult(answer=msg, declined=True)

        if interp.action == "focus":
            res = tracer.call("focus_view", interp.tool_input)
            desc = ctx.get("current_descriptor")
            answer, grounded = self._grounded_line(desc, interp.tool_input.get("feature", ""))
            return OrchestrationResult(
                answer=answer, scene=ctx.get("current_scene"),
                area=(desc or {}).get("area", ""), quantities=self._q(ctx),
                directives=[res.directive] if res.ok and res.directive else [],
                grounded_in=grounded)

        if interp.action == "chat":
            desc = ctx.get("current_descriptor")
            if not desc:
                return OrchestrationResult(
                    answer="Ask me to solve a problem first, then I can answer questions about it.",
                    declined=True)
            ans = Explainer(solution_for(desc).require_verified()).answer(interp.question)
            directives = []
            if interp.focus_feature:
                fres = tracer.call("focus_view", {"feature": interp.focus_feature})
                if fres.ok and fres.directive:
                    directives.append(fres.directive)
            return OrchestrationResult(
                answer=ans["answer"], scene=ctx.get("current_scene"),
                area=desc.get("area", ""), quantities=self._q(ctx),
                directives=directives, grounded_in=ans["grounded_in"])

        # interp.action == "solve"
        res = tracer.call(interp.tool, interp.tool_input)
        if not res.ok:
            return OrchestrationResult(
                answer=(f"I understood this as {interp.note}, but the tools could not solve "
                        f"it ({res.error}). Try rephrasing, or ask for a nearby example."),
                declined=True)
        sol = solution_for(res.descriptor).require_verified()
        if res.descriptor.get("subtype") == "constrained":
            seed = "explain the lagrange multiplier"
        else:
            seed = _SEED.get(res.area, "explain this")
        explained = Explainer(sol).answer(seed)
        title = to_notation(res.scene.get("title", ""))
        headline = f"{title} — " if title else ""
        return OrchestrationResult(
            answer=headline + explained["answer"],
            scene=res.scene, area=res.area, quantities=res.quantities,
            grounded_in=explained["grounded_in"],
            walkthrough=res.scene.get("lesson") or res.scene.get("steps", []))

    def answer_step(self, text: str, step: dict, ctx: dict, tracer) -> OrchestrationResult:
        """Deterministic per-step follow-up (the offline fallback for G17): the grounded
        Explainer answers, biased to the step's own verified quantity."""
        desc = ctx.get("current_descriptor")
        if not desc:
            return OrchestrationResult(
                answer="Ask me to solve a problem first, then I can answer questions about a step.",
                declined=True)
        ans = Explainer(solution_for(desc).require_verified()).answer_about(
            text, (step or {}).get("quantity"))
        return OrchestrationResult(
            answer=ans["answer"], grounded_in=ans["grounded_in"],
            quantities=(ctx.get("current_scene") or {}).get("quantities", []))

    # --- helpers ---------------------------------------------------------------

    @staticmethod
    def _q(ctx: dict) -> list[dict]:
        scene = ctx.get("current_scene") or {}
        return scene.get("quantities", [])

    @staticmethod
    def _grounded_line(desc, feature):
        if not desc:
            return f"Here is {feature}.", []
        try:
            ans = Explainer(solution_for(desc).require_verified()).answer(f"where is the {feature}?")
            return ans["answer"], ans["grounded_in"]
        except Exception:
            return f"Here is {feature}.", []
