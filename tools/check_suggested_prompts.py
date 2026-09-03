#!/usr/bin/env python3
"""CHK-019 — the user is offered clickable suggested prompts (G18).

Continuing the walkthrough and asking common questions should not require typing: the dock shows
clickable suggestions — including one that advances to the next step and drives the visual — and
the launcher offers example prompts to start from. Frontend wiring checked in the app source; the
felt behaviour is confirmed in the running app. Offline (C-LOCAL).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_JS = ROOT / "web" / "app.js"
INDEX = ROOT / "web" / "index.html"


def main() -> int:
    errs = []
    js = APP_JS.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")

    checks = [
        ('id="suggestions"' in html, "index.html has no suggested-prompts row"),
        ("function updateSuggestions" in js, "app.js builds no suggested prompts"),
        ("class = \"sugchip\"" in js or "sugchip" in js, "app.js suggested prompts have no chips"),
        # a suggestion that advances the walkthrough and moves the visual
        ("function nextStep" in js, "app.js has no next-step action"),
        ("show me the next step" in js, "app.js offers no 'show me the next step' suggestion"),
        ("next: true" in js, "app.js suggestions do not flag the next-step action"),
        ("nextStep()" in js, "app.js next-step suggestion is not wired to advance"),
        ("driveStep" in js, "app.js next-step does not drive the visualization"),
        (".onclick = ()" in js and "sendQuestion" in js, "app.js question suggestions are not clickable"),
        # example prompts on the launcher, to start without typing
        ('class="ex"' in html, "index.html launcher has no example prompts"),
    ]
    for ok, msg in checks:
        if not ok:
            errs.append(msg)

    # nextStep must both append a step message and drive the visual
    start = js.find("function nextStep")
    if start != -1:
        body = js[start:start + 600]
        if "appendStepMsg" not in body or "driveStep" not in body:
            errs.append("nextStep does not both add the step message and move the visualization")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nSUGGESTED-PROMPTS GAP — {len(errs)} issue(s).")
        return 1
    print("  ok    clickable suggested prompts, including 'show me the next step'")
    print("  ok    the next-step suggestion advances the walkthrough and drives the visual")
    print("  ok    the launcher offers example prompts to start from")
    print("\nSUGGESTED PROMPTS — common moves are a click away (G18).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
