"""Solve a problem descriptor and build its scene — the dispatch shared by the server.

A *descriptor* is a small dict naming an area and its parameters. This maps one to the
right engine solver and scene builder, returning the verified solution plus renderable
geometry. The built-in ``CATALOG`` holds canonical example problems for the demo UI; it is
deliberately *not* the governed representative suite (that is fixed by proposal P-0001 and,
once approved, lives in ``suite/problems.json`` with independent reference values). Users
can also pose their own problems through the same descriptor path.
"""

from __future__ import annotations

from engine.scalar_field import ScalarField
from engine.optimization import OptimizationLandscape, ConstrainedProblem
from engine.vector_field import VectorField
from engine.linalg import LinearTransformation
from engine.dynamics import DynamicalSystem
from engine.explain import Explainer
from engine import scene as S


def _dyn_domain(d: dict) -> tuple:
    """The fixed-point search / flow-field domain for a dynamical system descriptor."""
    if d.get("domain"):
        return tuple(tuple(p) for p in d["domain"])
    return tuple((-3.0, 3.0) for _ in d["vars"])


def _dyn_solution(d: dict, pid: str, title: str):
    ds = DynamicalSystem(d["components"], d["vars"])
    return ds, ds.solve(
        pid, title,
        domain=_dyn_domain(d),
        trajectories=d.get("trajectories"),
        t_span=tuple(d.get("t_span", (0.0, 20.0))),
        samples=int(d.get("samples", 2000)),
        grid=int(d.get("grid", 7)),
        chaotic=bool(d.get("chaotic", False)),
    )


# A grounded question per walkthrough step, so each step's narration comes from the same
# verified Explainer the chat uses — one place, applied to every area.
_STEP_Q = {
    "gradient": "what is the gradient?",
    "hessian": "explain the hessian",
    "critical_points": "where are the critical points?",
    "descent": "did the descent converge?",
    "minimum": "where is the minimum?",
    "constrained_optimum": "explain the lagrange multiplier",
    "divergence": "what is the divergence?",
    "curl": "what is the curl?",
    "determinant": "what is the determinant?",
    "eigen": "what are the eigenvalues?",
    "svd": "what are the singular values?",
    "fixed_points": "where are the equilibria?",
    "stability": "explain the stability",
    "trajectory_1": "explain the trajectory",
    "separation": "explain sensitive dependence",
}


def _narrate(sol) -> None:
    """Attach a short, grounded per-step ``description`` to each walkthrough step, drawn from
    the verified Explainer — so a stepped walkthrough reads as intuitive prose, not bare
    labels. Applied uniformly to every area; steps whose quantity has no mapping keep their
    label. Never raises."""
    try:
        ex = Explainer(sol)
    except Exception:
        return
    for s in sol.steps:
        q = _STEP_Q.get(s.get("quantity", ""))
        if not q:
            continue
        try:
            s["description"] = ex.answer(q)["answer"]
        except Exception:
            pass


