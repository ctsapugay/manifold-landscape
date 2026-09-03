#!/usr/bin/env python3
"""CHK-014 — whole-test-set output-quality sweep (G15, C-SUITE-QUALITY; also G11/G12 structure).

The point of this check is the thing Clara asked for: don't spot-check a couple of problems —
DRIVE EVERY case in the test set and, for each one, confirm all four output dimensions are on
point, failing if any case falls short on any dimension:

  * ANSWER      — the solution's quantities are all tool-computed (engine provenance, never
                  "model") and independently verified (a passing verification record);
  * EXPLANATION — the walkthrough is a genuine LESSON (G11/G12): decomposed into many small,
                  single-idea steps (not a few dense ones); every multi-stage calculation is
                  shown STAGE BY STAGE (contiguous stages, each with its own result); each step
                  carries the visual that matches it (a real reveal level); and its text is
                  READABLE — separated blocks, mathematics shown as notation (no raw ``**`` /
                  ``*`` source), no single wall-of-text block, and any verified claim names the
                  verified quantity it rests on;
  * VISUAL      — the scene is well-formed: it has layers, a base layer at step 0, and every
                  layer is a known kind with the geometry its builder needs;
  * ANIMATION   — every layer maps to a defined entrance (a shape draws on, points grow, a
                  field/grid/eigenvectors fade) — an unhandled kind, which would pop in with no
                  animation, fails here.

It sweeps the governed representative suite (suite/problems.json) AND the demo catalog
(web/problems.py CATALOG) — every canonical problem across all five areas and every layer /
animation kind. Deterministic and offline (constraint C-LOCAL); the agent-interpretation sweep
over the natural-language test set is CHK-008, and the felt pacing / genuine clarity is
confirmed in the running app and recorded as the criteria's evidence. This remains a WHOLE-SET,
PER-CASE, ALL-DIMENSION gate: a single case weak on a single dimension fails it.
"""

from __future__ import annotations

import json
import re
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

LINE_KINDS = {"say", "math", "calc", "note"}
WALL_OF_TEXT = 320          # a single readable block should not exceed this many characters
MAX_LINES_PER_STEP = 6      # a single-idea step should not pile up more than a handful of lines
MAX_TITLE = 80
# raw machine source that must never reach the reader as-is (C-READABLE-OUTPUT / G12):
RAW_MULT = re.compile(r"[\w)\]]\s*\*\s*[\w(]")


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


