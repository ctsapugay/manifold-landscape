#!/usr/bin/env python3
"""CHK — transparent and responsive experience (criterion G7).

G7 has three parts. This backs the automatable slice:

  * the agent exposes an INSPECTABLE trace — the honest data behind the tool-call view: a
    tool sequence and per-call provenance + verification, so "show the agent's tool calls"
    reveals what was actually computed;
  * the interface wires up the transparency TOGGLE and a THINKING INDICATOR (checked in the
    app source), and the scene render loop runs on requestAnimationFrame independently of the
    agent request (so it keeps animating while the agent thinks — the responsiveness whose
    frame budget CHK-002 bounds).

The fully-interactive parts (clicking the toggle, watching the spinner, orbiting while the
agent computes) are verified in the running app and recorded as G7's evidence. Offline, no
network (C-LOCAL).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402

APP_JS = ROOT / "web" / "app.js"
INDEX = ROOT / "web" / "index.html"


def main() -> int:
    errs = []

    # 1. the trace data behind the toggle is present and honest
    agent = build_agent(force="offline")
    r = agent.run("show me an example of chaos")
    trace = r.trace
    if "tool_sequence" not in trace or "calls" not in trace:
        errs.append("agent trace is missing the tool sequence / calls")
    elif not trace["calls"]:
        errs.append("agent trace recorded no tool calls to show")
    else:
        c = trace["calls"][0]
        if not c.get("provenance") or not c.get("produced"):
            errs.append("trace call carries no provenance/produced info to display")
        if not c.get("verified"):
            errs.append("trace does not record verification of tool output")

    # 2. the UI wires up the toggle, the thinking indicator, and an independent render loop
    js = APP_JS.read_text(encoding="utf-8")
    html = INDEX.read_text(encoding="utf-8")
    checks = [
        ('trace-toggle' in html, "index.html has no tool-call toggle control"),
        ('trace-panel' in html, "index.html has no tool-call panel"),
        ('trace-toggle' in js and 'hidden' in js, "app.js does not wire the toggle to show/hide the trace"),
        ('id="thinking"' in html, "index.html has no thinking indicator"),
        ('thinkingEl.hidden = false' in js, "app.js does not show the thinking indicator during a request"),
        ('requestAnimationFrame' in js, "app.js render loop is not on requestAnimationFrame"),
        ('renderTrace' in js, "app.js does not render the trace"),
    ]
    for ok, msg in checks:
        if not ok:
            errs.append(msg)

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nTRANSPARENCY/RESPONSIVENESS GAP — {len(errs)} issue(s).")
        return 1
    print("  ok    agent trace is inspectable (tool sequence + provenance + verification)")
    print("  ok    UI wires the tool-call toggle, thinking indicator, and rAF render loop")
    print("\nTRANSPARENT & RESPONSIVE — the automatable slice of G7 holds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
