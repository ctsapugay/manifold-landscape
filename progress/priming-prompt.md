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

IMPORTANT — the core is BUILT and WORKING; your job is PHASE 2, making the tutoring genuinely
pedagogical. Phase 1 (on main, all MET): the deterministic engine for all five areas
(engine/), the interactive 3D web app (web/), the tool-orchestrating AI agent (agent/, live
Claude + offline fallback), multi-turn grounded chat, the transparency toggle + thinking
indicator, and the draw-on animation system (shapes draw/grow on; surfaces grow from the
centre with a toggle that blooms level-set CONTOURS and back). Criteria G1–G10 are met and
python3 tools/verify.py is GREEN (CHK-001…013).

PHASE 2 is the open part of the goal (criteria G11–G15, UNMET). It came from Clara reviewing
the tutor on a multi-part Lorenz problem and finding it not good enough at TEACHING. The
OUTCOMES still to reach — the finished tutor must: teach a complex problem in small,
bite-sized, single-idea steps that show multi-stage calculations stage by stage with the
matching visual, at a pace a first-time learner can follow; give clearly formatted, readable
explanations (not walls of text, math shown as notation); let the user ask follow-up questions
about an individual step; give the user their chat history through a control that doesn't crowd
the visual; and hold this quality across the WHOLE test set — every case on point on answer,
explanation, visual, and animation, judged by driving all cases, not spot-checks.

HOW you achieve these is YOURS to decide inside the constraints — the goal and the constraints
say what must be true, not how to build it. goals/criteria.md is the authoritative finish line
(each criterion names the check that backs it), and progress/checkpoint.md carries the current
state and useful pointers; python3 tools/brief.py --goal prints live status. Do NOT weaken
anything already met (G1–G10). Math stays tool-computed + verified or labelled model-derived
(C-VERIFIED-MATH); when a tool gap appears, prefer building a tool over letting the model
compute. Operational: the Anthropic key is in .env (never commit it); run the LIVE app from the
venv (./.venv/bin/python web/server.py) and the offline engine + checks on base python3; you may
add constraints/checks freely (appends are auto-approved) but editing or removing an existing
one needs Clara; keep python3 tools/verify.py green as you go.

When you have done all four steps, briefly confirm you understand the system and the
project, and report the current checkpoint and any open blockers. Then wait — I will seed
goal mode with the Phase-2 goal (via /goal). Do not start work until then.
```

## Step 2 — seed goal mode

After the session has oriented (Step 1), use Claude Code's `/goal` command and paste the
block below to hand it the finish line. It then works toward the goal condition under the
constraints, following the persistence / blocker / checkpoint protocol in `CLAUDE.md`.

```
Enter goal mode on Manifold Landscape. Work toward the finish line below, inside the
constraints in constraints/, using your own judgment on HOW to get there. The constraints and
this goal say what must be TRUE, never how to build it — you decide the work. This finish line
is GOVERNED: not yours to change (propose via commands/propose.md, don't edit).

THE PRODUCT — a locally-run, AI-tutored tool for building intuition in the geometry of
continuous mathematics across five areas: scalar fields & surfaces, gradients & optimization,
vector fields, linear algebra as geometry, and dynamical systems (ODEs). What must be true of
it:
- A user can pose a problem however they like — an equation, a word problem, or an open
  request like "show me an example of chaos".
- An AI agent interprets the request and orchestrates deterministic tools to solve it, so every
  result the user sees is tool-computed and independently verified, or else clearly labelled as
  model-derived (the model doing the math itself is a last resort).
- By default it answers with an interactive 3D visualization the user can rotate, zoom, and pan
  smoothly; shapes appear by being drawn on, not by popping in.
- On request it TUTORS: a genuinely pedagogical walkthrough that breaks a complex problem into
  small, bite-sized, single-idea steps, shows multi-stage calculations stage by stage with the
  matching visual, is clearly formatted and readable, and is paced so a first-time learner can
  follow it.
- The user can ask follow-up questions about any individual step, answered from that step's
  verified state, and can bring up their chat history through a clean control that never crowds
  the visualization.
- The agent's tool use is inspectable, and the visualization stays responsive while it thinks.
- This quality holds across the WHOLE test set: every case is on point on every dimension the
  user experiences — the answer, the explanation, the visualization, and the animation — judged
  by driving all the cases, not by spot-checking a few.
It is built to a portfolio standard that shows mathematical depth and agentic-AI craft.

DONE only when every criterion in goals/criteria.md is met with real evidence, AND
`python3 tools/verify.py` is green, AND every constraint in constraints/ held throughout. Those
files — not this paragraph — are the authoritative finish line; `python3 tools/brief.py --goal`
prints them live and shows which outcomes already hold and which remain. Within the
constraints, you have full freedom to decide what work achieves them.

Re-ground with `python3 tools/brief.py` as you go; work across unblocked fronts, stopping only
when fully blocked or a decision is genuinely dangerous or irreversible; log at natural breaks
and keep progress/checkpoint.md current. Stop when the criteria are met and verify.py is green —
then say so, and don't work past the finish line.
```

> This box mirrors the **governed** goal condition (`goals/goal-condition.md`) and criteria
> (`goals/criteria.md`); it is frozen with them. The source of truth is those files —
> `python3 tools/brief.py --goal` prints them live. If a proposal ever changes the finish
> line, refresh this box to match.
