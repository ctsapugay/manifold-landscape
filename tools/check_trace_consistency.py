#!/usr/bin/env python3
"""CHK — the tool-call trace reliably reflects the tools that were used (criterion G25).

The bug Clara hit: the "Tool calls" view showed nothing even when tools ran, because the
follow-up path (``Agent.answer_step``) built a tracer but returned a result with no ``trace``.
This check drives the offline agent across the three request types G25 names and confirms:

  * a SOLVE records its solve tool call, with engine provenance and a passing verification;
  * a grounded FOLLOW-UP that drives the view records its focus_view call (the follow-up path
    now carries its trace — the fix), not an empty/blank panel;
  * a SIMULATION records its run_simulation call, verified;
  * a genuinely tool-free follow-up carries an EMPTY call list (which the UI renders as
    "answered from the current problem"), never a broken/blank trace.

Runs the offline brain (no network — C-LOCAL). Backs criterion G25.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402


def _calls(trace):
    return (trace or {}).get("calls", [])


def main() -> int:
    errs = []

    # --- 1) a solve populates the trace with a verified tool call --------------
    a = build_agent(force="offline")
    r = a.run("minimize x^2 + 3y^2 starting at (3,2)")
    solve_calls = [c for c in _calls(r.trace) if c["tool"].startswith("solve_")]
    if not solve_calls:
        errs.append("solve: trace has no solve_* call")
    for c in solve_calls:
        if c["ok"] and c["produced"] and not c["verified"]:
            errs.append(f"solve: {c['tool']} produced an unverified value")
        if any((not p) or p == "model" for p in c["provenance"]):
            errs.append(f"solve: {c['tool']} value lacks engine provenance")

    # --- 2) a follow-up that drives the view records its focus_view call -------
    # (the step names a feature, so the offline brain issues focus_view through the tracer)
    step = {"quantity": "minimum", "focus": "the minimum",
            "focus_target": [0, 0, 0], "id": "opt-min-loc", "title": "The minimum"}
    r2 = a.answer_step("where exactly is the minimum?", step)
    if not r2.trace:
        errs.append("follow-up: answer_step returned no trace at all (the G25 bug)")
    if not any(c["tool"] == "focus_view" for c in _calls(r2.trace)):
        errs.append("follow-up: a view-driving follow-up recorded no focus_view call")
    for c in _calls(r2.trace):
        if c["tool"] == "focus_view" and not c["ok"]:
            errs.append("follow-up: focus_view call was not ok")

    # --- 3) a tool-free follow-up carries an empty (not missing) call list -----
    step2 = {"quantity": "gradient", "focus": None, "focus_target": None,
             "id": "opt-grad", "title": "Downhill is −∇f"}
    r3 = a.answer_step("what does the gradient tell me here?", step2)
    if not isinstance(r3.trace, dict) or "calls" not in r3.trace:
        errs.append("tool-free follow-up: trace is not a well-formed dict with a calls list")
    elif _calls(r3.trace):
        # it's allowed to call a tool, but this question names no feature, so expect none
        errs.append("tool-free follow-up: unexpectedly recorded tool calls")

    # --- 4) a simulation records its verified run_simulation call --------------
    a2 = build_agent(force="offline")
    r4 = a2.run("run a multi-start descent sweep to see which basin wins")
    sim_calls = [c for c in _calls(r4.trace) if c["tool"] == "run_simulation"]
    if not sim_calls:
        errs.append("simulation: trace has no run_simulation call")
    for c in sim_calls:
        if not c["ok"] or not c["verified"]:
            errs.append("simulation: run_simulation call is not ok/verified in the trace")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nTRACE INCONSISTENT — {len(errs)} issue(s).")
        return 1
    print("  ok    a solve records its verified tool call")
    print("  ok    a view-driving follow-up records its focus_view call (no blank trace)")
    print("  ok    a tool-free follow-up carries an empty call list (answered from context)")
    print("  ok    a simulation records its verified run_simulation call")
    print("\nTRACE CONSISTENT — the tool-call view reflects the tools used, across "
          "solve / follow-up / simulation (G25).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
