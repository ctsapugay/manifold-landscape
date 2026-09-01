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
- **state:** unmet
- **evidence:**

## G2 — Interactive three-dimensional visualization

- **criterion:** Each solved problem is shown as a three-dimensional scene the user can rotate, zoom, and pan, and the scene keeps responding smoothly while they do so on Clara's machine.
- **check:** Open a representative set of solved problems, manipulate each view, and observe smooth interaction; a scripted or instrumented measurement records a sustained frame rate above the threshold set in `checks/registry.md` during manipulation (constraint C-INTERACTIVE).
- **state:** unmet
- **evidence:**

## G3 — Step-through builds the visualization in sync

- **criterion:** For a solved problem the user can move through the solution one step at a time, and the scene shown at each step contains exactly the geometry that step introduces — no more, no less.
- **check:** Advance through a representative problem step by step and confirm at each step that the newly shown geometry corresponds to that step's mathematical operation (e.g. the gradient vector appears when the gradient step runs), with nothing from later steps shown early.
- **state:** unmet
- **evidence:**

## G4 — Grounded questions and answers at any step

- **criterion:** At any point in a solved problem the user can pose a question and receives an explanation that agrees with the engine's computed values for that problem and contradicts none of them.
- **check:** For a set of scripted questions across representative problems, confirm each answer references the correct computed values and asserts nothing the engine's results contradict (constraint C-GROUNDED-EXPLANATION).
- **state:** unmet
- **evidence:**

## G5 — Polished, unbroken end-to-end flow

- **criterion:** The complete path from posing a problem to a solved, explorable, explained result runs end to end for every problem in the representative suite with no error, dead end, or placeholder in the interface.
- **check:** Walk the full flow — pose, solve, visualize, step through, ask a question — for every problem in the representative suite; confirm no crash, no unhandled error surfaced to the user, and no placeholder or broken state anywhere in the core flow.
- **state:** unmet
- **evidence:**

## G6 — Scope and future expansion are documented

- **criterion:** The repository documents the supported scope and the planned future expansions — including physics and higher-than-three-dimensional visualization — distinguishing what is in scope now from what is deferred.
- **check:** Open the scope/expansion documentation in the repository and confirm it states the four supported areas and lists the deferred expansions (at least physics and higher-dimensional visualization) clearly enough that a user is not misled about what the tool does.
- **state:** unmet
- **evidence:**
