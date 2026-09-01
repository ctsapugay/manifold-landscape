# Proposal template

Copy this to `proposals/P-000N-short-slug.md`, fill it in, and tell Clara it is waiting.
Numbering is sequential; take the next unused number.

A proposal is a request, not a change. Writing one does nothing on its own — that is the
point. The constraint you are asking about stays fully in force until Clara approves.

Never set `status: approved` yourself. Approval is recorded by `tools/approve.py`, which
Clara runs, in a commit that says `APPROVED: P-000N`. `tools/validate.py` cross-checks
the two and reports a mismatch as an error.

```
## P-0001 — Short title

- **status:** proposed
- **kind:** waiver | constraint-change | goal-change | new-constraint
- **targets:** the constraint id or goal criterion id this concerns
- **proposed:** YYYY-MM-DD
- **because:** Why the current rule is wrong, mis-scoped, or genuinely blocking. Be
  specific: what did you try, what did it prevent, what is the cost of leaving it as is.
  "It is inconvenient" is not a reason.
- **change:** Exactly what would differ if this is approved. Quote the replacement text
  so Clara can read the new rule rather than imagine it.
- **risk:** What this stops protecting, and what could go wrong as a result.
- **approved:**
```

Guidance on writing a good one:

- **Argue against yourself.** The `risk:` field is where you say what the constraint was
  protecting and what is lost. A proposal with an empty risk field reads as advocacy.
- **Prefer narrowing to removing.** If a rule is too broad, propose the narrower rule
  that still catches the failure it was written for.
- **A blocked task is not automatically a bad constraint.** Sometimes the constraint is
  right and the approach is wrong. Say which you think it is.
- **One proposal, one change.** Bundled proposals are hard to approve in part.
