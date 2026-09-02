## P-0002 — Verification check battery for G2–G6 (and a regression net)

- **status:** approved
- **kind:** new-constraint
- **targets:** checks/registry.md (CHK-002 … CHK-007); criteria G2, G3, G4, G5, G6
- **proposed:** 2026-09-01
- **because:** P-0001 registered CHK-001 (the suite, backing G1). The other five criteria
  need their own executable checks so the completion gate actually re-verifies them and a
  later change that breaks one turns the suite red — which is the whole point of the check
  registry (CLAUDE.md: "register checks as you build … keep them green"). All six capabilities
  now exist and each check passes; this registers them as governed content so they cannot be
  quietly weakened, and so `python3 tools/verify.py` green means what the goal condition says
  it means. Without this, G2–G6 would rest on criteria evidence alone with nothing guarding
  against regression.

- **change:** Register the following checks in `checks/registry.md` (already written there,
  pending this approval); approving re-records the baseline to include them. Each is
  deterministic and offline (constraint C-LOCAL), and each currently passes:
  - **CHK-002 (G2)** `tools/check_render_budget.py` — bounds the geometry each suite scene
    sends to the GPU, so a change that would tank the frame rate fails here. The *actual*
    sustained frame rate is measured in the running app (`window.__ml.state().fps`) during
    manipulation and recorded as G2's evidence; this check is the automated regression guard
    that keeps that measurement honest (see the note in the registry).
  - **CHK-003 (G3)** `tools/check_stepthrough.py` — at each step, exactly the geometry that
    step introduces becomes visible, nothing from a later step early, for every suite problem.
  - **CHK-004 (G4)** `tools/check_grounded.py` — scripted questions across problems; each
    answer cites only verified quantities, states the correct computed value, and asserts
    nothing the engine contradicts (C-GROUNDED-EXPLANATION).
  - **CHK-005 (G5)** `tools/check_e2e.py` — the full flow (pose → solve → scene → step → ask)
    runs cleanly for every suite problem, with no error, unverified value, or broken step.
  - **CHK-006 (G6)** `tools/check_scope_docs.py` — `docs/scope.md` names the four supported
    areas and the deferred expansions (physics, higher-dimensional visualization).
  - **CHK-007 (G1, regression net)** `python3 -m pytest tests/ -q` — the engine unit suite.

- **risk:** Registering checks fixes what "verified" requires, so a check that is too weak
  would let a regression pass, and one too brittle would fail on a harmless change and block
  completion until re-approved. Mitigations: each check asserts an observable behaviour tied
  to its criterion (step visibility, grounded values, flow completion, documented scope) rather
  than an implementation detail, and each is deterministic and already green on the current
  code. The one indirection is G2: a headless process cannot measure real WebGL frame rate, so
  CHK-002 guards a geometry budget and the true frame-rate number is recorded as G2 evidence
  from the running app — this is disclosed, not hidden. Approving does not lock the checks
  forever; only *weakening* one later needs re-approval, which is the asymmetry governance
  enforces.

- **approved:** 2026-09-02
