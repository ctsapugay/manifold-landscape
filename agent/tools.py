"""The tool registry — the deterministic tools the agent orchestrates.

Each tool wraps the verification-backed engine: it takes structured input, runs the
relevant solver, and returns the verified quantities plus the renderable scene. The
mathematics is done here, by the engine, never by the model (C-VERIFIED-MATH); a tool that
cannot compute its result returns an error rather than inventing one, which is how the agent
declines or degrades gracefully (G2, G8).

The registry also exposes Anthropic-style JSON schemas (``schemas()``) so the same tools can
be handed to Claude for real tool-use, and are self-describing for the offline interpreter.

Scene-driving is a tool too: ``focus_view`` resolves a named feature ("the minimum", "the
saddle", "the attractor") to a camera/highlight directive using the *verified* geometry of
the current problem — the mechanism behind the tutor driving the visualization (G5).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# The engine dispatch already returns only verified quantities; reuse it rather than
# re-deriving solutions here.
from web.problems import solve_descriptor, solution_for


@dataclass
class ToolResult:
    ok: bool
    tool: str
    area: str = ""
    descriptor: dict | None = None
    scene: dict | None = None
    quantities: list[dict] = field(default_factory=list)
    directive: dict | None = None
    summary: str = ""
    error: str = ""

    @property
    def provenance(self) -> list[str]:
        return [q.get("provenance", "") for q in self.quantities]

    @property
    def produced(self) -> list[str]:
        return [q.get("name", "") for q in self.quantities]

    @property
    def all_verified(self) -> bool:
        return bool(self.quantities) and all(
            q.get("verification", {}).get("passed") for q in self.quantities
        )


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    fn: Callable[..., ToolResult]

    def schema(self) -> dict:
        return {"name": self.name, "description": self.description,
                "input_schema": self.input_schema}


def _from_descriptor(tool: str, descriptor: dict) -> ToolResult:
    """Solve a descriptor through the engine and package the verified scene."""
    try:
        scene = solve_descriptor(descriptor)
    except Exception as exc:  # engine could not solve it — decline gracefully, never crash
        return ToolResult(ok=False, tool=tool, area=descriptor.get("area", ""),
                          descriptor=descriptor, error=f"{type(exc).__name__}: {exc}")
    q = scene.get("quantities", [])
    summary = "; ".join(x["display"] for x in q[:3])
    return ToolResult(ok=True, tool=tool, area=scene.get("area", ""), descriptor=descriptor,
                      scene=scene, quantities=q, summary=summary)


# --- individual tools --------------------------------------------------------


def _t_scalar(expr: str, variables=("x", "y"), domain=None, **_) -> ToolResult:
    d = {"area": "scalar-fields", "id": "agent", "title": f"f = {expr}", "expr": expr,
         "vars": list(variables)}
    if domain:
        d["domain"] = domain
    return _from_descriptor("solve_scalar_field", d)


def _t_optimization(expr: str, start=None, lr=None, steps=None, variables=("x", "y"),
                    domain=None, **_) -> ToolResult:
    d = {"area": "optimization", "id": "agent", "title": f"minimize f = {expr}",
         "expr": expr, "vars": list(variables)}
    if start is not None:
        d["start"] = start
    if lr is not None:
        d["lr"] = lr
    if steps is not None:
        d["steps"] = steps
    if domain:
        d["domain"] = domain
    return _from_descriptor("solve_optimization", d)


def _t_constrained(objective: str, constraint: str, variables=("x", "y"), **_) -> ToolResult:
    d = {"area": "optimization", "subtype": "constrained", "id": "agent",
         "title": f"minimize {objective} s.t. {constraint} = 0",
         "f": objective, "g": constraint, "vars": list(variables)}
    return _from_descriptor("solve_constrained_optimization", d)


def _t_vector(components, variables, **_) -> ToolResult:
    d = {"area": "vector-fields", "id": "agent",
         "title": f"F = ({', '.join(components)})",
         "components": list(components), "vars": list(variables)}
    return _from_descriptor("solve_vector_field", d)


def _t_linalg(matrix, want=None, **_) -> ToolResult:
    d = {"area": "linear-algebra", "id": "agent", "title": f"A = {matrix}", "matrix": matrix}
    if want:
        d["want"] = list(want)
    return _from_descriptor("solve_linear_algebra", d)


def _t_dynamics(components, variables, domain=None, trajectories=None, t_span=None,
                samples=None, chaotic=False, **_) -> ToolResult:
    d = {"area": "dynamical-systems", "id": "agent",
         "title": f"ẋ = ({', '.join(components)})",
         "components": list(components), "vars": list(variables), "chaotic": bool(chaotic)}
    if domain:
        d["domain"] = domain
    if trajectories:
        d["trajectories"] = trajectories
    if t_span:
        d["t_span"] = t_span
    if samples:
        d["samples"] = samples
    return _from_descriptor("solve_dynamical_system", d)


def _resolve_feature(scene: dict, feature: str, index: int = 0):
    """Find the 3-D position of a named feature in a solved scene, from verified data."""
    feature = (feature or "").lower()
    layers = {l["id"]: l for l in scene.get("layers", [])}

    def points_of(layer_id):
        l = layers.get(layer_id)
        return l["data"]["points"] if l else []

    # critical points / optima (scalar & optimization)
    if any(k in feature for k in ("min", "bottom", "optimum", "optima")):
        for lid in ("minimum", "constrained_optimum", "critical_points"):
            for p in points_of(lid):
                if lid != "critical_points" or p.get("type") == "minimum":
                    return p["position"], lid
    if "max" in feature:
        for p in points_of("critical_points"):
            if p.get("type") == "maximum":
                return p["position"], "critical_points"
    if "saddle" in feature:
        for p in points_of("critical_points"):
            if p.get("type") == "saddle":
                return p["position"], "critical_points"
    # dynamical-systems equilibria / attractor
    if any(k in feature for k in ("equilibri", "fixed", "rest point", "steady")):
        pts = points_of("fixed_points")
        if pts:
            return pts[min(index, len(pts) - 1)]["position"], "fixed_points"
    if any(k in feature for k in ("attractor", "trajector", "orbit", "flow", "curve")):
        for l in scene.get("layers", []):
            if l["id"].startswith("trajectory"):
                return l["data"]["end"], l["id"]
    if "origin" in feature:
        return [0.0, 0.0, 0.0], None
    return None, None


def _t_focus(ctx, feature: str, index: int = 0, **_) -> ToolResult:
    scene = (ctx or {}).get("current_scene")
    if not scene:
        return ToolResult(ok=False, tool="focus_view", error="no current problem to focus on")
    pos, layer = _resolve_feature(scene, feature, index)
    if pos is None:
        return ToolResult(ok=False, tool="focus_view",
                          error=f"could not locate feature {feature!r} in the current scene")
    directive = {"type": "focus", "target": [float(c) for c in pos],
                 "highlight_layer": layer, "label": feature}
    return ToolResult(ok=True, tool="focus_view", area=scene.get("area", ""),
                      directive=directive, summary=f"focus on {feature} at {pos}")


class ToolRegistry:
    """The deterministic tools available to the agent, with their Anthropic schemas."""

    def __init__(self) -> None:
        num = {"type": "number"}
        self._tools: dict[str, Tool] = {}
        self._add(Tool(
            "solve_scalar_field",
            "Analyze a scalar field f(x,y) as a surface: its gradient, Hessian, and critical "
            "points (minima/maxima/saddles). Use for 'f = ...', surfaces, gradients, critical "
            "points.",
            {"type": "object", "properties": {
                "expr": {"type": "string", "description": "f as a Python/SymPy expression, e.g. 'x**2 + y**2'"},
                "variables": {"type": "array", "items": {"type": "string"}, "default": ["x", "y"]},
                "domain": {"type": "array", "items": {"type": "array", "items": num}},
            }, "required": ["expr"]}, _t_scalar))
        self._add(Tool(
            "solve_optimization",
            "Analyze an optimization landscape f(x,y): run gradient descent to a minimum and "
            "report the minimum. Use for 'minimize ...', gradient descent, descent trajectories.",
            {"type": "object", "properties": {
                "expr": {"type": "string"},
                "variables": {"type": "array", "items": {"type": "string"}, "default": ["x", "y"]},
                "start": {"type": "array", "items": num},
                "lr": num, "steps": {"type": "integer"},
                "domain": {"type": "array", "items": {"type": "array", "items": num}},
            }, "required": ["expr"]}, _t_optimization))
        self._add(Tool(
            "solve_constrained_optimization",
            "Minimize an objective subject to an equality constraint g=0, via Lagrange "
            "multipliers. Use for 'minimize f subject to g = 0'.",
            {"type": "object", "properties": {
                "objective": {"type": "string"},
                "constraint": {"type": "string", "description": "g written so that g = 0 is the constraint, e.g. 'x + y - 1'"},
                "variables": {"type": "array", "items": {"type": "string"}, "default": ["x", "y"]},
            }, "required": ["objective", "constraint"]}, _t_constrained))
        self._add(Tool(
            "solve_vector_field",
            "Analyze a vector field F: its divergence (local expansion) and curl (local "
            "rotation), in 2-D or 3-D. Use for 'F = (P, Q)', divergence, curl, flux, rotation.",
            {"type": "object", "properties": {
                "components": {"type": "array", "items": {"type": "string"}},
                "variables": {"type": "array", "items": {"type": "string"}},
            }, "required": ["components", "variables"]}, _t_vector))
        self._add(Tool(
            "solve_linear_algebra",
            "Analyze a matrix as a geometric transformation: determinant (area/volume scale), "
            "eigenvalues/eigenvectors (invariant directions), or SVD (sphere→ellipsoid). Use "
            "for a matrix, eigenvalues, determinant, singular values.",
            {"type": "object", "properties": {
                "matrix": {"type": "array", "items": {"type": "array", "items": num}},
                "want": {"type": "array", "items": {"type": "string"},
                         "description": "any of 'determinant', 'eigen', 'svd'"},
            }, "required": ["matrix"]}, _t_linalg))
        self._add(Tool(
            "solve_dynamical_system",
            "Analyze an autonomous ODE system ẋ = F(x): equilibria (F=0), their stability from "
            "the Jacobian (sink/source/saddle/spiral/centre), integral-curve trajectories, and "
            "— if chaotic — a sensitive-dependence (Lyapunov) measurement. Use for phase "
            "portraits, x'=..., stability, chaos, the Lorenz system.",
            {"type": "object", "properties": {
                "components": {"type": "array", "items": {"type": "string"},
                               "description": "the right-hand sides f_i of ẋ_i = f_i(x)"},
                "variables": {"type": "array", "items": {"type": "string"}},
                "domain": {"type": "array", "items": {"type": "array", "items": num}},
                "trajectories": {"type": "array", "items": {"type": "array", "items": num}},
                "t_span": {"type": "array", "items": num},
                "samples": {"type": "integer"},
                "chaotic": {"type": "boolean"},
            }, "required": ["components", "variables"]}, _t_dynamics))
        self._add(Tool(
            "focus_view",
            "Drive the 3-D view to a named feature of the CURRENT solved problem, to draw the "
            "user's attention while explaining. feature is e.g. 'the minimum', 'the saddle', "
            "'the attractor', 'an equilibrium'. Only meaningful after a problem is solved.",
            {"type": "object", "properties": {
                "feature": {"type": "string"},
                "index": {"type": "integer", "default": 0},
            }, "required": ["feature"]}, _t_focus))

    def _add(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def names(self) -> list[str]:
        return list(self._tools)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict]:
        return [t.schema() for t in self._tools.values()]

    def run(self, name: str, tool_input: dict, ctx: dict | None = None) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(ok=False, tool=name, error=f"no such tool: {name}")
        kwargs = dict(tool_input or {})
        try:
            if name == "focus_view":
                return tool.fn(ctx, **kwargs)
            return tool.fn(**kwargs)
        except TypeError as exc:
            return ToolResult(ok=False, tool=name, error=f"bad tool input: {exc}")
