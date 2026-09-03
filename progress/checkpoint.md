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
- **phase:** ✅ **PHASE 3 COMPLETE — the conversation redesign (G16–G20 MET).** Completion gate
  **✓ COMPLETE**: 20/20 criteria met, `python3 tools/verify.py` GREEN (21/21, CHK-001…021),
  65-test unit suite green. G1–G15 not weakened. Being recorded + committed + pushed.
- **what shipped (Phase 3 — Clara-initiated, combined A+C design):**
  - **One conversation (G16):** frontend rebuilt around a single dock/thread — walkthrough steps,
    user questions and agent answers are all messages in one `#thread` with one composer; the
    separate tutor card / per-step input / history panel are gone. (`web/index.html`, `web/app.js`
    UI half rewritten, `web/style.css` Phase-3 section.)
  - **Agent-driven answers (G17):** `Agent.answer_step` routes through the brain — live
    `ClaudeBrain.answer_step` (step + verified values injected) or offline Explainer; grounding
    gate labels un-verified figures. Fixes the Phase-2 "deterministic answer" bug.
  - **Suggested prompts (G18):** clickable chips at the top of the dock incl. "show me the next
    step" (advances the walkthrough + drives the visual via `nextStep`); launcher example chips.
  - **Start→session→new-chat + collapsible (G19):** centred `#launcher`; `startSession` seeds the
    opening prompt as the first thread entry; `#new-chat` returns to the launcher; dock collapses
    to a left-edge `#dock-tab`.
  - **Expandable bounds (G20):** `Agent.rescale` re-solves the current descriptor over a scaled
    domain (`/api/rescale`), verified like any solve; gated off for linear-algebra.
  - Checks: CHK-016 updated for the new model (G14 still holds); CHK-017…021 added for G16–G20.
- **app-verified (offline brain, localhost):** full flow — launcher → Lorenz session (thread =
  prompt + answer + streamed staged steps) → "walk me through it"/"next step" advance + drive
  visual → inline grounded follow-up with place preserved → collapse/reopen → new chat → scalar
  field → **bounds ×3 grew the paraboloid**, Lorenz ×2, bounds hidden for a matrix. No console errors.
- **guardrails held:** scene/animation/draw-on machinery untouched (CHK-012/013 tokens preserved);
  math tool-computed + verified incl. rescaled scenes (C-VERIFIED-MATH); offline on base python3.
- **HOW TO RUN:** live `./.venv/bin/python web/server.py` → :8765; offline `ANTHROPIC_API_KEY=""
  python3 web/server.py`; checks `python3 tools/verify.py`.
- **note:** a pre-existing `.venv` server on :8765 (not started by this session) was stopped by a
  broad `pkill` during testing — just a dev server; relaunch with the run command.
- **next:** record baseline (Clara-initiated Phase-3 change) + commit code + push. Then done —
  do NOT work past the finish line.
- **open blockers:** none.
