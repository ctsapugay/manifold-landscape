"""The grounding gate — the last line of defence for C-VERIFIED-MATH / C-GROUNDED-EXPLANATION.

Whatever produced the answer text, before it is shown we check that its quantitative content
traces to a verified tool result. Numbers the tools actually computed are fine; a number that
appears nowhere in the verified state is flagged, and the caller labels it model-derived and
unverified rather than presenting it as fact.

For the offline brain the answer is composed *from* the verified quantities (the Explainer),
so it passes by construction; the value of the gate is on the Claude path, where the model
writes prose and could, in principle, state a number the tools never produced.
"""

from __future__ import annotations

import re

_NUM = re.compile(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?")
# numbers that are structural, not mathematical claims about the problem
_STOPWORDS_CONTEXT = ("step", "steps", "iteration", "iterations", "point", "points",
                      "dimension", "dimensions", "axis", "axes", "variable", "variables")


def _numbers_in(text: str) -> list[float]:
    out = []
    for m in _NUM.finditer(text or ""):
        try:
            out.append(round(float(m.group(0)), 4))
        except ValueError:
            pass
    return out


def _reference_numbers(quantities: list[dict]) -> set[float]:
    """Every number that appears in the verified quantities' values and displays."""
    refs: set[float] = set()

    def walk(v):
        if isinstance(v, bool):
            return
        if isinstance(v, (int, float)):
            refs.add(round(float(v), 4))
        elif isinstance(v, str):
            for n in _numbers_in(v):
                refs.add(n)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                walk(x)

    for q in quantities:
        walk(q.get("value"))
        walk(q.get("display"))
        walk(q.get("verification", {}).get("residual"))
    return refs


def check(answer: str, quantities: list[dict], extra_text: str = "", tol: float = 0.05) -> dict:
    """Return {grounded, unverified_numbers} for ``answer`` against verified quantities.

    A number in the answer is grounded if it is within ``tol`` (relative, or absolute for
    small values) of some number in the verified state, appears in ``extra_text`` (the
    problem as the user posed it — coefficients the user typed are given, not model-derived),
    or is a small integer (0, 1, 2, 3 — dimensions, counts, tiny coefficients).
    """
    refs = _reference_numbers(quantities)
    refs |= set(_numbers_in(extra_text))
    unverified = []
    for n in _numbers_in(answer):
        if abs(n) <= 3 and float(n).is_integer():
            continue
        ok = any(abs(n - r) <= max(tol * max(abs(r), 1.0), 1e-3) for r in refs)
        if not ok:
            unverified.append(n)
    return {"grounded": not unverified, "unverified_numbers": unverified,
            "reference_count": len(refs)}
