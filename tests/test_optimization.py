"""Optimization landscapes: descent, minima, and constrained optima (O1–O3)."""

import numpy as np

from engine.optimization import OptimizationLandscape, ConstrainedProblem


def test_anisotropic_bowl_O1():
    """f = x^2 + 3y^2: descent converges to the origin; objective never increases."""
    land = OptimizationLandscape("x**2 + 3*y**2")
    sol = land.solve_descent("O1", "Anisotropic bowl", start=[3.0, 2.0], lr=0.1, steps=80).require_verified()

    descent = sol.get("descent").value
    assert np.allclose(descent["final_point"], [0.0, 0.0], atol=1e-3)
    # objective monotonically non-increasing
    fs = descent["f_values"]
    assert all(fs[i + 1] <= fs[i] + 1e-12 for i in range(len(fs) - 1))

    minimum = sol.get("minimum").value
    assert np.allclose(minimum["point"], [0.0, 0.0], atol=1e-5)
    assert minimum["type"] == "minimum"


def test_rosenbrock_O2():
    """Rosenbrock: global minimum at (1,1) with f=0, verified."""
    land = OptimizationLandscape("(1-x)**2 + 100*(y-x**2)**2")
    q = land.minimum([-1.0, 1.0])
    assert q.verified
    assert np.allclose(q.value["point"], [1.0, 1.0], atol=1e-4)
    assert abs(q.value["f"]) < 1e-6
    assert q.value["type"] == "minimum"


def test_constrained_O3():
    """min x^2+y^2 s.t. x+y=1: optimum (1/2,1/2), and ∇f=λ∇g holds."""
    prob = ConstrainedProblem("x**2 + y**2", "x + y - 1")
    sol = prob.solve("O3", "Constrained minimum").require_verified()
    opt = sol.get("constrained_optimum").value
    assert np.allclose(opt["point"], [0.5, 0.5], atol=1e-9)
    assert abs(opt["f"] - 0.5) < 1e-9
    assert opt["constraint_residual"] < 1e-9
    assert opt["stationarity_residual"] < 1e-9
