# Check registry

Executable checks that verify this project. They live here, not in the goal condition, so
a complex project can register many of them without turning the finish line into a task
list. `tools/verify.py` runs every active check; the goal condition's completion gate is
satisfied only when each one is **passing**, or **waived with Clara's countersignature**.

Results (pass/fail, output, timestamps) are written to `checks/results.json`, which is
gitignored and is **not** part of what Clara approves. The checks themselves — their
commands and their waivers — are governed content: adding, changing, or waiving one is a
deliberate act, and once governance is engaged it needs Clara's approval, exactly like a
constraint.

**Entry format** (same heading-plus-fields convention as everything else):

```
## CHK-001 — Short title
- **covers:** optional — the criterion, outcome, or constraint id this check backs (e.g. G2)
- **run:** the shell command verify.py runs; exit 0 means pass, any nonzero means fail
- **status:** active | waived
- **waived:** required only when waived — the reason it is acceptable for this not to pass
- **waived-by:** required only when waived — countersigned by Clara via
  `python3 tools/approve.py --waive-check CHK-001 "reason"`
```

Marking a check `waived` by hand has **no effect on its own**: the check keeps binding
until Clara countersigns it (a `WAIVED-CHECK: CHK-001` commit), exactly as an unapproved
constraint waiver keeps binding. `verify.py` and `validate.py` both report an
un-countersigned waiver as still required.

Keep each `run:` command deterministic and self-contained: it should pass or fail on the
project's real behaviour, exit nonzero on failure, and not depend on network access
(constraint C-LOCAL) or on state left by another check.

<!-- INTAKE / GOAL MODE: register the project's checks below this line. -->

## The test set (protected core + appendable coverage)

Several criteria (G1–G3, G8) are judged over a **held-out test set** spanning the five areas
and the input styles (equation, word problem, conceptual request). Its governance is
**asymmetric**, by Clara's rule:

- A **protected core** of canonical problems may **not** be removed or weakened without
  Clara's approval — that is the bar the agent cannot quietly lower.
- The agent may **freely add** problems to broaden coverage; additions do not need approval.

