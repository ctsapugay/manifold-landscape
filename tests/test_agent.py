"""The agentic tutor: orchestration, interpretation across areas/styles, grounding, the
tutor driving the view, multi-turn chat, and the Claude tool-use loop (offline, canned)."""

from types import SimpleNamespace

import pytest

from agent import build_agent
from agent.claude_brain import ClaudeBrain
from agent.tools import ToolRegistry


# --- offline brain: interpretation across the five areas and three input styles ----

@pytest.mark.parametrize("text, area, tool", [
    ("f = x^2 - y^2", "scalar-fields", "solve_scalar_field"),
    ("minimize x^2 + 3y^2 starting at (3,2)", "optimization", "solve_optimization"),
    ("minimize x^2 + y^2 subject to x + y = 1", "optimization", "solve_constrained_optimization"),
    ("F = (-y, x)", "vector-fields", "solve_vector_field"),
    ("[[2,1],[1,2]]", "linear-algebra", "solve_linear_algebra"),
    ("x' = y, y' = -x - y", "dynamical-systems", "solve_dynamical_system"),
    # conceptual / word-problem styles
    ("show me an example of chaos", "dynamical-systems", "solve_dynamical_system"),
    ("what does a saddle look like", "scalar-fields", "solve_scalar_field"),
    ("show me a rotating vector field", "vector-fields", "solve_vector_field"),
    ("give me an example of eigenvalues", "linear-algebra", "solve_linear_algebra"),
])
def test_offline_interprets_and_solves(text, area, tool):
    a = build_agent(force="offline")
    r = a.run(text)
    assert not r.declined, f"unexpectedly declined: {text!r}"
    assert r.area == area
    assert r.trace["tool_sequence"] == [tool]
    assert r.scene and r.scene.get("layers")
    # every displayed value came from a verified tool call
    assert r.trace["calls"][0]["verified"]
    assert not r.model_derived


def test_different_inputs_drive_different_tool_sequences():
    a = build_agent(force="offline")
    seqs = {a.run(t).trace["tool_sequence"][0]
            for t in ["f = x^2+y^2", "F = (x, y)", "[[1,1],[0,1]]", "show me chaos"]}
    assert len(seqs) == 4  # the agent chose a different tool for each


def test_out_of_scope_declines_without_fabricating():
    a = build_agent(force="offline")
    for text in ["integrate x^2 dx", "what is the weather", "prove the twin prime conjecture"]:
        r = a.run(text)
        assert r.declined
        assert not r.scene
        assert not r.model_derived


def test_followup_chat_is_grounded_in_current_problem():
    a = build_agent(force="offline")
    a.run("f = x^2 - y^2")           # establishes the current problem
    r = a.run("what is the gradient?")  # a plain follow-up (no focusable feature named)
    assert not r.declined
    assert "2*x" in r.answer          # the actual computed gradient component
    assert r.grounded_in              # cites verified quantities
    assert r.trace["tool_sequence"] == []  # answered from state, no re-solve, no view move


def test_tutor_drives_the_view_on_a_focusing_question():
    a = build_agent(force="offline")
    a.run("minimize x^2 + 3y^2 starting at (3,2)")
    r = a.run("where is the minimum?")
    assert r.directives, "a focusing question should move the view"
    d = r.directives[0]
    assert d["type"] == "focus"
    # the view lands on the actual computed minimum (near the origin)
    assert abs(d["target"][0]) < 0.1 and abs(d["target"][1]) < 0.1


def test_multi_turn_conversation_keeps_context():
    a = build_agent(force="offline")
    a.run("[[2,1],[1,2]]")
    r1 = a.run("what are the eigenvalues?")
    r2 = a.run("what is the determinant?")
    assert "3" in r1.answer  # eigenvalue 3
    assert "3" in r2.answer  # determinant 3
    assert not r1.declined and not r2.declined


# --- the Claude tool-use loop, exercised offline with a canned client --------

def _blocks(*bs):
    return list(bs)


class _FakeMessages:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def create(self, **kwargs):
        # snapshot the messages list, which the brain mutates after the call returns
        self.calls.append({**kwargs, "messages": list(kwargs.get("messages", []))})
        return self.script.pop(0)


class _FakeClient:
    def __init__(self, script):
        self.messages = _FakeMessages(script)


def test_claude_brain_loop_threads_messages_and_calls_tools():
    """No network, no key: a scripted client returns a tool_use then a final answer, and we
    verify the loop executed the tool and threaded the messages correctly."""
    registry = ToolRegistry()
    script = [
        SimpleNamespace(stop_reason="tool_use", content=_blocks(
            SimpleNamespace(type="text", text="Let me analyze that surface."),
            SimpleNamespace(type="tool_use", name="solve_scalar_field",
                            input={"expr": "x**2 + y**2"}, id="tool_1"),
        )),
        SimpleNamespace(stop_reason="end_turn", content=_blocks(
            SimpleNamespace(type="text", text="It is a bowl with a single minimum at the origin."),
        )),
    ]
    fake = _FakeClient(script)
    brain = ClaudeBrain(registry, client=fake)
    from agent.agent import Agent
    agent = Agent(brain, registry)

    r = agent.run("f = x^2 + y^2")
    assert r.brain == "claude"
    assert not r.declined
    assert r.area == "scalar-fields"
    assert r.scene and r.scene.get("layers")
    assert "minimum" in r.answer.lower()
    assert r.trace["tool_sequence"] == ["solve_scalar_field"]
    # two API calls; the second carried the tool_result back to the model
    assert len(fake.messages.calls) == 2
    second_msgs = fake.messages.calls[1]["messages"]
    assert second_msgs[-1]["role"] == "user"
    assert second_msgs[-1]["content"][0]["type"] == "tool_result"
    assert second_msgs[-1]["content"][0]["tool_use_id"] == "tool_1"


def test_claude_brain_labels_unverified_numbers_model_derived():
    """If the model states a number no tool produced, the grounding gate labels it."""
    registry = ToolRegistry()
    script = [
        SimpleNamespace(stop_reason="tool_use", content=_blocks(
            SimpleNamespace(type="tool_use", name="solve_scalar_field",
                            input={"expr": "x**2 + y**2"}, id="t1"),
        )),
        SimpleNamespace(stop_reason="end_turn", content=_blocks(
            # 42.7 appears in no verified quantity for this problem
            SimpleNamespace(type="text", text="The curvature is exactly 42.7 everywhere."),
        )),
    ]
    brain = ClaudeBrain(registry, client=_FakeClient(script))
    from agent.agent import Agent
    r = Agent(brain, registry).run("f = x^2 + y^2")
    assert r.model_derived
    assert "model-derived" in r.answer.lower()


def test_build_agent_falls_back_to_offline_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    a = build_agent()
    assert a.brain.kind == "offline"
