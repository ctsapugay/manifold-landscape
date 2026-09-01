---
description: Render the Constraint Board and publish it — once, or watch and re-publish live
---

Render the phone-friendly progress dashboard and publish it as an Artifact, always to the
**same URL** so a bookmark shows the latest. `$ARGUMENTS` selects the mode.

## Publishing (all modes)

- Render: `python3 tools/status.py --html --out checks/board.html`
- Publish, keeping the link stable:
  - If `checks/board-url.txt` exists, read the URL and update *that* artifact (pass it as
    the artifact `url`).
  - Otherwise publish `checks/board.html` as a new artifact — title "Constraint Board",
    favicon 🧭 — then write its URL to `checks/board-url.txt`.

## Modes

- **`/board`** (no argument): publish once and report the URL. Do **not** re-run checks —
  from an observer session while the worker is mid-task, re-running could collide with it.
  Skipping is safe: the board shows a STALE flag when the code changed since the last
  verify. If it's stale, tell Clara to run `/board fresh` or have the worker run verify.

- **`/board fresh`**: run `python3 tools/verify.py` first (only if no other session is
  actively running the worker here), then publish once. Use when you want the checks
  re-proven now.

- **`/board watch`**: publish once as above, then keep the Artifact live:
  1. Run `python3 tools/board_watch.py --once` — it blocks until the board's state
     actually changes (a criterion ticks over, a verify run lands, drift appears), or
     returns `timeout` after ~50s with nothing changed.
  2. On `changed`, re-render and re-publish to the same URL. On `timeout`, do nothing and
     loop again to keep watching.
  3. Repeat until Clara stops it (interrupt, or "stop the board"). Do **not** re-run checks
     in this loop — a worker verify run is itself a change the watcher will catch.

  Tell Clara plainly what watch mode is: this keeps *this* session working in a loop, and
  it re-publishes the Artifact whenever the board moves. Whether her open phone tab updates
  on its own or needs a pull-to-refresh depends on the Claude app; either way the link
  always holds the latest. For a guaranteed no-refresh view she is at the Mac for, point
  her at `python3 tools/board_server.py --open` instead.

This command is read-only over the constraint system: it renders and publishes state, and
never edits constraints, goals, the registry, or runs `approve.py`.
