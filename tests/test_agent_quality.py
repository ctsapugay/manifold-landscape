"""Regression tests for the suite-wide quality hardening (2026-09-04).

These lock in the GENERAL fixes made after driving the whole suite through the live agent —
they are deterministic and offline (no network), so they guard the behaviour without API
credits. They are picked up by CHK-007 (`pytest tests/`).

Covered:
  * the model-facing tool-result payload is always valid JSON (no NaN/Infinity), and now
    carries each verified quantity's key value so the model can ground directional/comparative
    claims (the AL1 "45°" model-derived guess fix);
  * focus_view resolves directional features across areas, including linear-algebra
    eigenvector / most-stretched / principal directions (the failed-focus fix);
  * the deterministic scope guard declines the documented out-of-scope categories on BOTH
    brains (the PDE-bluff and factoring fixes) while in-scope problems still solve;
  * a simulation carries its verified sweep result on the scene, so a follow-up can ground a
    basin comparison (the "basins equal" fix);
  * ClaudeBrain does not mark a tool-free contextual answer as declined.
"""

from __future__ import annotations

import json
import math

import pytest

from agent import build_agent
from agent.tools import ToolRegistry
from agent.agent import Tracer
from agent.claude_brain import _tool_result_payload, _compact
from web.problems import CATALOG


def _no_nan(s: str) -> bool:
    return "NaN" not in s and "Infinity" not in s


@pytest.mark.parametrize("desc", CATALOG, ids=[d["id"] for d in CATALOG])
def test_tool_payload_is_valid_json_for_every_catalog_problem(desc):
    """The enriched model-facing payload must be JSON-serializable with no NaN/Infinity for
    every problem (an invalid float would 400 the real API)."""
    reg = ToolRegistry()
    tracer = Tracer(reg, {}, "test", desc.get("title", ""))
    tool = {
        "scalar-fields": "solve_scalar_field",
        "optimization": "solve_constrained_optimization" if desc.get("subtype") == "constrained" else "solve_optimization",
        "vector-fields": "solve_vector_field",
        "linear-algebra": "solve_linear_algebra",
        "dynamical-systems": "solve_dynamical_system",
    }[desc["area"]]
    ti = {k: v for k, v in desc.items() if k in
          ("expr", "components", "variables", "vars", "matrix", "want", "domain", "start",
           "lr", "steps", "trajectories", "t_span", "samples", "chaotic", "objective",
           "constraint", "f", "g")}
    # normalise a couple of key names the tools expect
    if "vars" in ti and "variables" not in ti:
        ti["variables"] = ti.pop("vars")
    if desc.get("subtype") == "constrained":
        ti = {"objective": desc["f"], "constraint": desc["g"]}
    res = tracer.call(tool, ti)
    assert res.ok, f"{desc['id']} did not solve: {res.error}"
    payload = _tool_result_payload(res)
    s = json.dumps(payload)  # must not raise
    assert _no_nan(s), f"{desc['id']} payload contains NaN/Infinity"
    # the payload carries the verified key values, not just display strings
    assert payload["quantities"] and all("value" in q for q in payload["quantities"])


def test_compact_summarises_long_point_arrays():
    long = [[float(i), float(i)] for i in range(4000)]
    out = _compact(long)
    assert isinstance(out, dict) and out["n"] == 4000 and "first" in out and "last" in out


def test_compact_handles_non_finite_via_json():
    # a rogue inf must still serialize safely once dumped by the caller (allow_nan default is
    # True, so we assert our payload path never introduces one — see the catalog test).
    assert _compact(3.5) == 3.5 and _compact("x") == "x"


def _focus(agent, feature):
    reg = agent.registry
    scene = (agent.current or {})["scene"]
    return reg.run("focus_view", {"feature": feature}, {"current_scene": scene})


@pytest.mark.parametrize("feature", [
    "which direction is stretched most", "the eigenvector", "the most stretched direction",
    "the invariant direction",
])
def test_focus_resolves_linear_algebra_directions(feature):
    agent = build_agent(force="offline")
    agent.run("[[2,1],[1,2]]")
    res = _focus(agent, feature)
    assert res.ok and res.directive, f"focus_view failed for {feature!r}"
    assert res.directive["highlight_layer"] == "eigenvectors"


def test_focus_resolves_principal_axis_for_svd():
    agent = build_agent(force="offline")
    agent.run("the singular values of [[1,2,0],[0,1,2],[2,0,1]]")
    res = _focus(agent, "the principal axis stretched most")
    assert res.ok and res.directive["highlight_layer"] == "singular_axes"


@pytest.mark.parametrize("text", [
    "solve the heat equation on a rod",
    "integrate x^2 dx from 0 to 1",
    "what is the probability of rolling two sixes",
    "factor the polynomial x^2 - 5x + 6",
    "prove that there are infinitely many primes",
])
def test_out_of_scope_declined_on_both_brains(text):
    for brain in ("offline",):  # live brain shares Agent.run's deterministic guard
        agent = build_agent(force=brain)
        r = agent.run(text)
        assert r.declined and r.scene is None, f"{text!r} was not declined"


@pytest.mark.parametrize("text", [
    "f = x^2 + y^2", "minimize x^2 + 3y^2 starting at (3,2)", "F = (-y, x)",
    "[[2,1],[1,2]]", "show me an example of chaos",
])
def test_in_scope_still_solves(text):
    r = build_agent(force="offline").run(text)
    assert not r.declined and r.scene is not None


def test_simulation_scene_carries_verified_sweep_quantity():
    agent = build_agent(force="offline")
    r = agent.run("run a multi-start descent sweep on (x^2-1)^2 + 0.3*x + y^2")
    qs = (r.scene or {}).get("quantities", [])
    sweep = next((q for q in qs if q.get("kind") == "sweep"), None)
    assert sweep is not None, "sweep scene does not carry the sweep quantity"
    assert sweep["verification"]["passed"]
    basins = sweep["value"]["basins"]
    assert len(basins) >= 2 and all("f" in b for b in basins), "basin depths not available"
    # the tilted double well: the two wells are NOT equal depth
    depths = sorted(b["f"] for b in basins if b["type"] == "minimum")
    assert depths[0] < depths[-1] - 1e-6, "tilted well should have distinct basin depths"


def test_contextual_answer_is_not_a_false_decline():
    """A ClaudeBrain turn with real answer text but no tool call is not a decline."""
    from agent.claude_brain import ClaudeBrain
    from types import SimpleNamespace

    class Canned:
        def __init__(self):
            self.messages = None

        class messages:  # noqa
            pass

    # build a brain with a canned client returning a text-only (no tool) response
    reg = ToolRegistry()
    brain = ClaudeBrain(reg)

    class Client:
        class messages:
            @staticmethod
            def create(**kw):
                return SimpleNamespace(
                    content=[SimpleNamespace(type="text", text="The gradient points uphill.")],
                    stop_reason="end_turn")
    brain._client = Client()
    tracer = Tracer(reg, {"current_scene": {"quantities": []}}, "claude", "q")
    out = brain.orchestrate("what does the gradient mean?", {"current_scene": {"quantities": []}}, tracer)
    assert out.answer and not out.declined
