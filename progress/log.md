# Progress log

Append-only. Newest entries at the bottom. One entry per working session, plus an entry
any time a default constraint is exercised (an approval given, an assumption made, an
irreversible action taken).

This file exists so a session with no memory can resume the work. Write it for that
reader: state, not narrative.

**Entry format:**

```
## YYYY-MM-DD — short title

- **state:** where the project actually is right now
- **done:** what became true this session
- **next:** what the next session should pick up
- **decisions:** choices made and why, including assumptions made without asking
- **approvals:** anything Clara explicitly approved this session, quoted
- **proposals:** any proposal raised this session, and its status
- **dead ends:** what was tried and abandoned, so it is not retried
```

---

## 2026-08-31 — Repository created from constraint-base

- **state:** Fresh clone. No intake run yet.
- **next:** Run intake with Clara (see `CLAUDE.md`), then get the goal condition approved.

## 2026-09-01 — Intake run; goal condition drafted; blocker/checkpoint/priming subsystems added

- **state:** Intake complete and written. Goal condition is `state: draft`, awaiting Clara's
  approval and baseline. Repo is now a private→**public** GitHub repo
  (`ctsapugay/manifold-landscape`); local-only development under C-LOCAL.
- **done:**
  - Cloned constraint-base, disconnected it from its origin, re-init'd as its own repo,
    created the GitHub repo, and moved the project to `~/Projects/manifold-landscape`.
  - Ran intake. Wrote `constraints/project.md` (C-VERIFIED-MATH, C-INTERACTIVE,
    C-GROUNDED-EXPLANATION), `goals/outcomes.md`, `goals/goal-condition.md`,
    `goals/criteria.md` (G1–G6).
  - Extended the constraint system with three new mechanisms Clara asked for:
    a **blocker ledger** (`progress/blockers.md`), a **checkpoint / anti-rot** card
    (`progress/checkpoint.md`), and a **priming prompt** (`progress/priming-prompt.md`);
    wired open blockers + current checkpoint into `tools/brief.py` (with loaders in
    `tools/constraint_files.py`); and added a "Staying on task across a long run" section to
    `CLAUDE.md` covering the persistence directive (keep working; stop only when blocked on
    all fronts or when a decision is genuinely dangerous), the blocker protocol, and the
    checkpoint protocol.
- **next:**
  1. Clara reviews the drafted goal condition + criteria.
  2. On approval, set `goals/goal-condition.md` `state: approved` + date.
  3. Clara runs `python3 tools/approve.py --baseline` to engage governance.
  4. Goal mode: first define + register the representative problem suite in
     `checks/registry.md` for her approval.
- **decisions (assumptions, reversible):**
  - Scope spine = geometry of continuous math; v1 beachhead = scalar fields & surfaces,
    gradients & optimization landscapes, vector fields, linear-algebra-as-geometry.
  - Interactive 3D is the target for "multi-dimensional"; 4D+ is documented future work.
  - Physics is out of v1, documented as future expansion (criterion G6).
  - Priorities: correctness is the floor (non-negotiable), visuals the hook, explanation the
    payoff — reflected in constraints and criteria.
  - AI/agentic architecture (orchestration, tool-driven solving, verification, multi-agent)
    is implementation and stays out of constraints/goals; the *outcome* — verified results,
    grounded explanations — is what is pinned (C-VERIFIED-MATH, C-GROUNDED-EXPLANATION).
  - Delivery form = local graphical app; exact form is an implementation call.
- **approvals:** Clara approved the spine, audience lean (student/learner), priority order,
  the agentic approach, the non-goals, making C-VERIFIED-MATH a cornerstone, and adding the
  blocker + checkpoint + priming subsystems with brief.py integration. Goal condition itself
  is drafted, not yet approved — baseline not yet run.
- **proposals:** none.
- **dead ends:** none.

## 2026-09-01 — Goal condition approved; intake finalized (baseline pending)

- **state:** Clara reviewed and approved the full intake in chat. Goal condition set to
  `state: approved` (2026-09-01). Governance **not yet engaged** — the baseline command has
  not been run. Constraints and goal condition are still technically editable until it is.
- **done:**
  - During review, added an explicit enforcement line to the goal condition's completion
    contract: completion is confirmed **through the constraint system** (running the tools),
    never asserted from the agent's judgment. Portable base improvement.
  - Removed a `commands/goal.md` slash command that had been wrongly added — "goal mode" is
    invoked via Claude Code itself, not a custom command. Reverted CLAUDE.md back to its
    five stock commands; priming prompt now points at Claude Code's goal command + pasting
    the goal condition.
  - Added Clara's GitHub-noreply email to `governance/approvers.txt` alongside her gmail, so
    her approval commits verify whichever identity git uses on her machine.
- **next:**
  1. Clara runs `python3 tools/approve.py --baseline` to engage governance.
  2. Fresh session for goal mode (priming prompt → seed with goal condition).
  3. First task: define + register the representative problem suite in `checks/registry.md`.
- **approvals:** Clara, in chat: "Looks good to me. I approve everything." Covers the 3
  project constraints (C-VERIFIED-MATH, C-INTERACTIVE, C-GROUNDED-EXPLANATION), the goal
  statement, criteria G1–G6, the non-goals, and keeping all 9 defaults unwaived. The
  baseline itself is hers to run and is not yet run.
- **proposals:** none.
- **dead ends:** the `/goal` custom command idea — abandoned (goal mode is a Claude Code
  feature, not part of the constraint system).

## 2026-09-01 — Baseline engaged (signed); governance now in force

