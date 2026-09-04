#!/usr/bin/env python3
"""Live end-to-end verification of the agent across the WHOLE test suite.

This is the credit-funded companion to the offline checks: it drives EVERY case in
``suite/agent_tests.json`` through the REAL Claude agent (not the deterministic offline
brain) and, per case, verifies the dimensions the offline checks cannot judge on the live
brain — that the live agent picks the right tools, keeps every displayed value tool-verified
(or honestly labelled), and answers follow-ups accurately with the right tool-driven visual.

It is NOT a registry check: it needs the network and an API key, so it is nondeterministic
and cannot live in ``tools/verify.py`` (constraint C-LOCAL). Run it by hand when verifying
the agent's live quality:

    ./.venv/bin/python tools/live_eval.py            # solves only
    ./.venv/bin/python tools/live_eval.py --followups  # + per-area follow-up probes

It requires ANTHROPIC_API_KEY (loaded from .env). If the balance is exhausted it says so and
exits non-zero rather than reporting a false pass.

Bar (mirrors CHK-008 plus live-only dimensions):
  * in-scope: not declined, a verified scene (every quantity engine-verified, no unlabelled
    model-derived), the expected area, and the agent chose a solve tool;
  * out-of-scope: declined, no scene, no tool fabrication;
  * follow-ups (with --followups): a "manipulate/animate" request drives the right tool
    (focus_view / animate_motion / run_simulation) with a verified directive; a "why/what"
    question stays grounded (not model-derived) with a non-empty answer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import web.server  # noqa: E402  (loads .env)
from agent import build_agent  # noqa: E402
from agent.agent import _claude_available  # noqa: E402

SET = ROOT / "suite" / "agent_tests.json"

# per-area follow-up probes: a manipulate/animate command (must drive a tool) + a grounded
# question. General to the area, not tied to a specific problem.
FOLLOWUPS = {
    "scalar-fields": [("show", "zoom in on a critical point"),
                      ("ask", "what do the Hessian eigenvalues tell us about each critical point?")],
    "optimization": [("show", "animate the descent"),
                     ("ask", "did the descent actually reach the minimum, and how do we know?")],
    "vector-fields": [("ask", "what does the divergence tell us physically?"),
                      ("ask", "is there any rotation in this field?")],
    "linear-algebra": [("show", "which direction is stretched most?"),
                       ("ask", "what do the eigenvalues tell us geometrically?")],
    "dynamical-systems": [("show", "animate the trajectory"),
                          ("ask", "is this system chaotic, and how can we tell?")],
}


def _solved_ok(r, expect_area):
    if r.declined:
        return False, "declined an in-scope problem"
    if not (r.scene and r.scene.get("layers")):
        return False, "no scene produced"
    if expect_area and r.area != expect_area:
        return False, f"area {r.area!r} != expected {expect_area!r}"
    qs = r.scene.get("quantities", [])
    if not qs:
        return False, "no quantities"
    for q in qs:
        if not q.get("verification", {}).get("passed"):
            return False, f"quantity {q.get('name')!r} unverified"
        if not q.get("provenance") or q["provenance"] == "model":
            return False, f"quantity {q.get('name')!r} lacks engine provenance"
    if r.model_derived:
        return False, "answer stated an unlabelled model-derived value"
    if not any(t.startswith("solve_") or t == "run_simulation" for t in r.trace.get("tool_sequence", [])):
        return False, "no solve tool was orchestrated"
    return True, "ok"


def _declined_ok(r):
    if not r.declined:
        return False, "answered an out-of-scope request instead of declining"
    if r.scene:
        return False, "produced a scene for an out-of-scope request"
    return True, "ok"


def _followup_ok(kind, fr):
    if not (fr.answer and fr.answer.strip()):
        return False, "empty answer"
    if fr.model_derived:
        return False, "follow-up stated an unlabelled model-derived value"
    if kind == "show":
        dirs = {d.get("type") for d in (fr.directives or [])}
        if not (dirs & {"focus", "animate", "simulate"}):
            return False, "manipulate/animate request drove no view tool"
        for d in fr.directives or []:
            if d.get("type") in ("animate", "simulate") and not d.get("verified"):
                return False, "playback directive not verified"
    return True, "ok"


def main(argv) -> int:
    if not _claude_available():
        print("LIVE UNAVAILABLE — no ANTHROPIC_API_KEY / SDK. Cannot verify live quality.")
        return 2
    do_fups = "--followups" in argv
    cases = json.loads(SET.read_text())["cases"]
    fails, core_fails = [], []
    probed = set()

    for c in cases:
        agent = build_agent(force="claude")
        try:
            r = agent.run(c["text"])
        except Exception as exc:
            msg = str(exc)
            if "credit balance" in msg.lower():
                print("\nLIVE BLOCKED — Anthropic credit balance exhausted. Top up credits and "
                      "re-run; this is not a pass.")
                return 3
            ok, why = False, f"exception {type(exc).__name__}"
            r = None
        else:
            # Agent.run swallows an API failure into a declined result; catch that signature
            # so we abort as BLOCKED rather than mis-reporting it as a content failure.
            if r and r.declined and "went wrong interpreting" in (r.answer or ""):
                low = (r.answer or "").lower()
                if "credit" in low or "badrequest" in low:
                    print("\nLIVE BLOCKED — Anthropic API error (likely credit balance exhausted): "
                          + r.answer.strip() + "\nTop up credits and re-run; this is NOT a pass.")
                    return 3
                print("\nLIVE ERROR — the API failed: " + r.answer.strip() + "\nRe-run; not a pass.")
                return 3
            ok, why = _solved_ok(r, c.get("area")) if c["expect"] == "solve" else _declined_ok(r)
        mark = "ok  " if ok else "FAIL"
        print(f"  {mark} {c['id']:4} [{c['style']:10}] {c['text'][:44]:46} "
              f"{'' if ok else '— ' + why}")
        if not ok:
            fails.append((c["id"], why));  core_fails += [(c["id"], why)] if c.get("core") else []
            continue
        # follow-up probes: first in-scope case per area
        area = c.get("area")
        if do_fups and r and not r.declined and area in FOLLOWUPS and area not in probed:
            probed.add(area)
            for kind, q in FOLLOWUPS[area]:
                fr = agent.run(q) if kind == "show" else agent.answer_step(
                    q, ((r.scene or {}).get("lesson") or [{}])[0])
                fok, fwhy = _followup_ok(kind, fr)
                fmark = "ok  " if fok else "FAIL"
                print(f"      {fmark} follow-up [{kind}] {q[:44]:46} "
                      f"{'' if fok else '— ' + fwhy}")
                if not fok:
                    fails.append((c["id"] + "/fup", fwhy))

    total = len(cases)
    passed = total - len([f for f in fails if "/fup" not in f[0]])
    core = [c for c in cases if c.get("core")]
    core_rate = (len(core) - len(core_fails)) / len(core) if core else 1.0
    print(f"\nLIVE solve: {passed}/{total}  |  protected core: "
          f"{len(core) - len(core_fails)}/{len(core)} = {core_rate:.0%}"
          f"{'  |  follow-ups probed: ' + str(len(probed)) if do_fups else ''}")
    if fails:
        print("ISSUES:", fails)
        print("LIVE NOT CLEAN.")
        return 1
    print("LIVE CLEAN — every case correct on math/tools/scope"
          + (" and follow-ups" if do_fups else "") + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
