# Priming prompt — worker

A ready-to-paste prompt for starting a fresh **worker** session on this project — after a
context reset, a new day, or a handoff from a session that was getting long. It tells a cold
session what to read to understand the constraint system, what this project is, and where
the current state lives.

For an **observer** session (read-only, watches the worker without interrupting it — often
Clara's phone over Remote Control), use `progress/priming-prompt-observer.md` instead.

It is deliberately **orientation only** — it gets the session to *understand*, and then
stops. Seeding it into goal mode is a separate, second step (see below), so a fresh session
does not start changing things before you have handed it the goal.

This is **progress, not governed content**. Edit it freely; keep it current when the
project's focus shifts (the checkpoint carries the moment-to-moment detail, so this prompt
rarely needs to change).

## How the two-step seed works

1. **Paste the block below** into the fresh session. It reads `CLAUDE.md`, runs
   `brief.py`, and reads the current state — then waits.
2. **Seed goal mode** using Claude Code's own goal command, and hand the session the goal
   condition — paste the goal-condition block (what `python3 tools/brief.py --goal` prints).
   That puts it into goal mode, working toward the finish line under the constraints.

---

## Step 1 — paste this into a fresh session (orientation)

```
You are the worker on the Manifold Landscape project. Get oriented, then STOP and wait for
the goal condition — do not start changing anything yet.

1. Read CLAUDE.md fully — it is the entry point for the constraint system that governs
   this repo: how goal mode works, what you may and may not change, and the persistence /
   blocker / checkpoint protocol in "Staying on task across a long run".
2. Run:  python3 tools/brief.py
   This prints the active constraints, the goal condition and criteria status, any open
   blockers, and the current checkpoint. It is your re-grounding call — run it again
   periodically once you are working.
3. Read progress/checkpoint.md — the current-state "resume here" card: where the work is
   now, what to do next, and what to watch out for.
4. Skim the last few entries of progress/log.md for how we got here, and
   progress/blockers.md for anything stuck.

The project: a locally-run tool for building intuition in the geometry of continuous math
(scalar fields & surfaces, gradients & optimization landscapes, vector fields, and linear-
algebra-as-geometry). It solves problems with a verification-backed engine (never trusting
the model for raw math — constraint C-VERIFIED-MATH), renders interactive 3D visualizations
you can manipulate and step through, and explains the intuition. See goals/ for the full
finish line.

When you have done all four, briefly confirm you understand the system and the project, and
report the current checkpoint and any open blockers. Then wait — I will seed goal mode with
the goal condition next (via /goal). Do not start work until then.
```

## Step 2 — seed goal mode

Use Claude Code's goal command and hand the session the goal condition — paste the block
that `python3 tools/brief.py --goal` prints (the statement plus the criteria). The session
then works toward that finish line under the constraints, following the persistence /
blocker / checkpoint protocol in `CLAUDE.md`.
