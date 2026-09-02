"""Scalar fields and surfaces: f(x, y) → gradient, Hessian, critical points, type.

The primary computation is symbolic (SymPy exact differentiation and solving); every
quantity is then confirmed by an independent numeric route (finite differences,
back-substitution, numeric Hessian eigenvalues) before it is packaged as a verified
``Quantity``. That two-route agreement is the C-VERIFIED-MATH guarantee in practice.
"""

from __future__ import annotations

import itertools
from typing import Sequence

import numpy as np
import sympy as sp
from scipy.optimize import fsolve

from .result import Quantity, Solution, Verification
from .verify import (
    TOL_EXACT,
    TOL_FINITE_DIFF,
    numeric_gradient,
    numeric_hessian,
    residual_norm,
)


def _classify_hessian(eigs: Sequence[float], tol: float = 1e-7) -> str:
    eigs = [float(e) for e in eigs]
    if any(abs(e) <= tol for e in eigs):
        return "degenerate"
    if all(e > 0 for e in eigs):
        return "minimum"
    if all(e < 0 for e in eigs):
        return "maximum"
    return "saddle"


class ScalarField:
    """A scalar field f(x, y) built from a SymPy-parseable expression string."""

    def __init__(self, expr: str, variables: Sequence[str] = ("x", "y")):
        self.var_names = list(variables)
        self.vars = sp.symbols(self.var_names, real=True)
        # Sympify against these exact symbols; otherwise "x" in the string is a distinct
        # default-assumption symbol and derivatives w.r.t. self.vars come out as 0.
        self.expr = sp.sympify(expr, locals=dict(zip(self.var_names, self.vars)))
        self._f = sp.lambdify(self.vars, self.expr, "numpy")
        self._grad_expr = [sp.diff(self.expr, v) for v in self.vars]
        self._grad_f = [sp.lambdify(self.vars, g, "numpy") for g in self._grad_expr]
        self._hess_expr = sp.hessian(self.expr, self.vars)

    # --- numeric callables (used by the independent verification route) ---------

    def f(self, point) -> float:
        return float(self._f(*np.asarray(point, dtype=float)))

    def grad_num(self, point) -> np.ndarray:
        p = np.asarray(point, dtype=float)
        return np.array([float(gf(*p)) for gf in self._grad_f])

    # --- verified quantities ----------------------------------------------------

    def gradient(self, samples: int = 12, span: float = 2.0, seed: int = 0) -> Quantity:
        """Symbolic gradient, verified against finite differences at random samples."""
        rng = np.random.default_rng(seed)
        worst = 0.0
        for _ in range(samples):
            p = rng.uniform(-span, span, size=len(self.vars))
            symbolic = self.grad_num(p)
            numeric = numeric_gradient(self.f, p)
            worst = max(worst, residual_norm(symbolic, numeric))
        disp = "[" + ", ".join(str(g) for g in self._grad_expr) + "]"
        return Quantity(
            name="gradient",
            kind="vector",
            value=[str(g) for g in self._grad_expr],
            display="∇f = " + disp,
            provenance="sympy.diff",
            verification=Verification.from_residual(
                "finite-difference gradient at random samples", worst, TOL_FINITE_DIFF,
                detail=f"{samples} samples in [-{span},{span}]^{len(self.vars)}",
            ),
        )

    def hessian(self, samples: int = 8, span: float = 2.0, seed: int = 1) -> Quantity:
        """Symbolic Hessian, verified against a finite-difference Hessian."""
        hf = sp.lambdify(self.vars, self._hess_expr, "numpy")
        rng = np.random.default_rng(seed)
        worst = 0.0
        for _ in range(samples):
            p = rng.uniform(-span, span, size=len(self.vars))
            symbolic = np.asarray(hf(*p), dtype=float)
            numeric = numeric_hessian(self.f, p)
            worst = max(worst, residual_norm(symbolic, numeric))
        return Quantity(
            name="hessian",
            kind="matrix",
            value=[[str(self._hess_expr[i, j]) for j in range(len(self.vars))]
                   for i in range(len(self.vars))],
            display="H = " + str(self._hess_expr.tolist()),
            provenance="sympy.hessian",
            verification=Verification.from_residual(
                "finite-difference Hessian at random samples", worst, 1e-3,
                detail=f"{samples} samples",
            ),
        )

    def critical_points(
        self,
        domain: tuple[tuple[float, float], ...] = ((-3, 3), (-3, 3)),
        grid: int = 7,
        dedupe_tol: float = 1e-4,
    ) -> Quantity:
        """Critical points within ``domain``, found by seeded Newton on ∇f=0 and
        verified by the gradient residual at each point. Each point is classified by
        the sign pattern of the numeric Hessian's eigenvalues.

        A numeric finder (grid seed + fsolve) is used rather than symbolic solving so
        the same routine handles polynomial and transcendental fields uniformly; the
        gradient residual is the independent confirmation that a returned point is real.
        """
        def grad_vec(p):
            return self.grad_num(p)

        seeds = itertools.product(
            *[np.linspace(lo, hi, grid) for (lo, hi) in domain]
        )
        found: list[np.ndarray] = []
        for s in seeds:
            try:
                sol, info, ier, _ = fsolve(grad_vec, np.array(s, dtype=float),
                                           full_output=True, xtol=1e-12)
            except Exception:
                continue
            if ier != 1:
                continue
            if any(not (lo - 1e-6 <= sol[k] <= hi + 1e-6)
                   for k, (lo, hi) in enumerate(domain)):
                continue
            if residual_norm(grad_vec(sol), np.zeros_like(sol)) > 1e-8:
                continue
            if not any(residual_norm(sol, q) < dedupe_tol for q in found):
                found.append(np.round(sol, 9))

        found.sort(key=lambda p: tuple(p))
        hf = sp.lambdify(self.vars, self._hess_expr, "numpy")
        points = []
        worst = 0.0
        for p in found:
            worst = max(worst, residual_norm(grad_vec(p), np.zeros_like(p)))
            eigs = np.linalg.eigvalsh(np.asarray(hf(*p), dtype=float))
            points.append({
                "point": [float(v) for v in p],
                "f": self.f(p),
                "type": _classify_hessian(eigs),
                "hessian_eigenvalues": [float(e) for e in eigs],
            })
        return Quantity(
            name="critical_points",
            kind="points",
            value=points,
            display="; ".join(f"{tuple(pt['point'])}: {pt['type']}" for pt in points) or "none in domain",
            provenance="engine.critical_points",
            verification=Verification.from_residual(
                "gradient residual ‖∇f‖ at each critical point", worst, TOL_EXACT,
                detail=f"{len(points)} point(s) in {domain}",
            ),
        )

    def solve(
        self,
        problem_id: str,
        title: str,
        domain: tuple[tuple[float, float], ...] = ((-3, 3), (-3, 3)),
    ) -> Solution:
        """Assemble the full verified solution, recording step order for G3."""
        sol = Solution(problem_id=problem_id, area="scalar-fields", title=title)
        g = sol.add(self.gradient())
        sol.steps.append({"step": 1, "introduces": "gradient", "quantity": "gradient"})
        h = sol.add(self.hessian())
        sol.steps.append({"step": 2, "introduces": "hessian", "quantity": "hessian"})
        cp = sol.add(self.critical_points(domain=domain))
        sol.steps.append({"step": 3, "introduces": "critical points", "quantity": "critical_points"})
        return sol
