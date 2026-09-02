"""Verified results — the mechanism behind constraint C-VERIFIED-MATH.

Every mathematical quantity the tool will ever display is produced as a ``Quantity``:
a value, a record of *which deterministic computation produced it* (``provenance``),
and a record of *how it was independently confirmed* (``verification``). A quantity
that has not passed verification is not allowed to surface — ``require_verified``
raises before anything unverified reaches the interface.

The language model is never a source here. ``provenance`` names an engine routine
(``sympy.diff``, ``numpy.linalg.eig``, …); ``MODEL_PROVENANCE`` is rejected on
construction, so no displayed number can trace back to model text alone. This module
is what CHK-001 inspects when it confirms G1: each displayed quantity carries a
passing verification record whose origin is the engine, not a model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

# A provenance value that must never appear: the model is not a computation engine.
MODEL_PROVENANCE = "model"

# A displayed value's provenance must name a deterministic computation routine. We accept
# any routine from the scientific stack the engine actually uses, plus the engine's own
# composed routines (``engine.*`` — built from other *verified* quantities, never from a
# model). The point is not a rigid whitelist but a hard floor: nothing sourced from a
# language model, and nothing whose origin is unstated, is allowed to surface.
ALLOWED_PROVENANCE_PREFIXES = ("sympy.", "numpy.", "scipy.", "mpmath.", "engine.")

# Common routines, listed for reference and typo-catching; not the sole allowed set.
ALLOWED_PROVENANCE = {
    "sympy.diff",
    "sympy.hessian",
    "numpy.linalg.eig",
    "numpy.linalg.eigh",
    "numpy.linalg.det",
    "numpy.linalg.svd",
    "scipy.optimize.fsolve",
    "scipy.optimize.minimize",
    "engine.critical_points",
    "engine.optimize.gradient_descent",
    "engine.optimize.lagrange",
    "engine.derived",
}


def _provenance_ok(provenance: str) -> bool:
    return bool(provenance) and provenance != MODEL_PROVENANCE and any(
        provenance.startswith(p) for p in ALLOWED_PROVENANCE_PREFIXES
    )


class UnverifiedResultError(RuntimeError):
    """Raised when an unverified (or model-sourced) quantity is about to be used."""


@dataclass
class Verification:
    """An independent confirmation that a computed value is correct.

    ``method`` names the *independent* check (e.g. finite-difference gradient, residual
    of A·v − λ·v). ``residual`` is the measured discrepancy against that check;
    ``passed`` is ``residual <= tolerance``. This is the "and a verification step
    confirmed it" half of C-VERIFIED-MATH — a second computation, by a different route,
    agreeing with the first.
    """

    method: str
    residual: float
    tolerance: float
    passed: bool
    detail: str = ""

    @staticmethod
    def from_residual(method: str, residual: float, tolerance: float, detail: str = "") -> "Verification":
        return Verification(
            method=method,
            residual=float(residual),
            tolerance=float(tolerance),
            passed=bool(float(residual) <= float(tolerance)),
            detail=detail,
        )


@dataclass
class Quantity:
    """One value the tool may display, with its provenance and verification.

    ``value`` is a JSON-serializable form of the result (numbers, lists, nested lists);
    ``display`` is the human-facing rendering (e.g. ``"[2*x, 2*y]"``). ``reference`` is
    an independently-known expected value when the suite carries one — filled by the
    check, not by the engine, so the engine cannot mark its own homework.
    """

    name: str
    kind: str  # "scalar" | "vector" | "matrix" | "symbolic" | "points" | "trajectory"
    value: Any
    display: str
    provenance: str
    verification: Verification

    def __post_init__(self) -> None:
        if not _provenance_ok(self.provenance):
            raise UnverifiedResultError(
                f"quantity {self.name!r} has provenance {self.provenance!r}; a displayed "
                "quantity must come from a deterministic engine routine (one of "
                f"{ALLOWED_PROVENANCE_PREFIXES}), never a model (C-VERIFIED-MATH)."
            )

    @property
    def verified(self) -> bool:
        return self.verification.passed

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class Solution:
    """The full verified solution to one problem: an ordered list of quantities.

    ``steps`` records the order in which quantities are introduced, so a step-through
    (G3) can reveal exactly the geometry a step adds — the field is populated by each
    area's solver as it builds the solution.
    """

    problem_id: str
    area: str
    title: str
    quantities: list[Quantity] = field(default_factory=list)
    steps: list[dict] = field(default_factory=list)

    def add(self, q: Quantity) -> Quantity:
        self.quantities.append(q)
        return q

    def get(self, name: str) -> Quantity:
        for q in self.quantities:
            if q.name == name:
                return q
        raise KeyError(name)

    @property
    def all_verified(self) -> bool:
        return bool(self.quantities) and all(q.verified for q in self.quantities)

    def require_verified(self) -> "Solution":
        """Guard: refuse to hand back a solution with any unverified quantity."""
        bad = [q.name for q in self.quantities if not q.verified]
        if bad or not self.quantities:
            raise UnverifiedResultError(
                f"solution {self.problem_id!r} has unverified quantities: {bad or 'none computed'}."
            )
        return self

    def to_dict(self) -> dict:
        return {
            "problem_id": self.problem_id,
            "area": self.area,
            "title": self.title,
            "quantities": [q.to_dict() for q in self.quantities],
            "steps": self.steps,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
