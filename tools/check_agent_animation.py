#!/usr/bin/env python3
"""CHK — the agent drives step-by-step playback / animation in the 3-D through tools (G22).

Over scripted requests where motion aids understanding ("animate the trajectory", "play the
descent path"), the agent must issue a well-formed animation directive that the view can carry
out, and the motion must follow a VERIFIED quantity — an integrated trajectory or a descent
path (C-VERIFIED-MATH, C-VERIFIED-MOTION), never fabricated.

Checks, from the recorded agent turn:
  * the animation tool was called and recorded in the trace, verified with engine provenance;
  * the emitted directive is well-formed (type 'animate', a path of >= 2 points, a named
    source quantity, verified: true);
  * the directive's path matches the scene layer built from that verified quantity, so the
    motion is a faithful replay of tool-computed data, not invented.

Runs the offline brain (no network — C-LOCAL). Backs criterion G22.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402

# (opening problem, animation request, the scene layer id the motion should trace to)
CASES = [
    ("show me an example of chaos", "animate the trajectory", "trajectory"),
    ("minimize x^2 + 3y^2 starting at (3,2)", "play the descent path", "descent_path"),
]


def main() -> int:
    errs = []
    for problem, request, layer_kind in CASES:
        agent = build_agent(force="offline")
        solved = agent.run(problem)
        scene = solved.scene or {}
        r = agent.run(request)

        # the tool must have been called and recorded, verified with engine provenance
        anim_calls = [c for c in r.trace.get("calls", []) if c["tool"] == "animate_motion"]
        if not anim_calls:
            errs.append(f"{request!r}: no animate_motion tool call was recorded")
            continue
        call = anim_calls[0]
        if not call["ok"] or not call["verified"]:
            errs.append(f"{request!r}: animate_motion call not ok/verified in the trace")
        if any((not p) or p == "model" for p in call["provenance"]):
            errs.append(f"{request!r}: animation motion lacks engine provenance")

        # the directive must be well-formed
        directive = next((d for d in r.directives if d.get("type") == "animate"), None)
        if not directive:
            errs.append(f"{request!r}: no 'animate' directive emitted")
            continue
        path = directive.get("path") or []
        if len(path) < 2 or not all(len(p) == 3 for p in path):
            errs.append(f"{request!r}: animate path is not a list of >= 2 xyz points")
        if not directive.get("verified"):
            errs.append(f"{request!r}: animate directive is not marked verified")
        qname = directive.get("source_quantity")
        if not qname:
            errs.append(f"{request!r}: animate directive names no source quantity")

        # the motion must trace to a VERIFIED quantity in the scene (C-VERIFIED-MOTION)
        sq = next((q for q in scene.get("quantities", []) if q.get("name") == qname), None)
        if not sq or not sq.get("verification", {}).get("passed"):
            errs.append(f"{request!r}: source quantity {qname!r} is not a verified scene quantity")

        # and the path must be the SAME geometry as the layer built from that quantity
        layer = next((l for l in scene.get("layers", [])
                      if l["id"] == directive.get("layer")), None)
        if not layer or layer.get("data", {}).get("points") != path:
            errs.append(f"{request!r}: animate path does not match the verified scene layer "
                        f"(motion would not be a faithful replay)")
        else:
            print(f"  ok    {request:26} → animate {len(path)} verified points "
                  f"(via {qname}, layer {directive.get('layer')})")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nANIMATION GAP — {len(errs)} issue(s).")
        return 1
    print("\nAGENT ANIMATION — playback directives are well-formed and grounded in verified "
          "motion (G22, C-VERIFIED-MOTION).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
