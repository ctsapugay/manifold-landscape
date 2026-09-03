#!/usr/bin/env python3
"""CHK-013 — shapes are drawn on, and a surface's reveal style is switchable (G10, C-DRAW-ON).

This backs the automatable slice of the entrance-animation contract:

  * every shape ENTERS by being progressively drawn or grown on (a reveal driven by a
    growing draw-range for meshes/lines, a scale-in for point markers), not by popping in
    or cross-fading a finished whole; supporting overlays (the vector field) fade in;
  * a SURFACE is revealed, by default, as a mesh growing from its centre, and the user can
    switch it to a contour view that blooms from the centre and back — with grow-from-centre
    always the default for a new problem;
  * a walkthrough ends framed on the whole finished picture.

The frontend wiring is checked in the app source (there is no headless WebGL here); the
fully-visual behaviour — watching the surface grow, toggling to contours and back — is
verified in the running app and recorded as G10's evidence. The check also confirms, through
the real engine, that a surface scene actually carries the height grid the contour reveal is
built from, so the wiring has real data to act on. Offline, no network (constraint C-LOCAL).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

APP_JS = ROOT / "web" / "app.js"
INDEX = ROOT / "web" / "index.html"


def main() -> int:
    errs = []

    js = APP_JS.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")

    # 1. shapes are drawn/grown on (not popped or whole-faded); the field fades in
    wiring = [
        ("setDrawRange" in js, "app.js does not reveal geometry progressively (no draw-range reveal)"),
        ("triggerDraw" in js, "app.js has no draw-on trigger for shapes"),
        ("triggerGrow" in js, "app.js has no grow-in trigger for point markers"),
        ("fadeIn" in js, "app.js does not fade supporting overlays (the vector field) in"),
        # 2. the surface has two reveal styles, switchable, defaulting to grow-from-centre
        ("buildContours" in js, "app.js has no contour (level-set) reveal for surfaces"),
        ("surfaceMode" in js, "app.js does not track which surface reveal style is active"),
        ('surfaceMode = "surface"' in js, "app.js does not default the surface to grow-from-centre"),
        ("fadeOut" in js, "app.js cannot fade the surface out when switching to contours"),
        ("contourToggle" in js, "app.js does not wire the surface-reveal toggle"),
        ('id="contour-toggle"' in html, "index.html has no surface-reveal toggle control"),
        # 3. a walkthrough ends framed on the whole picture
        ("The full picture" in js, "app.js walkthrough does not end framed on the whole scene"),
    ]
    for ok, msg in wiring:
        if not ok:
            errs.append(msg)

    # 4. a surface scene really carries the height grid the contour reveal is built from
    try:
        from web.problems import solve_descriptor  # noqa: E402

        scene = solve_descriptor({"id": "S1", "area": "scalar-fields",
                                  "title": "check", "expr": "x**2 + y**2"})
        surf = next((l for l in scene.get("layers", []) if l.get("type") == "surface"), None)
        if surf is None:
            errs.append("a scalar-field scene exposes no surface layer to draw on")
        else:
            d = surf.get("data", {})
            need = ("x", "y", "z", "z_min", "z_max")
            missing = [k for k in need if k not in d]
            if missing:
                errs.append(f"surface layer is missing the height grid the contour reveal needs: {missing}")
            elif not (isinstance(d.get("z"), list) and d["z"] and isinstance(d["z"][0], list)):
                errs.append("surface layer's height field is not a 2-D grid")
    except Exception as e:  # pragma: no cover - defensive
        errs.append(f"could not build a surface scene to check the contour source data: {e}")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nDRAW-ON GAP — {len(errs)} issue(s).")
        return 1
    print("  ok    shapes draw/grow on (progressive reveal) and the vector field fades in")
    print("  ok    the surface grows from its centre by default and can switch to contours and back")
    print("  ok    a surface scene carries the height grid the contour reveal is built from")
    print("\nDRAW-ON HOLDS — the automatable slice of G10 / C-DRAW-ON is wired.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
