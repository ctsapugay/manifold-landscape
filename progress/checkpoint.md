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
- **phase:** 🚧 **INTAKE EXPANSION drafted — awaiting Clara's baseline.** The narrower v1
  goal was met + shipped (commit `f3d98d6`). Clara then redid intake to a much bigger vision:
  an **agentic AI tutor** that solves *arbitrary* in-scope problems, adds a **fifth area
  (dynamical systems / ODEs)**, drives the visualization, and chats. The governed spec has
  been rewritten to match; **Clara records it next.**
- **NEXT — Clara runs (one command):** `python3 tools/approve.py --baseline` to record the
  expanded constraints + goal + criteria as the new baseline (validate.py will show DRIFT on
  constraints/goal until she does — that is expected for a Clara-initiated change). Then she
  seeds a **fresh worker + observer** from the updated priming prompts.
- **what changed in the spec (this session):** `constraints/project.md` (C-VERIFIED-MATH now
  "tool-computed & verified OR clearly labelled model-derived"; C-INTERACTIVE "smooth even
  while the agent thinks"; C-GROUNDED-EXPLANATION for LLM answers). `goals/outcomes.md`,
  `goals/goal-condition.md` (state reset to `approved`; new statement; updated out-of-scope),
  `goals/criteria.md` (new **G1–G9**). `checks/registry.md` (test-set governance: protected
  core can't shrink without Clara, additions free; existing CHK-001…007 are the foundation
  regression net; new checks to be registered by the worker). New `.env.example` (+ `.gitignore`
  allows it). Both priming prompts rewritten.
- **then — the fresh worker builds (does NOT need re-approval to start):** the tool-orchestrating
  **agent** (Anthropic/Claude API via `.env`), **arbitrary problem intake** (equation / word
  problem / conceptual), the **5th area (ODEs)** — reuse vector-field + linalg engine (flow
  field, integrate trajectories, fixed points at F=0, stability via Jacobian eigenvalues,
  Lorenz-type chaos), the **tutor driving the visuals**, **multi-turn grounded chat**, the
  **tool-call transparency toggle**, and a **thinking indicator**. Register new checks + revise
  CHK-004/005/006 (governed); grow the test set (additions free).
- **watch:** This is an EXPANSION on a working foundation (`engine/`, `web/`, tests, CHK-001…007
  all green on main) — reuse it, don't rebuild. C-VERIFIED-MATH still binds: tools first, verify,
  and anything the model itself derives must be checked-where-possible and otherwise labelled
  model-derived — never shown as verified. Keep the API key out of tracked files (`.env`
  gitignored; public repo — C-SECRETS). Signed governance (approval commits SSH-signed; git
  config local to this clone).
- **open blockers:** none. (Waiting on Clara's baseline is the handoff, not a blocker.)