def solve_descriptor(d: dict) -> dict:
    """Return a scene dict (verified quantities + step-tagged geometry) for descriptor ``d``."""
    area = d["area"]
    pid = d.get("id", "custom")
    title = d.get("title", pid)

    if area == "scalar-fields":
        field = ScalarField(d["expr"], d.get("vars", ("x", "y")))
        domain = tuple(tuple(p) for p in d.get("domain", ((-3, 3), (-3, 3))))
        sol = field.solve(pid, title, domain=domain).require_verified()
        _narrate(sol)
        return S.build_scalar_scene(field, sol, domain=domain)

    if area == "optimization":
        if d.get("subtype") == "constrained":
            prob = ConstrainedProblem(d["f"], d["g"], d.get("vars", ("x", "y")))
            sol = prob.solve(pid, title).require_verified()
            _narrate(sol)
            # constrained optima render on the constraint curve; reuse the scalar surface
            field = ScalarField(d["f"], d.get("vars", ("x", "y")))
            domain = tuple(tuple(p) for p in d.get("domain", ((-3, 3), (-3, 3))))
            scene = S.build_scalar_scene(field, ScalarField(d["f"]).solve(pid, title, domain),
                                         domain=domain)
            scene["area"] = "optimization"
            scene["steps"] = sol.steps          # the constrained walkthrough (with narration)
            scene["quantities"] = [q.to_dict() for q in sol.quantities]
            opt = sol.get("constrained_optimum").value
            scene["layers"].append({
                "id": "constrained_optimum", "type": "points", "step": 1,
                "label": "constrained optimum (∇f = λ∇g)",
                "data": {"points": [{"position": [opt["point"][0], opt["point"][1],
                                                  field.f(opt["point"])],
                                     "type": "minimum", "color": "#d95f02"}]}})
            return scene
        land = OptimizationLandscape(d["expr"], d.get("vars", ("x", "y")))
        domain = tuple(tuple(p) for p in d.get("domain", ((-3, 3), (-3, 3))))
        sol = land.solve_descent(pid, title, start=d.get("start", [2.0, 2.0]),
                                 lr=d.get("lr", 0.05), steps=d.get("steps", 80)).require_verified()
        _narrate(sol)
        return S.build_optimization_scene(land, sol, domain=domain)

    if area == "vector-fields":
        vf = VectorField(d["components"], d["vars"])
        sol = vf.solve(pid, title).require_verified()
        _narrate(sol)
        dom = tuple(tuple(p) for p in d.get("domain", ((-2, 2), (-2, 2))))
        return S.build_vector_scene(vf, sol, domain=dom)

    if area == "linear-algebra":
        T = LinearTransformation(d["matrix"])
        want = tuple(d.get("want", ("determinant", "eigen")))
        sol = T.solve(pid, title, want=want).require_verified()
        _narrate(sol)
        return S.build_linear_scene(T, sol)

    if area == "dynamical-systems":
        ds, sol = _dyn_solution(d, pid, title)
        sol.require_verified()
        _narrate(sol)
        return S.build_dynamics_scene(ds, sol, domain=_dyn_domain(d))

    raise ValueError(f"unknown area: {area!r}")


def solution_for(d: dict):
    """Re-solve a descriptor to its verified ``Solution`` (used by grounded Q&A)."""
    area = d["area"]
    pid = d.get("id", "custom")
    title = d.get("title", pid)
    if area == "scalar-fields":
        domain = tuple(tuple(p) for p in d.get("domain", ((-3, 3), (-3, 3))))
        return ScalarField(d["expr"], d.get("vars", ("x", "y"))).solve(pid, title, domain=domain)
    if area == "optimization":
        if d.get("subtype") == "constrained":
            return ConstrainedProblem(d["f"], d["g"], d.get("vars", ("x", "y"))).solve(pid, title)
        return OptimizationLandscape(d["expr"], d.get("vars", ("x", "y"))).solve_descent(
            pid, title, start=d.get("start", [2.0, 2.0]), lr=d.get("lr", 0.05),
            steps=d.get("steps", 80))
    if area == "vector-fields":
        return VectorField(d["components"], d["vars"]).solve(pid, title)
    if area == "linear-algebra":
        return LinearTransformation(d["matrix"]).solve(
            pid, title, want=tuple(d.get("want", ("determinant", "eigen"))))
    if area == "dynamical-systems":
        return _dyn_solution(d, pid, title)[1]
    raise ValueError(f"unknown area: {area!r}")


def answer_question(d: dict, question: str) -> dict:
    """Answer a question about a problem, grounded entirely in its verified quantities."""
    return Explainer(solution_for(d).require_verified()).answer(question)


