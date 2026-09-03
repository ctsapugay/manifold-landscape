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

- **updated:** 2026-09-02
- **phase:** ✅ **DONE.** The agentic-tutor expansion is complete and the goal condition is
  **met**. Gate satisfied: **9/9 criteria met** (evidence in `goals/criteria.md`),
  `python3 tools/verify.py` **GREEN** (CHK-001…012, 0 waived), all 12 constraints held,
  `validate.py` no errors. `goals/goal-condition.md` state = `met`.
- **how it finished:** Clara approved **P-0003** this session (delegated, signed, recorded
  `--on-behalf-of-clara`), registering the five agent checks (CHK-008…012) and the ODE
  protected core (D1–D4). Then G1–G9 were marked met with recorded evidence and the goal set met.
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
- **UI redesigned (2026-09-02, post-completion, Clara-directed):** web/ rebuilt to the approved
  refined-dark "floating tutor" look — immersive 3-D stage, self-drawing curves, tutor card that
  flies the camera to each step, Replay, vector-field toggle, plain-prose Claude answers. Browser-
  verified live on Sonnet 4.6; all 12 checks green. Design canvas source: `manifold-redesign.html`
  (published artifact) + `Main/Annotations/SideRail.dc.html` + `canvas.json` (untracked, repo root).
- **open item (not a gate failure):** the redesign + earlier criteria/goal `met` edits are
  **uncommitted** (criteria/goal state+evidence are excluded from the governed digest, so no
  drift). Awaiting Clara's go-ahead to commit + push (harness: commit only when asked). Run the
  live app from the venv: `./.venv/bin/python web/server.py` → :8765.
- **standing policy (Clara, this session):** append-only additions (new constraints/checks)
  are auto-approved; editing/removing existing ones still needs her explicit sign-off. Record
  every delegated approval via `approve.py --on-behalf-of-clara` so validate.py flags it.
- **do NOT keep building:** the finish line is reached. `goal-condition.md`'s "out of scope
  for done" holds — PDEs/physics/4D+ are documented future work, not this project.
- **open blockers:** none.