- **state:** Governance ENGAGED. Clara ran `python3 tools/approve.py --baseline`; baseline
  recorded and SSH-signed (commit `910ee46`). `tools/validate.py`: governance engaged,
  signed, no drift. Constraints and goal condition are now frozen — agent proposes, does not
  edit. Everything pushed to GitHub main. Still no project code; ready for goal mode.
- **done:**
  - Diagnosed the first baseline attempt's failure: repo is in signed governance mode
    (`governance/allowed_signers` holds Clara's ed25519 key), so `approve.py` signs approval
    commits, but git here had no signing method configured and fell back to a missing gpg.
  - Fixed by configuring SSH signing **locally** for this clone: `gpg.format=ssh`,
    `user.signingkey=~/.ssh/id_ed25519_ctsapugay.pub` (matches the key in allowed_signers,
    signs without a passphrase). Rolled back the half-written uncommitted baseline.txt from
    the failed run, then Clara re-ran the baseline successfully.
- **next:** First goal-mode session — define + register the representative problem suite in
  `checks/registry.md` for Clara's approval, then build toward G1 (verified solving).
- **approvals:** Clara ran the baseline herself (signed commit `910ee46`).
- **decisions:** Kept signed governance mode (did not downgrade to attribution). Signing
  config is local to this clone and not committed; a fresh clone re-runs the two git config
  lines.
- **proposals:** none.
- **dead ends:** none.

## 2026-09-01 — Goal mode begins: suite proposed (P-0001), engine core + scalar fields built

- **state:** Goal mode. Governance engaged. **P-0001 (representative problem suite) is
  PENDING Clara's approval** — do not build the suite data / wire G1 green until she
  approves it (`python3 tools/approve.py P-0001`). Engine core + the scalar-fields module
  exist and pass tests. Nothing committed by the agent (per harness norm: commit when Clara
  asks); the P-0001 registry edit + proposal are left uncommitted so her approval commit
  bundles them.
- **done:**
  - **Filed P-0001** = the representative problem suite (12 problems, 3 per beachhead area:
    S1–S3 scalar fields, O1–O3 optimization, V1–V3 vector fields, L1–L3 linear algebra).
    Registered the suite table + **CHK-001** (`run: python3 tools/run_suite.py`, covers G1)
    in `checks/registry.md`. `validate.py` shows the expected checks-digest drift + 1 pending
    proposal; her approval re-records the baseline and clears it.
  - **Built the engine core** (`engine/`): `result.py` — the C-VERIFIED-MATH mechanism:
    every displayed value is a `Quantity` carrying `provenance` (a deterministic engine
    routine; `"model"` and unknown sources are rejected at construction) and a `Verification`
    (an independent second-route check with residual/tolerance/passed); `Solution.require_verified()`
    refuses to surface anything unverified. `verify.py` — independent verification primitives
    (finite-difference gradient/Hessian/Jacobian, divergence/curl, eig/SVD residuals,
    orthonormality).
  - **Scalar-fields module** (`engine/scalar_field.py`): symbolic gradient/Hessian (verified
    vs finite differences), critical points (grid-seeded Newton, verified by gradient
    residual), Hessian-eigenvalue classification. `tests/test_scalar_field.py`: 5 tests pass —
    S1 paraboloid→minimum, S2 saddle→saddle, and two tests proving verification actually
    gates (model provenance rejected; unverified quantity refused).
  - Added `requirements.txt` (numpy/sympy/scipy/mpmath/pytest) for C-RESUMABLE.
- **next:**
  1. Continue the engine (independent of P-0001): optimization (`O`-type: gradient descent +
     Lagrange), vector fields (div/curl), linear algebra (eig/det/SVD).
  2. On P-0001 approval: write `suite/problems.json` with independent references, build
     `tools/run_suite.py`, run `verify.py` → drive CHK-001/G1 green.
  3. Then G2 visualization (web/Three.js), G3 step-through, G4 grounded Q&A, G5 e2e, G6 docs.
- **decisions (implementation, mine per outcomes.md "Delivery form"; reversible):**
  - **Stack:** Python engine (SymPy exact symbolic + NumPy/SciPy numeric + mpmath) with a
    **local web frontend (browser + Three.js/WebGL)** served on localhost for portfolio-grade
    interactive 3D (C-INTERACTIVE). All local (C-LOCAL). Explanation layer (G4) added later,
    grounded in engine values; the model never sources a displayed number.
  - **Verification pattern:** primary route symbolic, confirmed by an independent numeric
    route (finite diff / residual identities); a quantity surfaces only if both agree.
  - Numeric grid-seeded critical-point finder (not pure symbolic solve) so one routine
    handles polynomial and transcendental fields; gradient residual is the confirmation.
- **approvals:** none new (P-0001 awaiting Clara).
- **proposals:** **P-0001 proposed, pending.**
- **dead ends:** none. (Fixed a latent bug: `sympify` must be given the real-assumption
  symbols via `locals=`, else derivatives w.r.t. them are silently 0 — comment in
  `scalar_field.py`.)

## 2026-09-01 — Engine complete for all four areas; scene builders for G2/G3

- **state:** Goal mode. **P-0001 still PENDING Clara** (verified via `approve.py --status`;
  1 proposal pending, checks drift shown — both expected). Verification-backed engine now
  covers **all four beachhead areas**, plus a scene-spec layer that turns any solution into
  step-tagged 3-D geometry (the bridge to G2/G3). `pytest tests/` = **19 green**. Still no
  frontend rendering yet; G1 suite data still gated on P-0001. Nothing committed by agent.
- **done:**
  - **engine/optimization.py** — gradient descent (verified: objective non-increasing along
    the path), unconstrained `minimum` (scipy BFGS gtol=1e-10, verified by ∇f≈0 + Hessian
    pos-def), and `ConstrainedProblem` Lagrange solver (verified: g=0 and ∇f=λ∇g residuals).
    Tests O1/O2(Rosenbrock→(1,1))/O3(→(½,½),λ) pass.
  - **engine/vector_field.py** — symbolic divergence & curl (2-D scalar, 3-D vector), each
    verified vs finite-difference operators. Tests V1/V2/V3 pass.
  - **engine/linalg.py** — determinant (exact vs numeric), eigen-structure (exact SymPy
    eigenvects + defective detection, verified by ‖Av−λv‖), SVD (verified by reconstruction
    + orthonormality). Tests L1/L2(defective shear)/L3(SVD) pass.
  - **engine/scene.py** — scene specs for all four areas: surface/gradient/critical-points
    (scalar), +descent/min (optimization), arrows+div/curl grids (vector), circle→ellipse
    +eigenvectors / sphere→ellipsoid+singular-axes (linear). Every layer tagged with the
    solution `step` it appears at → drives G3 (a step shows exactly its geometry, nothing
    later). `tests/test_scene.py` verifies well-formedness, JSON-serializability, step order.
  - Refined the provenance guard in `engine/result.py` to a prefix allowlist
    (sympy./numpy./scipy./mpmath./engine.), rejecting `model` and unstated sources; fixed
    two real bugs (exact SymPy matrix so a defective shear is detected; complex-safe eigen
    residual).
- **next:**
  1. Frontend: local stdlib HTTP server (`web/server.py`) with a `/api/solve` endpoint +
     an index.html/app.js Three.js renderer with orbit controls (G2) and step controls (G3).
  2. **G6 scope docs** — writeable now (non-governed): four supported areas + deferred
     expansions (physics, higher-dim). Register its check as a governed addition.
  3. On P-0001 approval: `suite/problems.json` + `tools/run_suite.py` → CHK-001/G1 green.
  4. Then G4 (grounded Q&A), G2 framerate check, G5 e2e.
- **decisions (implementation, mine; reversible):**
  - Frontend will load **Three.js from a pinned CDN** to iterate now; **vendor it locally
    before "done"** for offline robustness (portfolio). Noted so it isn't forgotten.
  - Scene meshes are visual sampling of the same functions; the *math values* shown are the
    verified `Quantity` objects carried in the scene, so C-VERIFIED-MATH still holds.
- **approvals:** none new (P-0001 awaiting Clara).
- **proposals:** P-0001 proposed, pending.
- **dead ends:** none.

## 2026-09-01 — Interactive 3-D frontend working (G2/G3 substance); G6 docs written

- **state:** Goal mode. **P-0001 still PENDING Clara.** A working local web app now solves
  any of the 12 catalog problems, renders them as interactive 3-D scenes, steps through them,
  and shows the verified results with provenance. `pytest tests/` = 19 green. Server runs at
  http://127.0.0.1:8765 (`python3 web/server.py`). Criteria not yet marked met (deferred to a
  coordinated check-registration + evidence pass). Nothing committed by agent.
