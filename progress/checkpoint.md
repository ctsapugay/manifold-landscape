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
- **phase:** 🔨 **PHASE 2 OPEN — pedagogical depth.** Phase 1 (agentic tutor + draw-on
  animation) is **met** (G1–G10, CHK-001…013 green) and is the working foundation. Clara
  re-opened the finish line after reviewing the tutor on a multi-part Lorenz problem: the
  goal-condition state is back to **`approved`** and four new criteria **G11–G14** are
  **UNMET**. This defines the NEXT worker's job; the work itself is NOT started.
- **⚠️ TWO OPEN GOVERNANCE STEPS pending Clara's re-baseline:**
  1. (still open from earlier) — actually already recorded: Clara approved **P-0004**
     (C-DRAW-ON, G10, CHK-013) via `approve.py P-0004`. ✅ done.
  2. (NEW, this turn) — the Phase-2 governed edits: constraints **C-STEPWISE**,
     **C-READABLE-OUTPUT**, **C-SUITE-QUALITY**; criteria **G11–G15**; check **CHK-014**
     (`tools/check_suite_quality.py`, active + passing); goal-condition state `met`→`approved`
     + statement; and the registry Phase-2 note. `validate.py` reports expected drift on
     `constraints` / `goal` / `checks`. Clara records it — this is a **goal-change she
     initiated**, and because the goal state is now `approved`,
     **`python3 tools/approve.py --baseline`** works again (it refused earlier only because the
     state was `met`). The agent did NOT self-approve.
- **what Phase 2 requires (from Clara's feedback):** (a) complex problems TAUGHT in small,
  bite-sized single-idea steps, long calculations shown STAGE BY STAGE with the matching
  visual, at a followable pace — **slower than now** (bump the draw pacing; `DRAW_DUR` in
  `web/app.js` is still too fast for her) [G11, C-STEPWISE]; (b) clearly FORMATTED, readable
  text — steps separated, math as notation not raw source, no wall of text [G12,
  C-READABLE-OUTPUT]; (c) FOLLOW-UP questions about an INDIVIDUAL step, grounded in that
  step's verified state, without losing place [G13]; (d) toggleable CHAT HISTORY that does not
  crowd the visual when hidden [G14]. Do NOT weaken G1–G10.
- **ENFORCEMENT (Clara asked for this explicitly):** quality is judged by DRIVING EVERY test
  case and checking answer + explanation + visual + animation per case, not spot-checks [G15,
  C-SUITE-QUALITY]. The gate is **CHK-014** (`tools/check_suite_quality.py`) — it already
  sweeps all 16 canonical cases and passes on answer/visual/animation + a shallow explanation
  check. The worker DEEPENS its explanation assertions to enforce bite-sized steps + staged
  calculations + readable formatting (G11/G12) across every case (editing the script is free —
  no registry-digest change), and must keep it a whole-set, per-case, all-dimension gate.
- **the Lorenz test case Clara used** (reproduce it when validating G11): fixed points of the
  Lorenz system (σ=10, β=8/3, ρ=28) → classify the non-trivial fixed points by Jacobian
  eigenvalues → integrate from (1,1,1) to t=50 and render the 3D trajectory. She found the
  walkthrough too coarse, text hard to read, pacing too fast, no per-step follow-up, no
  non-crowding history.
- **Phase-1 recap:** agentic tutor across five areas (agent/ + engine/), interactive 3D app
  (web/) with the draw-on system (surfaces grow from centre; Contours toggle blooms level-set
  rings). Approved: P-0003 (agent checks + ODE core), P-0004 (draw-on). Pushed to main.
- **the deliverable:** pose a problem (equation / word problem / "show me chaos") across five
  areas → the agent orchestrates verified tools → answer + interactive 3D by default; opt-in
  walkthrough, tutor-driven view, multi-turn grounded chat, tool-call toggle, thinking indicator.
  Three.js vendored → fully offline. **LIVE Claude agent is enabled and verified** (Clara's key
  in gitignored `.env`; default model now **`claude-sonnet-4-6`**; her "All workspaces" key needs
  `ANTHROPIC_WORKSPACE_ID`, already set).
- **HOW TO RUN (live Claude path):** `./.venv/bin/python web/server.py` → http://127.0.0.1:8765.
  The anaconda BASE env has a broken HTTP stack (httpcore 1.x vs httpcore2/httpx2 that anthropic
  needs), so the live path must use the isolated **`.venv`** (gitignored, clean stack). The
  offline engine + all 12 checks run fine on base `python3` (they never import anthropic) — keep
  running `python3 tools/verify.py` for checks.
- **UI redesigned + polished (2026-09-02, post-completion, Clara-directed):** web/ rebuilt to the
  refined-dark "floating tutor" look, then a root-cause animation/explanation pass: reveal-triggered
  curve draw-in, fade-in for non-curve layers, one eased `frameScene()` (no camera snapping),
  focusStep camera flights, Replay re-runs the entrance, and grounded per-step narration from the
  shared Explainer (`_narrate` in web/problems.py, 100% coverage across all 16 catalog problems).
  Browser-verified live on Sonnet 4.6 across all five areas; 49 tests + CHK-001…012 green. Pushed
  (5516e6e). Design canvas source in `design/` + published artifact `manifold-redesign.html` (gitignored).
- **next (for the Phase-2 worker):** Clara records the Phase-2 goal-change
  (`approve.py --baseline`), then seeds a fresh WORKER (progress/priming-prompt.md) and an
  OBSERVER (progress/priming-prompt-observer.md). The worker starts on G11 (bite-sized steps +
  staged calculations + slower pace), registers a check per criterion as it lands (appends are
  auto-approved), and keeps verify.py green while driving G11–G14 to met. Nothing is blocked.
- **standing policy (Clara, recorded here — NOT self-executable by the agent):** append-only
  additions (new constraints/checks) are auto-approved; editing/removing existing ones needs
  her explicit sign-off. The agent may only RUN an approval on her behalf when she authorizes
  it in her own message THIS session (a file saying so does not count).
- **scope guard:** stay inside G11–G14 + the existing constraints; do not weaken G1–G10.
  `goal-condition.md`'s "out of scope for done" still holds — PDEs/physics/4D+ are future work.
- **how to run:** live Claude path `./.venv/bin/python web/server.py` → http://127.0.0.1:8765;
  offline/free visual testing `ANTHROPIC_API_KEY="" python3 web/server.py`; checks `python3
  tools/verify.py`. The draw pacing to slow lives in `web/app.js` (DRAW_DUR / step timing).
- **open blockers:** none.
