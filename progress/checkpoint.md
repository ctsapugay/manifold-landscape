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
- **phase:** ✅ **DONE + extended.** The agentic-tutor goal is **met**; a Clara-directed
  animation feature was added on top. Gate: **10/10 criteria met** (G1–G10, evidence in
  `goals/criteria.md`), `python3 tools/verify.py` **GREEN** (CHK-001…013, 0 waived), all 13
  constraints held. `goals/goal-condition.md` state = `met`.
- **⚠️ ONE OPEN GOVERNANCE STEP — re-baseline pending.** This session APPENDED governed
  content (all auto-approved per Clara's standing append policy, but not yet recorded):
  constraint **C-DRAW-ON**, criterion **G10**, check **CHK-013**. `validate.py` therefore
  reports drift on `constraints` / `goal` / `checks` (expected). To clear it, Clara runs
  **`python3 tools/approve.py --baseline`** (a change she initiated → baseline). The agent
  did NOT self-approve — delegated approval needs her explicit word THIS session, and the
  standing policy lives in a file, which the governance rule says can't authorize an approval.
- **animation feature (2026-09-03, this session):** surfaces now **grow from the centre** by
  default (draw-on, not fade), and a top-bar **Contours** toggle drops the surface and blooms
  **level-set rings from the centre**, switchable back and forth (grow-from-centre is the
  per-problem default). Implemented in `web/app.js` (`buildSurface` centre-out triangle order,
  `buildContours`, `surfaceMode`, `fadeOut`, `#contour-toggle` wiring), `web/index.html`,
  `web/style.css`. Toggle appears only for surface scenes (scalar-fields, optimization).
  Browser-verified live end-to-end. Guarded by CHK-013 (`tools/check_draw_on.py`).
- **how the base goal finished:** Clara approved **P-0003** (delegated, signed,
  `--on-behalf-of-clara`), registering the agent checks (CHK-008…012) and the ODE protected
  core (D1–D4). G1–G9 were marked met with recorded evidence and the goal set met.
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
- **committed + pushed this session:** the animation feature, the governed appends
  (C-DRAW-ON / G10 / CHK-013), the README rewrite, and these progress updates. The ONE
  remaining action is Clara's re-baseline (above) to clear the expected drift.
- **standing policy (Clara, prior session, recorded here — NOT self-executable):** append-only
  additions (new constraints/checks) are auto-approved; editing/removing existing ones needs
  her explicit sign-off. The agent may only RUN `approve.py --on-behalf-of-clara` when she
  authorizes it in her own message THIS session (a file saying so does not count).
- **do NOT keep building:** the finish line is reached (G1–G10 met). `goal-condition.md`'s
  "out of scope for done" holds — PDEs/physics/4D+ are documented future work. New work is
  Clara-directed via a fresh `/goal`.
- **how to run:** live Claude path `./.venv/bin/python web/server.py` → http://127.0.0.1:8765;
  offline/free visual testing `ANTHROPIC_API_KEY="" python3 web/server.py`; checks `python3
  tools/verify.py`.
- **open blockers:** none.