The worker implements this as a guard: a check fails if any protected-core problem is
dropped or altered, while new problems can be appended at will. The initial **protected
core** is the twelve canonical problems below (from the shipped foundation); the worker
grows both the core (with Clara's approval) and the broader appendable set (freely) to cover
dynamical systems and the word-problem / conceptual input styles.

| id | area | problem | core operation exercised |
|----|------|---------|--------------------------|
| S1 | scalar fields & surfaces | `f = x² + y²` | gradient; minimum (Hessian pos-def) |
| S2 | scalar fields & surfaces | `f = x² − y²` | gradient; saddle (Hessian indefinite) |
| S3 | scalar fields & surfaces | `f = sin(x)·cos(y)` | multiple critical points, mixed type |
| O1 | gradients & optimization | `f = x² + 3y²` | gradient descent converging to min |
| O2 | gradients & optimization | Rosenbrock `(1−x)² + 100(y−x²)²` | hard landscape; min at (1,1) |
| O3 | gradients & optimization | min `x²+y²` s.t. `x+y=1` | Lagrange condition; constrained optimum |
| V1 | vector fields | `F = (−y, x)` | curl without divergence |
| V2 | vector fields | `F = (x, y)` | divergence without curl |
| V3 | vector fields | `F = (−y, x, z)` | divergence and curl of a 3-D field |
| L1 | linear algebra as geometry | `A = [[2,1],[1,2]]` | eigen-decomposition; determinant |
| L2 | linear algebra as geometry | `A = [[1,1],[0,1]]` | shear; non-diagonalizable; determinant |
| L3 | linear algebra as geometry | `A = [[1,2,0],[0,1,2],[2,0,1]]` | SVD; ellipsoid semi-axes |
| D1 | dynamical systems (ODEs) | `ẋ=y, ẏ=−x−y` | equilibrium at origin; stable spiral (Jacobian eigenvalues) |
| D2 | dynamical systems (ODEs) | `ẋ=x, ẏ=−y` | saddle equilibrium (eigenvalues +1, −1) |
| D3 | dynamical systems (ODEs) | pendulum `ẋ=y, ẏ=−sin(x)` | centre + two saddles; multiple equilibria |
| D4 | dynamical systems (ODEs) | Lorenz (σ=10, ρ=28, β=8/3) | chaos; verified trajectory + positive finite-time Lyapunov |

Dynamical-systems (ODE) problems D1–D4 were added to the protected core when the fifth area
was built (proposal **P-0003**). Together with the twelve above they are the canonical set
that must keep succeeding; the worker may still freely append more problems (to
`suite/problems.json` and `suite/agent_tests.json`) to broaden coverage.

## CHK-001 — Suite solved and verified against independent references

- **covers:** G1
- **run:** python3 tools/run_suite.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-002 — Scenes stay within the interactive render budget

- **covers:** G4
- **run:** python3 tools/check_render_budget.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-003 — Step-through builds each scene in sync

- **covers:** G4
- **run:** python3 tools/check_stepthrough.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-004 — Answers are grounded in the verified computed state

- **covers:** G6
- **run:** python3 tools/check_grounded.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-005 — End-to-end flow runs for every suite problem

- **covers:** G8
- **run:** python3 tools/check_e2e.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-006 — Scope and future expansion are documented

- **covers:** G9
- **run:** python3 tools/check_scope_docs.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-007 — Engine unit suite (regression net)

- **covers:** G1
- **run:** python3 -m pytest tests/ -q
- **status:** active
- **waived:**
- **waived-by:**

## CHK-008 — Agent coverage across the five areas and three input styles

- **covers:** G2
- **run:** python3 tools/check_agent_coverage.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-009 — Agentic, tool-orchestrated solving (from the recorded trace)

- **covers:** G3
- **run:** python3 tools/check_agent_trace.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-010 — The tutor drives the visualization to the right feature

- **covers:** G5
- **run:** python3 tools/check_agent_focus.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-011 — Grounded multi-turn chat and the unbroken agent flow

- **covers:** G6, G8
- **run:** python3 tools/check_agent_flow.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-012 — Transparent and responsive experience (automatable slice)

- **covers:** G7
- **run:** python3 tools/check_agent_transparency.py
- **status:** active
- **waived:**
- **waived-by:**

## CHK-013 — Shapes draw on, and a surface's reveal style is switchable

- **covers:** G10, C-DRAW-ON
- **run:** python3 tools/check_draw_on.py
- **status:** active
- **waived:**
- **waived-by:**

<!--
Note on G2 (C-INTERACTIVE). THRESHOLD: sustained 60 fps during manipulation, i.e. a frame
cost at or below 16.7 ms/frame, on Clara's development machine. CHK-002 is the automated
regression guard (it bounds the geometry each scene sends to the GPU so a change that would
tank the frame rate fails there). The actual frame cost is measured in the running app with
window.__ml.bench(): across the suite's scenes it is ≤ ~2 ms/frame (heaviest: the 3-D vector
field V3 at ~1.95 ms), i.e. 8×–100× under the 16.7 ms budget — recorded as G2's evidence.
-->

<!--
EXPANSION (2026-09-02, agentic AI tutor). CHK-001…007 above are the shipped FOUNDATION's
regression net: they guard the deterministic tool layer + the base UI the agent orchestrates.
They stay green as the agent is built on top. As the agentic layer lands, the worker
REGISTERS NEW CHECKS (governed additions — propose them) and REVISES some existing ones
(also governed):

  - CHK-00N (G2) — run the agent over the held-out test set; ≥90% success and 100% of the
    protected core; out-of-scope requests mapped or honestly declined, never fabricated.
  - CHK-00N (G3) — from a recorded agent trace, confirm the agent chose/sequenced tool calls
    from the input (different inputs → different sequences) and every displayed value came
    from a tool or is labelled model-derived.
  - CHK-00N (G5) — over scripted "focusing" questions, the view lands on / highlights the
    correct feature (the tutor drives the visualization).
  - CHK-00N (G7) — the tool-call view toggles on/off; a thinking indicator shows during agent
    work; the scene stays interactive while the agent computes.
  - CHK-004 (G6) will be REVISED from the template explainer to the agentic tutor's grounded,
    multi-turn answers (verified-or-labelled). CHK-005 (G8) will be REVISED to the full
    agentic flow (pose → interpret → solve → visualize → step → chat). CHK-006 (G9) will be
    REVISED to require FIVE areas + deferred PDEs. These revisions are governed — propose them.

Test-set governance (Clara's rule): a check must FAIL if any protected-core problem is
removed or weakened, but adding problems is free and needs no approval.
-->

