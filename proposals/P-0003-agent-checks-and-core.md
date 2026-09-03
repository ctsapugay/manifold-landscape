## P-0003 — Register the agentic-tutor checks and lock in the ODE canonicals

- **status:** approved
- **kind:** new-constraint
- **targets:** criteria G2, G3, G5, G6, G7, G8 (their "an automated check exercises this"
  clauses); and the protected-core test set in `checks/registry.md`.
- **proposed:** 2026-09-02
- **because:** The approved expansion (baseline `32722e2`) set criteria G2, G3, G5, G7 that
  each say "an automated check in `checks/registry.md` exercises this", and re-scoped G6/G8
  to the agentic flow — but the only checks that existed (CHK-001…007) test the deterministic
  foundation, not the agent. Those criteria cannot honestly be marked met until real checks
  exercise the agent (C-EVIDENCE), and adding a check once governance is engaged is a governed
  act. This registers the missing checks, now built and passing. Separately, the fifth area
  (dynamical systems / ODEs) is built and its four canonical problems D1–D4 are in the suites;
  they belong in the **protected core** so the bar for that area cannot later be quietly
  lowered — which the registry's own note said would be added "with Clara's approval". Leaving
  this unapproved means the finish line for the whole agentic half of the project rests on no
  executable evidence, and the new ODE canonicals are freely removable.
- **change:** In `checks/registry.md`, (a) add four rows (D1–D4) to the protected-core table
  — stable spiral, saddle, pendulum (centre + two saddles), and the Lorenz chaos system — and
  update the note beneath it to say the worker may still freely *append* coverage; and
  (b) register five new active checks, each backed by a new, passing, offline (no-network)
  script under `tools/`:
  - **CHK-008 (G2)** `python3 tools/check_agent_coverage.py` — the agent solves the held-out
    set in `suite/agent_tests.json` (five areas × equation/word/conceptual) at ≥90% overall
    and 100% of its protected core, and declines out-of-scope requests instead of bluffing.
  - **CHK-009 (G3)** `python3 tools/check_agent_trace.py` — from the recorded trace, different
    inputs drive different tool sequences and every displayed value is tool-produced/verified.
  - **CHK-010 (G5)** `python3 tools/check_agent_focus.py` — focusing questions drive the view
    to the correct verified feature.
  - **CHK-011 (G6, G8)** `python3 tools/check_agent_flow.py` — the full agent flow runs
    pose→solve→scene→step→multi-turn chat with no crash, every turn grounded.
  - **CHK-012 (G7)** `python3 tools/check_agent_transparency.py` — the agent trace is
    inspectable and the UI wires the tool-call toggle, thinking indicator, and rAF render loop.
  Approving re-records the baseline (`approve.py P-0003`) so these become part of the gate.
  (No existing check is weakened; CHK-001…007 are unchanged. The strengthening of
  `tools/check_scope_docs.py` to require five areas + PDEs, and of `tools/run_suite.py` to
  check ODE references, are not part of this proposal — they only make existing checks stricter
  and change no registry entry.)
- **risk:** These checks run the deterministic offline brain, not the live Claude agent
  (C-LOCAL forbids network in checks), so they prove the orchestration machinery, tool
  choice, grounding, and view-driving — but not that the Claude API path specifically
  behaves (that is exercised by an injected-client unit test and by manual use, and depends
  on a key). G7's fully-interactive parts (clicking the toggle, the spinner, orbiting while
  the agent thinks) are checked in the source and verified manually, not clicked by a bot.
  If the held-out set were made easy, CHK-008 could pass on a weak agent — mitigated by its
  protected core and by the set being a fair spread of phrasings; the set may be broadened
  freely but its core may not shrink without your approval. Adding D1–D4 to the protected
  core makes them un-removable without a further proposal (that is the intent).
- **approved:** 2026-09-02