- **done:**
  - **web/server.py** — stdlib HTTP server (localhost only, C-LOCAL): `/api/catalog`,
    `/api/scene?id=`, `POST /api/solve`. Never computes math itself; calls the engine, which
    returns only verified quantities. Clean JSON errors, no stack traces to the UI.
  - **web/problems.py** — descriptor→solve→scene dispatch + a CATALOG of 12 example problems
    (the canonical cases; deliberately NOT the governed suite — that stays gated on P-0001).
    Verified headlessly: all 12 solve, all quantities verified, all JSON-serializable.
  - **web/index.html + style.css + app.js** — Three.js (pinned CDN) renderer, Z-up, orbit
    controls (rotate/zoom/pan → G2/C-INTERACTIVE). Renders every layer type (surface, param
    surface, vectors, points, polyline, curve, scalar grid, eigenvectors) with a viridis
    height map. **Step-through** shows only layers with step ≤ current (G3). **Verified-
    results panel** shows each quantity's value + "✓ verified · residual ≤ tol · via
    <provenance>" — the C-VERIFIED-MATH story made visible.
  - **Browser-verified:** paraboloid (bowl + radial gradient), anisotropic bowl, shear
    (circle→ellipse + eigenvector), 3×3 SVD (sphere→ellipsoid) all render well; drag-rotate
    works. G3 confirmed via a render-state hook `window.__ml`: at steps 0/1/2/3 the visible
    layer-steps were [0]/[0,1]/[0,1]/[0,1,3] — exactly the step's geometry, nothing early.
  - **docs/scope.md** (G6) — states the four supported areas and the deferred expansions
    (physics, higher-than-3-D visualization), plus intake non-goals. Written to be gr-eppable
    for an automated G6 check later.
  - Fixed frontend bugs found by running it: TDZ on the fps counter (moved render-loop start
    to end of module), and canvas sized 300×150 because `setSize(w,h,false)` skipped the CSS
    size (now `setSize(w,h)`); added camera auto-fit.
