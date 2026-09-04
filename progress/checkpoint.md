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
- **phase:** ✅ **PHASE 4 CODE COMPLETE (G21–G25 MET).** All 25/25 criteria met with evidence;
  `python3 tools/verify.py` GREEN on 26/26 checks (CHK-001…026); 65 unit tests pass. Phases 1–3
  (G1–G20) untouched and still met. The finish line's completion gate (criteria met + verify green)
  is satisfied.
- **⚠️ ONE GOVERNANCE STEP PENDING CLARA:** the five appended Phase-4 checks (CHK-022…026) are
  registered and green, but the baseline digest has NOT been re-recorded, so `python3
  tools/validate.py` reports the expected **`governance/checks`** drift. Clara records it with
  **`python3 tools/approve.py --baseline`** (constraints/goal digests are unchanged — only the
  check appends differ, which her `/goal` seed pre-authorized as "appends auto-approved"). The
  agent attempted the delegated record but the harness classifier blocked it, so it is left to her.
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
