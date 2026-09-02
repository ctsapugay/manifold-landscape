"""Vector fields: divergence and curl, in 2-D and 3-D.

Primary computation is symbolic (SymPy partial derivatives); each is confirmed against a
finite-difference evaluation of the same operator at random sample points before it is
allowed to surface. Divergence measures local expansion; curl measures local rotation
(a scalar z-component in 2-D, a full vector in 3-D).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import sympy as sp

from .result import Quantity, Solution, Verification
from .verify import curl_fd, divergence_fd, residual_norm


class VectorField:
    def __init__(self, components: Sequence[str], variables: Sequence[str]):
        self.var_names = list(variables)
        self.vars = sp.symbols(self.var_names, real=True)
        loc = dict(zip(self.var_names, self.vars))
        self.components = [sp.sympify(c, locals=loc) for c in components]
        self.dim = len(self.components)
        if self.dim != len(self.vars):
            raise ValueError("vector field needs one component per variable (2-D or 3-D)")
        self._F = [sp.lambdify(self.vars, c, "numpy") for c in self.components]

    def F_num(self, point) -> np.ndarray:
        p = np.asarray(point, dtype=float)
        return np.array([float(f(*p)) for f in self._F])

    # --- divergence -------------------------------------------------------------

    def divergence(self, samples: int = 10, span: float = 2.0, seed: int = 0) -> Quantity:
        div_expr = sum(sp.diff(self.components[i], self.vars[i]) for i in range(self.dim))
        div_f = sp.lambdify(self.vars, div_expr, "numpy")
        rng = np.random.default_rng(seed)
        worst = 0.0
        for _ in range(samples):
            p = rng.uniform(-span, span, size=self.dim)
            worst = max(worst, abs(float(div_f(*p)) - divergence_fd(self.F_num, p)))
        return Quantity(
            name="divergence",
            kind="symbolic",
            value=str(sp.simplify(div_expr)),
            display=f"div F = {sp.simplify(div_expr)}",
            provenance="sympy.diff",
            verification=Verification.from_residual(
                "finite-difference divergence at random samples", worst, 1e-5,
                detail=f"{samples} samples",
            ),
        )

    # --- curl -------------------------------------------------------------------

    def curl(self, samples: int = 10, span: float = 2.0, seed: int = 1) -> Quantity:
        if self.dim == 2:
            curl_expr = [sp.diff(self.components[1], self.vars[0])
                         - sp.diff(self.components[0], self.vars[1])]
        else:
            Fx, Fy, Fz = self.components
            x, y, z = self.vars
            curl_expr = [
                sp.diff(Fz, y) - sp.diff(Fy, z),
                sp.diff(Fx, z) - sp.diff(Fz, x),
                sp.diff(Fy, x) - sp.diff(Fx, y),
            ]
        curl_f = [sp.lambdify(self.vars, e, "numpy") for e in curl_expr]
        rng = np.random.default_rng(seed)
        worst = 0.0
        for _ in range(samples):
            p = rng.uniform(-span, span, size=self.dim)
            symbolic = np.array([float(cf(*p)) for cf in curl_f])
            worst = max(worst, residual_norm(symbolic, curl_fd(self.F_num, p)))
        simplified = [sp.simplify(e) for e in curl_expr]
        display = (f"curl F = {simplified[0]}" if self.dim == 2
                   else f"curl F = {tuple(simplified)}")
        return Quantity(
            name="curl",
            kind="symbolic" if self.dim == 2 else "vector",
            value=[str(e) for e in simplified],
            display=display,
            provenance="sympy.diff",
            verification=Verification.from_residual(
                "finite-difference curl at random samples", worst, 1e-5,
                detail=f"{samples} samples ({self.dim}-D)",
            ),
        )

    def solve(self, problem_id: str, title: str) -> Solution:
        sol = Solution(problem_id=problem_id, area="vector-fields", title=title)
        sol.add(self.divergence())
        sol.steps.append({"step": 1, "introduces": "divergence", "quantity": "divergence"})
        sol.add(self.curl())
        sol.steps.append({"step": 2, "introduces": "curl", "quantity": "curl"})
        return sol
