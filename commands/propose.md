---
description: Write a proposal to change a constraint or the goal condition
---

You believe a standing constraint or the goal condition is wrong, mis-scoped, or
blocking. You may not change it. Write a proposal.

First, read `docs/governance.md` and `proposals/TEMPLATE.md`.

Before writing, be honest with yourself about which of these is true:

- the constraint is genuinely wrong or mis-scoped, or
- the constraint is right and my approach is wrong, or
- the constraint is right, the approach is fine, and this is just hard.

Only the first is a reason to propose. Say in the proposal which one you concluded and
why — if you cannot rule out the second, try the other approach first.

Then create `proposals/P-000N-short-slug.md` using the next unused number, with:

- **targets** — the constraint or criterion id
- **because** — what you actually tried, what it prevented, and the cost of leaving it
- **change** — the exact replacement text, so Clara reads the new rule rather than
  imagining it
- **risk** — what stops being protected, argued as its strongest case against you
- **status: proposed** — never `approved`; that is not yours to set

Prefer narrowing a rule to removing it.

Then: leave everything else untouched, tell Clara the proposal is waiting and summarise
it in two sentences, and carry on inside the existing constraint — or say you are blocked
and stop. Do not proceed as though the proposal were approved.

Finally, note the proposal in `progress/log.md`.