- **next:**
  1. **G4 grounded Q&A** (no P-0001 needed): a deterministic explanation engine that answers
     questions by composing from the verified quantities — every number pulled from a verified
     `Quantity`, never model-sourced (C-VERIFIED-MATH, C-GROUNDED-EXPLANATION). Add /api/ask +
     a question box. Scripted-question test (G4 check).
  2. **On P-0001 approval:** `suite/problems.json` (independent references) + `tools/run_suite.py`
     → CHK-001/G1 green.
  3. **Coordinated finish pass:** register the remaining checks (G2 fps, G3 step, G4, G5 e2e,
     G6 docs) — a governed batch (propose as P-0002); run `tools/verify.py` green; mark
     criteria met with evidence. Vendor Three.js locally before "done" (offline robustness).
- **decisions:** G4 will be **deterministic/template-grounded**, not a free LLM, so grounding
  is guaranteed by construction and it runs offline (no key, C-SECRETS). An LLM phrasing layer
  can come later but must cite verified values only.
- **approvals:** none new (P-0001 awaiting Clara).
- **proposals:** P-0001 proposed, pending.
- **dead ends:** FPS measurement via the in-app browser pane is flaky (rAF pauses when the
  pane is hidden between tool calls) — defer the formal frame-rate check to a controlled setup.

## 2026-09-01 — All capabilities built; full check battery green; two approvals pending

- **state:** Goal mode. **The tool is functionally complete and every check passes.**
  `python3 tools/verify.py` → **7/7 GREEN** (CHK-001…007). `pytest tests/` → 25 green. The
  finish line now needs only Clara's two governance approvals + a short finish pass. Criteria
  still 0/6 met (deliberately — see below). Agent has committed nothing.
- **done:**
  - **G4 grounded Q&A** — `engine/explain.py`: deterministic explanation engine; answers are
    composed from verified quantities (every number pulled from a verified `Quantity`, geometric
    intuition selected by the verified classification), so grounded by construction, offline, no
    model in the numeric path. Wired into server (`/api/ask`) + a question box in the UI;
    browser-tested. `tests/test_explain.py` (6) green.
  - **G1 suite made real** — `suite/problems.json` (12 problems + INDEPENDENT references; L3
    singular values via eig(AᵀA), a route independent of the engine's SVD) and
    `tools/run_suite.py` (CHK-001): solves each, confirms every quantity is engine-produced &
    verified, checks answers against references. **All 12 pass.**
  - **Check battery for G2–G6** built and registered (CHK-002…007) and proposed as **P-0002**:
    `check_render_budget.py` (G2 geometry budget — regression guard for the frame rate),
    `check_stepthrough.py` (G3), `check_grounded.py` (G4), `check_e2e.py` (G5),
    `check_scope_docs.py` (G6), `pytest tests/` (G1 regression). All green via `verify.py`.
- **THE FINISH (needs Clara):**
  1. `python3 tools/approve.py P-0001`  — binds the suite + CHK-001 (the bar for G1–G5).
  2. `python3 tools/approve.py P-0002`  — binds CHK-002…007 (G2–G6 + regression).
     (Both clear the checks drift `validate.py` reports.)
  3. **Finish pass (agent, after approvals):** re-run `python3 tools/verify.py` (green), record
     G2's real frame rate from the running app (`window.__ml.state().fps` while manipulating)
     as G2 evidence, then set each criterion G1–G6 `state: met` in `goals/criteria.md` with the
     command run + result as `evidence:`, and set `goals/goal-condition.md` `state: met`. Run
     `python3 tools/validate.py` — must be clean.
- **why criteria not marked met yet:** in this system a criterion is `met` against a
  *sanctioned* check; the checks/suite are governed content still pending approval (P-0001,
  P-0002). Marking met + goal met is the coordinated final pass AFTER Clara approves, so the
  finish line is honest, not self-certified against unapproved checks. (C-EVIDENCE, governance.)
- **optional, not a completion requirement:** vendor Three.js locally (offline robustness for
  portfolio) — needs a file download, so needs Clara's OK. Current app loads Three.js from a
  pinned CDN and works with internet. A project README (how to run) would also help.
- **how to run:** `python3 web/server.py` → http://127.0.0.1:8765 (server is running now).
- **approvals:** none new (P-0001, P-0002 awaiting Clara).
- **proposals:** P-0001 (suite) and P-0002 (check battery) — both proposed, pending.
- **dead ends:** none.

## 2026-09-01 — G2 frame-rate evidence captured (finish-pass prep, non-blocked)

- **state:** Still awaiting Clara's P-0001 + P-0002 approvals for the formal finish. Gathered
  the one remaining piece of finish-pass evidence that doesn't need approval: G2 frame rate.
- **done:** Added `window.__ml.bench(n)` (times N forced renders while orbiting — independent
  of requestAnimationFrame, so it works even when the pane is hidden). Measured across the
  heaviest scenes (in-browser): S1 0.44 ms/frame, O2 0.46, **V3 1.95 (heaviest, 729 arrows)**,
  L3 0.13. All ≤ ~2 ms/frame vs the 16.7 ms budget for 60 fps → 8×–100× headroom → smooth
  interaction with large margin. Recorded the explicit G2 threshold (sustained 60 fps /
  ≤16.7 ms per frame) in the `checks/registry.md` G2 note.
- **G2 evidence string (for the finish pass, to paste into goals/criteria.md G2 evidence):**
  "Measured in-app via window.__ml.bench(180) on 2026-09-01: frame cost ≤ ~2 ms across all
  suite scenes (worst case 3-D vector field V3 = 1.95 ms/frame; surfaces ~0.45 ms; SVD 0.13
  ms) — well under the 16.7 ms/frame 60-fps budget, so sustained 60 fps with 8×+ headroom.
  Rotate/zoom/pan confirmed smooth in the browser. CHK-002 (render budget) green."
- **next:** Clara approves P-0001 + P-0002, then the finish pass (mark G1–G6 met with
  evidence, goal met, verify + validate clean).
- **approvals:** none new (P-0001, P-0002 pending).
- **proposals:** P-0001, P-0002 pending.
- **dead ends:** none.

## 2026-09-02 — DONE: goal condition met and verified

- **state:** ✅ **COMPLETE.** Clara approved P-0001 and P-0002 (signed commits). Finish pass
  done: all six criteria G1–G6 marked `met` in `goals/criteria.md` with recorded evidence;
  `goals/goal-condition.md` state set to `met`.
- **gate (all satisfied):**
  - `python3 tools/verify.py` → GREEN, CHK-001…007 all passing (suite + battery now governed).
  - `python3 tools/validate.py` → no errors; 6/6 criteria met; completion gate satisfied;
    governance engaged & signed, no drift.
  - All 12 constraints in force throughout, 0 waived.
- **what was delivered:** a locally-run tool (`python3 web/server.py` → localhost:8765) that
  solves problems across the four beachhead areas with a verification-backed engine (every
  displayed value engine-produced + independently verified; `model` provenance rejected),
  renders them as interactive 3-D scenes (orbit controls, ≤~2 ms/frame), steps through them in
  sync, answers questions grounded only in the verified state, and documents scope
  (`docs/scope.md`). Engine: `engine/` (result, verify, scalar_field, optimization,
  vector_field, linalg, scene, explain). Suite: `suite/problems.json` + `tools/run_suite.py`.
  Checks: CHK-001…007. Tests: `pytest tests/` 25 passed.
- **open item (not a gate failure):** the work is uncommitted — `validate.py` warns that
  goals/criteria.md + goal-condition.md (and all project code) should be committed so git
  history reflects the done state. Awaiting Clara's go-ahead to commit (harness: commit when
  asked). Optional follow-ups she flagged interest in: vendor Three.js for offline robustness;
  a project-level README for the public repo.
