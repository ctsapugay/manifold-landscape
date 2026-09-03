"""Dynamical systems (ODEs): the geometry of flow — the fifth area.

A system ẋ = F(x) turns a vector field into *motion*: every point flows along F, and
the long-run shape of that motion (where it settles, spirals, or wanders) is the geometry
this area makes visible. The quantities here are:

  * **fixed points** — the equilibria where F(x) = 0, found by seeded Newton and verified
    by the residual ‖F(x*)‖ ≈ 0 (the same independent-confirmation idea as a scalar
    field's critical points);
  * **stability** — at each fixed point the Jacobian's eigenvalues decide the local flow
    (sink, source, saddle, spiral, centre). The symbolic Jacobian is confirmed against a
    finite-difference Jacobian, and each eigen-pair by the residual ‖J·v − λ·v‖;
  * **trajectories** — an integral curve of the flow, produced by an adaptive integrator
    and verified by an *independent* integrator agreeing over each short segment. That
    segment-local check is deliberate: for a chaotic system (Lorenz) two integrators
    diverge over a long horizon no matter how accurate they are — sensitive dependence is
    the phenomenon — so trustworthiness is established locally, step by step, where it is
    well-posed, not by long-run reproducibility.

Primary computation is symbolic where it can be (Jacobian) and adaptive-numeric where it
must be (integration); every quantity is confirmed by a second, independent route before it
is allowed to surface (C-VERIFIED-MATH).
"""

from __future__ import annotations

import itertools
from typing import Sequence

import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve

from .result import Quantity, Solution, Verification
from .verify import (
    TOL_EXACT,
    numeric_jacobian,
    residual_norm,
    eig_residual,
)


def classify_equilibrium(eigs: Sequence[complex], tol: float = 1e-7) -> str:
    """Name the local flow near a fixed point from its Jacobian eigenvalues.

    The signs of the real parts decide attraction/repulsion; a non-zero imaginary part
    means rotation (a spiral, or a centre when the real part vanishes). A real part at
    zero is marginal — the linearisation does not settle nonlinear stability there, and
    the wording says so.
    """
    eigs = [complex(e) for e in eigs]
    re = [e.real for e in eigs]
    has_rotation = any(abs(e.imag) > tol for e in eigs)
    marginal = any(abs(r) <= tol for r in re)
    n = len(eigs)

    if marginal:
        # Purely imaginary conjugate pair with no other dynamics: a linear centre.
        if has_rotation and all(abs(r) <= tol for r in re):
            return "centre (linearisation marginal — nonlinear terms decide)"
        return "non-hyperbolic (a zero real part — linearisation is inconclusive)"

    all_neg = all(r < 0 for r in re)
    all_pos = all(r > 0 for r in re)
    if all_neg:
        base = "stable spiral" if has_rotation else ("stable node" if n <= 2 else "stable (sink)")
        return base
    if all_pos:
        base = "unstable spiral" if has_rotation else ("unstable node" if n <= 2 else "unstable (source)")
        return base
    # mixed signs
    return "saddle" if not has_rotation else "saddle-focus (unstable)"


