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
2. **Seed goal mode** using Claude Code's own goal command (`/goal`), and hand the session
   the goal condition — paste the goal-condition block in Step 2 (it mirrors what
   `python3 tools/brief.py --goal` prints). That puts it into goal mode, working toward the
   finish line under the constraints.

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

The project: a locally-run, AI-TUTORED tool for building intuition in the geometry of
continuous math across FIVE areas — scalar fields & surfaces, gradients & optimization
landscapes, vector fields, linear algebra as geometry, and dynamical systems (ODEs). A user
poses a problem HOWEVER they like (an equation, a word problem, or an open request like
"show me an example of chaos"); an AI AGENT interprets it and ORCHESTRATES a set of
deterministic tools to solve, visualize, and explain it — so every displayed value is
tool-computed and verified, or clearly labelled model-derived (constraint C-VERIFIED-MATH;
model math is a LAST RESORT — close gaps by building tools). By default it gives the answer
plus an interactive 3D visual you can manipulate; the step-by-step walkthrough is OPTIONAL —
when the user asks for it, it TUTORS, building the visual in sync and driving it to point at
what matters, and it answers questions at any step, grounded in the computed state.

IMPORTANT — the core is BUILT and WORKING, not a greenfield build. On main and passing:
the deterministic engine for all five areas (engine/), the interactive 3D web app (web/),
the tool-orchestrating AI agent (agent/, live Claude path + offline fallback), multi-turn
grounded chat, the transparency toggle and thinking indicator, and the draw-on animation
system — shapes DRAW/GROW themselves on (surfaces grow from the centre by default, with a
top-bar toggle that blooms level-set CONTOURS from the centre and back), the vector field
fades in, and a walkthrough ends framed on the whole picture. All ten criteria (G1–G10) are
MET with evidence and python3 tools/verify.py is GREEN (CHK-001…013); the goal condition is
`met`. When you hit a math gap the tools can't close, BUILD a deterministic tool for it (or
generate + execute + verify code) rather than letting the model compute the answer — model
math is a last resort and must be labelled model-derived (C-VERIFIED-MATH). The agent calls
the Anthropic (Claude) API — key lives in .env (gitignored; never commit it); the LIVE path
runs from the isolated venv (./.venv/bin/python web/server.py), the offline engine + all
checks run on base python3. Continued development is Clara-directed — she hands you the next
goal. See goals/ for the finish line and progress/checkpoint.md for exactly where things stand.

When you have done all four steps, briefly confirm you understand the system and the
project, and report the current checkpoint and any open blockers. Then wait — I will seed
goal mode with the next goal (via /goal). Do not start work until then.
```

## Step 2 — seed goal mode

After the session has oriented (Step 1), use Claude Code's `/goal` command and paste the
block below to hand it the finish line. It then works toward the goal condition under the
constraints, following the persistence / blocker / checkpoint protocol in `CLAUDE.md`.

```
Enter goal mode on the Manifold Landscape project. Work toward the finish line below, inside
the constraints, using your own judgment on everything the constraints don't fix. This
finish line is governed — not yours to change; if something is wrong, propose it
(commands/propose.md), don't edit it.

GOAL: Manifold Landscape is a locally-run, AI-tutored tool for building intuition in the
geometry of continuous mathematics across five areas — scalar fields & surfaces, gradients &
optimization landscapes, vector fields, linear algebra as geometry, and dynamical systems
(ODEs). A user poses a problem however they like (equation, word problem, or open conceptual
request); an AI agent interprets it and orchestrates deterministic tools to solve it, so
every displayed result is tool-computed and verified or clearly labelled model-derived
(C-VERIFIED-MATH; the model computing math itself is a last resort — close gaps by building
tools). By default it presents the answer as an interactive 3D visualization the user can
manipulate; when the user asks, it tutors — an optional step-by-step walkthrough that builds
the visualization in sync, drives it to point at what matters, and answers follow-up
questions at any step, grounded in the computed state. The agent's tool use is inspectable,
and the visualization stays responsive while it thinks. Built to a portfolio standard that
shows off mathematical depth and agentic-AI craft.

DONE only when every criterion is met with real evidence AND python3 tools/verify.py is
green AND every constraint held throughout. The authoritative criteria are in
goals/criteria.md (python3 tools/brief.py --goal prints them live). In brief:
  G1  Trustworthy math — every displayed result is tool-computed + verified, or clearly
      labelled model-derived; nothing unverified is shown as verified; model math is a last
      resort (close gaps by building tools), not routine.
  G2  Broad coverage — solves ≥90% of a large held-out test set across all five areas and
      all input styles (equation / word problem / conceptual), 100% of the protected core;
      out-of-scope requests mapped or honestly declined.
  G3  Agentic solving — an AI agent interprets input and orchestrates the tools (not a fixed
      pipeline); math is done by tools (or, only where none applies, by the agent per G1).
  G4  Answer + interactive 3D by DEFAULT (rotate/zoom/pan smooth, nothing forced); the
      step-through is an OPTIONAL opt-in walkthrough that builds the scene in sync, each step
      showing exactly its geometry.
  G5  The tutor drives the visualization — during the walkthrough or on a question, it
      focuses/highlights/transforms the relevant feature when it aids understanding.
  G6  Grounded multi-turn chat at any step — answers agree with the computed state, claims
      trace to a computed result or are labelled model-derived.
  G7  Transparent & responsive — a toggle shows the agent's tool-calls; a thinking indicator
      shows during agent work; the 3D stays smooth while it thinks.
  G8  Polished, unbroken end-to-end flow across the test set (pose → interpret → solve →
      visualize → step → chat).
  G9  Scope + future expansions documented (five areas; deferred PDEs, physics, 4D+).
  G10 Shapes are DRAWN ON — each shape builds up progressively (not a pop or whole-fade),
      the field fades in, a walkthrough ends framed on the whole picture; a surface grows
      from its CENTRE by default and the user can switch it to a CONTOUR bloom and back.

On main and complete: engine/ (deterministic tools for all five areas), web/ (the
interactive 3D app + draw-on animation system), agent/ (the tool-orchestrating agent, live
Claude path + offline fallback), tests/, and CHK-001…013 — all green, goal `met`. This goal
is DONE; a fresh session is for the NEXT goal Clara defines, or for maintenance that keeps
G1–G10 true and verify.py green. When a math gap can't be closed by an existing tool, BUILD
one (or generate + execute + verify code) rather than letting the model compute the answer —
model math is a last resort, always labelled model-derived. The Anthropic API key lives in
.env (never commit it — C-SECRETS); run the LIVE app from the venv (./.venv/bin/python
web/server.py), run checks on base python3. Register new checks as you build (appends are
auto-approved per Clara's standing policy; editing/removing an existing check or constraint
needs her sign-off). Test-set rule: you may ADD problems freely, but removing/weakening a
protected-core problem needs Clara's approval.

Start from progress/checkpoint.md's "next". Re-ground with python3 tools/brief.py as you go.
Keep working across unblocked fronts; stop only when blocked on all fronts or when a decision
is genuinely dangerous. Log at breaks; keep the checkpoint current. Stop when the criteria
are met and verify.py is green — then say so, don't work past the finish line.
```

> This box mirrors the **governed** goal condition (`goals/goal-condition.md`) and criteria
> (`goals/criteria.md`); it is frozen with them. The source of truth is those files —
> `python3 tools/brief.py --goal` prints them live. If a proposal ever changes the finish
> line, refresh this box to match.
