"""Build a *lesson* from a verified solution — the pedagogy layer (G11, G12).

Where ``engine/scene.py`` turns a ``Solution`` into geometry and each solver records a short,
coarse ``steps`` list (one entry per computed quantity), this module turns the same verified
solution into a **fine-grained, readable walkthrough**: many small single-idea steps, with any
multi-stage calculation shown *stage by stage* (its intermediate results, not just its answer),
each step carrying the visual that matches it and text formatted to be read.

The output is a list of *lesson steps*, each a plain dict:

    {
      "id":      stable id (used to ground a per-step follow-up question, G13),
      "title":   short heading naming the one idea this step introduces,
      "reveal":  the scene layer-step to show (an integer that exists in scene["layers"]),
      "focus":   a feature name to fly the view to (or None),
      "focus_target": the pre-resolved [x,y,z] of that feature (or None),
      "quantity": the verified quantity this step is grounded in (or None for a setup step),
      "verified": whether it makes a claim backed by a verified quantity,
      "stage":   {"group","index","total"} when the step is one stage of a staged
                 calculation, else None,
      "lines":   an ordered list of readable blocks, each {"kind","text"} with kind in
                 {"say","math","calc","note"} — separated points, math shown as NOTATION,
                 never a wall of text (C-READABLE-OUTPUT),
    }

Every number in a lesson comes straight from the solution's *verified* quantities, so the
walkthrough is grounded by construction (C-GROUNDED-EXPLANATION); mathematics is only ever
*re-displayed* here (through ``notation``), never recomputed (C-VERIFIED-MATH). Deterministic
and offline (C-LOCAL). ``build_lesson`` never raises — an area it cannot decompose falls back
to the coarse steps, so the flow never breaks (G8).
"""

from __future__ import annotations

from .notation import to_notation, vec_notation, matrix_notation, MINUS
from .result import Solution


# --- small formatting helpers -------------------------------------------------

def _n(v, nd: int = 3) -> str:
    """A number formatted for reading: integers stay integers, else nd significant digits."""
    f = float(v)
    if abs(f) < 1e-12:
        f = 0.0
    s = str(int(round(f))) if abs(f - round(f)) < 1e-9 and abs(f) < 1e6 else f"{f:.{nd}g}"
    return s.replace("-", MINUS)


def _point(p, nd: int = 3) -> str:
    return "(" + ", ".join(_n(c, nd) for c in p) + ")"


def _complex(re: float, im: float, nd: int = 3) -> str:
    if abs(im) < 1e-7:
        return _n(re, nd)
    sign = "+" if im >= 0 else MINUS
    return f"{_n(re, nd)} {sign} {_n(abs(im), nd)}i"


def _say(t):    return {"kind": "say", "text": t}
def _math(t):   return {"kind": "math", "text": t}
def _calc(t):   return {"kind": "calc", "text": t}
def _note(t):   return {"kind": "note", "text": t}


class _L:
    """Accumulates lesson steps and assigns stable ids."""

    def __init__(self, area: str, layer_steps, targets):
        self.area = area
        self.steps: list[dict] = []
        self.layer_steps = sorted(set(layer_steps)) or [0]
        self.maxstep = self.layer_steps[-1]
        self.targets = targets           # feature-name -> [x,y,z]
        self._n = 0

    def reveal_at(self, want: int) -> int:
        """Clamp a desired reveal level to the nearest real layer step ≤ it (≥ 0)."""
        avail = [s for s in self.layer_steps if s <= want]
        return max(avail) if avail else self.layer_steps[0]

    def add(self, title, lines, *, reveal=0, focus=None, quantity=None,
            verified=False, stage=None, sid=None):
        self._n += 1
        step = {
            "id": sid or f"{self.area}-{self._n}",
            "title": title,
            "reveal": self.reveal_at(reveal),
            "focus": focus,
            "focus_target": self.targets.get(focus) if focus else None,
            "quantity": quantity,
            "verified": bool(verified and quantity),
            "stage": stage,
            "lines": [l for l in lines if l and l.get("text")],
        }
        self.steps.append(step)
        return step

    def full_picture(self):
        self.add("The full picture",
                 [_say("Every feature together — rotate, zoom, and explore the finished "
                       "visual, or ask a question about any step.")],
                 reveal=self.maxstep, focus=None, sid=f"{self.area}-full")


