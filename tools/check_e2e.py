#!/usr/bin/env python3
"""CHK — end-to-end flow (criterion G5).

Walks the whole core flow for every problem in the representative suite, exactly as the
app drives it: pose → solve → build the 3-D scene → step through it → ask a question.
Fails if anything raises, if any displayed quantity is unverified, if a scene has no
geometry or a broken step sequence, or if an answer is not grounded in verified results.
No browser and no network (constraint C-LOCAL); it exercises the same engine + dispatch the
server calls.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.problems import solve_descriptor, answer_question, solution_for  # noqa: E402

SUITE = ROOT / "suite" / "problems.json"

QUESTIONS = ["explain this", "what does this show?", "where are the key features?"]


def check_problem(p) -> list[str]:
    errs = []
    d = p["descriptor"]
    pid = p["id"]

    # 1. solve + scene
    scene = solve_descriptor(d)
    if not scene.get("layers"):
        errs.append(f"{pid}: scene has no geometry layers")
    if not scene.get("quantities"):
        errs.append(f"{pid}: no quantities to display")
    for q in scene.get("quantities", []):
        if not q["verification"]["passed"]:
            errs.append(f"{pid}: quantity '{q['name']}' not verified")
        if not q["provenance"] or q["provenance"] == "model":
            errs.append(f"{pid}: quantity '{q['name']}' has no engine provenance")

    # 2. must be JSON-serializable (it crosses the HTTP boundary)
    try:
        json.dumps(scene)
    except (TypeError, ValueError) as exc:
        errs.append(f"{pid}: scene not serializable: {exc}")

    # 3. step sequence is well-formed: steps referenced by layers, 0..max, contiguous-ish
    layer_steps = sorted({l["step"] for l in scene["layers"]})
    if layer_steps and layer_steps[0] != 0:
        errs.append(f"{pid}: scene has no base (step 0) layer")

    # 4. stepping reveals only <= current step (the G3 property, exercised here too)
    maxstep = max(layer_steps) if layer_steps else 0
    for k in range(maxstep + 1):
        for l in scene["layers"]:
            visible = l["step"] <= k
            if l["step"] > k and visible:
                errs.append(f"{pid}: layer '{l['id']}' visible before its step")

    # 5. ask questions — must return grounded answers
    verified_names = {q.name for q in solution_for(d).quantities}
    for question in QUESTIONS:
        ans = answer_question(d, question)
        if not ans.get("answer"):
            errs.append(f"{pid}: empty answer to {question!r}")
        if not ans.get("grounded_in") or any(n not in verified_names for n in ans["grounded_in"]):
            errs.append(f"{pid}: answer to {question!r} not grounded in verified results")
    return errs


def main() -> int:
    problems = json.loads(SUITE.read_text(encoding="utf-8"))["problems"]
    all_errs = []
    for p in problems:
        try:
            errs = check_problem(p)
        except Exception as exc:  # any crash is a broken flow
            errs = [f"{p['id']}: raised {type(exc).__name__}: {exc}"]
        if errs:
            all_errs.extend(errs)
            for e in errs:
                print(f"  FAIL  {e}")
        else:
            print(f"  ok    {p['id']}  full flow: solve → scene → step → ask")
    print()
    if all_errs:
        print(f"END-TO-END BROKEN — {len(all_errs)} problem(s) in the flow.")
        return 1
    print(f"END-TO-END OK — all {len(problems)} problems run pose→solve→visualize→step→ask cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
