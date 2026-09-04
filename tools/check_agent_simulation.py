#!/usr/bin/env python3
"""CHK — on request the agent runs a simulation and plays it back, verified (criterion G23).

For a representative simulation request (a multi-start descent sweep on a landscape with more
than one basin), the agent must run it through the deterministic tools, report a VERIFIED
outcome (per-basin counts), and drive an animated playback of the ACTUAL runs. Nothing is
fabricated: every run is a real descent and every basin a verified minimum
(C-VERIFIED-MATH, C-VERIFIED-MOTION).

Checks, from the recorded agent turn:
  * a run_simulation tool call is recorded and verified with engine provenance;
  * the reported outcome (the sweep quantity) carries a passing verification record, with
    per-basin counts that sum to the number of runs and a winner that is the largest basin;
  * the emitted 'simulate' directive is well-formed — every run has a path of >= 2 points and
    a basin index, the basins carry counts, and the winner index is in range;
  * a multi-basin landscape actually resolves to more than one basin (the sweep is real).

Runs the offline brain (no network — C-LOCAL). Backs criterion G23.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402


def main() -> int:
    errs = []
    agent = build_agent(force="offline")
    # a tilted double well: two basins, one a clear winner
    r = agent.run("run a multi-start descent sweep on (x^2 - 1)^2 + 0.3*x + y^2")

    if r.declined:
        print(f"  FAIL  the simulation request was declined: {r.answer}")
        return 1

    # the tool call is recorded and verified
    sim_calls = [c for c in r.trace.get("calls", []) if c["tool"] == "run_simulation"]
    if not sim_calls:
        errs.append("no run_simulation tool call was recorded in the trace")
    else:
        c = sim_calls[0]
        if not c["ok"] or not c["verified"]:
            errs.append("run_simulation call is not ok/verified in the trace")
        if any((not p) or p == "model" for p in c["provenance"]):
            errs.append("simulation outcome lacks engine provenance")

    # the reported outcome is a verified sweep quantity
    sweep = next((q for q in r.quantities if q.get("kind") == "sweep"), None)
    if not sweep:
        errs.append("no sweep quantity in the result")
    else:
        if not sweep.get("verification", {}).get("passed"):
            errs.append("the sweep outcome does not carry a passing verification record")
        val = sweep.get("value", {})
        basins = val.get("basins", [])
        n = val.get("n_runs", 0)
        total = sum(b.get("count", 0) for b in basins)
        if total != n or n <= 0:
            errs.append(f"per-basin counts {total} do not sum to n_runs {n}")
        w = val.get("winner", -1)
        if not (0 <= w < len(basins)):
            errs.append("winner index is out of range")
        elif basins[w].get("count") != max(b.get("count", 0) for b in basins):
            errs.append("the winner is not the most-attracting basin")

    # the playback directive is well-formed and replays the actual runs
    directive = next((d for d in r.directives if d.get("type") == "simulate"), None)
    if not directive:
        errs.append("no 'simulate' directive emitted for playback")
    else:
        runs = directive.get("runs", [])
        if not runs:
            errs.append("simulate directive carries no runs to play back")
        for i, run in enumerate(runs):
            path = run.get("path", [])
            if len(path) < 2 or not all(len(p) == 3 for p in path):
                errs.append(f"run {i}: path is not >= 2 xyz points")
                break
            if not isinstance(run.get("basin"), int):
                errs.append(f"run {i}: no basin index")
                break
        d_basins = directive.get("basins", [])
        if len(d_basins) < 2:
            errs.append("the multi-basin landscape did not resolve to > 1 basin "
                        "(the sweep must be a real computation)")
        if not directive.get("verified"):
            errs.append("simulate directive is not marked verified")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nSIMULATION GAP — {len(errs)} issue(s).")
        return 1
    val = sweep["value"]
    b = val["basins"][val["winner"]]
    print(f"  ok    {val['n_runs']} runs → {len(val['basins'])} basins, "
          f"winner attracted {b['count']}/{val['n_runs']} ({100 * b['fraction']:.0f}%)")
    print("  ok    outcome verified; playback replays every actual run")
    print("\nAGENT SIMULATION — a verified multi-start sweep, played back animated "
          "(G23, C-VERIFIED-MOTION).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
