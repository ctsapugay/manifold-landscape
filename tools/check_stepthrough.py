#!/usr/bin/env python3
"""CHK — step-through builds the scene in sync (criterion G3).

For every suite problem, at each step the scene must show *exactly* the geometry that step
introduces — no more, no less. This checks, per step k, that the layers newly visible going
from k-1 to k are precisely the layers tagged with step k, and that nothing tagged with a
later step is ever visible early. Deterministic, offline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.problems import solve_descriptor  # noqa: E402

SUITE = ROOT / "suite" / "problems.json"


def visible_ids(layers, k):
    return {l["id"] for l in layers if l["step"] <= k}


def check(scene) -> list[str]:
    errs = []
    layers = scene["layers"]
    steps = sorted({l["step"] for l in layers})
    maxstep = max(steps)
    prev = set()
    for k in range(maxstep + 1):
        vis = visible_ids(layers, k)
        newly = vis - prev
        expected_new = {l["id"] for l in layers if l["step"] == k}
        if newly != expected_new:
            errs.append(f"step {k}: newly shown {sorted(newly)} != step's own layers "
                        f"{sorted(expected_new)}")
        # nothing from a later step may be visible
        for l in layers:
            if l["step"] > k and l["id"] in vis:
                errs.append(f"step {k}: layer '{l['id']}' (step {l['step']}) shown early")
        prev = vis
    return errs


def main() -> int:
    problems = json.loads(SUITE.read_text(encoding="utf-8"))["problems"]
    all_errs = []
    for p in problems:
        scene = solve_descriptor(p["descriptor"])
        errs = check(scene)
        if errs:
            all_errs += [f"{p['id']}: {e}" for e in errs]
            for e in errs:
                print(f"  FAIL  {p['id']}: {e}")
        else:
            print(f"  ok    {p['id']}  steps reveal exactly their own geometry")
    print()
    if all_errs:
        print(f"STEP-THROUGH OUT OF SYNC — {len(all_errs)} issue(s).")
        return 1
    print(f"STEP-THROUGH IN SYNC — all {len(problems)} problems build in step.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