- **approvals:** Clara approved P-0001 and P-0002 this session ("I approve both, continue");
  both recorded as signed APPROVED commits.
- **proposals:** P-0001, P-0002 — both approved.
- **dead ends:** none.

## 2026-09-02 — Intake redo: scope expanded to an agentic AI tutor (awaiting baseline)

- **state:** 🚧 Governed spec REWRITTEN for a much larger vision; **Clara records it next**
  with `python3 tools/approve.py --baseline`. This is a Clara-initiated goal change
  (CLAUDE.md Situation 3): edits made, `validate.py` shows expected DRIFT on constraints/goal
  until she baselines. v1 was met + shipped (`f3d98d6`) and is now the foundation.
- **the new vision (from a full re-interview):** an **AI tutor agent** that (1) takes a
  problem in ANY form — equation, word problem, or open request ("show me chaos"); (2)
  **orchestrates deterministic tools** to solve/visualize/explain (agent decides which tools,
  when); (3) adds a **fifth area: dynamical systems (ODEs)** — phase portraits, fixed points,
  stability via Jacobian eigenvalues, chaos; (4) **drives the visualization** as it tutors
  (zoom to the min, highlight a saddle); (5) **multi-turn grounded chat** at any step; (6) a
  **toggle** to show the agent's tool-calls; (7) a **thinking indicator**, 3D smooth while it
  thinks. Purpose: showcase math depth + agentic-AI skill, portfolio standard.
