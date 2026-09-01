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
- **phase:** intake COMPLETE, governance ENGAGED (signed baseline). Ready for goal mode —
  no code written yet.
- **now:** Baseline recorded and signed (commit `910ee46`, `APPROVED: BASELINE`);
  `tools/validate.py` reports governance engaged, signed, no drift. Constraints and the goal
  condition are now frozen — the agent proposes changes, does not make them. All pushed to
  GitHub (`ctsapugay/manifold-landscape`, main). No project code exists yet.
- **next (first goal-mode session):**
  1. Define and register the **representative problem suite** in `checks/registry.md`,
     spanning the four beachhead areas (scalar fields & surfaces; gradients & optimization
     landscapes; vector fields; linear-algebra-as-geometry). G1–G5 lean on it, and it is
     governed content — so bring it to Clara for approval (a proposal / her sign-off)
     before building against it.
  2. Then start building toward G1 (verified solving) with the engine + verification core,
     since C-VERIFIED-MATH is the floor everything else sits on.
- **watch:** Get the representative suite approved before building against it. Keep API keys
  out of tracked files (public repo — C-SECRETS); gitignored env files only. Governance is
  in **signed mode**: approval commits must be SSH-signed (git config for that is local to
  this clone: `gpg.format=ssh`, `user.signingkey=~/.ssh/id_ed25519_ctsapugay.pub`).
- **open blockers:** none (see `progress/blockers.md`).
