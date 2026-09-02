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

After the session has oriented (Step 1), use Claude Code's goal command and paste the block
below to hand it the finish line. It then works toward the goal condition under the
constraints, following the persistence / blocker / checkpoint protocol in `CLAUDE.md`.

```
Enter goal mode on the Manifold Landscape project. Work toward the finish line below, inside
the constraints, using your own judgment on everything the constraints don't fix. This
finish line is governed — not yours to change; if something is wrong, propose it
(commands/propose.md), don't edit it.

GOAL: Manifold Landscape is a locally-run tool for building intuition in the geometry of
continuous mathematics — scalar fields & surfaces, gradients & optimization landscapes,
vector fields, and linear-algebra-as-geometry. It solves a problem with a verification-
backed computation engine so the answer is trustworthy (the model is never the sole source
of a math result — C-VERIFIED-MATH), presents it as an interactive 3D visualization the user
can manipulate and step through, and explains the intuition while answering questions
grounded in the actual computed state. Built to a standard suitable as portfolio work.

DONE only when every criterion is met with real evidence AND python3 tools/verify.py is
green AND every constraint held throughout. The authoritative criteria are in
goals/criteria.md (python3 tools/brief.py --goal prints them live). In brief:
  G1  Correct, verified solutions across all four areas — each matches an independent
      reference, and every displayed value carries engine provenance + passing verification.
  G2  Interactive 3D — rotate / zoom / pan, smooth, no perceptible lag.
  G3  Step-through builds the visualization in sync — each step's geometry appears at its step.
  G4  Grounded Q&A at any step — answers agree with the engine's computed values.
  G5  Polished, unbroken end-to-end flow for every problem in the representative suite.
  G6  Scope + future expansions (physics, 4D+) documented.

Start from progress/checkpoint.md's "next". If this is the first goal-mode session, define
and register the representative problem suite in checks/registry.md and bring it to Clara
for approval before building against it. Re-ground with python3 tools/brief.py as you go.
Keep working across unblocked fronts; stop only when blocked on all fronts or when a decision
is genuinely dangerous. Log at breaks; keep the checkpoint current. Stop when the criteria
are met and verify.py is green — then say so, don't work past the finish line.
```

> This box mirrors the **governed** goal condition (`goals/goal-condition.md`) and criteria
> (`goals/criteria.md`); it is frozen with them. The source of truth is those files —
> `python3 tools/brief.py --goal` prints them live. If a proposal ever changes the finish
> line, refresh this box to match.
