# Blockers

The live blocker ledger. This is **progress, not governed content** — it changes freely
and is not part of the approved baseline.

## What this is for

Goal mode is meant to keep moving. When one piece of work is blocked, the agent records
the blocker here and **switches to other unblocked work** rather than stalling or forcing
past it. Only when *every* remaining front is blocked does the agent pause and surface all
open blockers to Clara at once — a single consolidated ask, not one interruption per
blocker. See `CLAUDE.md` § "Staying on task across a long run".

`tools/brief.py` prints the open blockers every time it runs, so re-grounding always shows
what is stuck.

**Entry format:**

```
## B1 — Short title
- **blocks:** what this holds up (a criterion id, a task, an area)
- **why:** what makes it stuck
- **needs:** what would unblock it (often "Clara's decision on X"; be specific)
- **status:** open | resolved
- **opened:** YYYY-MM-DD
- **resolved:** YYYY-MM-DD and how (only when resolved)
```

Blocker ids are `B` plus a number, unique here. Keep resolved entries — they are a record
of what was decided, and stop the same wall being hit twice.

---

## B1 — Anthropic API credit balance exhausted (blocks further LIVE verification)

- **blocks:** completing the LIVE full-suite re-verification of the new goal (driving every case
  through the real Claude agent + live follow-ups across all five areas). Offline verification and
  the browser VISUAL/ANIMATION pass (engine-produced, brain-independent) are NOT blocked.
- **why:** extensive live drives this session exhausted the credits; live agent calls now return
  `BadRequestError 400 — "Your credit balance is too low to access the Anthropic API."`
- **needs:** Clara to top up credits (Plans & Billing). Buying credits is a financial action the
  agent must not perform.
- **status:** open
- **opened:** 2026-09-04
- **progress made before it hit:** full suite driven live 39/39 (core 20/20) earlier; the 4 general
  fixes verified live and correct; scalar-fields + optimization follow-ups verified live (excellent).
  Vector-fields / linear-algebra / dynamical-systems live follow-ups still to re-confirm once credits
  return (offline versions pass).
