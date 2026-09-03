# Goal condition

The goal condition is short and stable on purpose. It gives a plain overview of the
project and defines what "done" means **by reference** — it does not list the criteria or
the checks, because those grow long and live in their own files (`goals/criteria.md` and
`checks/registry.md`). It is the contract the work is judged against, and it is not the
agent's to soften: see `constraints/defaults.md` (C-GOVERNED-CHANGE) and
`docs/governance.md`.

## Status

- **state:** met
- **approved:** 2026-09-02 by Clara — expanded scope (agentic AI tutor; arbitrary problem
  intake; fifth area, dynamical systems). The prior, narrower goal was met and shipped on
  2026-09-02 (commit `f3d98d6`) and now serves as the foundation this expansion builds on.
- **met:** 2026-09-02 — all nine criteria G1–G9 are `met` with recorded evidence in
  `goals/criteria.md`; `python3 tools/verify.py` is GREEN (CHK-001…012 all passing, 0 waived);
  every constraint held throughout. The one governed change needed (P-0003, registering the
  agent checks + the ODE protected core) was approved by Clara this session and recorded as a
  signed, agent-executed approval (`--on-behalf-of-clara`).
- **history:** original goal approved 2026-09-01 ("Looks good to me. I approve everything.")
  and met 2026-09-02 (six criteria, verify.py green); superseded by this expansion.

## Statement

Manifold Landscape is a locally-run, **AI-tutored** tool for building intuition in the
geometry of continuous mathematics. A user poses a problem **however they like** — a typed
equation, a word problem, or an open request like "show me an example of chaos" — across
**scalar fields & surfaces, gradients & optimization landscapes, vector fields, linear
algebra as geometry, and dynamical systems (ODEs)**. An **AI agent interprets the request
and orchestrates a set of deterministic tools** to solve it, so every result the user sees
is either tool-computed and verified or clearly labelled as model-derived (C-VERIFIED-MATH;
the model computing math itself is a last resort). **By default it presents the answer as an
interactive three-dimensional visualization** the user can manipulate; and, **when the user
asks for it**, it **tutors** — an optional step-by-step walkthrough that builds the
visualization in sync, drives it to point at what matters, and answers follow-up questions at
any step, grounded in the actual computed state. The agent's tool use is **inspectable**, and
the visualization stays responsive while it thinks. It is built to make that geometry
genuinely understandable and to demonstrate both mathematical depth and agentic-AI craft, to
a standard suitable as portfolio work.

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

- Only the five supported areas are covered; requests outside them may be mapped to the
  nearest in-scope illustration or honestly declined — they need not solve or render.
- **PDEs are a documented future expansion of the dynamical-systems area, not required here.**
- Physics problems are not supported — documented as future work.
- Visualization is three-dimensional; higher-dimensional projection is a documented future
  expansion, not required here.
- No deployment, hosting, accounts, billing, or multi-user support; the tool runs locally
  for a single user. (Calling an LLM API over the network is expected and is not deployment.)
- Not every conceivable input needs to succeed — the held-out test set defines the bar, not
  exhaustive coverage; the rest is handled gracefully rather than perfectly.
- A small class of results may be shown **clearly labelled as model-derived and unverified**;
  not everything is tool-verifiable, and that is acceptable when it is honestly marked.
- Polish is judged on the core flow being complete and unbroken, not on visual design being
  final or exhaustively themed.
