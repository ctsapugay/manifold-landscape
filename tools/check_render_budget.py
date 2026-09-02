#!/usr/bin/env python3
"""CHK — interactive-render budget (criterion G2 / C-INTERACTIVE, automated guard).

A true frame-rate measurement is taken in the browser (see checks/registry.md CHK-G2-FPS
and the G2 evidence): the app exposes window.__ml.state().fps, and sustained interaction
must stay above the recorded threshold on Clara's machine. THIS check is the automated
regression guard that keeps that measurement honest between runs: it bounds the geometry
each suite scene sends to the GPU, so a change that would tank the frame rate (an
accidentally huge mesh or arrow count) fails here rather than silently making the app
sluggish. Budgets are generous relative to what a laptop GPU renders smoothly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.problems import solve_descriptor  # noqa: E402

SUITE = ROOT / "suite" / "problems.json"

# Vertices/instances a mid laptop GPU renders at 60fps with big headroom.
MAX_VERTICES = 200_000
MAX_ARROWS = 2_000
MAX_POINTS = 5_000


def scene_load(scene) -> dict:
    verts = arrows = points = 0
    for l in scene["layers"]:
        d = l["data"]
        if l["type"] == "surface":
            verts += len(d["x"]) * len(d["y"])
        elif l["type"] == "param_surface":
            g = d["grid"]; verts += len(g) * len(g[0])
        elif l["type"] in ("vectors", "eigenvectors"):
            arrows += len(d["arrows"])
        elif l["type"] == "points":
            points += len(d["points"])
        elif l["type"] == "scalar_grid":
            points += len(d["x"]) * len(d["y"])
        elif l["type"] in ("curve", "polyline"):
            verts += len(d["points"])
    return {"vertices": verts, "arrows": arrows, "points": points}


def main() -> int:
    problems = json.loads(SUITE.read_text(encoding="utf-8"))["problems"]
    errs = []
    for p in problems:
        load = scene_load(solve_descriptor(p["descriptor"]))
        over = []
        if load["vertices"] > MAX_VERTICES:
            over.append(f"vertices {load['vertices']} > {MAX_VERTICES}")
        if load["arrows"] > MAX_ARROWS:
            over.append(f"arrows {load['arrows']} > {MAX_ARROWS}")
        if load["points"] > MAX_POINTS:
            over.append(f"points {load['points']} > {MAX_POINTS}")
        if over:
            errs.append(f"{p['id']}: " + "; ".join(over))
            print(f"  FAIL  {p['id']}  {load}")
        else:
            print(f"  ok    {p['id']}  {load}")
    print()
    if errs:
        print(f"OVER RENDER BUDGET — {len(errs)} scene(s) too heavy for smooth interaction.")
        return 1
    print(f"WITHIN RENDER BUDGET — all {len(problems)} scenes are light enough to stay responsive.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
