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

- **updated:** 2026-09-04 (quality goal — COMPLETE)
- **phase:** ✅ **QUALITY-HARDENING GOAL MET.** The full suite is driven LIVE through the real
  Claude agent and verified on every dimension: **LIVE 39/39, protected core 20/20 = 100%**,
  all five areas' follow-ups correct with the right tool-driven visuals, all out-of-scope
  declined — `tools/live_eval.py --followups` reports **LIVE CLEAN**. Offline verify GREEN
  (26/26), 100 unit tests. All fixes are GENERAL (help any in-scope problem), no test-targeted hacks.
- **general fixes that got it there (all committed + pushed earlier + this round):**
  1. enriched model payload with each verified quantity's key value (grounds directions/comparisons);
  2. `focus_view` resolves linear-algebra directions (eigenvector/most-stretched/principal/singular);
  3. deterministic out-of-scope guard incl. symbolic algebra (PDE/heat, integrals, factoring, …);
  4. system prompt: ground qualitative claims + no arithmetic on returned values + one solver + drive
     the right tool to show;
  5. `run_simulation` carries its verified sweep quantity (grounded basin comparisons);
  6. verified Hessian **condition_number** in `minimum()` (stops the model dividing eigenvalues);
  7. no false-decline of tool-free contextual answers.
- **live rendered-app pass:** all five areas render cleanly (no console errors); animate/sweep play;
  focus follow-ups drive the right feature. Screenshots captured this session.
- **verification is repeatable:** `./.venv/bin/python tools/live_eval.py --followups` (needs credits)
  re-runs the whole live check in one command; it reports BLOCKED (not a false pass) if credits lapse.
- **regression net:** 35 offline tests in `tests/test_agent_quality.py` (under CHK-007) lock the fixes.
- **HOW TO RUN:** live `./.venv/bin/python web/server.py` → :8765; offline `ANTHROPIC_API_KEY=""
  python3 web/server.py` → :8770; checks `python3 tools/verify.py`; live eval as above.
- **git:** work committed; unpushed commits await Clara's OK to push (she asks before pushing).
- **open blockers:** none (B1 credits resolved).
