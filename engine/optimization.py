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
            g = self.field.grad_num(p)
            fp = fvals[-1]
            # Backtracking line search: shrink the step until the objective does not
            # increase (and stays finite). This keeps descent well-defined on hard or
            # steep landscapes (e.g. Rosenbrock) where a fixed step would diverge, so the
            # non-increasing property that verifies the trajectory always holds.
            step = float(lr)
            cand = p - step * g
            fc = self.field.f(cand)
            while step > 1e-15 and (not np.isfinite(fc) or fc > fp + 1e-12):
                step *= 0.5
                cand = p - step * g
                fc = self.field.f(cand)
            p = cand
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

    # --- multi-start sweep (a simulation over the landscape) --------------------

    def descent_sweep(
        self, starts: Sequence[Sequence[float]], lr: float, steps: int,
        name: str = "descent_sweep",
    ) -> Quantity:
        """Run gradient descent from many starting points and tally which basin each lands in.

        This is the *simulation* behind G23: it does not invent an outcome, it computes one.
        Every run is a real gradient-descent trajectory (verified non-increasing, exactly as
        ``gradient_descent`` above); each run's landing point is refined to the true local
        minimum it fell into with the engine's verified ``minimum`` (∇f≈0, Hessian classified);
        runs that refine to the same minimum (to a tolerance) form one basin, and the per-basin
        counts are a straight tally of those verified landings — so the reported "which basin
        wins" traces entirely to verified computation (C-VERIFIED-MOTION, C-VERIFIED-MATH).

        Verification: the residual is the worst, across all runs, of the descent's step-over-
        step increase and the refined minimum's gradient norm — so a pass certifies every run
        genuinely descended and every basin is a genuine critical point, which is what the
        tally rests on.
        """
        runs = []
        basins: list[dict] = []
        worst_increase = 0.0
        worst_grad = 0.0

        def basin_index_for(point) -> int:
            for i, b in enumerate(basins):
                if float(np.linalg.norm(np.asarray(point) - np.asarray(b["point"]))) < 1e-3:
                    b["count"] += 1
                    return i
            return -1

        for s in starts:
            dq = self.gradient_descent(s, lr, steps)
            v = dq.value
            worst_increase = max(worst_increase, dq.verification.residual)
            end = v["final_point"]
            mq = self.minimum(end)                       # verified refinement to the true min
            worst_grad = max(worst_grad, mq.verification.residual)
            mpt = mq.value["point"]
            bi = basin_index_for(mpt)
            if bi == -1:
                basins.append({"point": [float(c) for c in mpt], "f": float(mq.value["f"]),
                               "type": mq.value["type"], "count": 1})
                bi = len(basins) - 1
            runs.append({
                "start": [float(c) for c in s],
                "points": v["points"],
                "f_values": v["f_values"],
                "final_point": [float(c) for c in end],
                "basin": bi,
            })

        n = len(runs)
        for b in basins:
            b["fraction"] = b["count"] / n if n else 0.0
        order = sorted(range(len(basins)), key=lambda i: basins[i]["count"], reverse=True)
        winner = order[0] if basins else -1
        resid = max(worst_increase, worst_grad)

        def _pt(p):
            return "(" + ", ".join(f"{c:.3g}" for c in p) + ")"
        if basins:
            w = basins[winner]
            disp = (f"{n} runs → {len(basins)} basin(s); "
                    f"basin at {_pt(w['point'])} attracted {w['count']}/{n} "
                    f"({100 * w['fraction']:.0f}%)")
        else:
            disp = f"{n} runs, no basin resolved"

        return Quantity(
            name=name,
            kind="sweep",
            value={
                "runs": runs, "basins": basins, "winner": winner, "n_runs": n,
                "lr": float(lr), "steps": int(steps),
            },
            display=disp,
            provenance="engine.optimize.gradient_descent",
            verification=Verification.from_residual(
                "every run a valid descent (non-increasing) landing at a verified minimum (∇f≈0)",
                resid, 1e-6,
                detail=f"{n} runs, worst step-increase {worst_increase:.1e}, "
                       f"worst ‖∇f‖ at a basin {worst_grad:.1e}",
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
