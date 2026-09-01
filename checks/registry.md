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

_No checks registered yet._