CATALOG: list[dict] = [
    {"id": "S1", "area": "scalar-fields", "title": "Paraboloid  f = x² + y²",
     "expr": "x**2 + y**2"},
    {"id": "S2", "area": "scalar-fields", "title": "Saddle  f = x² − y²",
     "expr": "x**2 - y**2"},
    {"id": "S3", "area": "scalar-fields", "title": "Ripples  f = sin(x)·cos(y)",
     "expr": "sin(x)*cos(y)", "domain": [[-3.14159, 3.14159], [-3.14159, 3.14159]]},
    {"id": "O1", "area": "optimization", "title": "Anisotropic bowl  f = x² + 3y²",
     "expr": "x**2 + 3*y**2", "start": [3.0, 2.0], "lr": 0.1, "steps": 80},
    {"id": "O2", "area": "optimization", "title": "Rosenbrock valley",
     "expr": "(1-x)**2 + 100*(y-x**2)**2", "start": [-1.0, 1.0], "lr": 0.001, "steps": 200,
     "domain": [[-2, 2], [-1, 3]]},
    {"id": "O3", "area": "optimization", "subtype": "constrained",
     "title": "Constrained  min x²+y²  s.t.  x+y=1", "f": "x**2 + y**2", "g": "x + y - 1"},
    {"id": "V1", "area": "vector-fields", "title": "Rotation  F = (−y, x)",
     "components": ["-y", "x"], "vars": ["x", "y"]},
    {"id": "V2", "area": "vector-fields", "title": "Source  F = (x, y)",
     "components": ["x", "y"], "vars": ["x", "y"]},
    {"id": "V3", "area": "vector-fields", "title": "3-D  F = (−y, x, z)",
     "components": ["-y", "x", "z"], "vars": ["x", "y", "z"]},
    {"id": "L1", "area": "linear-algebra", "title": "Symmetric  [[2,1],[1,2]]",
     "matrix": [[2, 1], [1, 2]], "want": ["determinant", "eigen"]},
    {"id": "L2", "area": "linear-algebra", "title": "Shear  [[1,1],[0,1]]",
     "matrix": [[1, 1], [0, 1]], "want": ["determinant", "eigen"]},
    {"id": "L3", "area": "linear-algebra", "title": "3×3 SVD  [[1,2,0],[0,1,2],[2,0,1]]",
     "matrix": [[1, 2, 0], [0, 1, 2], [2, 0, 1]], "want": ["svd"]},
    {"id": "D1", "area": "dynamical-systems", "title": "Stable spiral  ẋ=y, ẏ=−x−y",
     "components": ["y", "-x - y"], "vars": ["x", "y"], "domain": [[-3, 3], [-3, 3]],
     "trajectories": [[2.5, 0.0], [-2.0, 1.5]], "t_span": [0, 18], "samples": 1500},
    {"id": "D2", "area": "dynamical-systems", "title": "Saddle  ẋ=x, ẏ=−y",
     "components": ["x", "-y"], "vars": ["x", "y"], "domain": [[-3, 3], [-3, 3]],
     "trajectories": [[0.1, 2.8], [-0.1, 2.8], [2.8, 0.1]], "t_span": [0, 3], "samples": 600},
    {"id": "D3", "area": "dynamical-systems", "title": "Pendulum  ẋ=y, ẏ=−sin(x)",
     "components": ["y", "-sin(x)"], "vars": ["x", "y"], "domain": [[-4, 4], [-3, 3]],
     "trajectories": [[0.0, 1.0], [0.0, 2.4], [2.5, 0.0]], "t_span": [0, 14], "samples": 1200},
    {"id": "D4", "area": "dynamical-systems", "title": "Lorenz attractor (chaos)",
     "components": ["10*(y - x)", "x*(28 - z) - y", "x*y - 8*z/3"], "vars": ["x", "y", "z"],
     "domain": [[-25, 25], [-30, 30], [0, 50]], "trajectories": [[1.0, 1.0, 1.0]],
     "t_span": [0, 40], "samples": 4000, "chaotic": True},
]

CATALOG_BY_ID = {d["id"]: d for d in CATALOG}
