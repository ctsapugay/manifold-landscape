"""Scene specifications for all four areas: well-formed, serializable, step-tagged (G3)."""

import json

from engine.scalar_field import ScalarField
from engine.optimization import OptimizationLandscape
from engine.vector_field import VectorField
from engine.linalg import LinearTransformation
from engine import scene as S


def _assert_serializable_and_stepped(scn):
    json.dumps(scn)  # raises if any value is not JSON-serializable
    assert scn["layers"], "scene has no layers"
    for layer in scn["layers"]:
        assert isinstance(layer["step"], int) and layer["step"] >= 0
        assert layer["type"] and layer["label"]


def _visible_at(scn, step):
    return [l["id"] for l in scn["layers"] if l["step"] <= step]


def test_scalar_scene_steps():
    f = ScalarField("x**2 - y**2")
    sol = f.solve("S2", "Saddle")
    scn = S.build_scalar_scene(f, sol, res=30)
    _assert_serializable_and_stepped(scn)
    ids = {l["id"]: l["step"] for l in scn["layers"]}
    assert ids["surface"] == 0 and ids["gradient_field"] == 1 and ids["critical_points"] == 3
    # G3: at step 1 the critical points (a later step) are NOT yet shown
    assert "critical_points" not in _visible_at(scn, 1)
    assert "critical_points" in _visible_at(scn, 3)
    # surface mesh is a full res x res grid
    assert len(scn["layers"][0]["data"]["z"]) == 30


def test_optimization_scene_steps():
    land = OptimizationLandscape("x**2 + 3*y**2")
    sol = land.solve_descent("O1", "Bowl", start=[3.0, 2.0], lr=0.1, steps=40)
    scn = S.build_optimization_scene(land, sol, res=30)
    _assert_serializable_and_stepped(scn)
    ids = {l["id"] for l in scn["layers"]}
    assert {"surface", "gradient_field", "descent_path", "minimum"} <= ids


def test_vector_scene_steps():
    vf = VectorField(["-y", "x"], ["x", "y"])
    sol = vf.solve("V1", "Rotation")
    scn = S.build_vector_scene(vf, sol)
    _assert_serializable_and_stepped(scn)
    ids = {l["id"]: l["step"] for l in scn["layers"]}
    assert ids["vector_field"] == 0 and ids["divergence_field"] == 1 and ids["curl_field"] == 2


def test_linear_scene_2d():
    T = LinearTransformation([[2, 1], [1, 2]])
    sol = T.solve("L1", "Symmetric", want=("determinant", "eigen"))
    scn = S.build_linear_scene(T, sol)
    _assert_serializable_and_stepped(scn)
    ids = {l["id"] for l in scn["layers"]}
    assert {"unit_circle", "image_ellipse", "eigenvectors"} <= ids


def test_linear_scene_3d_svd():
    T = LinearTransformation([[1, 2, 0], [0, 1, 2], [2, 0, 1]])
    sol = T.solve("L3", "SVD", want=("svd",))
    scn = S.build_linear_scene(T, sol)
    _assert_serializable_and_stepped(scn)
    ids = {l["id"] for l in scn["layers"]}
    assert {"unit_sphere", "image_ellipsoid", "singular_axes"} <= ids
