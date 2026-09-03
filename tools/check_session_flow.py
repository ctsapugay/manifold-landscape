#!/usr/bin/env python3
"""CHK-020 — start state → session → new chat, with a collapsible conversation (G19).

A single centred launcher opens into a session that preserves the opening prompt as the first
thread entry; a "new chat" control returns to the launcher; and the conversation collapses to
free the visualization and restores cleanly. Frontend wiring checked in the app source; the felt
flow is confirmed in the running app. Offline (C-LOCAL).
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
        # a single centred launcher (start state)
        ('id="launcher"' in html, "index.html has no start-state launcher"),
        ('id="launch-input"' in html, "index.html launcher has no composer"),
        ("function solveProblem" in js, "app.js does not pose a problem from the launcher"),
        ("function startSession" in js, "app.js does not open a session"),
        ("launcher.hidden = true" in js, "app.js does not leave the launcher when a session starts"),
        # the opening prompt is preserved as the first thread entry
        ("pushUserMsg(userText)" in js, "app.js does not preserve the opening prompt in the thread"),
        # a new-chat control returns to the launcher
        ('id="new-chat"' in html, "index.html has no new-chat control"),
        ("function newChat" in js, "app.js has no new-chat action"),
        ("newChatBtn.onclick = newChat" in js, "app.js does not wire the new-chat control"),
        ("launcher.hidden = false" in js, "app.js new-chat does not return to the launcher"),
        # the conversation collapses to free the visual and restores
        ('id="dock-collapse"' in html, "index.html has no collapse control"),
        ('id="dock-tab"' in html, "index.html has no reopen tab"),
        ("dockCollapse.onclick" in js and "dockTab.onclick" in js,
         "app.js does not wire collapse/restore of the conversation"),
    ]
    for ok, msg in checks:
        if not ok:
            errs.append(msg)

    # startSession must open the session (leave launcher, show dock) AND seed the opening prompt
    start = js.find("function startSession")
    if start != -1:
        end = js.find("\nfunction ", start + 10)
        body = js[start:end if end != -1 else start + 1600]
        if "launcher.hidden = true" not in body or "dock.hidden = false" not in body:
            errs.append("startSession does not open the session UI")
        if "pushUserMsg(userText)" not in body:
            errs.append("startSession does not seed the opening prompt as the first thread entry")
    # newChat must reset back to the launcher
    start = js.find("function newChat")
    if start != -1:
        body = js[start:start + 700]
        if "launcher.hidden = false" not in body or "dock.hidden = true" not in body:
            errs.append("newChat does not return cleanly to the launcher")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nSESSION-FLOW GAP — {len(errs)} issue(s).")
        return 1
    print("  ok    a centred launcher opens into a session, preserving the opening prompt")
    print("  ok    a new-chat control returns to the launcher")
    print("  ok    the conversation collapses to free the visual and restores")
    print("\nSESSION FLOW — start → session → new chat, conversation collapsible (G19).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
