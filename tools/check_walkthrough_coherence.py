#!/usr/bin/env python3
"""CHK — the walkthrough stays coherent when questions are interleaved (criterion G24).

The bug Clara hit: asking a question mid-walkthrough left steps repeated and the visual
confused. This check guards both halves of the fix:

Backend contract (deterministic, offline): a per-step follow-up must NOT disturb the session's
place — ``Agent.answer_step`` leaves ``agent.current`` (the problem + its scene) exactly as it
was and returns no scene and no walkthrough, so a question can never rebuild, reset, or advance
the walkthrough. The live Claude brain is additionally instructed not to re-solve mid-question.

Frontend wiring (app source, like the other UI-slice checks): a typed "next"/"continue" is
routed to the LOCAL walkthrough (never the agent, which would re-narrate and repeat a step);
``sendQuestion`` never mutates the step cursor or the lesson steps; ``nextStep`` advances by
exactly one; and driving a step re-establishes that step's reveal state.

Backs criterion G24.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402

APP_JS = ROOT / "web" / "app.js"
CLAUDE_BRAIN = ROOT / "agent" / "claude_brain.py"


def _backend_contract(errs):
    agent = build_agent(force="offline")
    agent.run("minimize x^2 + 3y^2 starting at (3,2)")
    before = copy.deepcopy(agent.current)
    step = {"quantity": "minimum", "focus": "the minimum", "focus_target": [0, 0, 0],
            "id": "opt-min-loc", "title": "The minimum"}
    r = agent.answer_step("why is this a genuine minimum?", step)
    # a question must not rebuild the scene or reset/advance the walkthrough
    if r.scene is not None:
        errs.append("answer_step returned a scene — a question could rebuild the visual")
    if r.walkthrough:
        errs.append("answer_step returned a walkthrough — a question could reset the steps")
    if agent.current != before:
        errs.append("answer_step disturbed agent.current — the session's place moved")
    # a second interleaved question must still leave it untouched (no drift)
    agent.answer_step("and what is the gradient there?", step)
    if agent.current != before:
        errs.append("a second interleaved question disturbed the session's place")


def _frontend_wiring(errs):
    js = APP_JS.read_text(encoding="utf-8")

    # advance intent is detected and routed locally through nextStep, not the agent
    if "isAdvanceIntent" not in js or "ADVANCE_RE" not in js:
        errs.append("app.js has no advance-intent detection")
    # inside sendQuestion, an advance intent short-circuits to nextStep()
    start = js.find("async function sendQuestion")
    body = js[start:js.find("\nasync function", start + 10)] if start != -1 else ""
    if "isAdvanceIntent(text)" not in body or "nextStep();" not in body:
        errs.append("sendQuestion does not route an advance intent to the local nextStep")
    # sendQuestion must NOT mutate the walkthrough cursor or the lesson steps
    for bad in ("stepCursor =", "stepCursor +=", "stepCursor-=", "lessonSteps ="):
        if bad in body:
            errs.append(f"sendQuestion mutates walkthrough state ({bad.strip()}) — it must not")

    # nextStep advances by exactly one (init -1->0, else +=1) and re-drives the step
    ns = js.find("function nextStep")
    nbody = js[ns:js.find("\nfunction ", ns + 10)] if ns != -1 else ""
    if "stepCursor = 0" not in nbody or "stepCursor += 1" not in nbody:
        errs.append("nextStep does not advance by exactly one step")
    if "driveStep(step)" not in nbody:
        errs.append("nextStep does not drive the visual for the new step")

    # driving a step re-establishes that step's reveal (so the visual is coherent after a Q)
    ds = js.find("function driveStep")
    dbody = js[ds:js.find("\nfunction ", ds + 10)] if ds != -1 else ""
    if "setStep(" not in dbody or "clearHighlight()" not in dbody:
        errs.append("driveStep does not re-establish the step's reveal/highlight state")


def _live_brain_guard(errs):
    src = CLAUDE_BRAIN.read_text(encoding="utf-8")
    # the live brain must tell the model not to re-solve while answering an interleaved question
    if "do NOT call any solve_ tool" not in src:
        errs.append("claude_brain.answer_step does not forbid re-solving mid-question")


def main() -> int:
    errs: list[str] = []
    _backend_contract(errs)
    _frontend_wiring(errs)
    _live_brain_guard(errs)

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nWALKTHROUGH COHERENCE GAP — {len(errs)} issue(s).")
        return 1
    print("  ok    a follow-up leaves the session's place, scene, and steps untouched")
    print("  ok    a typed 'next' advances locally; sendQuestion never mutates step state")
    print("  ok    nextStep advances by exactly one and re-drives the visual")
    print("  ok    the live brain does not re-solve mid-question")
    print("\nWALKTHROUGH COHERENT across interleaved questions (G24).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
