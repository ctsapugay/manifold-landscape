#!/usr/bin/env python3
"""CHK — grounded questions and answers (criterion G4 / C-GROUNDED-EXPLANATION).

Poses scripted questions across representative problems and confirms each answer (a) is
grounded only in the problem's verified quantities, (b) references the correct computed
value, and (c) asserts nothing the engine's results contradict. Deterministic, offline —
the explanation engine builds answers from the verified state, so this checks that the
answers stay faithful to it.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.problems import CATALOG_BY_ID, answer_question, solution_for  # noqa: E402

# (problem id, question, substrings that MUST appear, substrings that must NOT appear)
CASES = [
    ("S1", "where is the minimum?", ["(0, 0)", "minimum"], ["maximum", "saddle"]),
    ("S1", "what is the gradient?", ["2*x", "2*y"], []),
    ("S2", "is the origin a saddle?", ["saddle"], ["a minimum", "a maximum"]),
    ("O2", "where is the minimum?", ["(1, 1)"], []),
    ("O3", "explain the lagrange multiplier", ["(0.5, 0.5)", "λ"], []),
    ("V1", "what is the curl?", ["2", "rotat"], ["irrotational"]),
    ("V2", "does the field diverge?", ["div F = 2"], []),
    ("V3", "what is the divergence?", ["div F = 1"], []),
    ("L1", "what are the eigenvalues?", ["3", "1"], ["defective"]),
    ("L2", "why can't this be diagonalized?", ["defective"], []),
    ("L3", "what are the singular values?", ["3", "1.73"], []),
]


def main() -> int:
    errs = []
    for pid, question, must, must_not in CASES:
        desc = CATALOG_BY_ID[pid]
        verified = {q.name for q in solution_for(desc).quantities if q.verified}
        ans = answer_question(desc, question)
        text = ans["answer"]
        # grounding: cites only verified quantities, and cites at least one
        if not ans["grounded_in"] or any(n not in verified for n in ans["grounded_in"]):
            errs.append(f"{pid} {question!r}: grounding {ans['grounded_in']} not all verified")
        for s in must:
            if s not in text:
                errs.append(f"{pid} {question!r}: missing expected value {s!r}")
        for s in must_not:
            if s in text:
                errs.append(f"{pid} {question!r}: contains contradicted claim {s!r}")
        if not errs or errs[-1].split()[0] != pid:
            print(f"  ok    {pid}  {question!r}")
    print()
    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nUNGROUNDED OR WRONG — {len(errs)} answer issue(s).")
        return 1
    print(f"GROUNDED — all {len(CASES)} scripted answers cite the correct verified values.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
