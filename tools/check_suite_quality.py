#!/usr/bin/env python3
"""CHK-014 — whole-test-set output-quality sweep (G15, C-SUITE-QUALITY; also G11/G12 structure).

The point of this check is the thing Clara asked for: don't spot-check a couple of problems —
DRIVE EVERY case in the test set and, for each one, confirm all four output dimensions are on
point, failing if any case falls short on any dimension:

  * ANSWER      — the solution's quantities are all tool-computed (engine provenance, never
                  "model") and independently verified (a passing verification record);
  * EXPLANATION — the walkthrough has steps, and every step carries readable text (a grounded
                  description, or at least a label) — nothing blank. [Phase 2 DEEPENS this: the
                  worker tightens it to enforce bite-sized single-idea steps (G11), staged
                  calculations, and readable formatting (G12) as those land — see the asserts
                  marked DEEPEN below.]
  * VISUAL      — the scene is well-formed: it has layers, a base layer at step 0, and every
                  layer is a known kind with the geometry its builder needs;
  * ANIMATION   — every layer maps to a defined entrance (a shape draws on, points grow, a
                  field/grid/eigenvectors fade) — an unhandled kind, which would pop in with no
                  animation, fails here.

It sweeps the governed representative suite (suite/problems.json) AND the demo catalog
(web/problems.py CATALOG) — every canonical problem across all five areas and every layer /
animation kind. Deterministic and offline (constraint C-LOCAL); the agent-interpretation sweep
over the natural-language test set is CHK-008, and the felt pacing / genuine clarity is
confirmed in the running app and recorded as the criteria's evidence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.problems import solve_descriptor, CATALOG  # noqa: E402

# mirrors web/app.js revealAnim(): every layer kind must map to one of these entrances, or it
# would appear with no draw-on animation at all.
ENTRANCE = {
    "surface": "draw", "param_surface": "draw", "polyline": "draw", "curve": "draw",
    "points": "grow",
    "vectors": "fade", "scalar_grid": "fade", "eigenvectors": "fade",
}


def _descriptors():
    """(label, descriptor) for every case in the test set, de-duplicated by id."""
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


def _check_case(label: str, descriptor: dict) -> list[str]:
    fails = []
    try:
        scene = solve_descriptor(descriptor)  # raises if the answer is not verified
    except Exception as e:
        return [f"{label}: solve/verify raised — {e}"]

    # ANSWER — every quantity tool-computed and independently verified
    qs = scene.get("quantities") or []
    if not qs:
        fails.append(f"{label} [answer]: no computed quantities to show")
    for q in qs:
        v = q.get("verification") or {}
        if not v.get("passed"):
            fails.append(f"{label} [answer]: quantity {q.get('name')!r} is not verified")
        if (q.get("provenance") or "").lower() == "model":
            fails.append(f"{label} [answer]: quantity {q.get('name')!r} is model-derived, unlabelled")

    # VISUAL + ANIMATION — well-formed scene, every layer a known kind with a defined entrance
    layers = scene.get("layers") or []
    if not layers:
        fails.append(f"{label} [visual]: scene has no layers")
    if layers and not any((l.get("step", 0) == 0) for l in layers):
        fails.append(f"{label} [visual]: no base layer at step 0")
    for l in layers:
        t = l.get("type")
        if t not in ENTRANCE:
            fails.append(f"{label} [animation]: layer kind {t!r} has no defined entrance (would pop in)")
        if not l.get("data"):
            fails.append(f"{label} [visual]: layer {l.get('id')!r} carries no geometry data")

    # EXPLANATION — a walkthrough with readable text on every step (nothing blank)
    steps = scene.get("steps") or []
    if not steps:
        fails.append(f"{label} [explanation]: no walkthrough steps")
    for s in steps:
        text = (s.get("description") or s.get("label") or s.get("introduces") or "").strip()
        if not text:
            fails.append(f"{label} [explanation]: a walkthrough step has no readable text")
        # DEEPEN (Phase 2): the worker tightens the explanation assertions here as G11/G12 land
        # — require a GROUNDED description on calculation steps (not just a label), enforce
        # bite-sized single-idea step scoping, and check that multi-stage calculations are
        # shown stage by stage. Until then this guards that nothing is blank.

    return fails


def main() -> int:
    cases = _descriptors()
    all_fails, ok = [], 0
    for label, d in cases:
        f = _check_case(label, d)
        if f:
            all_fails.extend(f)
        else:
            ok += 1

    if all_fails:
        for f in all_fails:
            print(f"  FAIL  {f}")
        print(f"\nSUITE QUALITY GAP — {len(all_fails)} issue(s) across {len(cases)} cases "
              f"({ok} fully on point).")
        return 1
    print(f"  ok    drove all {len(cases)} test cases; every one on point on all four dimensions")
    print("  ok    answer verified · scene well-formed · every layer has a defined entrance · steps readable")
    print("\nSUITE QUALITY HOLDS — every case is on point (answer, explanation, visual, animation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
