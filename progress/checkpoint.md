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

- **updated:** 2026-09-04 (quality-hardening round)
- **phase:** 🔨 **QUALITY-HARDENING GOAL in progress — BLOCKED on API credits (B1).** New goal from
  Clara: drive the WHOLE suite LIVE and verify math, explanations, visuals, animations, and
  follow-ups are all correct/clear/clean/relevant — with GENERAL fixes only (no test-targeted
  hacks; the agent must be good on ANY in-scope problem). General fixes are DONE + committed +
  pushed + offline-verified; remaining LIVE re-verification is blocked (credits exhausted).
- **prior state (still true):** Phase 4 (G21–G25) complete; 25/25 criteria met; verify GREEN
  (26/26); baseline recorded; validate clean; G1–G20 untouched. 100 unit tests pass (was 65).
- **general fixes this round (committed a2fc7c3; all 6 verified offline, #1/#2/#5 also live before
  credits ran out):**
  1. ClaudeBrain tool-result payload now carries each verified quantity's KEY value (compacted;
     long arrays summarised) → the model grounds directions/comparisons (eigenvectors, basin
     depths, Hessian eigenvalues) instead of guessing. Fixed AL1 "45°" model-derived guess.
  2. `focus_view` resolves linear-algebra directions (eigenvector / most-stretched / principal /
     singular axes). Fixed the failed "which direction is stretched most?" focus.
  3. Deterministic out-of-scope guard extended to symbolic algebra (factor/roots/solve-for-x);
     `Agent.run` declines before the model can bluff. Fixed AX6.
  4. System prompt: ground qualitative claims in provided values; one solve_ tool per problem;
     drive the right tool to SHOW not just tell.
  5. `run_simulation` carries its verified sweep quantity on the scene → "which basin is deeper?"
     is grounded (fixed the old "exactly equal" error).
  6. ClaudeBrain no longer false-declines a tool-free contextual answer.
  Locked in by 35 offline regression tests in `tests/test_agent_quality.py` (under CHK-007).
- **verified so far:** LIVE full suite (before credits) core 20/20=100%; the 4 key fixes verified
  LIVE + correct; scalar+optimization LIVE follow-ups excellent. OFFLINE browser VISUAL pass across
  all 5 areas + 3D SVD ellipsoid + Phase-4 animate/sweep: clean, no console errors (visuals are
  brain-independent, so this dimension is fully covered offline).
- **⚠️ BLOCKED (B1):** LIVE re-verification of vector-fields/linalg/dynamics follow-ups + a full
  live re-drive confirming the fixes hold suite-wide + a live rendered-app pass all need API
  credits. **Clara: top up credits (Plans & Billing).** Buying credits is a financial action the
  agent must not take.
- **note:** two nondeterministic labelled-model-derived cases (AO3/AO6 on some runs) are
  constraint-compliant (always labelled, never shown as verified) and reduced by fix #1.
- **known limitation (candidate future engine fix):** the agent may gracefully DECLINE to
  plain-solve some quartics as scalar fields (critical-point verification fails, e.g.
  `(x^2-1)^2+0.3x+y^2`); the SWEEP on the same landscape still works.
- **HOW TO RUN:** live `./.venv/bin/python web/server.py` → :8765 (needs API credits!); offline
  `ANTHROPIC_API_KEY="" python3 web/server.py` → :8770; checks `python3 tools/verify.py`.
- **next when credits return:** re-drive the full suite live (fixes hold, core 100%, out-of-scope
  declined); live follow-up drive for vector-fields/linalg/dynamics; live rendered-app browser pass.
- **open blockers:** B1 — API credits exhausted (blocks live re-verification).
