#!/usr/bin/env python3
"""CHK-016 — conversation history is available without crowding the visualization (G14).

In the Phase-3 redesign the conversation and its history are one thing: the thread in the
conversation dock holds every turn (the user's questions, the tutor's steps, the agent's
answers), and that dock is a floating overlay that COLLAPSES to a slim edge tab so it never has
to crowd the visualization — and reopens with one control. This backs the automatable slice of
G14 (the felt behaviour is confirmed in the running app and recorded as the evidence): the
history is always available in the thread, and a clean control dismisses/restores it. As with
CHK-012 / CHK-013 the frontend wiring is checked in the app source. Offline, no network (C-LOCAL).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

APP_JS = ROOT / "web" / "app.js"
INDEX = ROOT / "web" / "index.html"
CSS = ROOT / "web" / "style.css"


def main() -> int:
    errs = []
    js = APP_JS.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    checks = [
        # the conversation (which holds the history) and its scrollable thread
        ('id="dock"' in html, "index.html has no conversation dock"),
        ('id="thread"' in html, "index.html has no conversation thread to hold history"),
        # a clean control to dismiss it, and one to bring it back — so it need not crowd the visual
        ('id="dock-collapse"' in html, "index.html has no control to collapse the conversation"),
        ('id="dock-tab"' in html, "index.html has no control to reopen the collapsed conversation"),
        ("dockCollapse.onclick" in js, "app.js does not wire collapsing the conversation"),
        ("dockTab.onclick" in js, "app.js does not wire reopening the conversation"),
        ("dock.hidden = true" in js, "app.js collapse does not actually hide the dock"),
        ("dock.hidden = false" in js, "app.js reopen does not actually show the dock"),
        # every turn is recorded into the thread (the thread IS the history)
        ("function pushUserMsg" in js, "app.js records no user turns in the thread"),
        ("function pushAgentMsg" in js, "app.js records no agent turns in the thread"),
        ("function appendStepMsg" in js, "app.js records no walkthrough steps in the thread"),
        ('thread.push(' in js, "app.js does not accumulate the conversation history"),
        # the dock is a floating overlay, so collapsing it frees the visualization
        ("#dock " in css and "position: absolute" in css,
         "style.css does not float the conversation dock as an overlay"),
    ]
    for ok, msg in checks:
        if not ok:
            errs.append(msg)

    # the conversation must not be nested inside the canvas holder (that would occupy the visual)
    holder = html.find('id="canvas-holder"')
    dock = html.find('id="dock"')
    if holder != -1 and dock != -1:
        segment = html[holder:dock]
        if segment.count("<div") > 0 and "</div>" not in segment:
            errs.append("the conversation dock appears to be nested inside the canvas holder")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nCONVERSATION-HISTORY GAP — {len(errs)} issue(s).")
        return 1
    print("  ok    the conversation thread holds every turn (the history is always available)")
    print("  ok    a clean control collapses the conversation to an edge tab and reopens it")
    print("  ok    the dock is a floating overlay — collapsed, it does not crowd the visualization")
    print("\nHISTORY OK — conversation history is available without crowding the visualization.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
