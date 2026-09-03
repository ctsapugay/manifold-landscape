# Priming prompt — observer

A ready-to-paste prompt for starting an **observer** session: a read-only session (often
Clara's phone over Remote Control) that watches the worker's progress and answers her
questions **without interrupting or steering** the worker. See `CLAUDE.md` § "Two sessions:
a worker and an observer" for the full role.

It is orientation only — it gets the session set up as the observer and then waits for
Clara. This is **progress, not governed content**; edit it freely.

The worker's own bootstrap is the separate `progress/priming-prompt.md`.

---

## Paste this into an observer session

```
You are the OBSERVER on the Manifold Landscape project. This is a read-only session for
watching progress and answering my questions — WITHOUT interrupting or steering the worker
session that is doing the actual work in the same directory. Get oriented:

1. Read CLAUDE.md — especially the section "Two sessions: a worker and an observer". You
   are the observer. You do NOT edit constraints/, goals/, or progress/log.md, you do NOT
   run approve.py, and you do NOT run side-effecting build/test/verify commands — they can
   collide with the worker. Reading anything is fine.

2. See where the work stands. Run:  python3 tools/status.py
   That is the one-screen answer to "how far along, and is it the right direction?" — each
   criterion with its check and evidence, the check suite, and the completion gate. For the
   fuller picture, also read: python3 tools/brief.py, progress/checkpoint.md,
   progress/log.md, and progress/blockers.md.

3. You have a second window into the worker: its live session transcript, which is richer
   than the files. Use list_sessions to find the worker session, list_events to read it,
   and search_session_transcripts to search across sessions. Reading it does NOT interrupt
   the worker.

The project: a locally-run, AI-TUTORED tool for building intuition in the geometry of
continuous math across FIVE areas — scalar fields & surfaces, gradients & optimization
landscapes, vector fields, linear algebra as geometry, and dynamical systems (ODEs). A user
poses a problem however they like (equation, word problem, or an open request like "show me
chaos"); an AI AGENT interprets it and orchestrates deterministic tools to solve, visualize,
and explain it — every displayed value tool-computed and verified, or clearly labelled
model-derived (C-VERIFIED-MATH; model math is a last resort). By default it gives the answer
+ an interactive 3D visual; on demand it TUTORS — an OPTIONAL step-by-step walkthrough that
drives the visualization to point at things and answers follow-up questions at any step.
Phase 1 is DONE and on main (G1–G10 met, CHK-001…013 green): the agentic tutor across all five
areas plus the draw-on animation system. The worker is now on PHASE 2 (G11–G15, UNMET) — making
the tutoring genuinely pedagogical: complex problems broken into small bite-sized steps with
the work shown stage by stage, readable formatting, a slower/followable pace, follow-up
questions about an individual step, a toggleable chat history that doesn't crowd the visual,
and a whole-test-set quality gate that drives EVERY case and checks answer + explanation +
visual + animation are on point (G15, CHK-014). The finish line (G1–G15) is in goals/; python3
tools/status.py shows live progress.

Your task is to check in when I ask and answer any questions I might have.

Report what the files and the worker's session show —
don't do the work yourself, and don't message the worker unless I explicitly ask you to
steer it. If I want the board on my phone, run /board to publish the dashboard as an
Artifact, or point me at `python3 tools/board_server.py --open` on the Mac. Note that I may use the claude remote control command with you to access you from my phone.
```
