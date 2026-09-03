#!/usr/bin/env python3
"""CHK — agent coverage across the five areas and three input styles (criterion G2).

Runs the agent (deterministic offline brain, no network — constraint C-LOCAL) over the
held-out test set in ``suite/agent_tests.json`` and checks that it:

  * solves the in-scope problems — interpreting equations, word problems, and open
    conceptual prompts across all five areas — returning a VERIFIED scene (every displayed
    quantity engine-produced and passed verification), succeeding on at least 90% overall
    and on 100% of the protected core;
  * declines the out-of-scope requests honestly (no scene, no fabricated answer) rather
    than bluffing.

Exit 0 only if both bars are met. Backs criterion G2.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402

SET = ROOT / "suite" / "agent_tests.json"


def _solved_ok(r, expect_area) -> tuple[bool, str]:
    if r.declined:
        return False, "declined an in-scope problem"
    if not (r.scene and r.scene.get("layers")):
        return False, "no scene produced"
    if expect_area and r.area != expect_area:
        return False, f"area {r.area!r}, expected {expect_area!r}"
    quantities = r.scene.get("quantities", [])
    if not quantities:
        return False, "no quantities"
    for q in quantities:
        if not q.get("verification", {}).get("passed"):
            return False, f"quantity {q.get('name')!r} unverified"
        if not q.get("provenance") or q["provenance"] == "model":
            return False, f"quantity {q.get('name')!r} has no engine provenance"
    if r.model_derived:
        return False, "answer contained unlabelled model-derived values"
    return True, "ok"


def _declined_ok(r) -> tuple[bool, str]:
    if not r.declined:
        return False, "answered an out-of-scope request instead of declining"
    if r.scene:
        return False, "produced a scene for an out-of-scope request"
    return True, "ok"


def main() -> int:
    cases = json.loads(SET.read_text(encoding="utf-8"))["cases"]
    in_scope = [c for c in cases if c["expect"] == "solve"]
    core = [c for c in cases if c.get("core")]
    fails = []
    core_fails = []

    for c in cases:
        agent = build_agent(force="offline")  # a fresh session per case
        r = agent.run(c["text"])
        if c["expect"] == "solve":
            ok, why = _solved_ok(r, c.get("area"))
        else:
            ok, why = _declined_ok(r)
        mark = "ok  " if ok else "FAIL"
        print(f"  {mark}  {c['id']:4} [{c['style']:10}] {c['text'][:52]:54} {'' if ok else '— ' + why}")
        if not ok:
            fails.append((c["id"], why))
            if c.get("core"):
                core_fails.append((c["id"], why))

    total = len(cases)
    passed = total - len(fails)
    in_scope_pass = sum(1 for c in in_scope
                        if (c["id"], ) not in [(f[0],) for f in fails])
    rate = passed / total
    core_rate = (len(core) - len(core_fails)) / len(core) if core else 1.0

    print()
    print(f"overall: {passed}/{total} = {rate:.0%}   |   protected core: "
          f"{len(core) - len(core_fails)}/{len(core)} = {core_rate:.0%}")
    ok = rate >= 0.90 and core_rate >= 1.0
    if not ok:
        if core_fails:
            print(f"PROTECTED CORE NOT 100% — {core_fails}")
        if rate < 0.90:
            print(f"OVERALL BELOW 90% — {[f[0] for f in fails]}")
        return 1
    print("AGENT COVERAGE OK — ≥90% overall and 100% of the protected core, out-of-scope declined.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
