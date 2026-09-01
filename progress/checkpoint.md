# Checkpoint

The **current-state** snapshot — overwritten in place, not appended. Unlike
`progress/log.md` (which is history), this is the single short "resume here" card: where
the work stands *right now*, what to do next, and what is live in the agent's head that the
files alone would not tell a fresh session.

Refresh this at natural breaks, before context grows large, and whenever the session shows
signs of drift or rot. When a session is getting long, refresh this and recommend starting
a fresh one — a new session resuming from this card plus `python3 tools/brief.py` beats a
long, degraded one. This is **progress, not governed content**.

`tools/brief.py` prints this checkpoint every time it runs.

**Format:** keep it short. Replace the body below each refresh.

---

- **updated:** 2026-09-01
- **phase:** intake complete — goal condition APPROVED by Clara. Awaiting the baseline
  (governance engagement) before goal mode begins.
- **now:** All intake files written and approved (constraints, outcomes, goal condition,
  criteria G1–G6). Goal condition is `state: approved`. `tools/validate.py` is clean and
  32/32 tool tests pass. Governance is **not yet engaged** — the baseline has not been run.
- **next:**
  1. Clara runs `python3 tools/approve.py --baseline` (interactive terminal) to engage
     governance. From that point the constraints and goal condition are frozen — the agent
     proposes changes, does not make them.
  2. Start a fresh session for goal mode: paste the Step-1 priming prompt
     (`progress/priming-prompt.md`), let it orient, then seed it with the goal condition.
  3. First goal-mode task: define and register the **representative problem suite** in
     `checks/registry.md` for Clara's approval (it is governed content the finish line
     leans on — G1–G5 reference it).
- **watch:** Get the representative suite right and approved before building against it.
  Keep API keys out of tracked files (public repo, C-SECRETS); they belong in gitignored
  env files only. Approver identity: Clara's gmail and GitHub-noreply emails are both in
  `governance/approvers.txt`.
- **open blockers:** none (see `progress/blockers.md`).
