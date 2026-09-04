"""Interpreting an arbitrary request into a plan the tools can execute.

This is the deterministic reading of the user's input — the interpretation the offline brain
uses (and the graceful fallback when Claude is unavailable). It accepts the three input
styles the tool promises: a typed **equation** ('f = x^2 - y^2', 'F = (-y, x)', '[[2,1],
[1,2]]', "x' = y, y' = -x"), a **word problem** ('minimize x squared plus y squared subject
to x + y = 1'), and an **open conceptual** request ('show me an example of chaos', 'what
does a saddle look like'). It returns a structured ``Interpretation`` naming which tool to
call with which input, or a graceful decline that points at the nearest in-scope idea.

Expressions are parsed forgivingly (implicit multiplication, '^' for powers) and re-emitted
in the engine's canonical form, so the tools always receive clean input. Nothing here
computes mathematics — it only decides *what to ask the tools for*.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

_TRANSFORMS = standard_transformations + (convert_xor, implicit_multiplication_application)

# words that clearly belong to another domain — used to decline honestly
_OUT_OF_SCOPE = (
    ("integral", "integrate", "antiderivative", "∫"),
    ("probability", "statistic", "bayes", "random variable", "distribution"),
    ("partial differential", "pde", "heat equation", "wave equation", "navier"),
    ("prime number", "factorial", "combinatoric", "number theory"),
    ("weather", "stock", "recipe", "translate"),
    ("prove", "theorem", "proof by"),
)


@dataclass
class Interpretation:
    action: str  # "solve" | "chat" | "focus" | "animate" | "simulate" | "decline"
    tool: str = ""
    tool_input: dict = field(default_factory=dict)
    question: str = ""
    focus_feature: str = ""   # when a chat question also warrants a view move (G5)
    note: str = ""            # human-readable interpretation, shown in the trace
    reason: str = ""          # when declining
    suggestion: str = ""      # nearest in-scope idea, when declining
    out_of_scope: bool = False  # a decline because the request is outside the five areas


# --- expression helpers ------------------------------------------------------


def _clean(s: str) -> str:
    return (s.replace("×", "*").replace("·", "*").replace("−", "-")
            .replace("^", "**").strip())


def canon(expr: str, allowed: set[str]) -> str | None:
    """Parse ``expr`` forgivingly and re-emit it canonically, or None if it isn't a valid
    expression over ``allowed`` variables."""
    try:
        locals_ = {v: sp.Symbol(v, real=True) for v in ("x", "y", "z", "t")}
        parsed = parse_expr(_clean(expr).replace("**", "^"), transformations=_TRANSFORMS,
                            local_dict=locals_, evaluate=True)
    except Exception:
        return None
    syms = {str(s) for s in parsed.free_symbols}
    if not syms <= allowed:
        return None
    if parsed.free_symbols == set() and not re.search(r"[a-zA-Z]", str(parsed)):
        # a bare constant is not a field/surface worth rendering
        pass
    return str(parsed)


def _num_word_cleanup(text: str) -> str:
    """Turn a few common word-problem phrasings into symbols the parser understands."""
    t = text
    subs = [
        (r"\bsquared\b", "^2"), (r"\bcubed\b", "^3"),
        (r"\bplus\b", "+"), (r"\bminus\b", "-"), (r"\btimes\b", "*"),
        (r"\bdivided by\b", "/"),
        (r"\bthe function\b", "f ="), (r"\bthe surface\b", "f ="),
    ]
    for pat, rep in subs:
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)
    return t


# --- structural detectors ----------------------------------------------------


def _find_matrix(text: str):
    m = re.search(r"\[\s*\[.*?\]\s*\]", text, re.DOTALL)
    if not m:
        return None
    try:
        val = ast.literal_eval(m.group(0))
    except Exception:
        return None
    if (isinstance(val, list) and val and all(isinstance(r, list) for r in val)
            and len({len(r) for r in val}) == 1
            and all(isinstance(x, (int, float)) for r in val for x in r)):
        return val
    return None


_ODE_LINE = re.compile(
    r"(?:d\s*)?([xyz])\s*(?:/\s*d\s*t|dot|'|’|̇)\s*=\s*(.+?)(?=(?:[,;\n]|(?:\band\b))|$)",
    re.IGNORECASE)


def _find_ode(text: str):
    """Parse 'x' = ..., y' = ...' / 'dx/dt = ...' style systems. Returns (vars, components)."""
    if not re.search(r"[xyz]\s*(?:'|’|dot|/\s*d\s*t|̇)\s*=", text, re.IGNORECASE):
        return None
    found: dict[str, str] = {}
    for var, rhs in _ODE_LINE.findall(text):
        found.setdefault(var.lower(), rhs.strip())
    if not found:
        return None
    order = [v for v in ("x", "y", "z") if v in found]
    allowed = set(order)
    comps = []
    for v in order:
        c = canon(found[v], allowed)
        if c is None:
            return None
        comps.append(c)
    return order, comps


def _find_vector_field(text: str):
    """Parse 'F = (P, Q[, R])' or a bare tuple of expressions. Returns (vars, components)."""
    m = re.search(r"=\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)", text)
    if not m:
        m = re.search(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*$", text.strip())
    if not m:
        return None
    parts = _split_top(m.group(1))
    if len(parts) not in (2, 3):
        return None
    order = ["x", "y", "z"][: len(parts)]
    allowed = set(order)
    comps = []
    for p in parts:
        c = canon(p, allowed)
        if c is None:
            return None
        comps.append(c)
    return order, comps


def _split_top(s: str) -> list[str]:
    """Split on top-level commas (not inside parentheses)."""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _extract_expr_after_eq(text: str) -> str:
    """Everything after the first '=' (or the whole text if none)."""
    return text.split("=", 1)[1] if "=" in text else text


_LEAD_RE = re.compile(
    r"^\s*(?:please\s+|can you\s+|could you\s+|show me\s+|give me\s+|find\s+|compute\s+"
    r"|calculate\s+|plot\s+|graph\s+|analy[sz]e\s+|solve\s+|minimi[sz]e\s+|maximi[sz]e\s+"
    r"|optimi[sz]e\s+|gradient descent on\s+|descend\s+|the minimum of\s+|the maximum of\s+"
    r"|the function\s+|the surface\s+|of\s+)+", re.IGNORECASE)
_TRAIL_RE = re.compile(
    r"\b(?:start(?:ing)?|from\b|over\b|on the domain|with a learning|and\b|,)", re.IGNORECASE)
# 'what are the critical points of <expr>' / 'the gradient of <expr>' → keep only <expr>
_FEATURE_OF_RE = re.compile(
    r"^.*?\b(?:gradient|critical points?|hessian|minim\w*|maxim\w*|extrema|divergence|curl"
    r"|eigenvalues?|eigenvectors?|determinant|singular values?|surface|graph|plot|field)\b"
    r"[^=]*?\bof\b\s+", re.IGNORECASE)


def _math_core(text: str) -> str:
    """Strip leading verbs ('minimize', 'plot', 'the critical points of', …) and trailing
    clauses ('starting at …', 'and find …') so what remains is the bare expression."""
    t = _FEATURE_OF_RE.sub("", text)
    t = _LEAD_RE.sub("", t)
    t = _TRAIL_RE.split(t, maxsplit=1)[0]
    return t.strip()


def _find_start(text: str):
    m = re.search(r"start(?:ing)?\s*(?:at|from)?\s*\(?\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)?",
                  text, re.IGNORECASE)
    return [float(m.group(1)), float(m.group(2))] if m else None


# --- conceptual library ------------------------------------------------------

def _lorenz():
    return "solve_dynamical_system", {
        "components": ["10*(y - x)", "x*(28 - z) - y", "x*y - 8*z/3"],
        "variables": ["x", "y", "z"], "domain": [[-25, 25], [-30, 30], [0, 50]],
        "trajectories": [[1.0, 1.0, 1.0]], "t_span": [0, 40], "samples": 4000,
        "chaotic": True}

_CONCEPTUAL = [
    (("chaos", "chaotic", "lorenz", "butterfly", "strange attractor"), _lorenz, "the Lorenz system — the canonical example of deterministic chaos"),
    (("pendulum",), lambda: ("solve_dynamical_system", {
        "components": ["y", "-sin(x)"], "variables": ["x", "y"], "domain": [[-4, 4], [-3, 3]],
        "trajectories": [[0.0, 1.0], [0.0, 2.4], [2.5, 0.0]], "t_span": [0, 14], "samples": 1200}),
     "the undamped pendulum — a centre at rest, saddles at the top"),
    (("limit cycle", "van der pol", "vanderpol"), lambda: ("solve_dynamical_system", {
        "components": ["y", "2*(1 - x**2)*y - x"], "variables": ["x", "y"], "domain": [[-4, 4], [-4, 4]],
        "trajectories": [[0.1, 0.1], [3.0, 0.0]], "t_span": [0, 20], "samples": 2000}),
     "the Van der Pol oscillator — trajectories spiral onto a limit cycle"),
    (("spiral", "stable equilibrium", "phase portrait"), lambda: ("solve_dynamical_system", {
        "components": ["y", "-x - y"], "variables": ["x", "y"], "domain": [[-3, 3], [-3, 3]],
        "trajectories": [[2.5, 0.0], [-2.0, 1.5]], "t_span": [0, 18], "samples": 1500}),
     "a damped linear system — a stable spiral into the origin"),
    (("monkey saddle",), lambda: ("solve_scalar_field", {"expr": "x**3 - 3*x*y**2"}),
     "the monkey saddle f = x³ − 3xy²"),
    (("rosenbrock", "banana valley"), lambda: ("solve_optimization", {
        "expr": "(1 - x)**2 + 100*(y - x**2)**2", "start": [-1.0, 1.0], "lr": 0.001,
        "steps": 200, "domain": [[-2, 2], [-1, 3]]}),
     "the Rosenbrock 'banana' valley — a hard optimization landscape"),
    (("gradient descent", "optimization landscape", "descend"), lambda: ("solve_optimization", {
        "expr": "x**2 + 3*y**2", "start": [3.0, 2.0], "lr": 0.1, "steps": 80}),
     "gradient descent down an anisotropic bowl f = x² + 3y²"),
    (("constrained", "lagrange"), lambda: ("solve_constrained_optimization", {
        "objective": "x**2 + y**2", "constraint": "x + y - 1"}),
     "a constrained optimum: minimize x² + y² on the line x + y = 1"),
    (("saddle",), lambda: ("solve_scalar_field", {"expr": "x**2 - y**2"}),
     "the saddle surface f = x² − y²"),
    (("paraboloid", "bowl", "convex", "minimum"), lambda: ("solve_scalar_field", {"expr": "x**2 + y**2"}),
     "the paraboloid f = x² + y² — a single minimum"),
    (("ripple", "wave surface", "sinusoid"), lambda: ("solve_scalar_field", {
        "expr": "sin(x)*cos(y)", "domain": [[-3.14159, 3.14159], [-3.14159, 3.14159]]}),
     "f = sin(x)·cos(y) — a field of alternating peaks and pits"),
    (("rotation field", "curl", "vortex", "swirl", "whirl", "rotating", "rotational"),
     lambda: ("solve_vector_field", {"components": ["-y", "x"], "variables": ["x", "y"]}),
     "the rotational field F = (−y, x) — curl without divergence"),
    (("source", "outflow", "outward flow", "expanding field"),
     lambda: ("solve_vector_field", {"components": ["x", "y"], "variables": ["x", "y"]}),
     "the source field F = (x, y) — divergence without curl"),
    (("sink", "inflow", "inward flow"),
     lambda: ("solve_vector_field", {"components": ["-x", "-y"], "variables": ["x", "y"]}),
     "the sink field F = (−x, −y) — inward flow"),
    (("shear",), lambda: ("solve_linear_algebra", {"matrix": [[1, 1], [0, 1]]}),
     "a shear matrix [[1,1],[0,1]] — non-diagonalizable"),
    (("rotation matrix",), lambda: ("solve_linear_algebra", {"matrix": [[0, -1], [1, 0]]}),
     "a 90° rotation matrix [[0,−1],[1,0]] — complex eigenvalues"),
    (("singular value", "svd", "ellipsoid"), lambda: ("solve_linear_algebra", {
        "matrix": [[1, 2, 0], [0, 1, 2], [2, 0, 1]], "want": ["svd"]}),
     "the SVD of a 3×3 matrix — the unit sphere mapped to an ellipsoid"),
    (("eigen", "invariant direction"), lambda: ("solve_linear_algebra", {"matrix": [[2, 1], [1, 2]]}),
     "a symmetric matrix [[2,1],[1,2]] — real eigenvalues and orthogonal eigenvectors"),
    (("determinant", "area scale", "volume scale"),
     lambda: ("solve_linear_algebra", {"matrix": [[2, 1], [1, 3]]}),
     "the determinant of [[2,1],[1,3]] as an area scale factor"),
    (("divergence",), lambda: ("solve_vector_field", {"components": ["x", "y"], "variables": ["x", "y"]}),
     "the source field F = (x, y), whose divergence is positive everywhere"),
]

# motion / simulation cues (G22, G23). A default multi-basin landscape lets a bare
# "run a simulation of which basin wins" work with no problem posed yet.
_ANIMATE_WORDS = ("animate", "play the", "play it", "play back", "watch it move",
                  "watch the motion", "show the motion", "set it moving", "make it move",
                  "run the trajectory", "in motion")
_SIMULATE_WORDS = ("simulate", "simulation", "sweep", "multi-start", "multistart",
                   "multiple starts", "many starts", "which basin", "monte carlo",
                   "run it many", "run many")
_SWEEP_DEFAULT_EXPR = "(x**2 - 1)**2 + 0.3*x + y**2"  # a tilted double well: a clear winner

_FOCUS_WORDS = ("zoom", "focus", "look at", "point at", "highlight", "take me to",
                "center on", "centre on", "go to")
_FOCUS_FEATURES = ("minimum", "min", "maximum", "max", "saddle", "attractor",
                   "equilibrium", "fixed point", "origin", "critical point",
                   "optimum", "optima")


def _focus_feature_in(text: str) -> str:
    for feat in _FOCUS_FEATURES:
        if feat in text:
            return feat
    return ""


# --- top-level interpret -----------------------------------------------------


def interpret(text: str, has_current: bool = False) -> Interpretation:
    raw = (text or "").strip()
    if not raw:
        return Interpretation("decline", reason="empty request",
                              suggestion="try 'f = x^2 - y^2' or 'show me an example of chaos'")
    low = raw.lower()

    # 0) A simulation / sweep request — may carry its own expression, use the current
    #    problem, or fall back to a canonical multi-basin landscape (G23). Checked before
    #    problem detection so "run a sweep on f = ..." simulates rather than plain-solves.
    if any(w in low for w in _SIMULATE_WORDS):
        return _interpret_simulation(raw, low, has_current)

    # 0b) An animation / playback request on the current problem (G22).
    if has_current and any(w in low for w in _ANIMATE_WORDS):
        feat = _focus_feature_in(low)
        return Interpretation("animate", tool="animate_motion",
                              tool_input={"feature": feat} if feat else {},
                              note="play the verified motion in the view")

    # 1) A new, explicitly-typed problem always takes precedence.
    solved = _detect_problem(raw, low)
    if solved is not None:
        return solved

    # 2) Follow-up on the current problem: a view move or a grounded question.
    if has_current:
        feat = _focus_feature_in(low)
        if any(w in low for w in _FOCUS_WORDS) and feat:
            return Interpretation("focus", tool="focus_view", tool_input={"feature": feat},
                                  note=f"focus the view on {feat}")
        if _looks_like_question(low) or feat:
            return Interpretation("chat", question=raw, focus_feature=feat,
                                  note="answer from the current problem's verified state")

    # 3) A conceptual request with no explicit math.
    concept = _detect_conceptual(low)
    if concept is not None:
        return concept

    # 4) Out of scope or unparseable — decline gracefully.
    return _decline(low)


def _detect_problem(raw: str, low: str) -> Interpretation | None:
    prepped = _num_word_cleanup(raw)

    # matrix → linear algebra
    mat = _find_matrix(prepped)
    if mat is not None:
        want = None
        if any(k in low for k in ("singular", "svd", "ellipsoid")):
            want = ["svd"]
        elif "eigen" in low and "determinant" not in low:
            want = ["eigen"]
        elif "determinant" in low and "eigen" not in low:
            want = ["determinant"]
        ti = {"matrix": mat}
        if want:
            ti["want"] = want
        return Interpretation("solve", "solve_linear_algebra", ti,
                              note="a matrix as a geometric transformation")

    # ODE system → dynamical systems
    ode = _find_ode(prepped)
    if ode is not None:
        order, comps = ode
        chaotic = len(comps) == 3
        dom = [[-3, 3]] * len(order)
        traj = ([[1.0] * len(order)] if len(order) == 3
                else [[1.2, 0.4], [-1.0, 0.9], [0.4, 1.4]])
        ti = {"components": comps, "variables": order, "domain": dom,
              "trajectories": traj, "t_span": [0, 30 if chaotic else 10],
              "samples": 3000 if chaotic else 1200, "chaotic": chaotic}
        return Interpretation("solve", "solve_dynamical_system", ti,
                              note="an ODE system ẋ = F(x): equilibria, stability, flow")

    # vector field (needs a field cue OR a clear tuple with divergence/curl intent)
    if (re.search(r"\bF\s*(?:\([^)]*\))?\s*=", raw) or "vector field" in low
            or (any(k in low for k in ("divergence", "curl", "flux")) and "(" in raw)):
        vf = _find_vector_field(prepped)
        if vf is not None:
            order, comps = vf
            return Interpretation("solve", "solve_vector_field",
                                  {"components": comps, "variables": order},
                                  note="a vector field: divergence and curl")

    # constrained optimization
    if re.search(r"\bsubject to\b|\bs\.?t\.?\b|\bconstraint\b", low):
        obj, con = _split_constrained(prepped)
        if obj and con:
            return Interpretation("solve", "solve_constrained_optimization",
                                  {"objective": obj, "constraint": con},
                                  note="constrained optimization via Lagrange multipliers")

    # optimization landscape
    if re.search(r"\bminim|\bgradient descent\b|\bdescend\b|\boptimi", low):
        expr = canon(_extract_expr_after_eq(_math_core(prepped)), {"x", "y"})
        if expr:
            ti = {"expr": expr}
            start = _find_start(low)
            if start:
                ti["start"] = start
            return Interpretation("solve", "solve_optimization", ti,
                                  note="an optimization landscape: descent to a minimum")

    # scalar field / surface — explicit 'f =' or a bare expression in x, y
    core = _math_core(prepped)
    candidate = _extract_expr_after_eq(core) if "=" in core else core
    expr = canon(candidate, {"x", "y"})
    if expr and re.search(r"[xy]", expr):
        # require some cue that this is a field, OR that it clearly is an expression
        is_fieldish = (re.search(r"\bf\s*=", low) or "=" in prepped
                       or any(k in low for k in ("surface", "gradient", "hessian",
                                                 "critical", "saddle", "minimum", "maximum",
                                                 "extrem", "field", "plot", "graph")))
        if is_fieldish or re.search(r"[+\-*/]|\*\*", expr):
            return Interpretation("solve", "solve_scalar_field", {"expr": expr},
                                  note="a scalar field f(x, y) as a surface")
    return None


def _split_constrained(text: str):
    parts = re.split(r"\bsubject to\b|\bs\.?t\.?\b", text, flags=re.IGNORECASE)
    if len(parts) < 2:
        return None, None
    obj = canon(_extract_expr_after_eq(_math_core(parts[0])), {"x", "y"})
    con_raw = parts[1]
    # 'x + y = 1' -> 'x + y - 1'; 'x + y - 1 = 0' -> 'x + y - 1'
    if "=" in con_raw:
        lhs, rhs = con_raw.split("=", 1)
        con = canon(f"({lhs}) - ({rhs})", {"x", "y"})
    else:
        con = canon(con_raw, {"x", "y"})
    return obj, con


def _sweep_expr(raw: str) -> str | None:
    """Pull an f(x,y) out of a sweep request ('...sweep on (x^2-1)^2 + y^2'), or None."""
    prepped = _num_word_cleanup(raw)
    m = re.search(r"\b(?:on|of|for|over)\b\s+(.+)$", prepped, re.IGNORECASE)
    seg = m.group(1) if m else prepped
    core = _math_core(seg)
    cand = _extract_expr_after_eq(core) if "=" in core else core
    e = canon(cand, {"x", "y"})
    return e if (e and re.search(r"[xy]", e)) else None


def _interpret_simulation(raw: str, low: str, has_current: bool) -> Interpretation:
    """A multi-start descent sweep. Prefer an expression in the request; else the current
    problem; else a canonical multi-basin landscape so the request still works (G23)."""
    ti: dict = {}
    expr = _sweep_expr(raw)
    if expr:
        ti["expr"] = expr
    elif not has_current:
        ti["expr"] = _SWEEP_DEFAULT_EXPR
    # else: no expr and a current problem → the tool sweeps the current landscape
    return Interpretation("simulate", tool="run_simulation", tool_input=ti,
                          note="a multi-start gradient-descent sweep — which basin wins most")


def _detect_conceptual(low: str) -> Interpretation | None:
    for keys, factory, desc in _CONCEPTUAL:
        if any(k in low for k in keys):
            tool, ti = factory()
            return Interpretation("solve", tool, ti,
                                  note=f"conceptual request → {desc}")
    return None


def _looks_like_question(low: str) -> bool:
    return (low.endswith("?") or low.split()[:1] and low.split()[0] in (
        "what", "where", "why", "how", "is", "are", "does", "do", "can", "which",
        "explain", "describe", "tell"))


def _decline(low: str) -> Interpretation:
    for group in _OUT_OF_SCOPE:
        if any(k in low for k in group):
            return Interpretation(
                "decline",
                reason="that is outside this tool's five areas (scalar fields, optimization, "
                       "vector fields, linear algebra, and dynamical systems).",
                suggestion="I can show the nearest geometric idea — e.g. 'show me a saddle', "
                           "'an example of chaos', or 'the field F = (-y, x)'.",
                out_of_scope=True)
    return Interpretation(
        "decline",
        reason="I couldn't read that as a problem in one of the five areas.",
        suggestion="try a typed equation ('f = x^2 - y^2', 'F = (-y, x)', '[[2,1],[1,2]]', "
                   "\"x' = y, y' = -x\") or an open request ('show me an example of chaos').")
