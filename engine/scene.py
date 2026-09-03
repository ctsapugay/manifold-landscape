"""Scene specifications: turn a verified ``Solution`` into 3-D geometry to render.

A scene is a list of **layers** (surface, vectors, points, polyline, transformed grid),
each tagged with the solution ``step`` at which it appears. The frontend shows every layer
whose ``step`` is ≤ the current step, so stepping through reveals *exactly* the geometry a
step introduces and nothing from a later one (criterion G3). The scene also carries the
solution's verified quantities verbatim, so the interface only ever displays engine-verified
values (C-VERIFIED-MATH); the meshes here are visual sampling of the same functions, not a
separate source of the mathematical facts.

Everything is plain JSON-serializable data (lists of floats). No rendering happens here.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .result import Solution


def _linspace(lo: float, hi: float, n: int) -> list[float]:
    return [float(v) for v in np.linspace(lo, hi, n)]


def surface_layer(field, domain, res: int = 60, step: int = 0) -> dict:
    """A z = f(x, y) surface mesh sampled over ``domain``."""
    (x0, x1), (y0, y1) = domain
    xs = np.linspace(x0, x1, res)
    ys = np.linspace(y0, y1, res)
    X, Y = np.meshgrid(xs, ys)
    Z = np.empty_like(X)
    for i in range(res):
        for j in range(res):
            Z[i, j] = field.f([X[i, j], Y[i, j]])
    return {
        "id": "surface",
        "type": "surface",
        "step": step,
        "label": "surface z = f(x, y)",
        "data": {
            "x": _linspace(x0, x1, res),
            "y": _linspace(y0, y1, res),
            "z": [[float(v) for v in row] for row in Z],
            "z_min": float(np.min(Z)),
            "z_max": float(np.max(Z)),
        },
    }


def gradient_arrows_layer(field, domain, res: int = 12, step: int = 1) -> dict:
    """Gradient vectors on a coarse grid, drawn in the z = 0 plane (the domain)."""
    (x0, x1), (y0, y1) = domain
    arrows = []
    for x in np.linspace(x0, x1, res):
        for y in np.linspace(y0, y1, res):
            g = field.grad_num([x, y])
            arrows.append({"origin": [float(x), float(y), 0.0],
                           "vector": [float(g[0]), float(g[1]), 0.0]})
    return {
        "id": "gradient_field",
        "type": "vectors",
        "step": step,
        "label": "gradient field ∇f (steepest ascent)",
        "data": {"arrows": arrows},
    }


def critical_points_layer(cp_value, field, step: int = 3) -> dict:
    colors = {"minimum": "#2c7fb8", "maximum": "#d7301f", "saddle": "#756bb1",
              "degenerate": "#999999"}
    pts = []
    for cp in cp_value:
        x, y = cp["point"][0], cp["point"][1]
        pts.append({"position": [float(x), float(y), float(field.f([x, y]))],
                    "type": cp["type"], "color": colors.get(cp["type"], "#333333")})
    return {
        "id": "critical_points",
        "type": "points",
        "step": step,
        "label": "critical points (∇f = 0), classified by the Hessian",
        "data": {"points": pts},
    }


def descent_path_layer(descent_value, field, step: int = 2) -> dict:
    """The descent trajectory lifted onto the surface: (x, y, f(x,y)) per iterate."""
    path = [[float(p[0]), float(p[1]), float(fv)]
            for p, fv in zip(descent_value["points"], descent_value["f_values"])]
    return {
        "id": "descent_path",
        "type": "polyline",
        "step": step,
        "label": "gradient-descent trajectory",
        "data": {"points": path, "start": path[0], "end": path[-1]},
    }


def point_marker_layer(value, field, layer_id: str, label: str, color: str, step: int) -> dict:
    x, y = value["point"][0], value["point"][1]
    return {
        "id": layer_id,
        "type": "points",
        "step": step,
        "label": label,
        "data": {"points": [{"position": [float(x), float(y), float(field.f([x, y]))],
                             "type": value.get("type", ""), "color": color}]},
    }


def _base(solution: Solution, domain) -> dict:
    return {
        "problem_id": solution.problem_id,
        "area": solution.area,
        "title": solution.title,
        "domain": [[float(domain[0][0]), float(domain[0][1])],
                   [float(domain[1][0]), float(domain[1][1])]],
        "layers": [],
        "quantities": [q.to_dict() for q in solution.quantities],
        "steps": solution.steps,
    }


def build_scalar_scene(field, solution: Solution,
                       domain=((-3, 3), (-3, 3)), res: int = 60) -> dict:
    scene = _base(solution, domain)
    scene["layers"].append(surface_layer(field, domain, res, step=0))
    scene["layers"].append(gradient_arrows_layer(field, domain, step=1))
    try:
        cp = solution.get("critical_points")
        scene["layers"].append(critical_points_layer(cp.value, field, step=3))
    except KeyError:
        pass
    return scene


def build_optimization_scene(land, solution: Solution,
                             domain=((-3, 3), (-3, 3)), res: int = 60) -> dict:
    field = land.field
    scene = _base(solution, domain)
    scene["layers"].append(surface_layer(field, domain, res, step=0))
    scene["layers"].append(gradient_arrows_layer(field, domain, step=1))
    try:
        d = solution.get("descent")
        scene["layers"].append(descent_path_layer(d.value, field, step=2))
    except KeyError:
        pass
    try:
        m = solution.get("minimum")
        scene["layers"].append(point_marker_layer(m.value, field, "minimum",
                                                   "minimum reached", "#2c7fb8", step=3))
    except KeyError:
        pass
    return scene


# --- vector fields ------------------------------------------------------------

def build_vector_scene(vf, solution: Solution,
                       domain=((-2, 2), (-2, 2)), res: int = 9) -> dict:
    """Arrow glyphs on a grid (z = 0 plane in 2-D, a 3-D lattice in 3-D). Divergence and
    curl are shown as pointwise scalar grids in 2-D so their steps introduce visible
    geometry; in 3-D they remain verified quantity displays."""
    from .verify import curl_fd, divergence_fd
    d2 = domain if vf.dim == 2 else (domain[0], domain[1], (-2, 2))
    scene = _base(solution, domain)
    axes = [np.linspace(lo, hi, res) for (lo, hi) in d2]

    arrows = []
    if vf.dim == 2:
        for x in axes[0]:
            for y in axes[1]:
                v = vf.F_num([x, y])
                arrows.append({"origin": [float(x), float(y), 0.0],
                               "vector": [float(v[0]), float(v[1]), 0.0]})
    else:
        for x in axes[0]:
            for y in axes[1]:
                for z in axes[2]:
                    v = vf.F_num([x, y, z])
                    arrows.append({"origin": [float(x), float(y), float(z)],
                                   "vector": [float(v[0]), float(v[1]), float(v[2])]})
    scene["layers"].append({"id": "vector_field", "type": "vectors", "step": 0,
                            "label": "vector field F", "data": {"arrows": arrows}})

    if vf.dim == 2:
        gx = np.linspace(d2[0][0], d2[0][1], 20)
        gy = np.linspace(d2[1][0], d2[1][1], 20)
        div = [[float(divergence_fd(vf.F_num, [x, y])) for x in gx] for y in gy]
        curl = [[float(curl_fd(vf.F_num, [x, y])[0]) for x in gx] for y in gy]
        scene["layers"].append({"id": "divergence_field", "type": "scalar_grid", "step": 1,
                                "label": "divergence (local expansion)",
                                "data": {"x": [float(v) for v in gx],
                                         "y": [float(v) for v in gy], "values": div}})
        scene["layers"].append({"id": "curl_field", "type": "scalar_grid", "step": 2,
                                "label": "curl (local rotation)",
                                "data": {"x": [float(v) for v in gx],
                                         "y": [float(v) for v in gy], "values": curl}})
    return scene


# --- linear algebra as geometry ----------------------------------------------

def build_linear_scene(T, solution: Solution, res: int = 96) -> dict:
    """The unit circle/sphere and its image under A, plus invariant/singular directions.
    Shows *why* eigenvalues and singular values are the geometry: they are the scalings
    that turn the round object into the deformed one."""
    scene = _base(solution, ((-3, 3), (-3, 3)))
    A = T.A

    if T.rows == 2:
        theta = np.linspace(0, 2 * np.pi, res)
        circle = np.stack([np.cos(theta), np.sin(theta)])          # 2 x res
        image = A @ circle
        scene["layers"].append({
            "id": "unit_circle", "type": "curve", "step": 0, "label": "unit circle",
            "data": {"points": [[float(circle[0, k]), float(circle[1, k]), 0.0]
                                 for k in range(res)]}})
        scene["layers"].append({
            "id": "image_ellipse", "type": "curve", "step": 1,
            "label": "image A·(circle) — an ellipse",
            "data": {"points": [[float(image[0, k]), float(image[1, k]), 0.0]
                                 for k in range(res)]}})
        try:
            eig = solution.get("eigen").value
            arrows = []
            for p in eig["pairs"]:
                if abs(p["eigenvalue"][1]) > 1e-9:        # skip complex eigenvectors
                    continue
                lam = p["eigenvalue"][0]
                v = np.array([c[0] for c in p["eigenvector"]], dtype=float)
                v = v / np.linalg.norm(v)
                arrows.append({"origin": [0.0, 0.0, 0.0],
                               "vector": [float(v[0]), float(v[1]), 0.0],
                               "image": [float(lam * v[0]), float(lam * v[1]), 0.0],
                               "eigenvalue": float(lam)})
            scene["layers"].append({"id": "eigenvectors", "type": "eigenvectors", "step": 2,
                                    "label": "eigenvectors (invariant directions, scaled by λ)",
                                    "data": {"arrows": arrows}})
        except KeyError:
            pass

    elif T.rows == 3:
        nu, nv = 24, 48
        u = np.linspace(0, np.pi, nu)
        v = np.linspace(0, 2 * np.pi, nv)
        sphere = np.array([
            [[np.sin(uu) * np.cos(vv), np.sin(uu) * np.sin(vv), np.cos(uu)]
             for vv in v] for uu in u])                            # nu x nv x 3
        ell = sphere @ A.T
        scene["layers"].append({"id": "unit_sphere", "type": "param_surface", "step": 0,
                                "label": "unit sphere",
                                "data": {"grid": sphere.tolist()}})
        scene["layers"].append({"id": "image_ellipsoid", "type": "param_surface", "step": 1,
                                "label": "image A·(sphere) — an ellipsoid",
                                "data": {"grid": ell.tolist()}})
        try:
            svd = solution.get("svd").value
            U = np.array(svd["U"]); S = svd["singular_values"]
            arrows = [{"origin": [0.0, 0.0, 0.0],
                       "vector": [float(S[k] * U[0, k]), float(S[k] * U[1, k]),
                                  float(S[k] * U[2, k])],
                       "singular_value": float(S[k])} for k in range(3)]
            scene["layers"].append({"id": "singular_axes", "type": "vectors", "step": 2,
                                    "label": "principal axes (singular vectors × singular values)",
                                    "data": {"arrows": arrows}})
        except KeyError:
            pass
    return scene


# --- dynamical systems (ODEs) ------------------------------------------------

_EQUILIBRIUM_COLORS = (  # matched by substring, first hit wins
    ("stable spiral", "#2c7fb8"),
    ("unstable spiral", "#d7301f"),
    ("saddle-focus", "#d7301f"),
    ("stable node", "#2c7fb8"),
    ("unstable node", "#d7301f"),
    ("stable", "#2c7fb8"),
    ("unstable", "#d7301f"),
    ("source", "#d7301f"),
    ("sink", "#2c7fb8"),
    ("saddle", "#756bb1"),
    ("centre", "#31a354"),
    ("non-hyperbolic", "#999999"),
)


def _equilibrium_color(kind: str) -> str:
    k = kind.lower()
    for needle, color in _EQUILIBRIUM_COLORS:
        if needle in k:
            return color
    return "#cccccc"


def build_dynamics_scene(ds, solution: Solution, domain, res: int = 13) -> dict:
    """A phase portrait: the flow field, its equilibria (coloured by stability), and the
    integral curves that flow through it. In 2-D this lives in the phase plane (z = 0); in
    3-D (a Lorenz-type system) the trajectory is the attractor itself in space.

    Layers are step-tagged so the walkthrough reveals exactly a step's geometry: step 0 the
    flow field, step 1 the equilibria, step 3 the trajectories (step 2 — stability — and
    step 4 — sensitive dependence — re-read the geometry already shown rather than adding
    new meshes)."""
    dim = ds.dim
    scene = _base(solution, (domain[0], domain[1]))

    # step 0 — the flow field F(x)
    axes = [np.linspace(lo, hi, res if dim == 2 else max(4, res // 3)) for (lo, hi) in domain]
    arrows = []
    if dim == 2:
        for x in axes[0]:
            for y in axes[1]:
                v = ds.F_num([x, y])
                arrows.append({"origin": [float(x), float(y), 0.0],
                               "vector": [float(v[0]), float(v[1]), 0.0]})
    else:
        for x in axes[0]:
            for y in axes[1]:
                for z in axes[2]:
                    v = ds.F_num([x, y, z])
                    arrows.append({"origin": [float(x), float(y), float(z)],
                                   "vector": [float(v[0]), float(v[1]), float(v[2])]})
    scene["layers"].append({"id": "flow_field", "type": "vectors", "step": 0,
                            "label": "flow field ẋ = F(x)", "data": {"arrows": arrows}})

    # step 1 — equilibria, coloured by stability
    try:
        fps = solution.get("fixed_points").value
        pts = []
        for fp in fps:
            p = fp["point"]
            pos = [float(p[0]), float(p[1]), float(p[2]) if dim == 3 else 0.0]
            pts.append({"position": pos, "type": fp["type"],
                        "color": _equilibrium_color(fp["type"])})
        if pts:
            scene["layers"].append({"id": "fixed_points", "type": "points", "step": 1,
                                    "label": "equilibria F = 0 (colour = stability)",
                                    "data": {"points": pts}})
    except KeyError:
        pass

    # step 3 — trajectories (integral curves)
    for q in solution.quantities:
        if q.name.startswith("trajectory"):
            pts = [[float(c) for c in row] for row in q.value["points"]]
            scene["layers"].append({
                "id": q.name, "type": "polyline", "step": 3,
                "label": "trajectory (an integral curve of the flow)",
                "data": {"points": pts, "start": pts[0], "end": pts[-1]},
            })
    return scene