def _xyz(p) -> list:
    """A position as a 3-vector (2-D features live in the z = 0 plane)."""
    p = list(p) + [0.0, 0.0, 0.0]
    return [float(p[0]), float(p[1]), float(p[2])]


def _targets_from_scene(scene: dict) -> dict:
    """Pre-resolve feature names to 3-D positions from the verified scene geometry."""
    t: dict = {"origin": [0.0, 0.0, 0.0]}
    layers = {l.get("id"): l for l in scene.get("layers", [])}

    def pts(lid):
        l = layers.get(lid)
        return (l.get("data", {}) or {}).get("points", []) if l else []

    for p in pts("critical_points"):
        t.setdefault(p.get("type", "critical"), _xyz(p["position"]))
        t["a critical point"] = _xyz(p["position"])
    for lid in ("minimum", "constrained_optimum"):
        if pts(lid):
            t["the minimum"] = _xyz(pts(lid)[0]["position"])
            t["the optimum"] = _xyz(pts(lid)[0]["position"])
    fps = pts("fixed_points")
    for i, p in enumerate(fps):
        t[f"equilibrium {i}"] = _xyz(p["position"])
    if fps:
        t["an equilibrium"] = _xyz(fps[0]["position"])
    for l in scene.get("layers", []):
        if str(l.get("id", "")).startswith("trajectory"):
            end = (l.get("data", {}) or {}).get("end")
            if end:
                t["the trajectory"] = _xyz(end)
            break
    return t


# --- per-area lesson builders -------------------------------------------------

def _scalar(sol: Solution, scene: dict, L: _L, expr_src: str) -> None:
    L.add("The surface",
          [_say("Height above the plane is the value of f — hills are large values, "
                "valleys are small ones."),
           _math(f"f = {to_notation(expr_src)}")],
          reveal=0)

    if _has(sol, "gradient"):
        g = sol.get("gradient")
        L.add("The gradient ∇f",
              [_say("The gradient points in the direction of steepest increase; its length "
                    "is how steep the climb is."),
               _math(to_notation(g.display))],
              reveal=1, quantity="gradient", verified=True)
        L.add("Where the ground is level",
              [_say("A critical point is where the surface is flat in every direction — the "
                    "gradient vanishes there."),
               _math("∇f = 0")],
              reveal=1, quantity="gradient", verified=True)

    if _has(sol, "critical_points"):
        cps = sol.get("critical_points").value
        _intuition = {
            "minimum": "a minimum — the surface curves upward in every direction.",
            "maximum": "a maximum — the surface curves downward in every direction.",
            "saddle": "a saddle — up one way, down another.",
            "degenerate": "degenerate — the second-derivative test is inconclusive.",
        }
        if not cps:
            L.add("No critical points here",
                  [_say("The gradient never vanishes on this domain, so there are no flat "
                        "spots to classify.")],
                  reveal=1, quantity="critical_points", verified=True)
        for i, cp in enumerate(cps):
            grp = f"crit-{i}"
            L.add(f"A flat spot at {_point(cp['point'])}",
                  [_say("The gradient is zero here, so the surface is momentarily level."),
                   _calc(f"f = {_n(cp['f'])} at {_point(cp['point'])}")],
                  reveal=3, focus="a critical point", quantity="critical_points",
                  verified=True, stage={"group": grp, "index": 1, "total": 3},
                  sid=f"scalar-crit{i}-loc")
            eigs = cp.get("hessian_eigenvalues", [])
            L.add("Curvature — the Hessian eigenvalues",
                  [_say("The Hessian's eigenvalues are the curvatures along the surface's "
                        "principal directions."),
                   _calc("eigenvalues " + ", ".join(_n(e) for e in eigs))],
                  reveal=3, focus="a critical point", quantity="critical_points",
                  verified=True, stage={"group": grp, "index": 2, "total": 3},
                  sid=f"scalar-crit{i}-hess")
            L.add(f"So it is {cp['type']}",
                  [_say("Reading the signs: " + _intuition.get(cp["type"], cp["type"] + "."))],
                  reveal=3, focus="a critical point", quantity="critical_points",
                  verified=True, stage={"group": grp, "index": 3, "total": 3},
                  sid=f"scalar-crit{i}-type")