- **done (spec edits, all governed content Clara will baseline):**
  - `constraints/project.md`: **C-VERIFIED-MATH revised** — tools are the primary source and a
    result is shown verified only after an independent check; the agent MAY derive math itself
    when no tool applies, but it's checked where possible and otherwise **clearly labelled
    model-derived/unverified** (per Clara's explicit instruction to edit this). C-INTERACTIVE
    now covers "smooth even while the agent thinks". C-GROUNDED-EXPLANATION covers LLM answers +
    the labelled-model-derived nuance.
  - `goals/outcomes.md` rewritten; `goals/goal-condition.md` new statement + **state reset
    `met`→`approved`** + updated out-of-scope (PDEs/physics/4D+ deferred; API calls OK; a small
    labelled-model-derived class OK). `goals/criteria.md`: new **G1–G9** (all unmet).
  - `checks/registry.md`: **test-set governance** = protected core can't shrink without Clara,
    additions free; CHK-001…007 kept as the foundation regression net; covers remapped to new
    criteria; worker-notes on new checks (G2/G3/G5/G7) + revisions (CHK-004/005/006).
  - `.env.example` added (placeholders, committable) + `.gitignore` `!.env.example`; real key
    goes in gitignored `.env`.
  - Both priming prompts rewritten (worker + observer) for the agentic vision.
- **next:** (1) Clara: `python3 tools/approve.py --baseline`; (2) Clara seeds fresh worker +
  observer from the priming prompts; (3) worker builds the agentic tutor on the existing
  foundation (reuse engine/ + web/), registering/revising checks as governed changes.
- **decisions/notes:** 9 criteria (validate warns >8 — justified for a project this size:
  each is a distinct, checkable outcome). Existing checks still pass on the foundation, so
  verify.py stays green after baseline while criteria are 0/9 met → goal correctly not "met".
  G2 threshold set at ≥90% held-out + 100% protected core (Clara can adjust before baselining).
- **approvals:** Clara directed the whole expansion in-session incl. explicitly authorizing the
  C-VERIFIED-MATH edit; she records it via `--baseline`. No proposal (Situation 3 change).
- **proposals:** none new (P-0001, P-0002 remain approved).
- **dead ends:** none.

## 2026-09-02 — Intake clarifications (still pre-baseline): last-resort model math; optional tutor

- **state:** Two clarifications from Clara folded into the (still-uncommitted) expanded spec,
  before she baselines.
- **done:**
  - **C-VERIFIED-MATH:** strengthened — model-computed math is a **last resort** used only
    where no deterministic tool can produce/check the result; the expectation is to **close
    gaps by building tools** (a new solver, or model-generated code executed deterministically
    and verified), not by leaning on the model. Updated the rule, check, and why; and the
    worker priming prompt now directs "hit a gap → build a tool, don't let the model compute."
  - **Tutor/step-by-step is OPTIONAL:** default experience = answer + interactive 3D visual
    (nothing forced); the step-by-step walkthrough is opt-in (a button/toggle), and only then
    does the tutor build the scene in sync and drive the visuals. Updated outcomes (pts 4–6),
    the goal statement, criteria G4 (default answer+visual; opt-in walkthrough) and G5 (tutor
    drives visuals during the walkthrough or on a question), and both priming prompts.
- **next:** unchanged — Clara `python3 tools/approve.py --baseline`, then seed fresh worker +
  observer.
- **approvals:** clarifications directed by Clara in-session; recorded via `--baseline`.
- **proposals:** none new.
- **dead ends:** none.

## 2026-09-02 — Expansion build begins: fifth area (dynamical systems / ODEs) landed

- **state:** 🚧 Goal mode, building the agentic-tutor expansion on the shipped foundation.
  **Milestone 1 done:** the 5th area (dynamical systems / ODEs) is fully implemented,
  verified, and integrated. All **31 tests** pass (25 foundation + 6 new) and **CHK-001…007
  are GREEN** over the now-expanded suite (which includes the ODE problems, Lorenz chaos
  included). No governance changes yet — everything so far is non-governed content.
- **done:**
  - `engine/dynamics.py` — `DynamicalSystem(components, vars)` for ẋ=F(x): **fixed points**
    (F=0, seeded Newton, verified by ‖F(x*)‖ with a scale-aware tolerance so Lorenz-scale
    roots at radius ~27 aren't punished), **stability** (Jacobian eigenvalues → sink/source/
    saddle/spiral/centre; symbolic Jacobian confirmed vs finite-difference, each eigenpair by
    ‖Jv−λv‖), **trajectories** (scipy `solve_ivp` RK45, verified by an INDEPENDENT integrator
    DOP853 agreeing over each SHORT segment — chaos-robust: never asks two integrators to
    agree over a long horizon, only per well-posed step), and **separation** (finite-time
    Lyapunov estimate = quantitative sensitive dependence, verified via the two segment-
    verified curves). `classify_equilibrium()` names the local flow honestly (a zero real
    part is flagged "linearisation marginal/inconclusive", not silently called stable).
  - `engine/scene.py` — `build_dynamics_scene()`: step-tagged phase portrait (flow field
    step 0, equilibria coloured by stability step 1, trajectories step 3; stability=step 2
    and separation=step 4 re-read existing geometry). Reuses the frontend's existing
    vectors/points/polyline renderers, so **no JS change was needed to render ODE scenes or
    the Lorenz attractor**.
  - `web/problems.py` — dispatch + `solution_for` for area `dynamical-systems`; **D1–D4**
    added to CATALOG (stable spiral, saddle, pendulum [centre + two saddles], Lorenz chaos).
  - `engine/explain.py` — grounded intents for equilibria / stability / trajectory / chaos
    (verified spot-checks pass).
  - `suite/problems.json` — D1–D4 appended (free coverage) with INDEPENDENT references
    (known equilibrium locations + analytic stability types; Lorenz: 3 equilibria + positive
    Lyapunov). `tools/run_suite.py` extended with `fixed_points` and `chaotic` reference
    handlers — a STRENGTHENING (broadens coverage; the protected core's existing references
    are untouched), and CHK-001's `run:` command is unchanged, so no `checks`-digest drift.
  - `tests/test_dynamics.py` — 6 tests (D1–D4 + classification + independent-verification).
- **next:** Milestone 2 — the **agent layer** (`agent/` package): a transport-agnostic
  tool-orchestration loop with a pluggable brain. `ClaudeBrain` (real, lazy `anthropic`
  import, key from `.env`, default model `claude-opus-5` via MANIFOLD_MODEL) drives the
  product; a deterministic `OfflineBrain` drives the offline checks and is the graceful
  no-key fallback. Tool registry wraps the engine ops (each returns verified quantities);
  the loop records an inspectable trace + a grounding gate. Then Milestone 3 (frontend:
  free-form intake, thinking indicator, tool-call toggle, optional walkthrough with tutor
  scene-driving, multi-turn chat) and Milestone 4 (governed batch: register CHK for
  G2/G3/G5/G7, revise CHK-004/005/006 + scope doc for 5 areas + PDEs, propose adding the
  ODE canonicals to the protected core — all as proposals for Clara).
- **decisions:** (1) **Checks stay offline/deterministic** (C-LOCAL bars network in checks),
  so the agent loop is transport-agnostic and the automated G2/G3/G5/G7 checks will run the
  loop with the OfflineBrain; the real Claude path is wired + unit-testable against canned
  responses, and manually demoable once Clara supplies a key. This is an implementation
  choice (how, not what): the shipped product's agent IS Claude; the offline brain is a
  fallback + test substrate. Will be documented in scope docs. (2) Trajectory verification
  is segment-local, not long-horizon — a deliberate, math-honest choice for chaos. (3)
  Lorenz fixed-point tolerance is scale-relative. (4) D4 in the suite uses samples=2500,
  t_span 35 (lighter than the CATALOG's 4000/40) to keep the check suite snappy.
- **blockers:** none. (An API key is needed to DEMO the live Claude agent, but is NOT needed
  to meet the automated criteria; will note as a soft blocker when the agent path lands.)
- **approvals/proposals:** none this segment.
- **dead ends:** none.

## 2026-09-02 — Milestone 2: the agentic tutor (tool-orchestration layer)

- **state:** 🚧 Goal mode. **Milestone 2 done:** the transport-agnostic agent layer is built
  and tested. **49 tests pass** (25 foundation + 6 dynamics + 18 agent); **CHK-001…007 GREEN**.
  Still all non-governed content.
- **done — new `agent/` package:**
  - `tools.py` — `ToolRegistry`: the engine wrapped as 7 schema'd tools (solve_scalar_field,
    solve_optimization, solve_constrained_optimization, solve_vector_field,
    solve_linear_algebra, solve_dynamical_system, **focus_view**). Each returns verified
    quantities + scene; a solver that can't compute returns an error (graceful, never crashes).
    `focus_view` resolves a named feature ("the minimum", "the saddle", "the attractor") to a
    camera/highlight directive from the VERIFIED geometry — the mechanism for the tutor
    driving the view (G5).
  - `trace.py` — inspectable `AgentTrace`/`ToolCall` (tool sequence, per-call provenance +
    verified flag) → backs the G7 transparency toggle and the G3 trace check.
  - `intake.py` — deterministic interpreter: equations / word problems / conceptual prompts
    → tool plans, across all 5 areas; forgiving expression parsing (implicit mult, '^'),
    prose-stripping ("minimize … starting at (3,2)"), a conceptual library ("show me chaos"→
    Lorenz, "a rotating field"→(−y,x), etc.), and graceful decline w/ nearest-in-scope.
  - `brain.py` + `offline_brain.py` + `claude_brain.py` — pluggable brains. **OfflineBrain**
    (deterministic; drives offline checks + no-key fallback; composes answers via the
    grounded `Explainer`). **ClaudeBrain** (real product; manual Anthropic tool-use loop;
    **lazy** `anthropic` import; message history for multi-turn G6; default `claude-opus-5`
    via MANIFOLD_MODEL; injectable client for offline tests).
  - `agent.py` — `Agent` (session state: current problem + view) + `Tracer` + `build_agent()`
    (picks Claude when key+SDK present, else offline). **Grounding gate** (`grounding.py`):
    scans the answer's numbers against the verified quantities; anything untraceable is
    labelled "model-derived and unverified" (C-VERIFIED-MATH backstop on the Claude path).
  - `tests/test_agent.py` — 18 tests: interpretation across 5 areas × 3 styles, different
    inputs → different tool sequences (G3), out-of-scope decline (G2), grounded multi-turn
    chat (G6), the tutor moving the view on a focusing question (G5), and the **Claude
    tool-use loop threaded correctly with a canned client — no network, no key**.
- **engine improvement:** `optimization.gradient_descent` now does **backtracking line
  search** (shrink the step until the objective doesn't increase / stays finite), so arbitrary
  landscapes (e.g. Rosenbrock from a generic start) no longer diverge/overflow — the descent
  is always well-defined and its non-increasing verification always holds. Foundation suite +
  tests still green. Also relabelled the constrained scene's `area` to "optimization".
- **next:** Milestone 3 — **web integration**: `/api/agent` endpoint (per-session stateful
  Agent) + `/api/agent/health`; rewrite the frontend so the free-form box + example prompts
  ALL route through the agent (unifies G4/G5/G6/G7): default = answer + interactive 3D (no
  forced stepping), OPT-IN walkthrough, thinking indicator, tool-call transparency toggle,
  tutor driving the camera/highlights via directives, multi-turn chat. Then M4 (governed
  proposals: new CHK for G2/G3/G5/G7, revise CHK-004/005/006 + scope doc, ODE core → protected
  core) and M5 (mark criteria met).
- **decisions:** unified flow — everything goes through the agent (catalog items become
  example prompts sent as text), so chat/focus/walkthrough work uniformly (offline brain
  parses instantly, no network). Per-session Agents kept in an in-memory dict keyed by a
  frontend-generated session id (local single-user tool).
- **blockers:** none. (Live Claude demo still needs a key — soft, not gating the criteria.)
- **approvals/proposals:** none this segment.

## 2026-09-02 — Milestone 3: web integration (the app is live locally)

- **state:** 🚧 Goal mode. **Milestone 3 done & browser-verified.** The agentic tutor runs
  end-to-end at `python3 web/server.py` → localhost:8765. 49 tests + CHK-001…007 green.
- **done:**
  - `web/server.py` — `/api/agent` (per-session stateful Agent, in-memory dict) + `/api/agent/health`.
  - `web/index.html`, `web/app.js`, `web/style.css` rewritten: free-form "pose a problem" box
    + example prompts (all route through the agent); answer panel; **tool-call transparency
    toggle** (shows interpretation + each tool call's provenance/verified — G7); verified
    results; **opt-in walkthrough** (default = full interactive scene, no forced stepping — G4);
    **thinking indicator** (spinner while the agent works — G7); **multi-turn chat** (G6);
    **tutor drives the view** (focus directives → eased camera + pulsing highlight marker — G5).
  - Browser-verified (offline brain): Lorenz butterfly renders in 3D; answer grounded;
    trace toggle shows verified provenance; walkthrough steps in sync ([0]→[0,1]); focusing
    questions ("where is the minimum/attractor?") drive the view to the right feature; decline
    is graceful. **bench() = 0.367 ms/frame on the Lorenz scene (~45× under the 60fps budget)**
    → C-INTERACTIVE / G4 smoothness confirmed.
- **next:** Milestone 4 — back the new criteria with checks. NON-GOVERNED (do now): held-out
  agent test set (suite/agent_tests.json) + check scripts (coverage G2, trace G3, focus G5,
  flow+multiturn G6/G8, transparency G7); update docs/scope.md → 5 areas + PDEs deferred and
  strengthen check_scope_docs.py (G9). GOVERNED (propose to Clara, P-0003): register the new
  CHK entries + add ODE canonicals D1–D4 to the protected core. Then M5: mark criteria met.
- **decisions:** strengthening a check script (never weakening) is safe under governance and
  needs no proposal (same as the run_suite.py ODE handlers); ADDING registry CHK entries and
  elevating problems to the protected core ARE governed → P-0003 for Clara.
- **note:** a stale server from a previous session was holding :8765; killed and restarted.
- **blockers:** none.

## 2026-09-02 — Milestone 4: checks + scope for the new criteria; P-0003 awaiting Clara

- **state:** 🚧 Goal mode. All five build milestones DONE and the whole agentic tutor works
  end-to-end. **All 12 checks pass** (`verify.py` GREEN: CHK-001…012). **One governed change,
  P-0003, is WAITING on Clara** — until she approves it, `validate.py` correctly reports
  `checks` drift and the new checks are not yet part of the baseline, so the criteria stay
  unmarked. This is the handoff.
- **done (non-governed):**
  - Held-out agent test set `suite/agent_tests.json` (5 areas × equation/word/conceptual +
    out-of-scope; protected-core flags). New check scripts: `check_agent_coverage.py` (G2),
    `check_agent_trace.py` (G3), `check_agent_focus.py` (G5), `check_agent_flow.py` (G6/G8),
    `check_agent_transparency.py` (G7) — all pass offline.
  - `docs/scope.md` → FIVE areas (added dynamical systems/ODEs) + PDEs as a first-class
    deferred item; strengthened `tools/check_scope_docs.py` to require the 5th area + PDEs (G9).
  - Interpreter/engine robustness fixes surfaced by the coverage bar (now 100%/100%): trailing
    "and …"/"… of <expr>" stripping; scale-aware trajectory verification tolerance (saddles
    that fly off to ~1e7 now verify); grounding gate now treats numbers the user typed
    (problem coefficients) as given, not model-derived; "optimum/optima" added to focus vocab.
- **done (governed — in P-0003, needs approval):** registered CHK-008…012 in
  `checks/registry.md`; added ODE canonicals **D1–D4 to the protected core** table.
- **NEXT — Clara runs ONE command:** `python3 tools/approve.py P-0003`
  (review `git diff` + `proposals/P-0003-agent-checks-and-core.md` first). This re-records the
  baseline to include the five new checks + the ODE core; drift clears. If she'd rather not,
  `--decline P-0003`. She can delegate in-session ("approve P-0003") → I run it with
  `--on-behalf-of-clara`.
- **THEN (worker, after approval):** mark G1–G9 `met` in `goals/criteria.md` with recorded
  evidence (each criterion's backing check output), set goal state `met`, final `verify.py`
  + `validate.py` green = done. (Blocked until approval: marking criteria met while P-0003 is
  unapproved would leave validate red on the drift.)
- **decisions:** strengthening `check_scope_docs.py`/`run_suite.py` (stricter, never weaker)
  needs no proposal; ADDING registry checks + protected-core rows does → P-0003.
- **blockers:** the finish is gated on Clara approving P-0003 (governed; only she can, or
  delegated in-session). All build work is complete; nothing else is blocked.

## 2026-09-02 — Hardening while P-0003 is pending: Three.js vendored locally

- **state:** 🚧 Still waiting on Clara's `approve.py P-0003` (the only path to done). Used the
  blocked time on the one self-flagged pre-"done" task. verify.py still GREEN (12/12).
- **done (non-governed):** vendored **Three.js r160** + OrbitControls into `web/vendor/`
  (index.html importmap → local paths; server.py serves `/vendor/*` with a path-traversal
  guard). The locally-run tool now has **no runtime CDN dependency** — it renders fully
  offline. Browser-verified: paraboloid scene builds from the vendored lib, 1.12 ms/frame,
  no console errors; all 12 checks unaffected and green.
- **next:** unchanged — Clara approves P-0003, then worker marks G1–G9 met with evidence and
  sets the goal met.
- **blockers:** finishing gated on Clara approving P-0003 (governed). Optional remaining
  polish (not gating, not started): a project-facing README (the repo's README.md is the
  constraint-base framework readme — replacing the repo's public face is Clara's call).

## 2026-09-02 — Delegated approval (agent-executed)

- APPROVED: P-0003
- Clara's stated authority, verbatim: "Yes. I approve. Go ahead and run the approval for me. I'm giving you permission and telling you that I approve."
- Attribution mode makes this an audit record, not proof the authority was real. Enable signing (docs/governance.md) for approval the agent cannot forge.
