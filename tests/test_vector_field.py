"""Vector fields: divergence and curl (V1–V3)."""

import sympy as sp

from engine.vector_field import VectorField


def test_rotation_V1():
    """F = (-y, x): divergence 0, curl +2 (rotation without expansion)."""
    vf = VectorField(["-y", "x"], ["x", "y"])
    sol = vf.solve("V1", "Rotation").require_verified()
    assert sp.sympify(sol.get("divergence").value) == 0
    assert sp.sympify(sol.get("curl").value[0]) == 2


def test_source_V2():
    """F = (x, y): divergence 2, curl 0 (expansion without rotation)."""
    vf = VectorField(["x", "y"], ["x", "y"])
    sol = vf.solve("V2", "Source").require_verified()
    assert sp.sympify(sol.get("divergence").value) == 2
    assert sp.sympify(sol.get("curl").value[0]) == 0


def test_3d_field_V3():
    """F = (-y, x, z): divergence 1, curl (0,0,2)."""
    vf = VectorField(["-y", "x", "z"], ["x", "y", "z"])
    sol = vf.solve("V3", "3-D rotation with stretch").require_verified()
    assert sp.sympify(sol.get("divergence").value) == 1
    curl = [sp.sympify(c) for c in sol.get("curl").value]
    assert curl == [0, 0, 2]
