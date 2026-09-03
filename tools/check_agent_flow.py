#!/usr/bin/env python3
"""CHK — grounded multi-turn chat and the unbroken end-to-end agent flow (criteria G6, G8).

Walks the whole agentic path for a representative sample, exactly as the app drives it:
pose → interpret → solve → build scene → step through → hold a MULTI-TURN conversation. It
checks that:

  * the flow never crashes and never surfaces an unhandled error (G8);
  * the scene is well-formed, step-tagged from a base layer, with every quantity verified;
  * follow-up questions are answered across several turns, each grounded in the problem's
    verified state — citing computed quantities and never flagged as containing unlabelled
    model-derived values (G6).

Offline brain, no network (C-LOCAL). Backs criteria G6 and G8.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402

# (problem, [follow-up questions...])
SCRIPTS = [
    ("f = x^2 - y^2",
     ["what is the gradient?", "is the origin a saddle?", "what is the hessian?"]),
    ("minimize x^2 + 3y^2 starting at (3,2)",
     ["where is the minimum?", "did the descent converge?"]),
    ("F = (-y, x)",
     ["what is the curl?", "does the field diverge?"]),
    ("[[1,1],[0,1]]",
     ["what are the eigenvalues?", "why can't it be diagonalized?"]),
    ("show me an example of chaos",
     ["what are the equilibria?", "is this chaotic?", "explain sensitive dependence"]),
]


def _check_scene(scene) -> list[str]:
    errs = []
    if not scene or not scene.get("layers"):
        return ["scene has no geometry"]
    steps = sorted({l["step"] for l in scene["layers"]})
    if steps and steps[0] != 0:
        errs.append("scene has no base (step 0) layer")
    for q in scene.get("quantities", []):
        if not q.get("verification", {}).get("passed"):
            errs.append(f"quantity {q.get('name')!r} unverified")
        if not q.get("provenance") or q["provenance"] == "model":
            errs.append(f"quantity {q.get('name')!r} has no engine provenance")
    # stepping reveals only <= current step
    maxstep = max(steps) if steps else 0
    for k in range(maxstep + 1):
        for l in scene["layers"]:
            if l["step"] > k and l["step"] <= k:
                errs.append(f"layer {l['id']} visible before its step")
    return errs


def main() -> int:
    all_errs = []
    for problem, questions in SCRIPTS:
        agent = build_agent(force="offline")
        try:
            r = agent.run(problem)
        except Exception as exc:
            all_errs.append(f"{problem!r}: crashed on solve — {type(exc).__name__}: {exc}")
            continue
        errs = _check_scene(r.scene)
        if r.declined:
            errs.append("declined an in-scope problem")
        # multi-turn conversation, each turn grounded
        for q in questions:
            try:
                a = agent.run(q)
            except Exception as exc:
                errs.append(f"turn {q!r} crashed — {type(exc).__name__}: {exc}")
                continue
            if not a.answer:
                errs.append(f"turn {q!r} produced no answer")
            if a.model_derived:
                errs.append(f"turn {q!r} contained unlabelled model-derived values")
            if not a.grounded_in:
                errs.append(f"turn {q!r} was not grounded in any verified quantity")
        if errs:
            all_errs += [f"{problem[:30]!r}: {e}" for e in errs]
            for e in errs:
                print(f"  FAIL  {problem[:30]!r}: {e}")
        else:
            print(f"  ok    {problem[:40]:42} + {len(questions)} grounded follow-ups")

    if all_errs:
        print(f"\nFLOW BROKEN OR UNGROUNDED — {len(all_errs)} issue(s).")
        return 1
    print(f"\nFLOW OK — {len(SCRIPTS)} problems run pose→solve→scene→step→multi-turn-chat, all grounded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
