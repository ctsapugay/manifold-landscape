#!/usr/bin/env python3
"""CHK-021 — the visualization's bounds can be expanded where meaningful (G20).

Where a problem is drawn over a domain, the user can expand it and see the geometry re-computed
over the larger region — still tool-computed and verified (C-VERIFIED-MATH). Where expanding is
meaningless (linear-algebra's unit circle/sphere), the control is absent.

This drives the real re-solve deterministically and offline (C-LOCAL): for each domain-based
area it rescales the agent's current problem and confirms the recomputed scene is genuinely
larger and still fully verified; it confirms linear-algebra is not rescalable; and it checks the
frontend gates the control to domain-based areas and wires the /api/rescale round trip.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402

APP_JS = ROOT / "web" / "app.js"
INDEX = ROOT / "web" / "index.html"
SERVER = ROOT / "web" / "server.py"

CASES = [
    ("scalar-fields", "f = x^2 + y^2"),
    ("optimization", "minimize x^2 + 3*y^2"),
    ("vector-fields", "F = (-y, x)"),
    ("dynamical-systems", "show me the Lorenz system"),
]


def _extent(domain):
    return [float(hi) - float(lo) for (lo, hi) in domain]


def main() -> int:
    errs = []

    for area, prompt in CASES:
        agent = build_agent(force="offline")
        agent.run(prompt)
        before = agent.current.get("base_domain")
        if not before:
            errs.append(f"{area}: no base domain to expand from")
            continue
        res = agent.rescale(2.0)
        if res is None or not res.scene:
            errs.append(f"{area}: rescale produced no scene")
            continue
        new = res.scene.get("domain")
        # the scene domain is 2-D (a projection); compare its extent to the base's first two axes
        base_ext = _extent(before)[:2]
        new_ext = _extent(new)
        if not all(n > b + 1e-6 for n, b in zip(new_ext, base_ext)):
            errs.append(f"{area}: expanded domain {new_ext} is not larger than base {base_ext}")
        qs = res.scene.get("quantities") or []
        if not qs or not all((q.get("verification") or {}).get("passed") for q in qs):
            errs.append(f"{area}: expanded scene is not fully verified")

    # linear-algebra is not domain-based — rescale must decline
    la = build_agent(force="offline")
    la.run("eigenvalues of [[2,1],[1,2]]")
    if la.rescale(2.0) is not None:
        errs.append("linear-algebra was rescaled, but it has no domain to expand")

    # the frontend gates and wires the control
    js = APP_JS.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")
    server = SERVER.read_text(encoding="utf-8")
    wiring = [
        ('id="bounds"' in html, "index.html has no bounds control"),
        ('boundsEl.hidden = !domainBased' in js, "app.js does not gate the bounds control to domain-based areas"),
        ('"linear-algebra"' in js, "app.js does not exclude linear-algebra from the bounds control"),
        ("/api/rescale" in js, "app.js does not call the rescale endpoint"),
        ("function applyBounds" in js, "app.js has no apply-bounds action"),
        ('path == "/api/rescale"' in server, "server has no /api/rescale endpoint"),
    ]
    for ok, msg in wiring:
        if not ok:
            errs.append(msg)

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nEXPANDABLE-BOUNDS GAP — {len(errs)} issue(s).")
        return 1
    print(f"  ok    each domain-based area ({', '.join(a for a, _ in CASES)}) re-solves larger and stays verified")
    print("  ok    linear-algebra is not rescalable (no domain); the control is gated off there")
    print("  ok    the frontend gates and wires the bounds control through /api/rescale")
    print("\nEXPANDABLE BOUNDS — the domain expands with verified geometry, gated where meaningless (G20).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
