#!/usr/bin/env python3
"""CHK — the tutor drives the visualization (criterion G5).

Over a scripted set of "focusing" questions where a view move is clearly warranted, the
agent must issue a focus directive that lands on (or highlights) the CORRECT feature, using
the problem's verified geometry. Each case solves a problem, then asks the focusing question
and checks the resulting directive's target against the expected feature location.

Offline brain, no network (C-LOCAL). Backs criterion G5.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402

# (setup problem, focusing question, expected target [x, y] within tolerance)
CASES = [
    ("minimize x^2 + 3y^2 starting at (3,2)", "where is the minimum?", [0.0, 0.0]),
    ("f = x^2 - y^2", "show me the saddle", [0.0, 0.0]),
    ("minimize x^2 + y^2 subject to x + y = 1", "where is the optimum?", [0.5, 0.5]),
    ("x' = y, y' = -x - y", "where is the equilibrium?", [0.0, 0.0]),
]


def main() -> int:
    errs = []
    for setup, question, expect in CASES:
        agent = build_agent(force="offline")
        agent.run(setup)
        r = agent.run(question)
        if not r.directives:
            errs.append(f"{question!r} on {setup!r}: no view move was made")
            continue
        target = r.directives[0].get("target", [])
        if len(target) < 2 or not np.allclose(target[:2], expect, atol=0.05):
            errs.append(f"{question!r}: view landed on {target[:2]}, expected {expect}")
            continue
        print(f"  ok    {question[:34]:36} → view on {[round(c,3) for c in target[:2]]}")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nTUTOR DID NOT DRIVE THE VIEW — {len(errs)} issue(s).")
        return 1
    print("TUTOR DRIVES THE VIEW — focusing questions land on the correct verified feature.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
