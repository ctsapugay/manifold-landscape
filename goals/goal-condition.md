# Goal condition

The goal condition is short and stable on purpose. It gives a plain overview of the
project and defines what "done" means **by reference** — it does not list the criteria or
the checks, because those grow long and live in their own files (`goals/criteria.md` and
`checks/registry.md`). It is the contract the work is judged against, and it is not the
agent's to soften: see `constraints/defaults.md` (C-GOVERNED-CHANGE) and
`docs/governance.md`.

## Status

- **state:** draft
- **approved:** _not yet approved by Clara_

## Statement

<!-- INTAKE: one short paragraph. What the project is, and what becomes true when it
     exists. The overview a newcomer reads first. Not a list of requirements. -->

_Not yet drafted._

## What completion requires

The task is complete only when **all** of the following hold, and the work is judged
**only** against these. None may be softened, removed, or reinterpreted except through the
governance process in `docs/governance.md`.

1. **Every criterion in `goals/criteria.md` is `met`, each with recorded evidence.**
   Check their live status with `python3 tools/brief.py --goal` or `python3 tools/status.py`.
2. **`python3 tools/verify.py` is green** — every check in `checks/registry.md` is passing,
   or waived with Clara's countersignature.
3. **Every constraint in `constraints/` held throughout** — none was violated, and any
   waiver is one Clara approved. See what binds with `python3 tools/brief.py`.

This section is standing and identical for every project. `tools/validate.py` enforces it:
marking the goal `met` while any criterion is unmet, the check suite is not green, or a
waiver is unbacked is an error. The finish line is these three files together, not a
description repeated here.

## Out of scope for "done"

<!-- INTAKE: things that will still be imperfect when the goal condition is met, and that
     is fine. Prevents an agent from working past the finish line. -->

- _..._
