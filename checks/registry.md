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

## The representative problem suite

Several criteria (G1–G5) are judged "for every problem in the approved representative
suite." That suite is defined here and its composition is approved by Clara through
proposal **P-0001** — so it is governed content the agent cannot quietly weaken to pass.
It is **representative, not exhaustive**: it fixes the standard the four beachhead areas
are held to, not every problem they could handle.

The problems live as data in `suite/problems.json` (built during goal mode), each carrying
its definition and an **independently-computed reference** for every quantity the tool
displays. CHK-001 runs the whole suite through the engine and fails if any problem is
missing, any displayed value disagrees with its independent reference, or any result lacks
a passing verification record (constraint C-VERIFIED-MATH).

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

## CHK-001 — Suite solved and verified against independent references

- **covers:** G1
- **run:** python3 tools/run_suite.py
- **status:** active
- **waived:**
- **waived-by:**

<!--
Further checks are registered as their capabilities are built, each a governed addition
(CLAUDE.md: "Register checks as you build ... a governed change — propose it like any
other"): a sustained-frame-rate measurement (G2/C-INTERACTIVE), a step-through sync check
(G3), a grounded-answer check (G4/C-GROUNDED-EXPLANATION), an end-to-end flow check (G5),
and a scope-documentation check (G6). They are added when the thing they verify exists,
so they are not registered red-and-hollow ahead of it.
-->

