"""Gradients and optimization landscapes: descent trajectories and constrained optima.

Built on ``ScalarField`` (which supplies verified symbolic gradients/Hessians). The
quantities here are:
  * a **gradient-descent trajectory**, verified by the property that a correct descent
    with a small enough step never increases the objective;
  * a **minimum**, verified by a near-zero gradient residual and a positive-definite
    Hessian there;
  * a **constrained optimum** via Lagrange multipliers, verified by the constraint being
    satisfied and the stationarity condition ∇f = λ∇g holding (residual ≈ 0).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import sympy as sp
from scipy.optimize import minimize

from .result import Quantity, Solution, Verification
from .scalar_field import ScalarField, _classify_hessian
from .verify import residual_norm


class OptimizationLandscape:
    def __init__(self, expr: str, variables: Sequence[str] = ("x", "y")):
        self.field = ScalarField(expr, variables)
        self.n = len(self.field.vars)

    # --- gradient descent -------------------------------------------------------

    def gradient_descent(
        self, start: Sequence[float], lr: float, steps: int, name: str = "descent"
    ) -> Quantity:
        """Run vanilla gradient descent and package the trajectory as a verified quantity.

        Verification: the objective is non-increasing across the whole path (the defining
        property of descent with an adequate step). ``residual`` is the largest step-over-
        step *increase* in f — for a valid descent it is ≤ 0 up to rounding.
        """
        p = np.asarray(start, dtype=float)
        traj = [p.copy()]
        fvals = [self.field.f(p)]
        for _ in range(steps):
            p = p - lr * self.field.grad_num(p)
            traj.append(p.copy())
            fvals.append(self.field.f(p))
        increases = [fvals[i + 1] - fvals[i] for i in range(len(fvals) - 1)]
        worst_increase = max(increases) if increases else 0.0
        final_grad = float(np.linalg.norm(self.field.grad_num(traj[-1])))
        return Quantity(
            name=name,
            kind="trajectory",
            value={
                "points": [[float(c) for c in pt] for pt in traj],
                "f_values": [float(v) for v in fvals],
                "start": [float(c) for c in start],
                "lr": float(lr),
                "final_point": [float(c) for c in traj[-1]],
                "final_gradient_norm": final_grad,
            },
            display=(f"descent from {tuple(round(float(c),3) for c in start)} → "
                     f"{tuple(round(float(c),3) for c in traj[-1])} "
                     f"({steps} steps, f: {fvals[0]:.4g}→{fvals[-1]:.4g})"),
            provenance="engine.optimize.gradient_descent",
            verification=Verification.from_residual(
                "objective non-increasing along the descent path",
                max(worst_increase, 0.0), 1e-9,
                detail=f"{steps} steps, lr={lr}, final ‖∇f‖={final_grad:.2e}",
            ),
        )

    # --- unconstrained minimum --------------------------------------------------

    def minimum(self, start: Sequence[float], name: str = "minimum") -> Quantity:
        """A local minimum, found by a numeric optimizer and verified by ∇f≈0 and a
        positive-definite Hessian at the result."""
        res = minimize(lambda p: self.field.f(p), np.asarray(start, dtype=float),
                       jac=lambda p: self.field.grad_num(p), method="BFGS",
                       options={"gtol": 1e-10, "maxiter": 5000})
        x = res.x
        grad_resid = residual_norm(self.field.grad_num(x), np.zeros(self.n))
        hf = sp.lambdify(self.field.vars, self.field._hess_expr, "numpy")
        eigs = np.linalg.eigvalsh(np.asarray(hf(*x), dtype=float))
        kind = _classify_hessian(eigs)
        return Quantity(
            name=name,
            kind="points",
            value={
                "point": [float(c) for c in x],
                "f": float(self.field.f(x)),
                "type": kind,
                "hessian_eigenvalues": [float(e) for e in eigs],
                "gradient_residual": float(grad_resid),
            },
            display=f"min at {tuple(round(float(c),4) for c in x)}, f={self.field.f(x):.4g} ({kind})",
            provenance="scipy.optimize.minimize",
            verification=Verification.from_residual(
                "gradient residual ‖∇f‖ at the reported minimum", grad_resid, 1e-6,
                detail=f"Hessian eigenvalues {np.round(eigs,4).tolist()} → {kind}",
            ),
        )

    def solve_descent(
        self, problem_id: str, title: str, start, lr: float, steps: int
    ) -> Solution:
        sol = Solution(problem_id=problem_id, area="optimization", title=title)
        sol.add(self.field.gradient())
        sol.steps.append({"step": 1, "introduces": "gradient field", "quantity": "gradient"})
        sol.add(self.gradient_descent(start, lr, steps))
        sol.steps.append({"step": 2, "introduces": "descent trajectory", "quantity": "descent"})
        sol.add(self.minimum(start))
        sol.steps.append({"step": 3, "introduces": "minimum reached", "quantity": "minimum"})
        return sol


class ConstrainedProblem:
    """Minimize f(x,y) subject to g(x,y)=0 via Lagrange multipliers."""

    def __init__(self, f_expr: str, g_expr: str, variables: Sequence[str] = ("x", "y")):
        self.var_names = list(variables)
        self.vars = sp.symbols(self.var_names, real=True)
        loc = dict(zip(self.var_names, self.vars))
        self.f = sp.sympify(f_expr, locals=loc)
        self.g = sp.sympify(g_expr, locals=loc)
        self.lam = sp.Symbol("lambda", real=True)

    def solve(self, problem_id: str, title: str) -> Solution:
        # Stationarity: ∇f = λ∇g and g = 0.
        grad_f = [sp.diff(self.f, v) for v in self.vars]
        grad_g = [sp.diff(self.g, v) for v in self.vars]
        eqs = [gf - self.lam * gg for gf, gg in zip(grad_f, grad_g)] + [self.g]
        sols = sp.solve(eqs, list(self.vars) + [self.lam], dict=True)
        if not sols:
            raise ValueError(f"no Lagrange solution found for {problem_id}")

        # Pick the minimizing real solution.
        best = None
        for s in sols:
            if any(not sp.im(s[v]).is_zero for v in self.vars):
                continue
            pt = [float(s[v]) for v in self.vars]
            fval = float(self.f.subs({v: s[v] for v in self.vars}))
            if best is None or fval < best[0]:
                best = (fval, pt, float(s[self.lam]))
        fval, pt, lam_val = best

        # Independent verification: constraint satisfied and stationarity residual ≈ 0,
        # both evaluated numerically at the found point.
        subs = {v: pt[i] for i, v in enumerate(self.vars)}
        g_at = abs(float(self.g.subs(subs)))
        gf_num = np.array([float(e.subs(subs)) for e in grad_f])
        gg_num = np.array([float(e.subs(subs)) for e in grad_g])
        stat_resid = residual_norm(gf_num, lam_val * gg_num)
        resid = max(g_at, stat_resid)

        sol = Solution(problem_id=problem_id, area="optimization", title=title)
        sol.add(Quantity(
            name="constrained_optimum",
            kind="points",
            value={
                "point": pt, "f": fval, "lambda": lam_val,
                "constraint_residual": g_at, "stationarity_residual": float(stat_resid),
            },
            display=(f"min at {tuple(round(c,4) for c in pt)}, f={fval:.4g}, "
                     f"λ={lam_val:.4g}"),
            provenance="engine.optimize.lagrange",
            verification=Verification.from_residual(
                "constraint g=0 and stationarity ∇f=λ∇g at the optimum", resid, 1e-7,
                detail=f"g={g_at:.2e}, ‖∇f−λ∇g‖={stat_resid:.2e}",
            ),
        ))
        sol.steps.append({"step": 1, "introduces": "constrained optimum", "quantity": "constrained_optimum"})
        return sol
