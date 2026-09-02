# Criteria

The measurable criteria that make up the finish line. The goal condition
(`goals/goal-condition.md`) points here and requires **every** one of these to be met; it
does not repeat them, because this list can grow long.

A criterion is a **checkable statement about the world** — something a skeptic who was not
in the conversation could verify by running or looking at something. It says what is true
at the end, never how to build it. See `docs/goal-conditions.md`.

**Entry format:**

```
## G1 — Short title
- **criterion:** What must be observably true.
- **check:** The specific thing someone runs, opens, or looks at to confirm it.
- **state:** unmet | met
- **evidence:** Empty until met. Then: what was run and what it showed, with a date.
```

Criteria ids are `G` plus a number, unique here. Keep the wording outcome-shaped; put
concrete commands and paths in `check:` (which is not shape-scanned), not in `criterion:`.
Executable checks that run automatically belong in `checks/registry.md` and can reference
a criterion with `covers:`.

> **On the representative problem suite.** Several criteria below refer to a *representative
> problem suite* spanning the four beachhead areas. That suite is defined and registered in
> `checks/registry.md` at the start of goal mode and approved by Clara — so it is governed
> content the agent cannot quietly weaken to pass. It sets the bar for "done"; it is not
> meant to be exhaustive.

---

## G1 — Correct, verified solutions across the four areas

- **criterion:** For every problem in the approved representative suite spanning all four beachhead areas, the solution the tool presents matches an independently computed reference, and each displayed quantity carries a record showing it came from the deterministic engine and passed verification.
- **check:** Run the suite via `python3 tools/verify.py`; each problem's solution is compared against a known-good reference computed independently, and each result's provenance-and-verification record is present and passing. No result traces back to model text alone (constraint C-VERIFIED-MATH).
- **state:** met
- **evidence:** 2026-09-02 `python3 tools/verify.py` GREEN. CHK-001 (`tools/run_suite.py`): all 12 suite problems solved; every displayed quantity is engine-produced (provenance in sympy./numpy./scipy./engine.*, `model` rejected at construction) and passed its independent verification step; every key answer matches an independently-computed reference — S1–S3 critical points & types, O1–O3 minima/Rosenbrock (1,1)/Lagrange (½,½) λ=1, V1–V3 divergence & curl, L1–L2 eigenvalues/determinant/defectiveness, L3 SVD singular values [3, √3, √3] (reference via eig(AᵀA), independent of the engine's SVD). CHK-007 (`pytest tests/`): 25 passed.

## G2 — Interactive three-dimensional visualization

- **criterion:** Each solved problem is shown as a three-dimensional scene the user can rotate, zoom, and pan, and the scene keeps responding smoothly while they do so on Clara's machine.
- **check:** Open a representative set of solved problems, manipulate each view, and observe smooth interaction; a scripted or instrumented measurement records a sustained frame rate above the threshold set in `checks/registry.md` during manipulation (constraint C-INTERACTIVE).
- **state:** met
- **evidence:** 2026-09-02 CHK-002 (`tools/check_render_budget.py`) GREEN — all 12 scenes within the interactive geometry budget. Threshold (registry): sustained 60 fps ≡ ≤16.7 ms/frame. Instrumented in the running app via `window.__ml.bench(180)`: frame cost ≤ ~2 ms/frame across all suite scenes — worst case the 3-D vector field V3 (729 arrows) at 1.95 ms; surfaces ~0.45 ms; SVD 0.13 ms — i.e. 8×–100× under the 60-fps budget. Rotate/zoom/pan confirmed smooth in the browser (drag-rotate verified on paraboloid and SVD scenes).

## G3 — Step-through builds the visualization in sync

- **criterion:** For a solved problem the user can move through the solution one step at a time, and the scene shown at each step contains exactly the geometry that step introduces — no more, no less.
- **check:** Advance through a representative problem step by step and confirm at each step that the newly shown geometry corresponds to that step's mathematical operation (e.g. the gradient vector appears when the gradient step runs), with nothing from later steps shown early.
- **state:** met
- **evidence:** 2026-09-02 CHK-003 (`tools/check_stepthrough.py`) GREEN — for all 12 suite problems, at each step the newly-visible layers are exactly those tagged with that step, and no later-step geometry is ever shown early. Confirmed live in the browser via `window.__ml`: stepping the paraboloid 0→1→2→3 gave visible layer-steps [0]/[0,1]/[0,1]/[0,1,3] — the gradient field appears at the gradient step, the critical point at the critical-point step.

## G4 — Grounded questions and answers at any step

- **criterion:** At any point in a solved problem the user can pose a question and receives an explanation that agrees with the engine's computed values for that problem and contradicts none of them.
- **check:** For a set of scripted questions across representative problems, confirm each answer references the correct computed values and asserts nothing the engine's results contradict (constraint C-GROUNDED-EXPLANATION).
- **state:** met
- **evidence:** 2026-09-02 CHK-004 (`tools/check_grounded.py`) GREEN — 11 scripted questions across S1/S2/O2/O3/V1/V2/V3/L1/L2/L3. Each answer cites only verified quantities (`grounded_in` ⊆ the problem's verified results), states the correct computed value (e.g. minimum at (0,0); curl = 2 with "rotates"; eigenvalues 3 and 1; singular values 3, 1.73), and contains no claim the engine contradicts (e.g. the saddle answer never says "minimum"/"maximum"). The explanation engine composes answers only from verified `Quantity` values — no model in the numeric path. `tests/test_explain.py`: 6 passed.

## G5 — Polished, unbroken end-to-end flow

- **criterion:** The complete path from posing a problem to a solved, explorable, explained result runs end to end for every problem in the representative suite with no error, dead end, or placeholder in the interface.
- **check:** Walk the full flow — pose, solve, visualize, step through, ask a question — for every problem in the representative suite; confirm no crash, no unhandled error surfaced to the user, and no placeholder or broken state anywhere in the core flow.
- **state:** met
- **evidence:** 2026-09-02 CHK-005 (`tools/check_e2e.py`) GREEN — for all 12 suite problems the full flow (pose → solve → build scene → step through → ask) runs with no exception, every displayed quantity verified and engine-sourced, a valid base+step sequence, and grounded answers. Exercised live in the browser through `web/server.py` (http://127.0.0.1:8765): selecting problems solves and renders them, stepping and the ask box work, and server errors surface as clean JSON messages, never stack traces or placeholders.

## G6 — Scope and future expansion are documented

- **criterion:** The repository documents the supported scope and the planned future expansions — including physics and higher-than-three-dimensional visualization — distinguishing what is in scope now from what is deferred.
- **check:** Open the scope/expansion documentation in the repository and confirm it states the four supported areas and lists the deferred expansions (at least physics and higher-dimensional visualization) clearly enough that a user is not misled about what the tool does.
- **state:** met
- **evidence:** 2026-09-02 CHK-006 (`tools/check_scope_docs.py`) GREEN — `docs/scope.md` names all four supported areas (scalar fields & surfaces, gradients & optimization, vector fields, linear algebra as geometry) and the deferred expansions (physics; higher-than-three-dimensional visualization), and distinguishes current scope from deferred/future work.