class DynamicalSystem:
    """An autonomous system ẋ = F(x), F: Rⁿ → Rⁿ, from SymPy-parseable components."""

    def __init__(self, components: Sequence[str], variables: Sequence[str]):
        self.var_names = list(variables)
        self.vars = sp.symbols(self.var_names, real=True)
        loc = dict(zip(self.var_names, self.vars))
        self.components = [sp.sympify(c, locals=loc) for c in components]
        self.dim = len(self.components)
        if self.dim != len(self.vars):
            raise ValueError("a system needs one equation per variable (ẋ_i = f_i(x))")
        self._F = [sp.lambdify(self.vars, c, "numpy") for c in self.components]
        self._J_expr = sp.Matrix(self.components).jacobian(self.vars)
        self._J = sp.lambdify(self.vars, self._J_expr, "numpy")

    # --- numeric callables (the independent verification route) -----------------

    def F_num(self, point) -> np.ndarray:
        p = np.asarray(point, dtype=float)
        return np.array([float(f(*p)) for f in self._F])

    def J_num(self, point) -> np.ndarray:
        p = np.asarray(point, dtype=float)
        return np.asarray(self._J(*p), dtype=float).reshape(self.dim, self.dim)

    # --- fixed points -----------------------------------------------------------

    def fixed_points(
        self,
        domain: tuple[tuple[float, float], ...] | None = None,
        grid: int = 7,
        dedupe_tol: float = 1e-4,
    ) -> Quantity:
        """Equilibria F(x) = 0 within ``domain``, by seeded Newton, verified by ‖F‖≈0.

        Each point is classified by its Jacobian eigenvalues (sink / source / saddle /
        spiral / centre). A numeric finder handles polynomial and transcendental fields
        uniformly; the residual ‖F(x*)‖ is the independent confirmation each root is real.
        """
        if domain is None:
            domain = tuple((-3.0, 3.0) for _ in range(self.dim))

        seeds = itertools.product(*[np.linspace(lo, hi, grid) for (lo, hi) in domain])
        found: list[np.ndarray] = []
        for s in seeds:
            try:
                sol, info, ier, _ = fsolve(self.F_num, np.array(s, dtype=float),
                                           full_output=True, xtol=1e-12)
            except Exception:
                continue
            if ier != 1:
                continue
            if any(not (lo - 1e-6 <= sol[k] <= hi + 1e-6)
                   for k, (lo, hi) in enumerate(domain)):
                continue
            if residual_norm(self.F_num(sol), np.zeros(self.dim)) > 1e-8:
                continue
            if not any(residual_norm(sol, q) < dedupe_tol for q in found):
                found.append(np.round(sol, 9))

        found.sort(key=lambda p: tuple(p))
        points = []
        worst = 0.0
        scale = 1.0
        for p in found:
            worst = max(worst, residual_norm(self.F_num(p), np.zeros(self.dim)))
            scale = max(scale, float(np.max(np.abs(p))))
            eigs = np.linalg.eigvals(self.J_num(p))
            points.append({
                "point": [float(v) for v in p],
                "type": classify_equilibrium(eigs),
                "jacobian_eigenvalues": [[float(e.real), float(e.imag)] for e in eigs],
            })
        # A root's absolute flow residual scales with the coordinate magnitude, so the
        # bound is relative to the largest equilibrium (an origin-scale system keeps the
        # tight 1e-9 floor; a Lorenz-scale one is judged at ~1e-10 relative, not punished
        # for living at radius 27).
        tol = TOL_EXACT * scale
        return Quantity(
            name="fixed_points",
            kind="points",
            value=points,
            display="; ".join(f"{tuple(round(c,3) for c in pt['point'])}: {pt['type']}"
                              for pt in points) or "no equilibria in domain",
            provenance="engine.dynamics.fixed_points",
            verification=Verification.from_residual(
                "flow residual ‖F(x*)‖ at each equilibrium", worst, tol,
                detail=f"{len(points)} equilibrium/equilibria in {domain}",
            ),
        )

    # --- stability (Jacobian spectrum) ------------------------------------------

    def stability(
        self,
        domain: tuple[tuple[float, float], ...] | None = None,
        grid: int = 7,
    ) -> Quantity:
        """At each fixed point, the Jacobian's eigen-structure and the stability it implies.

        The symbolic Jacobian is confirmed against a finite-difference Jacobian at each
        equilibrium, and each eigen-pair by the residual ‖J·v − λ·v‖; the reported residual
        is the worst of both, over all points.
        """
        fp = self.fixed_points(domain=domain, grid=grid).value
        entries = []
        worst = 0.0
        for pt in fp:
            p = np.array(pt["point"], dtype=float)
            J = self.J_num(p)
            worst = max(worst, residual_norm(J, numeric_jacobian(self.F_num, p)))
            vals, vecs = np.linalg.eig(J)
            for k in range(len(vals)):
                worst = max(worst, eig_residual(J, vals[k], vecs[:, k]))
            entries.append({
                "point": pt["point"],
                "type": pt["type"],
                "jacobian": [[float(v) for v in row] for row in J],
                "eigenvalues": [[float(v.real), float(v.imag)] for v in vals],
            })
        return Quantity(
            name="stability",
            kind="matrix",
            value=entries,
            display="; ".join(
                f"{tuple(round(c,3) for c in e['point'])}: {e['type']}" for e in entries
            ) or "no equilibria to classify",
            provenance="numpy.linalg.eig",
            verification=Verification.from_residual(
                "finite-difference Jacobian and eigen residual ‖J·v−λ·v‖", worst, 1e-5,
                detail=f"{len(entries)} equilibrium/equilibria classified",
            ),
        )

    # --- trajectories (integral curves of the flow) -----------------------------

    def trajectory(
        self,
        x0: Sequence[float],
        t_span: tuple[float, float] = (0.0, 20.0),
        samples: int = 2000,
        name: str = "trajectory",
        check_segments: int = 60,
    ) -> Quantity:
        """An integral curve from ``x0`` over ``t_span``, adaptively integrated and verified
        by an *independent* integrator agreeing over each short segment.

        Primary route: RK45 with dense output. Verification: for a set of consecutive
        sample points (t_k → t_{k+1}), re-integrate that one short segment from x_k with a
        different method (DOP853) and tight tolerances, and confirm it lands on x_{k+1}. The
        worst mismatch is the residual. This is chaos-robust: it never asks two integrators
        to agree over a long horizon (they can't, for a sensitive system), only over each
        well-posed step.
        """
        x0 = np.asarray(x0, dtype=float)
        t0, t1 = t_span
        t_eval = np.linspace(t0, t1, samples)

        def rhs(t, y):
            return self.F_num(y)

        prim = solve_ivp(rhs, (t0, t1), x0, method="RK45", t_eval=t_eval,
                         rtol=1e-9, atol=1e-9, dense_output=False)
        if not prim.success:
            raise RuntimeError(f"integration failed: {prim.message}")
        Y = prim.y.T  # (samples, dim)

        # Independent verification over short segments.
        idx = np.unique(np.linspace(0, samples - 1, min(check_segments, samples - 1) + 1)
                        .astype(int))
        worst = 0.0
        for a, b in zip(idx[:-1], idx[1:]):
            seg = solve_ivp(rhs, (t_eval[a], t_eval[b]), Y[a], method="DOP853",
                            rtol=1e-11, atol=1e-11)
            if not seg.success:
                raise RuntimeError(f"verification integration failed: {seg.message}")
            worst = max(worst, residual_norm(seg.y[:, -1], Y[b]))

        # The mismatch is an absolute position discrepancy, so a trajectory that ranges over
        # a large region (e.g. a saddle whose orbits fly off exponentially) is judged
        # relative to that range rather than against a fixed floor.
        pos_scale = float(np.max(np.abs(Y))) if Y.size else 1.0
        tol = max(1e-4, 1e-7 * pos_scale)
        points = [[float(v) for v in row] for row in Y]
        return Quantity(
            name=name,
            kind="trajectory",
            value={
                "points": points,
                "t": [float(t) for t in t_eval],
                "x0": [float(v) for v in x0],
                "t_span": [float(t0), float(t1)],
                "final_point": [float(v) for v in Y[-1]],
            },
            display=(f"trajectory from {tuple(round(float(c),3) for c in x0)} over "
                     f"t∈[{t0:g},{t1:g}] ({samples} pts)"),
            provenance="scipy.integrate.solve_ivp",
            verification=Verification.from_residual(
                "independent integrator (DOP853) agreeing over each short segment",
                worst, tol,
                detail=f"{len(idx)-1} segments checked",
            ),
        )

    def separation(
        self,
        x0: Sequence[float],
        delta: float = 1e-6,
        t_span: tuple[float, float] = (0.0, 25.0),
        samples: int = 800,
    ) -> Quantity:
        """Sensitive dependence, made quantitative: how a tiny initial perturbation grows.

        Integrates two trajectories from x0 and x0+δ and reports the final separation and
        the mean exponential growth rate (a finite-time Lyapunov estimate). Verified by the
        same segment-local check applied to the reference trajectory — an honest handle on
        chaos rather than an unverifiable long-horizon claim.
        """
        x0 = np.asarray(x0, dtype=float)
        pert = x0.copy()
        pert[0] += delta
        ref = self.trajectory(x0, t_span, samples, name="_ref")
        other = self.trajectory(pert, t_span, samples, name="_pert")
        A = np.asarray(ref.value["points"])
        B = np.asarray(other.value["points"])
        sep = np.linalg.norm(A - B, axis=1)
        d0 = max(sep[0], delta)
        dT = float(sep[-1])
        T = t_span[1] - t_span[0]
        lyap = float(np.log(max(dT, 1e-300) / d0) / T)
        worst = max(ref.verification.residual, other.verification.residual)
        return Quantity(
            name="separation",
            kind="scalar",
            value={
                "initial_separation": float(d0),
                "final_separation": dT,
                "finite_time_lyapunov": lyap,
                "delta": float(delta),
                "t_span": [float(t_span[0]), float(t_span[1])],
            },
            display=(f"δ₀={d0:.1e} grows to {dT:.3g} by t={t_span[1]:g} "
                     f"(mean rate ≈ {lyap:+.3f}/t)"),
            provenance="scipy.integrate.solve_ivp",
            verification=Verification.from_residual(
                "both trajectories segment-verified against an independent integrator",
                worst, 1e-4,
                detail="separation derived from two verified integral curves",
            ),
        )

    # --- assembly ---------------------------------------------------------------

    def solve(
        self,
        problem_id: str,
        title: str,
        domain: tuple[tuple[float, float], ...] | None = None,
        trajectories: Sequence[Sequence[float]] | None = None,
        t_span: tuple[float, float] = (0.0, 20.0),
        samples: int = 2000,
        grid: int = 7,
        chaotic: bool = False,
    ) -> Solution:
        """Assemble the verified solution, recording step order for the walkthrough.

        Steps: (1) the flow's equilibria, (2) their stability, (3) representative
        trajectories, and — for a chaotic system — (4) a sensitive-dependence measurement.
        """
        sol = Solution(problem_id=problem_id, area="dynamical-systems", title=title)
        sol.add(self.fixed_points(domain=domain, grid=grid))
        sol.steps.append({"step": 1, "introduces": "equilibria (F = 0)", "quantity": "fixed_points"})
        sol.add(self.stability(domain=domain, grid=grid))
        sol.steps.append({"step": 2, "introduces": "stability (Jacobian eigenvalues)", "quantity": "stability"})

        if trajectories:
            for i, x0 in enumerate(trajectories):
                q = self.trajectory(x0, t_span=t_span, samples=samples,
                                    name=f"trajectory_{i+1}")
                sol.add(q)
            sol.steps.append({"step": 3, "introduces": "trajectories (flow of the system)",
                              "quantity": "trajectory_1"})

        if chaotic and trajectories:
            sol.add(self.separation(trajectories[0], t_span=t_span, samples=min(samples, 1200)))
            sol.steps.append({"step": 4, "introduces": "sensitive dependence (chaos)",
                              "quantity": "separation"})
        return sol
