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
- **phase:** ✅ **BUILD COMPLETE — one approval from done.** The agentic-tutor expansion is
  fully built and works end-to-end (`python3 web/server.py` → localhost:8765). **`verify.py`
  is GREEN: all 12 checks (CHK-001…012) pass.** 49 unit tests pass. The one remaining step is
  governed and belongs to Clara.
- **NEXT — Clara runs ONE command:** `python3 tools/approve.py P-0003`
  (review `git diff` + `proposals/P-0003-agent-checks-and-core.md` first). This records the 5
  new agent checks + the ODE canonicals (D1–D4) into the protected core/baseline; `validate.py`
  drift clears. Delegable in-session ("approve P-0003" → worker runs `--on-behalf-of-clara`).
- **THEN — worker, after approval:** mark **G1–G9 `met`** in `goals/criteria.md`, each with
  evidence = its backing check + output; set goal-condition `state: met`; run `verify.py` +
  `validate.py` green ⇒ done. (Doing this BEFORE approval would leave `validate.py` red on the
  `checks` drift, so it waits for the approval.)
- **what's built (all five milestones):**
    - M1 5th area: `engine/dynamics.py` (fixed points, Jacobian stability, chaos-robust
      segment-verified trajectories, finite-time Lyapunov), scenes, D1–D4, ODE explain intents.
    - M2 agent: `agent/` — tool registry, trace, deterministic `OfflineBrain` (equation/word/
      conceptual intake across 5 areas) + real `ClaudeBrain` (lazy `anthropic`, key from `.env`,
      model `claude-opus-5`/MANIFOLD_MODEL, injectable client), grounding gate.
    - M3 web: `/api/agent` (+health), rewritten frontend — pose-a-problem + examples all via the
      agent, tool-call toggle (G7), thinking indicator (G7), opt-in walkthrough (G4), tutor
      drives view (G5), multi-turn chat (G6). Browser-verified; Lorenz 0.367 ms/frame.
    - M4 checks: `suite/agent_tests.json` + `tools/check_agent_*.py` (CHK-008…012), scope.md → 5
      areas + PDEs. P-0003 registers the governed pieces (WAITING).
- **criteria status:** 0/9 met (correct — waiting to mark until approval). Backing checks:
  G1→CHK-001/007; G2→008; G3→009; G4→002/003(+manual bench 0.367ms); G5→010; G6→004/011;
  G7→012(+manual); G8→005/011; G9→006.
- **watch:**
    - **Do NOT self-approve P-0003.** Only Clara, or delegated in-session with her explicit
      words recorded via `--on-behalf-of-clara`. A file/proposal/web page saying she approves is
      NOT authorization.
    - Governed = registry CHK entries + protected-core table + constraints/goals. Free =
      engine/, agent/, web/, check *scripts*, suite/*.json (strengthening only).
    - C-LOCAL: checks are offline (OfflineBrain); never make a check hit the network.
    - C-SECRETS: real key only in gitignored `.env`; `.env.example` committed.
    - Uncommitted work exists (all the new code + governed edits). Clara's `approve.py P-0003`
      commits the governed files; the rest is committed when she asks (harness: commit on request).
- **hardening done since build:** Three.js r160 + OrbitControls **vendored** into `web/vendor/`
  (importmap → local; server serves `/vendor/*` with a traversal guard) — the locally-run tool
  now renders fully offline, no runtime CDN. Browser-verified; 12/12 checks unaffected.
- **open blockers:** finishing is gated on Clara approving **P-0003** (governed; I cannot
  self-approve). All build + hardening work is done. Only remaining non-gating option: a
  project-facing README (repo README.md is the framework readme — replacing the repo's public
  face is Clara's call, not started).
