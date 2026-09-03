#!/usr/bin/env python3
"""CHK-015 — per-step follow-up questions, grounded in that step's verified state (G13).

While being walked through a problem the user can ask a question about a *specific step* and
get an answer that (a) addresses that step, (b) is grounded in the problem's verified computed
state and contradicts none of it, and (c) does not lose their place in the walkthrough.

This drives EVERY case in the test set: for each one it solves the problem, sets it as the
agent's current problem, and then — for each walkthrough step that rests on a verified quantity
— asks a follow-up through the same ``answer_step`` path the UI uses, asserting per answer:

  * it is not declined and returns non-empty ``grounded_in`` (it is answered from verified state);
  * the step's own verified quantity is among the grounding sources (it addresses THAT step);
  * ``model_derived`` is False and the grounding gate reports no unverified numbers
    (it contradicts nothing — C-GROUNDED-EXPLANATION / C-VERIFIED-MATH);
  * the agent's current problem is unchanged afterwards (the walkthrough position is preserved).

It also asks the concrete pointed question from Clara's Lorenz review ("why is this eigenvalue
…?" on a stability step) and confirms it is answered about that step. Deterministic and offline
(constraint C-LOCAL): it exercises the grounded ``answer_step`` path, which never calls a model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402
from web.problems import solve_descriptor, CATALOG, CATALOG_BY_ID  # noqa: E402


def _descriptors():
    out, seen = [], set()
    suite = json.loads((ROOT / "suite" / "problems.json").read_text(encoding="utf-8"))
    for entry in suite.get("problems", []):
        d = entry.get("descriptor")
        if d:
            out.append((f"suite:{entry.get('id')}", d))
            seen.add(d.get("id"))
    for d in CATALOG:
        if d.get("id") not in seen:
            out.append((f"catalog:{d.get('id')}", d))
    return out


def _steps_with_quantity(scene):
    """Representative grounded steps: one per distinct verified quantity in the lesson."""
    seen, picks = set(), []
    for s in scene.get("lesson", []):
        q = s.get("quantity")
        if q and s.get("verified") and q not in seen:
            seen.add(q)
            picks.append(s)
    return picks


def _check_case(label, descriptor) -> list[str]:
    fails = []
    scene = solve_descriptor(descriptor)
    agent = build_agent(force="offline")
    # set the solved problem as the session's current problem (the state a walkthrough runs on)
    agent.current = {"descriptor": descriptor, "scene": scene, "area": scene.get("area", "")}

    steps = _steps_with_quantity(scene)
    if not steps:
        return [f"{label}: no grounded walkthrough steps to interrogate"]

    for s in steps:
        place_before = agent.current
        r = agent.answer_step("Can you explain this step?", s)
        q = s.get("quantity")
        if r.declined:
            fails.append(f"{label} step {s.get('id')}: follow-up was declined")
            continue
        if not r.grounded_in:
            fails.append(f"{label} step {s.get('id')}: answer not grounded (empty grounded_in)")
        if q not in (r.grounded_in or []):
            fails.append(f"{label} step {s.get('id')}: answer does not address the step's "
                         f"quantity {q!r} (grounded_in={r.grounded_in})")
        if r.model_derived:
            fails.append(f"{label} step {s.get('id')}: answer is model-derived, not verified")
        if not r.grounding.get("grounded", True):
            fails.append(f"{label} step {s.get('id')}: answer states unverified numbers "
                         f"{r.grounding.get('unverified_numbers')}")
        if agent.current is not place_before:
            fails.append(f"{label} step {s.get('id')}: follow-up changed the session's place")
    return fails


def _check_lorenz_pointed() -> list[str]:
    """Clara's concrete case: a pointed question on the Lorenz stability step."""
    d = CATALOG_BY_ID["D4"]
    scene = solve_descriptor(d)
    agent = build_agent(force="offline")
    agent.current = {"descriptor": d, "scene": scene, "area": scene["area"]}
    step = next((s for s in scene["lesson"] if s.get("id") == "dyn-stab0-eig"), None)
    if step is None:
        return ["lorenz: no stability step to ask about"]
    r = agent.answer_step("why does this equilibrium have a positive eigenvalue?", step)
    fails = []
    if "stability" not in (r.grounded_in or []):
        fails.append(f"lorenz pointed Q: not grounded in stability (grounded_in={r.grounded_in})")
    if r.model_derived or not r.grounding.get("grounded", True):
        fails.append("lorenz pointed Q: answer not fully grounded in verified state")
    if "eigenvalue" not in r.answer.lower() and "saddle" not in r.answer.lower():
        fails.append("lorenz pointed Q: answer does not address the stability step")
    return fails


def main() -> int:
    cases = _descriptors()
    all_fails, ok = [], 0
    for label, d in cases:
        try:
            f = _check_case(label, d)
        except Exception as e:
            f = [f"{label}: raised {type(e).__name__}: {e}"]
        all_fails.extend(f)
        ok += 1 if not f else 0
    all_fails.extend(_check_lorenz_pointed())

    if all_fails:
        for f in all_fails:
            print(f"  FAIL  {f}")
        print(f"\nPER-STEP FOLLOW-UP GAP — {len(all_fails)} issue(s).")
        return 1
    print(f"  ok    drove per-step follow-ups across all {len(cases)} cases + Clara's Lorenz case")
    print("  ok    each answer addresses its step, grounded in verified state, place preserved")
    print("\nPER-STEP FOLLOW-UP OK — questions about a step are answered from that step's "
          "verified state without losing place.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
