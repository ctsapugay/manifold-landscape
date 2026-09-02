"""Grounded Q&A (G4): scripted questions must reference the correct verified values
and assert nothing the engine contradicts."""

from engine.scalar_field import ScalarField
from engine.vector_field import VectorField
from engine.linalg import LinearTransformation
from engine.optimization import ConstrainedProblem
from engine.explain import Explainer


def _grounding_is_valid(sol, ans):
    """Every quantity an answer cites must exist in the solution and be verified."""
    names = {q.name for q in sol.quantities if q.verified}
    return ans["grounded_in"] and all(n in names for n in ans["grounded_in"])


def test_scalar_questions_reference_computed_values():
    f = ScalarField("x**2 + y**2")
    sol = f.solve("S1", "Paraboloid").require_verified()
    ex = Explainer(sol)

    a = ex.answer("Where is the minimum?")
    assert "(0, 0)" in a["answer"] and "minimum" in a["answer"].lower()
    assert "critical_points" in a["grounded_in"]
    assert _grounding_is_valid(sol, a)

    g = ex.answer("What is the gradient here?")
    assert "2*x" in g["answer"] and "2*y" in g["answer"]
    assert _grounding_is_valid(sol, g)


def test_saddle_answer_matches_classification():
    f = ScalarField("x**2 - y**2")
    sol = f.solve("S2", "Saddle").require_verified()
    a = Explainer(sol).answer("Is the origin a saddle?")
    assert "saddle" in a["answer"].lower()
    # must not misclassify it as a min or max
    assert "a minimum" not in a["answer"] and "a maximum" not in a["answer"]


def test_vector_field_curl_and_divergence():
    vf = VectorField(["-y", "x"], ["x", "y"])
    sol = vf.solve("V1", "Rotation").require_verified()
    ex = Explainer(sol)

    c = ex.answer("What is the curl of this field?")
    assert "2" in c["answer"] and "rotat" in c["answer"].lower()
    assert "curl" in c["grounded_in"]

    d = ex.answer("Does the field have any divergence?")
    assert "div F = 0" in d["answer"]
    assert "expand" in d["answer"].lower() or "compress" in d["answer"].lower() \
        or "neither" in d["answer"].lower()


def test_eigen_answer_lists_eigenvalues():
    T = LinearTransformation([[2, 1], [1, 2]])
    sol = T.solve("L1", "Symmetric", want=("determinant", "eigen")).require_verified()
    a = Explainer(sol).answer("What are the eigenvalues and eigenvectors?")
    assert "3" in a["answer"] and "1" in a["answer"]
    assert "eigen" in a["grounded_in"]


def test_constrained_answer_reports_optimum_and_lambda():
    prob = ConstrainedProblem("x**2 + y**2", "x + y - 1")
    sol = prob.solve("O3", "Constrained").require_verified()
    a = Explainer(sol).answer("Explain the Lagrange multiplier and the constrained optimum.")
    assert "(0.5, 0.5)" in a["answer"] and "λ" in a["answer"]
    assert "constrained_optimum" in a["grounded_in"]


def test_unmatched_question_falls_back_to_grounded_overview():
    f = ScalarField("x**2 + y**2")
    sol = f.solve("S1", "Paraboloid").require_verified()
    a = Explainer(sol).answer("Tell me something interesting about this.")
    # the overview cites every verified quantity
    assert _grounding_is_valid(sol, a)
    assert set(a["grounded_in"]) == {q.name for q in sol.quantities}
