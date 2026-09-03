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

- **updated:** 2026-09-03
- **phase:** ✅ **PHASE 2 COMPLETE — pedagogical depth (G11–G15 MET).** Completion gate reads
  **✓ COMPLETE**: 15/15 criteria met, `python3 tools/verify.py` GREEN (16/16, CHK-001…016),
  65-test unit suite green. Goal-condition `state: met`. G1–G10 not weakened.
- **⚠️ ONE GOVERNANCE STEP FOR CLARA (only remaining item):** two checks were APPENDED —
  **CHK-015** (`tools/check_step_followup.py`, G13) and **CHK-016**
  (`tools/check_history_toggle.py`, G14). `validate.py` shows the ONLY drift is `checks`.
  Clara records them into the signed baseline with **`python3 tools/approve.py --baseline`**
  (she pre-authorised appends in the /goal message; the agent did NOT self-approve). Marking
  criteria met and deepening CHK-014's script are NOT governed drift (verified: `canonical_goal`
  excludes criterion state; check scripts aren't hashed — only registry.md fields are).
- **what shipped (Phase 2):**
  - `engine/notation.py` — raw expr → readable notation, display-only/value-preserving.
  - `engine/lesson.py` — `build_lesson()` → fine-grained, staged, readable walkthrough
    (`scene["lesson"]`); Lorenz = 17 steps, per-equilibrium Jacobian→eigenvalues→classify
    staged. Attached in `web/problems.py` WITHOUT touching `scene["steps"]`/`layers`.
  - Frontend: rich staged card (title + separated say/math/calc/note + "stage i/N" chip),
    slower pacing (DRAW_DUR 4200), per-step "ask about this step" (G13), History toggle (G14).
  - Backend G13: `Explainer.answer_about` + `Agent.answer_step` (grounded, place-preserving),
    `/api/agent` `step` context.
  - Checks: CHK-014 DEEPENED to the full G11/G12 per-case bar + pacing floor; CHK-015/016 added;
    `tests/test_lesson.py` (16 tests, suite 49→65).
- **app-verified (offline brain, localhost):** Clara's full multi-part Lorenz problem walked as
  18 staged beats; per-step follow-up grounded + place preserved (6/18); history toggles without
  crowding; 0.34 ms/frame (C-INTERACTIVE). Scalar saddle staged its Hessian.
- **guardrails held:** `scene["layers"]`+step tags unchanged; notation never alters a verified
  value (C-VERIFIED-MATH); all offline on base python3 (C-LOCAL); math stays tool-computed+verified.
- **HOW TO RUN:** live `./.venv/bin/python web/server.py` → :8765; offline visual
  `ANTHROPIC_API_KEY="" python3 web/server.py`; checks `python3 tools/verify.py`.
- **next:** nothing to build — do NOT work past the finish line. Clara: `approve.py --baseline`
  to record CHK-015/016. Live-path (real Claude) spot-check optional — the lesson is
  brain-independent (built by the deterministic engine), so the offline verification carries.
- **open blockers:** none.
