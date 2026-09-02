#!/usr/bin/env python3
"""CHK-001 — the representative suite, solved and checked against independent references.

For every problem in ``suite/problems.json`` this:
  1. solves it through the engine;
  2. confirms EVERY displayed quantity is engine-produced (provenance is a deterministic
     routine, never "model") and passed its own verification step — the C-VERIFIED-MATH
     requirement, traced per quantity;
  3. compares the problem's key answers (critical points, optima, divergence/curl,
     eigenvalues, singular values, …) against the INDEPENDENT references stored with it.

Exit 0 only if all of that holds for all problems; any mismatch, unverified quantity, or
model-sourced value exits nonzero. This backs criterion G1. Standard library + engine only;
no network (constraint C-LOCAL).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.problems import solution_for  # noqa: E402
from engine.result import MODEL_PROVENANCE  # noqa: E402

SUITE = ROOT / "suite" / "problems.json"
TOL = 1e-4


def _close(a, b, tol=TOL):
    return abs(float(a) - float(b)) <= tol


def _point_close(p, q, tol=TOL):
    return len(p) == len(q) and all(_close(a, b, tol) for a, b in zip(p, q))


def _num(v):
    """Parse a possibly-symbolic scalar ('0', '2', 2.0) to float."""
    try:
        return float(v)
    except (TypeError, ValueError):
        import sympy as sp
        return float(sp.sympify(v))


class Fail(Exception):
    pass


def check_references(sol, refs):
    """Raise Fail with a message if any reference is not matched by the solution."""
    by_name = {q.name: q for q in sol.quantities}

    def need(name):
        if name not in by_name:
            raise Fail(f"expected a '{name}' quantity, none produced")
        return by_name[name].value

    for key, expected in refs.items():
        if key == "critical_points":
            cps = need("critical_points")
            for exp in expected:
                match = [c for c in cps if _point_close(c["point"], exp["point"])]
                if not match:
                    raise Fail(f"no critical point near {exp['point']}")
                if match[0]["type"] != exp["type"]:
                    raise Fail(f"critical point {exp['point']} is '{match[0]['type']}', "
                               f"expected '{exp['type']}'")
        elif key == "critical_values_include":
            cps = need("critical_points")
            fvals = [c["f"] for c in cps]
            for want in expected:
                if not any(_close(fv, want, 1e-3) for fv in fvals):
                    raise Fail(f"no critical point with f≈{want} (got {sorted(set(round(v,3) for v in fvals))})")
        elif key == "types_include":
            cps = need("critical_points")
            types = {c["type"] for c in cps}
            missing = set(expected) - types
            if missing:
                raise Fail(f"missing critical-point types {missing} (got {types})")
        elif key == "minimum":
            m = need("minimum")
            if not _point_close(m["point"], expected["point"], 1e-3):
                raise Fail(f"minimum at {m['point']}, expected {expected['point']}")
            if "f" in expected and not _close(m["f"], expected["f"], 1e-4):
                raise Fail(f"minimum f={m['f']}, expected {expected['f']}")
        elif key == "descent_converges_to":
            d = need("descent")
            if not _point_close(d["final_point"], expected, 1e-2):
                raise Fail(f"descent ended at {d['final_point']}, expected near {expected}")
        elif key == "constrained_optimum":
            o = need("constrained_optimum")
            if not _point_close(o["point"], expected["point"]):
                raise Fail(f"optimum at {o['point']}, expected {expected['point']}")
            if not _close(o["f"], expected["f"]) or not _close(o["lambda"], expected["lambda"]):
                raise Fail(f"optimum f={o['f']}, λ={o['lambda']}; expected f={expected['f']}, λ={expected['lambda']}")
        elif key == "divergence":
            if not _close(_num(need("divergence")), expected):
                raise Fail(f"divergence {need('divergence')}, expected {expected}")
        elif key == "curl":
            got = [_num(v) for v in need("curl")]
            if len(got) != len(expected) or not all(_close(a, b) for a, b in zip(got, expected)):
                raise Fail(f"curl {got}, expected {expected}")
        elif key == "determinant":
            if not _close(need("determinant"), expected):
                raise Fail(f"determinant {need('determinant')}, expected {expected}")
        elif key == "eigenvalues":
            pairs = need("eigen")["pairs"]
            got = sorted(p["eigenvalue"][0] for p in pairs)
            exp = sorted(expected)
            if len(got) != len(exp) or not all(_close(a, b) for a, b in zip(got, exp)):
                raise Fail(f"eigenvalues {got}, expected {exp}")
        elif key == "defective":
            if need("eigen")["defective"] != expected:
                raise Fail(f"defective={need('eigen')['defective']}, expected {expected}")
        elif key == "singular_values":
            got = sorted(need("svd")["singular_values"], reverse=True)
            exp = sorted(expected, reverse=True)
            if len(got) != len(exp) or not all(_close(a, b, 1e-4) for a, b in zip(got, exp)):
                raise Fail(f"singular values {got}, expected {exp}")
        else:
            raise Fail(f"unknown reference key '{key}'")


def check_provenance_and_verification(sol):
    for q in sol.quantities:
        if q.provenance == MODEL_PROVENANCE or not q.provenance:
            raise Fail(f"quantity '{q.name}' has no engine provenance (would be model-sourced)")
        if not q.verification.passed:
            raise Fail(f"quantity '{q.name}' did not pass verification "
                       f"(residual {q.verification.residual} > tol {q.verification.tolerance})")


def main() -> int:
    data = json.loads(SUITE.read_text(encoding="utf-8"))
    problems = data["problems"]
    failures = []
    for p in problems:
        pid = p["id"]
        try:
            sol = solution_for(p["descriptor"]).require_verified()
            check_provenance_and_verification(sol)
            check_references(sol, p.get("references", {}))
            print(f"  ok    {pid}  {p['title']}")
        except Exception as exc:
            failures.append((pid, str(exc)))
            print(f"  FAIL  {pid}  {p['title']}  —  {exc}")

    print()
    total = len(problems)
    if failures:
        print(f"SUITE NOT VERIFIED — {len(failures)}/{total} problem(s) failed.")
        return 1
    print(f"SUITE VERIFIED — all {total} problems solved, every quantity engine-produced and "
          "verified, all answers match independent references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
