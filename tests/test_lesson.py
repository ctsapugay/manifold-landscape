"""Phase 2 — the pedagogy layer: readable notation, the fine-grained staged lesson, and the
grounded per-step follow-up (G11–G13). Offline and deterministic."""

import pytest

from engine.notation import to_notation, vec_notation, matrix_notation, MINUS
from engine.lesson import build_lesson
from agent import build_agent
from web.problems import solve_descriptor, CATALOG, CATALOG_BY_ID


# --- notation (G12) ----------------------------------------------------------

@pytest.mark.parametrize("src, expect", [
    ("x**2 + y**2", "x² + y²"),
    ("x**2 + 3*y**2", "x² + 3y²"),
    ("(1-x)**2 + 100*(y-x**2)**2", "(1 − x)² + 100(y − x²)²"),
    ("10*(y - x)", "10(y − x)"),
    ("x*y - 8*z/3", "x·y − 8z/3"),
    ("2*x", "2x"),
])
def test_notation_renders_readably(src, expect):
    assert to_notation(src) == expect


def test_notation_never_leaves_raw_source():
    for src in ("x**2 + 3*y**2", "x*(28 - z) - y", "sin(x)*cos(y)"):
        out = to_notation(src)
        assert "**" not in out and "*" not in out


def test_notation_is_display_only_and_value_preserving():
    # a plain variable / number passes through unchanged except for cosmetic minus
    assert to_notation("x") == "x"
    assert to_notation("-y") == MINUS + "y"
    assert vec_notation(["-y", "x"]) == f"({MINUS}y, x)"
    assert matrix_notation([[2, 1], [1, 2]]) == "[[2, 1]; [1, 2]]"


# --- the lesson is decomposed and staged (G11) -------------------------------

def _lesson(pid):
    return solve_descriptor(CATALOG_BY_ID[pid])["lesson"]


def test_every_catalog_problem_has_a_lesson():
    for d in CATALOG:
        lesson = solve_descriptor(d)["lesson"]
        assert lesson and all("title" in s and "lines" in s for s in lesson)


def test_lorenz_is_broken_into_many_small_steps():
    lesson = _lesson("D4")
    # a multi-part problem must be many bite-sized steps, not a handful of dense ones
    assert len(lesson) >= 12
    # single-idea: no step piles up more than a few lines
    assert all(len(s["lines"]) <= 6 for s in lesson)


def test_lorenz_stages_each_stability_calculation():
    lesson = _lesson("D4")
    groups = {}
    for s in lesson:
        st = s.get("stage")
        if st:
            groups.setdefault(st["group"], set()).add(st["index"])
    # three equilibria, each classified stage by stage (Jacobian -> eigenvalues -> type)
    stab_groups = [g for g in groups if g.startswith("stab-")]
    assert len(stab_groups) == 3
    for g in stab_groups:
        assert groups[g] == {1, 2, 3}


def test_descent_is_shown_stage_by_stage():
    lesson = _lesson("O1")
    stages = [s for s in lesson if (s.get("stage") or {}).get("group") == "descent"]
    assert len(stages) >= 3
    # the intermediate objective values fall — the work is shown, not jumped to
    fvals = [ln["text"] for s in stages for ln in s["lines"] if ln["kind"] == "calc"]
    assert any("f =" in t for t in fvals)


def test_every_lesson_step_maps_to_a_real_visual():
    for d in CATALOG:
        scene = solve_descriptor(d)
        steps = {l["step"] for l in scene["layers"]}
        for s in scene["lesson"]:
            assert s["reveal"] in steps


def test_build_lesson_falls_back_gracefully():
    # an area it cannot decompose returns the coarse steps rather than raising
    class _S:  # minimal stand-in
        area = "unknown-area"
        quantities = []
    scene = {"layers": [], "steps": [{"step": 1}]}
    assert build_lesson(_S(), scene, {}) == [{"step": 1}]


# --- per-step follow-up is grounded and preserves place (G13) ----------------

def test_answer_step_is_grounded_and_preserves_place():
    d = CATALOG_BY_ID["D4"]
    scene = solve_descriptor(d)
    agent = build_agent(force="offline")
    agent.current = {"descriptor": d, "scene": scene, "area": scene["area"]}
    step = next(s for s in scene["lesson"] if s["id"] == "dyn-stab0-eig")
    place = agent.current
    r = agent.answer_step("why is this eigenvalue positive?", step)
    assert not r.declined and not r.model_derived
    assert "stability" in r.grounded_in
    assert r.grounding["grounded"]           # contradicts nothing
    assert agent.current is place            # the walkthrough position is preserved


def test_answer_step_without_a_current_problem_declines():
    agent = build_agent(force="offline")
    r = agent.answer_step("why?", {"quantity": "stability"})
    assert r.declined
