---
description: Run project intake with Clara and draft a goal condition
---

Run intake for this project.

Read `docs/intake.md` and `docs/outcome-vs-implementation.md` first, then follow the
intake process exactly. Key points, so you do not have to re-derive them:

- It is a conversation. Two or three questions at a time, not a wall of them.
- Ask about outcomes, boundaries, and non-goals. Never about architecture, structure, or
  libraries. If Clara volunteers a technology, it becomes a constraint only if it is
  imposed on her from outside — and then it needs a `why:` field.
- Push back on vague answers. "Fast", "clean", "robust" are not outcomes until they are
  attached to something observable.
- Show her the seven inherited defaults and ask whether any should be waived. Do not
  encourage waiving.
- Draft nothing to disk until she has agreed to the substance.

Then write `goals/outcomes.md`, `constraints/project.md`, `goals/goal-condition.md`, and
the criteria in `goals/criteria.md`; read `docs/goal-conditions.md`, and present the goal
condition and its criteria for her approval or edit.

Finish by running `python3 tools/validate.py`, fixing what it reports, and appending an
entry to `progress/log.md`.