def _check_explanation(label: str, scene: dict) -> list[str]:
    """Enforce the LESSON bar (G11 stepwise + G12 readable) on scene['lesson']."""
    fails = []
    lesson = scene.get("lesson") or []
    if not lesson:
        return [f"{label} [explanation]: no walkthrough"]

    # a lesson is the fine-grained shape (title + lines); the coarse step list is not a lesson
    if not all(("title" in s and "lines" in s) for s in lesson):
        return [f"{label} [explanation]: walkthrough is not decomposed into a lesson "
                "(missing title/lines — the pedagogy layer did not run)"]

    verified_qnames = {q.get("name") for q in (scene.get("quantities") or [])
                        if (q.get("verification") or {}).get("passed")}
    nq = len(scene.get("quantities") or [])
    layer_steps = {l.get("step", 0) for l in (scene.get("layers") or [])}

    # 1. BITE-SIZED: step count scales with the problem's content — it cannot be collapsed to a
    #    few dense steps, nor padded (each verified quantity earns granularity).
    if len(lesson) < max(4, nq + 2):
        fails.append(f"{label} [explanation]: only {len(lesson)} steps for {nq} quantities — "
                     "not decomposed into small single-idea steps")

    # 2. STAGED CALCULATIONS: any multi-stage group must run 1..total contiguously, total >= 2,
    #    each stage carrying its own result — a calculation shown stage by stage, not jumped to.
    groups: dict[str, list[dict]] = {}
    for s in lesson:
        st = s.get("stage")
        if st:
            groups.setdefault(st.get("group"), []).append(s)
    for gid, members in groups.items():
        total = members[0].get("stage", {}).get("total")
        idxs = sorted(m.get("stage", {}).get("index") for m in members)
        if not total or total < 2:
            fails.append(f"{label} [explanation]: staged calc {gid!r} is not multi-stage")
        if idxs != list(range(1, len(idxs) + 1)) or (total and len(idxs) != total):
            fails.append(f"{label} [explanation]: staged calc {gid!r} stages {idxs} are not "
                         f"contiguous 1..{total}")

    # every problem that has a genuinely multi-stage calculation available (a classification, a
    # descent, an eigen/SVD/Lyapunov read) must actually stage it rather than deliver the result
    # whole. We detect that from the quantities present.
    STAGEABLE = {"critical_points", "descent", "minimum", "stability", "eigen", "svd",
                 "separation", "constrained_optimum"}
    if verified_qnames & STAGEABLE and not groups:
        fails.append(f"{label} [explanation]: has a multi-stage calculation "
                     f"({sorted(verified_qnames & STAGEABLE)}) but shows nothing stage by stage")

    # 3+4. PER-STEP: matching visual + readable formatting.
    for s in lesson:
        sid = s.get("id", "?")
        title = (s.get("title") or "").strip()
        if not title:
            fails.append(f"{label} [explanation]: step {sid} has no title")
        if len(title) > MAX_TITLE:
            fails.append(f"{label} [explanation]: step {sid} title is too long to scan")

        # matching visual: the reveal level is a real layer step
        if s.get("reveal") not in layer_steps:
            fails.append(f"{label} [explanation]: step {sid} reveal {s.get('reveal')} is not a "
                         f"real layer step {sorted(layer_steps)}")
        ft = s.get("focus_target")
        if ft is not None and not (isinstance(ft, (list, tuple)) and len(ft) == 3
                                   and all(isinstance(c, (int, float)) for c in ft)):
            fails.append(f"{label} [explanation]: step {sid} focus_target is malformed")

        # a verified step must rest on a verified quantity (ties readability to grounding, G1/G6)
        if s.get("verified") and s.get("quantity") not in verified_qnames:
            fails.append(f"{label} [explanation]: step {sid} claims verified but its quantity "
                         f"{s.get('quantity')!r} is not a verified quantity")

        lines = s.get("lines") or []
        if not lines:
            fails.append(f"{label} [explanation]: step {sid} has no readable text")
        if len(lines) > MAX_LINES_PER_STEP:
            fails.append(f"{label} [explanation]: step {sid} crams {len(lines)} lines into one "
                         "step (not a single idea)")
        for ln in lines:
            kind = ln.get("kind")
            text = (ln.get("text") or "").strip()
            if kind not in LINE_KINDS:
                fails.append(f"{label} [explanation]: step {sid} line kind {kind!r} unknown")
            if not text:
                fails.append(f"{label} [explanation]: step {sid} has a blank line")
            if len(text) > WALL_OF_TEXT:
                fails.append(f"{label} [explanation]: step {sid} has a wall-of-text block "
                             f"({len(text)} chars)")
            # mathematics must read as notation, never raw source
            if kind in ("math", "calc"):
                if "**" in text or RAW_MULT.search(text):
                    fails.append(f"{label} [explanation]: step {sid} shows raw source, not "
                                 f"notation: {text!r}")
    return fails


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

    # EXPLANATION — the full stepwise / readable lesson bar (G11 / G12)
    fails.extend(_check_explanation(label, scene))
    return fails


def _check_pacing() -> list[str]:
    """A regression guard on G11's unhurried reveal pacing: the draw-on duration must not slip
    back below the followable floor Clara signed off on. (Felt pacing itself is app-confirmed.)"""
    js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    m = re.search(r"const\s+DRAW_DUR\s*=\s*(\d+)", js)
    if not m:
        return ["app.js no longer defines DRAW_DUR (the reveal pacing)"]
    if int(m.group(1)) < 3500:
        return [f"draw-on pacing DRAW_DUR={m.group(1)}ms is faster than the followable floor "
                "(3500ms) — too quick for a first-time learner (G11)"]
    return []


def main() -> int:
    cases = _descriptors()
    all_fails, ok = [], 0
    for label, d in cases:
        f = _check_case(label, d)
        if f:
            all_fails.extend(f)
        else:
            ok += 1
    all_fails.extend(_check_pacing())

    if all_fails:
        for f in all_fails:
            print(f"  FAIL  {f}")
        print(f"\nSUITE QUALITY GAP — {len(all_fails)} issue(s) across {len(cases)} cases "
              f"({ok} fully on point).")
        return 1
    print(f"  ok    drove all {len(cases)} test cases; every one on point on all four dimensions")
    print("  ok    answer verified · scene well-formed · every layer has a defined entrance")
    print("  ok    explanation: bite-sized single-idea steps · staged calcs shown stage by "
          "stage · per-step visual · readable notation, no walls")
    print("\nSUITE QUALITY HOLDS — every case is on point (answer, explanation, visual, animation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
