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
- **phase:** ✅ **DONE.** Goal condition met and verified. P-0001 + P-0002 approved (signed).
  All six criteria G1–G6 `met` with evidence; `goals/goal-condition.md` state `met`.
  `python3 tools/verify.py` GREEN (CHK-001…007); `python3 tools/validate.py` no errors, no
  drift; 12 constraints held, 0 waived.
- **run it:** `python3 web/server.py` → http://127.0.0.1:8765
- **only open item (not a gate failure):** work is uncommitted — `validate.py` warns the
  goal/criteria files + project code should be committed so history reflects the done state.
  Awaiting Clara's go-ahead to commit. Optional follow-ups: vendor Three.js (offline
  robustness); project README for the public repo.
- **older phase note:** engine + scenes + interactive frontend + Q&A all built and working.
- **now:** Everything is built and **`python3 tools/verify.py` = 7/7 GREEN**; `pytest tests/`
  = 25 green. Engine (4 areas, provenance+verification), `engine/scene.py` (step-tagged
  geometry), `engine/explain.py` (grounded Q&A), the suite (`suite/problems.json` +
  `tools/run_suite.py`), and a **working local web app** (`python3 web/server.py` →
  http://127.0.0.1:8765) with Three.js 3-D + orbit controls (G2), step-through (G3), grounded
  ask box (G4), verified-results panel, and `docs/scope.md` (G6). Two proposals (P-0001 suite,
  P-0002 checks) PENDING. **No criteria marked met yet** — deliberate; done in the finish pass
  after approvals. Agent committed nothing (commit when Clara asks).
- **watch:** Don't mark criteria met / goal met until P-0001 + P-0002 approved (else the finish
  rests on unapproved checks). Frontend needs the pane VISIBLE for real canvas size + rAF (fps=0
  when hidden) — measure G2 fps with the app in front. SymPy footgun: `sympify(expr,
  locals=<real symbols>)` or derivatives are 0. Matrices: exact SymPy matrix (`nsimplify`), not
  the float ndarray, or defective-eigen detection is lost. Secrets out of tracked files (public
  repo). Signed governance (approval commits SSH-signed).
- **open blockers:** effectively blocked on Clara's two approvals for the finish (see top). No
  other in-scope, unblocked work remains that isn't past the finish line.