def _optimization(sol: Solution, scene: dict, L: _L, expr_src: str) -> None:
    L.add("The landscape to descend",
          [_say("We are looking for the lowest point of this surface by rolling downhill."),
           _math(f"f = {to_notation(expr_src)}")],
          reveal=0)
    if _has(sol, "gradient"):
        L.add("Downhill is −∇f",
              [_say("The negative gradient points in the direction of steepest descent — the "
                    "way the ball rolls."),
               _math(to_notation(sol.get("gradient").display))],
              reveal=1, quantity="gradient", verified=True)

    if _has(sol, "descent"):
        d = sol.get("descent").value
        fv = d["f_values"]
        idxs = _sample_indices(len(fv), 4)
        total = len(idxs) + 1
        L.add("Start rolling downhill",
              [_say("Gradient descent takes small steps against the gradient. Watch the "
                    "objective fall stage by stage."),
               _calc(f"start {_point(d['start'])}:  f = {_n(fv[0])}")],
              reveal=2, focus="the minimum", quantity="descent", verified=True,
              stage={"group": "descent", "index": 1, "total": total}, sid="opt-descent-0")
        for k, ix in enumerate(idxs, start=2):
            L.add(f"After {ix} steps",
                  [_calc(f"f = {_n(fv[ix])}"
                         + ("   (still falling)" if ix < len(fv) - 1 else ""))],
                  reveal=2, quantity="descent", verified=True,
                  stage={"group": "descent", "index": k, "total": total},
                  sid=f"opt-descent-{ix}")

    if _has(sol, "minimum"):
        m = sol.get("minimum").value
        eigs = m.get("hessian_eigenvalues", [])
        L.add(f"The minimum, at {_point(m['point'])}",
              [_say("Descent has settled where the gradient is essentially zero."),
               _calc(f"f = {_n(m['f'])},   ‖∇f‖ = {m.get('gradient_residual', 0):.1e}")],
              reveal=3, focus="the minimum", quantity="minimum", verified=True,
              stage={"group": "minimum", "index": 1, "total": 2}, sid="opt-min-loc")
        L.add("Why it is a true minimum",
              [_say("The Hessian is positive-definite here — the surface curves up in every "
                    "direction, so this is a genuine bottom, not a saddle."),
               _calc("Hessian eigenvalues " + ", ".join(_n(e) for e in eigs) + " (all > 0)")],
              reveal=3, focus="the minimum", quantity="minimum", verified=True,
              stage={"group": "minimum", "index": 2, "total": 2}, sid="opt-min-why")


def _constrained(sol: Solution, scene: dict, L: _L, f_src: str, g_src: str) -> None:
    L.add("The objective surface",
          [_say("We minimise f, but only along the constraint curve — not over the whole "
                "plane."),
           _math(f"minimise  f = {to_notation(f_src)}")],
          reveal=0)
    L.add("The constraint",
          [_say("The solution is forced to lie where g = 0."),
           _math(f"subject to  {to_notation(g_src)} = 0")],
          reveal=1)
    if _has(sol, "constrained_optimum"):
        o = sol.get("constrained_optimum").value
        L.add("Lagrange's condition",
              [_say("At the constrained optimum the level set of f is tangent to the "
                    "constraint, so their gradients line up."),
               _math("∇f = λ ∇g")],
              reveal=1, quantity="constrained_optimum", verified=True,
              stage={"group": "lagrange", "index": 1, "total": 3}, sid="con-cond")
        L.add(f"The tangency point",
              [_say("Solving that condition together with the constraint gives the optimum."),
               _calc(f"optimum {_point(o['point'])},   f = {_n(o['f'])}")],
              reveal=1, focus="the optimum", quantity="constrained_optimum", verified=True,
              stage={"group": "lagrange", "index": 2, "total": 3}, sid="con-point")
        L.add("The multiplier λ",
              [_say("λ measures how hard the constraint pushes — the rate f would change if "
                    "the constraint were relaxed."),
               _calc(f"λ = {_n(o['lambda'])}")],
              reveal=1, quantity="constrained_optimum", verified=True,
              stage={"group": "lagrange", "index": 3, "total": 3}, sid="con-lambda")


