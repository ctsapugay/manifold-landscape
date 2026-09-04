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

IMPORTANT — the core AND three phases of refinement are BUILT and WORKING; your job is PHASE 4.
Already on main and MET (do NOT weaken any of it): Phase 1 (G1–G10) — the deterministic engine
for all five areas (engine/), the interactive 3D web app (web/), the tool-orchestrating AI agent
(agent/, live Claude + offline fallback), grounded chat, the tool-call toggle + thinking
indicator, and the draw-on animation system. Phase 2 (G11–G15) — genuinely pedagogical tutoring:
a lesson layer (engine/lesson.py) breaks a problem into small single-idea steps with staged
calculations, readable notation (engine/notation.py), a grounded per-step follow-up, and a
whole-set per-case quality gate (CHK-014). Phase 3 (G16–G20) — the conversation redesign: the
explanation and chat are ONE thread; follow-ups answered by the agent's brain; clickable
suggested prompts (incl. "show me the next step"); a launcher → session → new-chat flow with a
collapsible dock; and an expandable visualization domain. python3 tools/verify.py is GREEN
(CHK-001…021); 65 unit tests pass.

PHASE 4 is the open part of the goal (criteria G21–G25, UNMET) — it came from Clara walking the
Phase-3 app. The OUTCOMES still to reach:
  - CHAT SESSIONS SAVED AUTOMATICALLY, and the user can REOPEN a past session (conversation +
    visualization restored) and DELETE one — all local (G21, C-LOCAL).
  - The agent has TOOLS to trigger STEP-BY-STEP PLAYBACK and ANIMATION in the 3D — playing a
    trajectory, animating a process — used both in its explanations and on request (G22).
  - On request the agent RUNS A SIMULATION / SWEEP (e.g. a multi-start gradient-descent sweep to
    see which basin wins most often) and PLAYS THE ACTUAL RUNS BACK ANIMATED, step by step, with
    every reported outcome tool-computed and VERIFIED (G23). New motion/simulation must trace to
    verified computation or be labelled — the new constraint C-VERIFIED-MOTION (build a tool;
    never let the model fabricate motion or invent sweep results).
  - TWO BUGS Clara hit to FIX: (a) interleaving a QUESTION mid-walkthrough left STEPS REPEATED and
    the visual CONFUSED afterward — the walkthrough must stay coherent (next step correct, no
    repeat/skip, clean visual) across interleaved questions (G24); (b) the "Tool calls" view showed
    NOTHING even when tools ran (inconsistent) — the trace must reliably reflect the tools used
    across a solve, a follow-up, and a simulation (G25). (Likely cause of (b): Agent.answer_step
    returns no trace — verify and fix through the criterion's check.)

HOW you achieve these is YOURS to decide inside the constraints — the goal and the constraints say
what must be true, not how. goals/criteria.md is the authoritative finish line (each criterion
names the check that backs it); progress/checkpoint.md carries current state + pointers; python3
tools/brief.py --goal prints live status. Do NOT weaken anything already met (G1–G20) and do NOT
narrow CHK-014. Math — and now MOTION/SIMULATION — stays tool-computed + verified or labelled
model-derived (C-VERIFIED-MATH, C-VERIFIED-MOTION); close a tool gap by building a tool, not by
leaning on the model. Operational: the Anthropic key is in .env (never commit it); run the LIVE
app from the venv (./.venv/bin/python web/server.py) and the offline engine + checks on base
python3; register a check as you make each criterion true (appends auto-approved) and keep python3
tools/verify.py green; editing/removing an existing constraint or check needs Clara.

When you have done all four steps, briefly confirm you understand the system and the
project, and report the current checkpoint and any open blockers. Then wait — I will seed
goal mode with the Phase-4 goal (via /goal). Do not start work until then.
```

## Step 2 — the goal-condition seed (paste ONLY this fenced block into `/goal`)

**This is the goal condition to seed.** After the session has oriented (Step 1), run Claude
Code's `/goal` command and paste **exactly the one fenced block below** — nothing else from this
file, and not the whole `goals/goal-condition.md` doc. It is a deliberately compact contract
(kept **under 4000 characters** for the `/goal` limit) that points at the authoritative files;
`goals/criteria.md` + `constraints/` + `python3 tools/brief.py --goal` are the real, live finish
line. Pasting it puts the worker into goal mode under the constraints, following the persistence /
blocker / checkpoint protocol in `CLAUDE.md`.

```
Enter goal mode on Manifold Landscape. Work toward the finish line defined in goals/criteria.md,
inside the constraints in constraints/, using your own judgment on HOW. The criteria and
constraints say what must be TRUE, never how to build it — you decide the work. The finish line
is GOVERNED: not yours to change (propose via commands/propose.md, don't edit).

THE PRODUCT — a locally-run, AI-tutored tool for building intuition in the geometry of continuous
mathematics across five areas: scalar fields & surfaces, gradients & optimization, vector fields,
linear algebra as geometry, and dynamical systems (ODEs). A user poses a problem however they
like — an equation, a word problem, or an open request like "show me an example of chaos" — and
an AI agent interprets it and orchestrates deterministic tools to solve, visualize, and explain
it, so every value shown is tool-computed and independently verified, or clearly labelled
model-derived (the model doing math itself is a last resort; close gaps by building tools). By
default: the answer plus an interactive 3D visual you can rotate/zoom/pan, shapes drawn on rather
than popped in. On request it TUTORS as ONE conversation — small single-idea steps, multi-stage
calculations shown stage by stage with the matching visual, readable notation, follow-ups
answered by the agent grounded in the step's verified state, clickable suggested prompts, a
start→session→new-chat flow with a collapsible dock, expandable visualization bounds, and
automatically-saved sessions the user can reopen and delete. The agent can drive step-by-step
playback, animation, and simulations/sweeps in the 3D, with every animated or simulated result
verified or labelled (never fabricated). Its tool use is inspectable and reliably reflects the
tools that ran; the visual stays responsive while it thinks. This quality holds across the WHOLE
test set — every case on point on answer, explanation, visual, and animation, judged by driving
all cases, not spot-checks. Built to a portfolio standard.

The authoritative, live finish line is the FILES, not this summary: goals/criteria.md (each
criterion names the check that backs it), constraints/, and python3 tools/brief.py --goal, which
prints them and shows what already holds (G1–G20 met) and what remains (the open phase is
G21–G25). DONE only when EVERY criterion in goals/criteria.md is met with real evidence, AND
python3 tools/verify.py is green, AND every constraint in constraints/ held throughout.

Re-ground with python3 tools/brief.py as you go; work across unblocked fronts, stopping only when
fully blocked or a decision is genuinely dangerous or irreversible; log at natural breaks and keep
progress/checkpoint.md current. Stop when the criteria are met and verify.py is green — then say
so, and don't work past the finish line.
```

> This fenced block is the **seed you paste into `/goal`** — a compact contract, not the whole
> finish line. The source of truth is the **files** it points at: `goals/goal-condition.md`
> (the standing contract), `goals/criteria.md` (the criteria), and `constraints/` — with
> `python3 tools/brief.py --goal` printing them live. Keep this block **under 4000 characters**
> (the `/goal` limit) and refresh it if the finish line changes, but it never needs to enumerate
> every criterion — the files do that.
