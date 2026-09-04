#!/usr/bin/env python3
"""CHK — chat sessions are saved automatically and managed by the user (criterion G21).

Sessions are persisted locally (the browser's localStorage — C-LOCAL), listed on the start
screen, re-opened (conversation + visualization restored), and deleted. This check guards:

Backend contract (deterministic, offline): a solved problem exposes a DESCRIPTOR, and
``Agent.restore(descriptor)`` re-solves it — rebuilding the (verified) visualization AND
re-establishing the server agent's current problem, so a follow-up on a re-opened session
still works (rather than "solve a problem first"). This is what makes re-open faithful and
keeps restored math tool-verified (C-VERIFIED-MATH).

Frontend wiring (app source, like the other UI-slice checks): auto-save to localStorage after
a turn, a listed set of saved sessions on the start screen, a re-open that restores the thread
and re-solves the scene, and a delete control.

Backs criterion G21.
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


def _backend_contract(errs):
    agent = build_agent(force="offline")
    r = agent.run("minimize x^2 + 3y^2 starting at (3,2)")
    desc = r.descriptor
    if not desc:
        errs.append("a solved problem does not expose a descriptor to save")
        return
    # a fresh server-side agent (as if the app was reopened) restores from the descriptor
    fresh = build_agent(force="offline")
    restored = fresh.restore(desc)
    if restored is None or not restored.scene:
        errs.append("Agent.restore did not rebuild the visualization from a saved descriptor")
        return
    if restored.area != r.area:
        errs.append("restored session is a different area than the saved one")
    if not any(q.get("verification", {}).get("passed") for q in restored.scene.get("quantities", [])):
        errs.append("restored scene is not tool-verified")
    # the restored session's follow-ups still work (agent.current was re-established)
    step = {"quantity": "minimum", "focus": "the minimum", "focus_target": [0, 0, 0],
            "id": "opt-min-loc", "title": "The minimum"}
    f = fresh.answer_step("where is the minimum?", step)
    if f.declined or not f.grounded_in:
        errs.append("a follow-up on a re-opened session was declined / not grounded "
                    "(the server agent's problem was not restored)")


def _frontend_wiring(errs):
    js = APP_JS.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")
    server = SERVER.read_text(encoding="utf-8")

    checks = [
        # local persistence
        ("localStorage" in js, "app.js does not use localStorage to persist sessions"),
        ("function saveSession" in js, "app.js has no saveSession"),
        ("saveSession()" in js, "app.js never calls saveSession after a turn"),
        # listing on the start screen
        ('id="recent"' in html, "index.html has no saved-sessions area on the start screen"),
        ('id="session-list"' in html, "index.html has no session list"),
        ("function renderSessionList" in js, "app.js does not render the session list"),
        ("renderSessionList()" in js, "app.js never renders the session list"),
        # re-open restores conversation + visualization
        ("function reopenSession" in js, "app.js has no reopenSession"),
        ("function replayThread" in js, "app.js does not replay a saved conversation"),
        ("/api/restore" in js, "app.js reopen does not restore the scene via /api/restore"),
        ("/api/restore" in server, "server.py has no /api/restore endpoint"),
        ("def restore" in (ROOT / "agent" / "agent.py").read_text(encoding="utf-8"),
         "Agent has no restore method"),
        # delete
        ("function deleteSession" in js, "app.js has no deleteSession"),
        ("rc-del" in js and "rc-del" in html or "rc-del" in js,
         "app.js has no delete control wiring"),
    ]
    for ok, msg in checks:
        if not ok:
            errs.append(msg)

    # saveSession must be called on the solve/session-start path
    ss = js.find("function startSession")
    sbody = js[ss:js.find("\nfunction ", ss + 10)] if ss != -1 else ""
    if "saveSession()" not in sbody:
        errs.append("startSession does not auto-save the session")


def main() -> int:
    errs: list[str] = []
    _backend_contract(errs)
    _frontend_wiring(errs)

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nSESSION-PERSISTENCE GAP — {len(errs)} issue(s).")
        return 1
    print("  ok    a solved problem is restorable from its descriptor (scene re-verified)")
    print("  ok    a re-opened session's follow-ups still work (server problem restored)")
    print("  ok    sessions auto-save locally, list on the start screen, re-open and delete")
    print("\nSESSIONS PERSISTED — saved automatically, re-openable and deletable, all local (G21).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
