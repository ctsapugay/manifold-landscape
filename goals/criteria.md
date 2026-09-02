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

> **On the test set.** Several criteria refer to a *held-out test set* spanning the five
> areas and the input styles (equation, word problem, conceptual request). That set lives in
> the repository and is described in `checks/registry.md`. Its governance is asymmetric
> (Clara's rule): a **protected core** of canonical problems may not be removed or weakened
> without her approval, but the agent may **freely add** problems to broaden coverage. The
> test set defines the bar for "done"; it is not meant to be exhaustive.

---

## G1 — Trustworthy mathematics: verified, or honestly labelled

- **criterion:** Every mathematical result the interface shows is either produced by a deterministic tool and independently verified, or clearly labelled to the user as model-derived and unverified; nothing unverified is ever presented as if it were verified.
- **check:** Across the test set, trace every displayed result: each is backed by a tool computation with a passing verification record, or carries a visible model-derived/unverified label. An automated check in `checks/registry.md` confirms no unverified value is presented as verified (constraint C-VERIFIED-MATH).
- **state:** unmet
- **evidence:**

## G2 — Broad problem coverage across the five areas and all input styles

- **criterion:** The agent solves problems spanning all five areas — scalar fields & surfaces, gradients & optimization landscapes, vector fields, linear algebra as geometry, and dynamical systems (ODEs) — posed as equations, word problems, or open conceptual prompts, succeeding on a large held-out test set, and handling out-of-scope inputs gracefully rather than crashing or bluffing.
- **check:** Run the agent over the held-out test set (in `checks/registry.md`); it succeeds on at least **90%** of it and on **100% of the protected core** of canonical problems, and a sample of deliberately out-of-scope requests is either mapped to the nearest in-scope illustration or honestly declined — never answered with an unlabelled fabrication.
- **state:** unmet
- **evidence:**

## G3 — Agentic, tool-orchestrated solving

- **criterion:** Solving is performed by an AI agent that interprets the user's input and decides which deterministic tools to call and in what order; it is not a fixed hard-coded pipeline, and the mathematics is done by the tools (or, only where no tool applies, by the agent subject to G1).
- **check:** For a representative set of problems, inspect the recorded agent trace: the agent chose and sequenced tool calls in response to the input (different inputs drive different tool sequences), and every displayed mathematical value came from a tool call or is labelled model-derived (constraint C-VERIFIED-MATH). An automated check in `checks/registry.md` exercises this.
- **state:** unmet
- **evidence:**

## G4 — Interactive three-dimensional visualization with in-sync step-through

- **criterion:** By default each solved problem is shown as the answer plus an interactive three-dimensional scene the user can rotate, zoom, and pan smoothly, with no step-through forced on them; and the user can opt into a step-by-step walkthrough (a control they choose) that builds the scene in sync, each step showing exactly the geometry it introduces — no more, no less, and nothing from a later step shown early.
- **check:** Open a representative set of solved problems; by default the answer and an explorable scene appear with no forced stepping, and manipulation is smooth (a measured sustained frame rate above the threshold in `checks/registry.md`, constraint C-INTERACTIVE); then start the optional walkthrough and advance step by step, confirming each step shows exactly its geometry at its step (check in `checks/registry.md`).
- **state:** unmet
- **evidence:**

## G5 — The tutor drives the visualization

- **criterion:** When the user is being tutored — the optional walkthrough, or a question they ask — and it aids understanding (a judgment the agent makes), the tutor's explanation manipulates the scene, focusing, highlighting, or transforming the relevant feature so the user's attention is drawn to what is being explained; it need not do so every time, only when it helps.
- **check:** Over a scripted set of "focusing" questions where a visual move is clearly warranted (e.g. "where is the minimum?"), the view demonstrably lands on or highlights the correct feature; and the agent has, and uses, the capability to drive camera, highlights, and transforms. An automated check in `checks/registry.md` exercises the focusing cases.
- **state:** unmet
- **evidence:**

## G6 — Grounded, multi-turn tutoring chat at any step

- **criterion:** At any point in a solved problem the user can converse with the tutor across multiple turns, and every answer is consistent with that problem's computed and verified state and contradicts none of it, with quantitative claims tracing to a computed result or labelled model-derived.
- **check:** For a set of scripted multi-turn conversations across representative problems, each answer references the correct computed values and asserts nothing the engine's results contradict; any claim not backed by a computed result is labelled model-derived (constraints C-GROUNDED-EXPLANATION, C-VERIFIED-MATH). An automated check in `checks/registry.md` exercises this.
- **state:** unmet
- **evidence:**

## G7 — Transparent and responsive experience

- **criterion:** The user can toggle a view of the agent's tool-calls (what it computed) on or off; a visible indicator shows while the agent is working; and the three-dimensional visualization stays responsive to manipulation while the agent thinks.
- **check:** In the running app, toggle the agent-activity view on and off (it shows the tool-calls when on, hides them when off); confirm a thinking indicator appears during agent work; and confirm the scene still rotates/zooms/pans smoothly while a response is being computed (constraint C-INTERACTIVE).
- **state:** unmet
- **evidence:**

## G8 — Polished, unbroken end-to-end flow

- **criterion:** The complete path — pose a problem, have it interpreted, solved, visualized, stepped through, and chatted about — runs end to end across the held-out test set with no crash, no unhandled error surfaced to the user, no dead end, and no placeholder in the interface.
- **check:** Walk the full flow (pose → interpret → solve → visualize → step → chat) for a representative sample of the test set; confirm no crash, no unhandled error reaches the user, and no placeholder or broken state anywhere in the core flow. An automated end-to-end check in `checks/registry.md` exercises the sample.
- **state:** unmet
- **evidence:**

## G9 — Scope and future expansion are documented

- **criterion:** The repository documents the five supported areas and the planned future expansions — at least PDEs, physics, and higher-than-three-dimensional visualization — distinguishing what is in scope now from what is deferred.
- **check:** Open the scope/expansion documentation in the repository and confirm it states the five supported areas (including dynamical systems / ODEs) and lists the deferred expansions (at least PDEs, physics, and higher-dimensional visualization) clearly enough that a user is not misled about what the tool does.
- **state:** unmet
- **evidence:**