def _vector(sol: Solution, scene: dict, L: _L, comps, has_div_layer: bool) -> None:
    dstep, cstep = (1, 2) if has_div_layer else (0, 0)
    L.add("The vector field F",
          [_say("Every point carries an arrow — the field's value there. Think of it as the "
                "velocity of a fluid."),
           _math(f"F = {vec_notation(comps)}")],
          reveal=0)
    if _has(sol, "divergence"):
        dv = sol.get("divergence")
        val = _flt(dv.value)
        meaning = ("positive — the flow spreads outward, like a source."
                   if val is not None and val > 1e-9 else
                   "negative — the flow contracts inward, like a sink."
                   if val is not None and val < -1e-9 else
                   "zero — the flow neither expands nor compresses.")
        L.add("Divergence — local expansion",
              [_say("Divergence measures how much the field spreads out of each point."),
               _math(to_notation(_first(dv.value)) and f"div F = {to_notation(_first(dv.value))}"),
               _say("Here it is " + meaning)],
              reveal=dstep, quantity="divergence", verified=True)
    if _has(sol, "curl"):
        c = sol.get("curl")
        L.add("Curl — local rotation",
              [_say("Curl measures the field's tendency to rotate — a paddle wheel dropped in "
                    "would spin."),
               _math(f"curl F = {to_notation(_first(c.value))}")],
              reveal=cstep, quantity="curl", verified=True)


def _linalg(sol: Solution, scene: dict, L: _L, matrix, is3d: bool) -> None:
    L.add("The matrix as a transformation",
          [_say("A matrix is a linear map: it sends every vector to a new one, bending space "
                "in a fixed way."),
           _math(f"A = {matrix_notation(matrix)}")],
          reveal=0)
    if is3d:
        L.add("The unit sphere → an ellipsoid",
              [_say("A linear map turns the unit sphere into an ellipsoid — that shape is the "
                    "transformation made visible.")],
              reveal=1)
    else:
        L.add("The unit circle → an ellipse",
              [_say("A linear map turns the unit circle into an ellipse; how it is stretched "
                    "and turned tells you everything about A.")],
              reveal=1)

    if _has(sol, "determinant"):
        det = _flt(sol.get("determinant").value) or 0.0
        if abs(det) < 1e-12:
            mean = "zero — A flattens space onto a lower dimension (it is singular)."
        elif det < 0:
            mean = f"{_n(det)} — it scales area by {_n(abs(det))} and flips orientation."
        else:
            mean = f"{_n(det)} — it scales area by that factor and keeps orientation."
        L.add("Determinant — the area scale",
              [_say("The determinant is the factor by which the map scales area (or volume)."),
               _calc("det A = " + mean)],
              reveal=1, quantity="determinant", verified=True)

    if _has(sol, "eigen"):
        e = sol.get("eigen").value
        pairs = e.get("pairs", [])
        L.add("Invariant directions",
              [_say("Some directions are only stretched by the map, never rotated — its "
                    "eigenvectors.")],
              reveal=2, focus="origin", quantity="eigen", verified=True,
              stage={"group": "eigen", "index": 1, "total": 3}, sid="lin-eig-dir")
        L.add("The eigenvalues",
              [_calc("λ = " + ", ".join(_complex(p["eigenvalue"][0], p["eigenvalue"][1])
                                        for p in pairs))],
              reveal=2, quantity="eigen", verified=True,
              stage={"group": "eigen", "index": 2, "total": 3}, sid="lin-eig-val")
        why = ("This matrix is defective — fewer independent eigenvectors than eigenvalues, "
               "so it cannot be diagonalised (a shear is the classic case)."
               if e.get("defective") else
               "A vector along each eigenvector is simply scaled by its λ — the map acts like "
               "a stretch along those axes.")
        L.add("What the eigenvalues mean",
              [_say(why)],
              reveal=2, quantity="eigen", verified=True,
              stage={"group": "eigen", "index": 3, "total": 3}, sid="lin-eig-why")

    if _has(sol, "svd"):
        s = sol.get("svd").value
        sv = s.get("singular_values", [])
        L.add("Singular values — the semi-axes",
              [_say("The singular values are the lengths of the ellipsoid's semi-axes: how far "
                    "the map stretches along each principal direction."),
               _calc("σ = " + ", ".join(_n(v) for v in sv))],
              reveal=2, focus="origin", quantity="svd", verified=True,
              stage={"group": "svd", "index": 1, "total": 2}, sid="lin-svd-val")
        L.add("The principal axes",
              [_say("The largest σ is the most the map can stretch a unit vector; the smallest "
                    "is the most it can shrink one. Their directions are the singular vectors.")],
              reveal=2, quantity="svd", verified=True,
              stage={"group": "svd", "index": 2, "total": 2}, sid="lin-svd-axes")


