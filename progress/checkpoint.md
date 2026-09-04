# Checkpoint

The **current-state** snapshot — overwritten in place, not appended. Unlike
`progress/log.md` (which is history), this is the single short "resume here" card: where
the work stands *right now*, what to do next, and what is live in the agent's head that the
files alone would not tell a fresh session.

Refresh this at natural breaks, before context grows large, and whenever the session shows
signs of drift or rot. When a session is getting long, refresh this and recommend starting
a fresh one — a new session resuming from this card plus `python3 tools/brief.py` beats a
long, degraded one. This is **progress, not governed content**.

`tools/brief.py` prints this checkpoint every time it runs.

**Format:** keep it short. Replace the body below each refresh.

---

- **updated:** 2026-09-04
- **phase:** ✅ **PHASE 4 COMPLETE + LIVE-VERIFIED (G21–G25 MET).** All 25/25 criteria met;
  `python3 tools/verify.py` GREEN (26/26); 65 unit tests pass; baseline recorded & committed;
  code committed (not yet pushed — awaiting Clara's OK). Phases 1–3 (G1–G20) untouched.
- **LIVE full-suite drive done (Clara's bar):** every one of the 39 `suite/agent_tests.json`
  cases driven through the REAL Claude brain (`.env` key), not the offline path. First drive
  failed (core 17/20 — a PDE bluffed, "minimize" on the wrong solver, a stray model-derived
  angle); after hardening (deterministic out-of-scope pre-decline in `Agent.run`; interpreter
  tool-read injected as a first-turn hint; stricter system prompt) the re-drive is **LIVE 39/39 =
  100%, protected core 20/20 = 100%**, all out-of-scope declined. Phase-4 flows (animate /
  simulate / follow-up trace) also driven live and passing. See the 2026-09-04 log entries.
- **known limitation (not a finish-line gap):** the live agent may gracefully DECLINE to
  plain-solve some quartics as scalar fields (critical-point verification fails, e.g.
  `(x^2-1)^2+0.3x+y^2`); the SWEEP on the same landscape still works. Candidate future engine fix.
- **what shipped (G21–G25):**
  1. **G21** — sessions auto-save to `localStorage`; start-screen list reopens (thread replayed +
     scene re-solved via new `/api/restore` + `Agent.restore`, so follow-ups keep working) and
     deletes. CHK-022.
  2. **G22** — `animate_motion` agent tool → well-formed `animate` directive whose path is a
     verified trajectory/descent; frontend plays a marker along it. CHK-023 (C-VERIFIED-MOTION).
  3. **G23** — engine `OptimizationLandscape.descent_sweep` (verified multi-start descent →
     per-basin counts) + `run_simulation` tool; frontend animates all runs into basins. CHK-024.
  4. **G24** — `answer_step` never disturbs the walkthrough; typed "next" routes to local
     `nextStep`; live brain told not to re-solve mid-question. CHK-025.
  5. **G25** — `answer_step` now returns its trace; view-moving follow-ups go through `focus_view`;
     tool-free replies show "answered from context". CHK-026.
- **guardrails held:** G1–G20 untouched; CHK-014 not narrowed; all new motion/sim rests on the
  verified Quantity path (C-VERIFIED-MATH, C-VERIFIED-MOTION). Only a non-governed check SCRIPT
  (`check_one_thread.py`) was widened (assertion unchanged) after `pushAgentMsg` grew.
- **HOW TO RUN:** live `./.venv/bin/python web/server.py` → :8765; offline `ANTHROPIC_API_KEY=""
  python3 web/server.py`; checks `python3 tools/verify.py`. (An offline server was run on :8770 for
  browser verification this session.)
- **uncommitted:** the Phase-4 code (agent/, engine/, web/, tools/*.py) + criteria evidence +
  registry appends are on disk, uncommitted. No push was requested for Phase 4. Clara: record the
  baseline, then commit when ready.
- **next:** Clara runs `approve.py --baseline` to record the check appends; optionally commit the
  code. Then Phase 4 is fully closed. Do NOT work past the finish line.
- **open blockers:** none.
