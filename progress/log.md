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