def _dynamics(sol: Solution, scene: dict, L: _L, comps, varnames) -> None:
    dots = [f"{v}̇" for v in varnames]  # x with combining dot above → ẋ
    lines = [_say("An ODE system turns a vector field into motion: every point flows along F.")]
    for d, c in zip(dots, comps):
        lines.append(_math(f"{d} = {to_notation(c)}"))
    L.add("The system  ẋ = F(x)", lines, reveal=0, sid="dyn-system")
    L.add("The flow field",
          [_say("The arrows show the velocity F(x) at each point — the direction and speed a "
                "particle there would move.")],
          reveal=0, sid="dyn-flow")

    fps = sol.get("fixed_points").value if _has(sol, "fixed_points") else []
    eq_lines = [_say("Equilibria are the points where the flow stops — set every rate to zero "
                     "and solve F(x) = 0.")]
    if fps:
        for i, fp in enumerate(fps):
            eq_lines.append(_calc(f"{_point(fp['point'])} — {fp['type']}"))
    else:
        eq_lines.append(_note("No equilibria lie in the region shown."))
    L.add("Find the equilibria: F = 0", eq_lines,
          reveal=1, focus="an equilibrium", quantity="fixed_points",
          verified=_has(sol, "fixed_points"), sid="dyn-equilibria")

    stab = sol.get("stability").value if _has(sol, "stability") else []
    for i, e in enumerate(stab):
        grp = f"stab-{i}"
        J = e.get("jacobian")
        L.add(f"Jacobian at {_point(e['point'])}",
              [_say("Near an equilibrium the flow behaves like its linearisation — the "
                    "Jacobian J, the matrix of partial derivatives of F."),
               _calc("J = " + (matrix_notation(J) if J else "—"))],
              reveal=1, focus=f"equilibrium {i}", quantity="stability", verified=True,
              stage={"group": grp, "index": 1, "total": 3}, sid=f"dyn-stab{i}-jac")
        L.add("Its eigenvalues",
              [_say("The Jacobian's eigenvalues decide the local flow."),
               _calc("λ = " + ", ".join(_complex(v[0], v[1]) for v in e.get("eigenvalues", [])))],
              reveal=1, focus=f"equilibrium {i}", quantity="stability", verified=True,
              stage={"group": grp, "index": 2, "total": 3}, sid=f"dyn-stab{i}-eig")
        L.add(f"Classification: {e['type']}",
              [_say("Negative real parts pull the flow in, positive push it out, and an "
                    "imaginary part makes it spiral. Reading the signs gives a "
                    + e["type"] + ".")],
              reveal=1, focus=f"equilibrium {i}", quantity="stability", verified=True,
              stage={"group": grp, "index": 3, "total": 3}, sid=f"dyn-stab{i}-type")

    traj = _first_traj(sol)
    if traj is not None:
        t = traj.value
        L.add("Integrate a trajectory",
              [_say("Starting from one point and following the flow forward in time traces an "
                    "integral curve — the actual path a particle takes."),
               _calc(f"from {_point(t['x0'])} to {_point(t['final_point'])} "
                     f"over t ∈ [{_n(t['t_span'][0])}, {_n(t['t_span'][1])}]")],
              reveal=3, focus="the trajectory", quantity=traj.name, verified=True,
              sid="dyn-trajectory")

    if _has(sol, "separation"):
        s = sol.get("separation").value
        lam = s["finite_time_lyapunov"]
        chaotic = lam > 1e-3
        L.add("Two nearby starts",
              [_say("To test for chaos, launch a second trajectory a hair away from the first."),
               _calc(f"initial gap  δ₀ = {s['initial_separation']:.1e}")],
              reveal=3, focus="the trajectory", quantity="separation", verified=True,
              stage={"group": "chaos", "index": 1, "total": 3}, sid="dyn-sep-start")
        L.add("They pull apart",
              [_calc(f"gap → {_n(s['final_separation'])} by t = {_n(s['t_span'][1])}")],
              reveal=3, quantity="separation", verified=True,
              stage={"group": "chaos", "index": 2, "total": 3}, sid="dyn-sep-grow")
        L.add("Positive Lyapunov ⇒ chaos" if chaotic else "Rate not positive ⇒ regular",
              [_say(("Nearby states separate exponentially — the hallmark of chaos: the "
                     "long-term path is unpredictable though every step is deterministic."
                     if chaotic else
                     "Nearby trajectories stay close, so the motion is regular, not chaotic.")),
               _calc(f"mean rate ≈ {lam:+.3f} per unit time")],
              reveal=3, quantity="separation", verified=True,
              stage={"group": "chaos", "index": 3, "total": 3}, sid="dyn-sep-rate")


