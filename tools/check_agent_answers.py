#!/usr/bin/env python3
"""CHK-018 — per-step follow-ups are answered by the AGENT, grounded (G17).

A follow-up is answered by the agent's brain — the live Claude brain when one is available,
the deterministic grounded explainer only as the offline fallback — and either way the answer
is grounded in the step's verified state and anything not tool-verified is labelled model-derived.

This drives both routes deterministically and offline (constraint C-LOCAL): the offline brain
directly, and the live route via a CANNED Anthropic client injected into the real ClaudeBrain
(no network). It confirms the live route actually goes through the brain (the client is called),
that a grounded answer is not mislabelled, and that the grounding gate DOES flag a fabricated
number on the agent's answer.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402
from agent.agent import Agent  # noqa: E402
from agent.claude_brain import ClaudeBrain  # noqa: E402
from agent.tools import ToolRegistry  # noqa: E402
from web.problems import solve_descriptor, CATALOG_BY_ID  # noqa: E402


class _CannedClient:
    """A stand-in Anthropic client whose one reply is a fixed text block (no tool use)."""
    def __init__(self, text):
        self._text = text
        self.calls = 0
        outer = self

        class _Messages:
            def create(self, **_kw):
                outer.calls += 1
                block = type("B", (), {"type": "text", "text": outer._text})()
                return type("R", (), {"content": [block], "stop_reason": "end_turn"})()
        self.messages = _Messages()


def _step(scene, sid):
    return next(s for s in scene["lesson"] if s.get("id") == sid)


def main() -> int:
    errs = []
    scene = solve_descriptor(CATALOG_BY_ID["D4"])
    step = _step(scene, "dyn-stab0-eig")

    # --- offline route: the deterministic grounded explainer answers, grounded in the step ---
    off = build_agent(force="offline")
    off.current = {"descriptor": CATALOG_BY_ID["D4"], "scene": scene, "area": "dynamical-systems"}
    ro = off.answer_step("why is one eigenvalue positive?", step)
    if ro.declined:
        errs.append("offline route declined a per-step follow-up")
    if "stability" not in (ro.grounded_in or []):
        errs.append(f"offline route not grounded in the step's quantity (grounded_in={ro.grounded_in})")
    if ro.model_derived:
        errs.append("offline route mislabelled a grounded answer as model-derived")

    # --- live route: the answer goes through the ClaudeBrain (canned client), grounded ---
    reg = ToolRegistry()
    good = ("The eigenvalue with a positive real part pushes nearby trajectories away along "
            "that direction, so it is a saddle-focus rather than a sink.")
    client = _CannedClient(good)
    ca = Agent(ClaudeBrain(reg, client=client), reg)
    ca.current = {"descriptor": CATALOG_BY_ID["D4"], "scene": scene, "area": "dynamical-systems"}
    rc = ca.answer_step("why is one eigenvalue positive?", step)
    if client.calls == 0:
        errs.append("live route did NOT go through the agent brain (Claude client not called)")
    if rc.declined or not rc.answer.strip():
        errs.append("live route produced no answer")
    if rc.model_derived:
        errs.append("live route mislabelled a grounded answer (only verified values) as model-derived")

    # --- the grounding gate must flag a fabricated number on the agent's answer ---
    bad = "The dominant eigenvalue is 999.123, an invented figure no tool produced."
    client2 = _CannedClient(bad)
    ca2 = Agent(ClaudeBrain(reg, client=client2), reg)
    ca2.current = {"descriptor": CATALOG_BY_ID["D4"], "scene": scene, "area": "dynamical-systems"}
    rb = ca2.answer_step("what is the dominant eigenvalue?", step)
    if not rb.model_derived:
        errs.append("grounding gate did not flag a fabricated number in the agent's answer")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nAGENT-ANSWER GAP — {len(errs)} issue(s).")
        return 1
    print("  ok    offline route: the deterministic explainer answers, grounded in the step")
    print("  ok    live route: the follow-up goes through the Claude brain, grounded")
    print("  ok    the grounding gate flags any fabricated number on the agent's answer")
    print("\nAGENT ANSWERS — follow-ups are answered by the agent, grounded and verified-or-labelled (G17).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
