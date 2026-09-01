# Goal condition

The goal condition is short and stable on purpose. It gives a plain overview of the
project and defines what "done" means **by reference** — it does not list the criteria or
the checks, because those grow long and live in their own files (`goals/criteria.md` and
`checks/registry.md`). It is the contract the work is judged against, and it is not the
agent's to soften: see `constraints/defaults.md` (C-GOVERNED-CHANGE) and
`docs/governance.md`.

## Status

- **state:** approved
- **approved:** 2026-09-01 by Clara ("Looks good to me. I approve everything.")

## Statement

Manifold Landscape is a locally-run tool for building intuition in the geometry of
continuous mathematics. A user brings a problem in its supported domain — scalar fields and
surfaces, gradients and optimization landscapes, vector fields, and linear-algebra-as-
geometry — and the tool solves it with a verification-backed computation engine so the
answer is trustworthy, presents the solution as an interactive three-dimensional
visualization the user can manipulate and step through, and explains the intuition while
answering questions grounded in the actual computed state. It is built to make that
geometry genuinely understandable, to a standard suitable as portfolio work.

## What completion requires

Completion is judged and confirmed **through this constraint system**, never asserted from
the agent's own judgment. The agent works inside the constraints throughout — re-grounding
with `python3 tools/brief.py` — and claims "done" only after **running** the system's own
checks and seeing them pass, not from memory or reasoning. If the tools are not green, the
work is not done, whatever the agent believes.

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

Things that will still be imperfect when the goal condition is met, and that is fine. They
stop an agent from working past the finish line.

- Only the four beachhead areas are covered; problems outside them may not solve or render.
- Visualization is three-dimensional; higher-dimensional projection is a documented future
  expansion, not required here.
- Physics problems are not supported — documented as future work.
- No deployment, hosting, accounts, billing, or multi-user support; the tool runs locally
  for a single user.
- Not every conceivable problem within an area needs to be handled — the representative
  suite defines the bar, not exhaustive coverage.
- Polish is judged on the core flow being complete and unbroken, not on visual design being
  final or exhaustively themed.
