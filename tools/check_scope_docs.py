#!/usr/bin/env python3
"""CHK — scope documentation (criterion G6).

Confirms the repository documents the supported scope and the deferred expansions clearly.
Fails if `docs/scope.md` is missing or does not name all four supported areas and the
deferred expansions (at least physics and higher-than-three-dimensional visualization).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "scope.md"

REQUIRED_AREAS = [
    ("scalar field", "surface"),
    ("gradient", "optimization"),
    ("vector field",),
    ("linear algebra",),
]
REQUIRED_DEFERRED = [
    ("physics",),
    ("higher", "dimension"),  # "higher-dimensional" / "higher-than-three-dimensional"
]


def main() -> int:
    if not DOC.exists():
        print(f"  FAIL  {DOC.relative_to(ROOT)} is missing")
        return 1
    text = DOC.read_text(encoding="utf-8").lower()
    errs = []

    for group in REQUIRED_AREAS:
        if not any(term in text for term in group):
            errs.append(f"scope doc does not mention supported area: {' / '.join(group)}")
    for group in REQUIRED_DEFERRED:
        if not all(term in text for term in group):
            errs.append(f"scope doc does not mention deferred expansion: {' '.join(group)}")

    # It must distinguish supported-now from deferred.
    if "deferred" not in text and "future" not in text:
        errs.append("scope doc does not distinguish current scope from deferred/future work")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print("\nSCOPE DOC INCOMPLETE.")
        return 1
    print("  ok    docs/scope.md names the four areas and the deferred expansions "
          "(physics, higher-dimensional)")
    print("\nSCOPE DOCUMENTED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
