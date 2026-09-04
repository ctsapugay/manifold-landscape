#!/usr/bin/env python3
"""CHK-017 — the explanation and the conversation are one thread (G16).

The walkthrough's steps, the user's questions, and the agent's answers all live in a single
thread with one composer — not a separate explanation card plus a separate per-step input and a
separate history panel. This backs the automatable slice (the felt single-surface experience is
confirmed in the running app); the frontend wiring is checked in the app source. Offline (C-LOCAL).
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
        # one thread, one composer
        ('id="thread"' in html, "index.html has no single conversation thread"),
        ('id="composer"' in html, "index.html has no single composer"),
        ('id="chat-input"' in html, "index.html has no conversation input"),
        # the SAME thread holds walkthrough steps, user turns and agent turns
        ("function appendStepMsg" in js, "app.js does not render walkthrough steps into the thread"),
        ('className = "msg tutor"' in js or 'msg tutor' in js, "app.js step messages are not thread messages"),
        ("threadEl.appendChild" in js, "app.js does not append messages to the one thread"),
        ("function pushUserMsg" in js and "function pushAgentMsg" in js,
         "app.js does not put user and agent turns in the thread"),
        # NO separate per-step question box and NO separate standalone history panel
        ('id="step-ask"' not in html, "index.html still has a separate per-step input box"),
        ('id="history-panel"' not in html, "index.html still has a separate history panel"),
        ('id="tutor-card"' not in html, "index.html still has the separate tutor card"),
    ]
    for ok, msg in checks:
        if not ok:
            errs.append(msg)

    # the step message, the user message and the agent message must all target the same thread
    for fn in ("function pushUserMsg", "function pushAgentMsg", "function appendStepMsg"):
        start = js.find(fn)
        if start != -1:
            nxt = js.find("\nfunction ", start + len(fn))
            body = js[start:nxt if nxt != -1 else start + 900]
            if "threadEl.appendChild" not in body:
                errs.append(f"{fn.split()[1]} does not append into the shared thread")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nONE-THREAD GAP — {len(errs)} issue(s).")
        return 1
    print("  ok    steps, questions and answers all render into one thread with one composer")
    print("  ok    no separate per-step input box and no separate standalone history panel")
    print("\nONE CONVERSATION — the explanation and the chat are a single thread (G16).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
