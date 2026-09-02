"""Scalar-field engine: correctness and that verification actually gates results."""

import numpy as np
import pytest

from engine.scalar_field import ScalarField
from engine.result import UnverifiedResultError, Quantity, Verification


def test_paraboloid_S1():
    """f = x^2 + y^2: gradient verified, one minimum at the origin."""
    field = ScalarField("x**2 + y**2")
    sol = field.solve("S1", "Paraboloid").require_verified()

    grad = sol.get("gradient")
    assert grad.verified
    assert grad.value == ["2*x", "2*y"]

    cps = sol.get("critical_points").value
    assert len(cps) == 1
    assert np.allclose(cps[0]["point"], [0.0, 0.0], atol=1e-6)
    assert cps[0]["type"] == "minimum"


def test_saddle_S2():
    """f = x^2 - y^2: a single saddle at the origin."""
    field = ScalarField("x**2 - y**2")
    sol = field.solve("S2", "Saddle").require_verified()

    cps = sol.get("critical_points").value
    assert len(cps) == 1
    assert np.allclose(cps[0]["point"], [0.0, 0.0], atol=1e-6)
    assert cps[0]["type"] == "saddle"


def test_all_quantities_verified():
    field = ScalarField("x**2 + y**2")
    sol = field.solve("S1", "Paraboloid")
    assert sol.all_verified


def test_model_provenance_is_rejected():
    """A quantity claiming a model source cannot even be constructed (C-VERIFIED-MATH)."""
    v = Verification.from_residual("n/a", 0.0, 1.0)
    with pytest.raises(UnverifiedResultError):
        Quantity(name="fake", kind="scalar", value=1, display="1",
                 provenance="model", verification=v)


def test_require_verified_blocks_unverified():
    """An unverified quantity is refused before it can surface."""
    from engine.result import Solution
    sol = Solution(problem_id="X", area="test", title="t")
    sol.add(Quantity(
        name="bad", kind="scalar", value=1, display="1",
        provenance="sympy.diff",
        verification=Verification(method="m", residual=10.0, tolerance=1e-9, passed=False),
    ))
    with pytest.raises(UnverifiedResultError):
        sol.require_verified()