# --- dispatch -----------------------------------------------------------------

def _has(sol: Solution, name: str) -> bool:
    try:
        return sol.get(name).verified
    except KeyError:
        return False


def _flt(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _first(v):
    """A symbolic quantity's value is a list of component source strings; take the first."""
    if isinstance(v, (list, tuple)):
        return v[0] if v else ""
    return v


def _sample_indices(n: int, k: int) -> list[int]:
    """k interior/end sample indices of a length-n sequence (skip 0, always include n-1)."""
    if n <= 1:
        return []
    import numpy as np
    raw = np.linspace(1, n - 1, min(k, n - 1))
    out = sorted({int(round(v)) for v in raw})
    if out and out[-1] != n - 1:
        out[-1] = n - 1
    return out


def _first_traj(sol: Solution):
    for q in sol.quantities:
        if q.name.startswith("trajectory") and q.verified:
            return q
    return None


def build_lesson(sol: Solution, scene: dict, descriptor: dict | None = None) -> list[dict]:
    """Return the fine-grained, staged, readable walkthrough for a solved problem.

    Never raises: on any trouble it returns the solution's coarse ``steps`` unchanged so the
    walkthrough still works (G8)."""
    try:
        d = descriptor or {}
        layer_steps = [l.get("step", 0) for l in scene.get("layers", [])]
        L = _L(sol.area, layer_steps, _targets_from_scene(scene))

        if sol.area == "scalar-fields":
            _scalar(sol, scene, L, d.get("expr", ""))
        elif sol.area == "optimization":
            if d.get("subtype") == "constrained":
                _constrained(sol, scene, L, d.get("f", ""), d.get("g", ""))
            else:
                _optimization(sol, scene, L, d.get("expr", ""))
        elif sol.area == "vector-fields":
            has_div = any(l.get("id") == "divergence_field" for l in scene.get("layers", []))
            _vector(sol, scene, L, d.get("components", []), has_div)
        elif sol.area == "linear-algebra":
            mat = d.get("matrix", [[1, 0], [0, 1]])
            _linalg(sol, scene, L, mat, is3d=len(mat) == 3)
        elif sol.area == "dynamical-systems":
            _dynamics(sol, scene, L, d.get("components", []), d.get("vars", ["x", "y"]))
        else:
            return list(scene.get("steps", []))

        if not L.steps:
            return list(scene.get("steps", []))
        L.full_picture()
        return L.steps
    except Exception:
        return list(scene.get("steps", []))
