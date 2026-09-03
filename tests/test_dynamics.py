"""Dynamical systems (ODEs): equilibria, stability, verified trajectories, chaos (D1–D4)."""

import numpy as np

from engine.dynamics import DynamicalSystem, classify_equilibrium


def test_stable_spiral_D1():
    """ẋ=y, ẏ=−x−y: one equilibrium at the origin, a stable spiral (eigenvalues −½±i√3/2)."""
    ds = DynamicalSystem(["y", "-x - y"], ["x", "y"])
    sol = ds.solve("D1", "Stable spiral", domain=((-3, 3), (-3, 3)),
                   trajectories=[[2.5, 0.0]], t_span=(0, 18), samples=1200).require_verified()
    fps = sol.get("fixed_points").value
    assert len(fps) == 1
    assert np.allclose(fps[0]["point"], [0, 0], atol=1e-6)
    assert "stable spiral" in fps[0]["type"]
    # the integral curve is verified by an independent integrator over each segment
    assert sol.get("trajectory_1").verified


def test_saddle_D2():
    """ẋ=x, ẏ=−y: the origin is a saddle (eigenvalues +1, −1)."""
    ds = DynamicalSystem(["x", "-y"], ["x", "y"])
    sol = ds.solve("D2", "Saddle").require_verified()
    fps = sol.get("fixed_points").value
    assert len(fps) == 1 and fps[0]["type"] == "saddle"


def test_pendulum_D3_multiple_equilibria():
    """ẋ=y, ẏ=−sin(x): a centre at the origin and saddles at (±π, 0)."""
    ds = DynamicalSystem(["y", "-sin(x)"], ["x", "y"])
    sol = ds.solve("D3", "Pendulum", domain=((-4, 4), (-3, 3))).require_verified()
    by_type = {}
    for fp in sol.get("fixed_points").value:
        kind = "centre" if "centre" in fp["type"] else fp["type"]
        by_type.setdefault(kind, []).append(fp["point"])
    assert "centre" in by_type and "saddle" in by_type
    # the two saddles sit near ±π
    xs = sorted(round(p[0], 2) for p in by_type["saddle"])
    assert xs[0] < -3.0 and xs[-1] > 3.0


def test_lorenz_D4_chaos_is_verified():
    """The Lorenz system: three equilibria, and a positive finite-time Lyapunov estimate.

    The trajectory is verified by segment-local agreement with an independent integrator —
    the only sound check for a chaotic path, since long-horizon reproducibility is
    impossible under sensitive dependence.
    """
    ds = DynamicalSystem(["10*(y - x)", "x*(28 - z) - y", "x*y - 8*z/3"], ["x", "y", "z"])
    sol = ds.solve("D4", "Lorenz", domain=((-25, 25), (-30, 30), (0, 50)),
                   trajectories=[[1.0, 1.0, 1.0]], t_span=(0, 30), samples=2000,
                   chaotic=True).require_verified()
    assert len(sol.get("fixed_points").value) == 3
    assert sol.get("trajectory_1").verified
    sep = sol.get("separation").value
    assert sep["finite_time_lyapunov"] > 0.0  # sensitive dependence


def test_classify_equilibrium_cases():
    assert classify_equilibrium([-1, -2]) == "stable node"
    assert classify_equilibrium([1, 2]) == "unstable node"
    assert classify_equilibrium([1, -2]) == "saddle"
    assert "stable spiral" in classify_equilibrium([-0.5 + 1j, -0.5 - 1j])
    assert "unstable spiral" in classify_equilibrium([0.5 + 1j, 0.5 - 1j])
    assert "centre" in classify_equilibrium([1j, -1j])


def test_trajectory_verification_is_independent():
    """A deliberately loose 'trajectory' still passes only because the second integrator
    agrees; the residual is a real measured discrepancy, not an assumption."""
    ds = DynamicalSystem(["y", "-x"], ["x", "y"])  # a centre: closed orbits
    q = ds.trajectory([1.0, 0.0], t_span=(0, 6.283185307), samples=800)
    assert q.verified
    assert q.verification.residual < 1e-4
    # a closed orbit returns near its start after one period
    assert np.allclose(q.value["final_point"], [1.0, 0.0], atol=1e-3)
