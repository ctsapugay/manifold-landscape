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
- **state:** met
- **evidence:** 2026-09-02 — `python3 tools/verify.py` GREEN. CHK-001 (`tools/run_suite.py`) solves every suite problem and confirms each displayed quantity carries an engine provenance (never "model") and a passing independent verification, matching stored independent references ("SUITE VERIFIED"). CHK-007 (`pytest tests/`, 49 passed) exercises the engine; `engine/result.py` rejects `MODEL_PROVENANCE` on construction, so no unverified/model value can surface. The agent's grounding gate (`agent/grounding.py`) labels any answer number without a verified source as "model-derived and unverified" (checked by CHK-008/009/011, which report `model_derived=False` across the sets).

## G2 — Broad problem coverage across the five areas and all input styles

- **criterion:** The agent solves problems spanning all five areas — scalar fields & surfaces, gradients & optimization landscapes, vector fields, linear algebra as geometry, and dynamical systems (ODEs) — posed as equations, word problems, or open conceptual prompts, succeeding on a large held-out test set, and handling out-of-scope inputs gracefully rather than crashing or bluffing.
- **check:** Run the agent over the held-out test set (in `checks/registry.md`); it succeeds on at least **90%** of it and on **100% of the protected core** of canonical problems, and a sample of deliberately out-of-scope requests is either mapped to the nearest in-scope illustration or honestly declined — never answered with an unlabelled fabrication.
- **state:** met
- **evidence:** 2026-09-02 — CHK-008 (`tools/check_agent_coverage.py`, approved in P-0003) runs the agent over `suite/agent_tests.json` (33 in-scope problems across all five areas × equation/word/conceptual styles + 6 out-of-scope) and reports **overall 39/39 = 100%, protected core 20/20 = 100%**; every in-scope case returns a verified scene and every out-of-scope case is declined with no scene and no fabrication ("AGENT COVERAGE OK"). Passes under `python3 tools/verify.py`.

## G3 — Agentic, tool-orchestrated solving

- **criterion:** Solving is performed by an AI agent that interprets the user's input and decides which deterministic tools to call and in what order; it is not a fixed hard-coded pipeline, and the mathematics is done by the tools (or, only where no tool applies, by the agent subject to G1).
- **check:** For a representative set of problems, inspect the recorded agent trace: the agent chose and sequenced tool calls in response to the input (different inputs drive different tool sequences), and every displayed mathematical value came from a tool call or is labelled model-derived (constraint C-VERIFIED-MATH). An automated check in `checks/registry.md` exercises this.
- **state:** met
- **evidence:** 2026-09-02 — CHK-009 (`tools/check_agent_trace.py`, approved in P-0003) inspects the recorded trace across six representative inputs: it observes **6 distinct tool sequences** (different inputs drive different orchestration, not a fixed pipeline), and confirms every value a tool produced carries engine provenance and passed verification with none unlabelled-model-derived ("AGENTIC"). The orchestration is a real interpret→plan→execute loop (`agent/agent.py`, `agent/brain.py`); the mathematics is done by the engine tools (`agent/tools.py`). Passes under `python3 tools/verify.py`.

## G4 — Interactive three-dimensional visualization with in-sync step-through

- **criterion:** By default each solved problem is shown as the answer plus an interactive three-dimensional scene the user can rotate, zoom, and pan smoothly, with no step-through forced on them; and the user can opt into a step-by-step walkthrough (a control they choose) that builds the scene in sync, each step showing exactly the geometry it introduces — no more, no less, and nothing from a later step shown early.
- **check:** Open a representative set of solved problems; by default the answer and an explorable scene appear with no forced stepping, and manipulation is smooth (a measured sustained frame rate above the threshold in `checks/registry.md`, constraint C-INTERACTIVE); then start the optional walkthrough and advance step by step, confirming each step shows exactly its geometry at its step (check in `checks/registry.md`).
- **state:** met
- **evidence:** 2026-09-02 — In the running app (localhost:8765), solving a problem shows the answer plus the full interactive scene with no forced stepping (`window.__ml.state().visibleSteps` = all steps, e.g. `[0,1,3]` for a scalar field / Lorenz). Manipulation is smooth: `window.__ml.bench(180)` measured **0.367 ms/frame on the Lorenz scene** (the heaviest) — ~45× under the 16.7 ms/frame (60 fps) threshold recorded in `checks/registry.md`. CHK-002 (`check_render_budget.py`) bounds every scene's geometry as the automated regression guard, and CHK-003 (`check_stepthrough.py`) confirms each step reveals exactly its own geometry; both pass under `verify.py`. The opt-in walkthrough was exercised in-browser: engaging it set `visibleSteps` to `[0]`, and advancing revealed `[0,1]` — in sync, nothing early.

## G5 — The tutor drives the visualization

- **criterion:** When the user is being tutored — the optional walkthrough, or a question they ask — and it aids understanding (a judgment the agent makes), the tutor's explanation manipulates the scene, focusing, highlighting, or transforming the relevant feature so the user's attention is drawn to what is being explained; it need not do so every time, only when it helps.
- **check:** Over a scripted set of "focusing" questions where a visual move is clearly warranted (e.g. "where is the minimum?"), the view demonstrably lands on or highlights the correct feature; and the agent has, and uses, the capability to drive camera, highlights, and transforms. An automated check in `checks/registry.md` exercises the focusing cases.
- **state:** met
- **evidence:** 2026-09-02 — CHK-010 (`tools/check_agent_focus.py`, approved in P-0003) runs four focusing questions where a view move is warranted ("where is the minimum/optimum/equilibrium?", "show me the saddle") and confirms each produces a focus directive whose target lands on the correct **verified** feature within 0.05 (minimum→origin, constrained optimum→(0.5,0.5), equilibrium→origin) — "TUTOR DRIVES THE VIEW". The `focus_view` tool (`agent/tools.py`) resolves features from verified geometry; the frontend (`web/app.js`) eases the camera and pulses a highlight marker. Browser-verified: "where is the minimum/attractor?" moved the view onto the feature. Passes under `verify.py`.

## G6 — Grounded, multi-turn tutoring chat at any step

- **criterion:** At any point in a solved problem the user can converse with the tutor across multiple turns, and every answer is consistent with that problem's computed and verified state and contradicts none of it, with quantitative claims tracing to a computed result or labelled model-derived.
- **check:** For a set of scripted multi-turn conversations across representative problems, each answer references the correct computed values and asserts nothing the engine's results contradict; any claim not backed by a computed result is labelled model-derived (constraints C-GROUNDED-EXPLANATION, C-VERIFIED-MATH). An automated check in `checks/registry.md` exercises this.
- **state:** met
- **evidence:** 2026-09-02 — CHK-011 (`tools/check_agent_flow.py`, approved in P-0003) holds five scripted multi-turn conversations (2–3 follow-ups each) across representative problems in all areas; every turn returns an answer grounded in the problem's verified quantities (`grounded_in` non-empty) with `model_derived=False`, and none asserts a value the engine's results contradict ("FLOW OK"). CHK-004 (`check_grounded.py`) additionally checks 11 scripted Q&A pairs cite the correct verified values and avoid contradicted claims. Both pass under `verify.py`. Multi-turn context is unit-tested in `tests/test_agent.py`.

## G7 — Transparent and responsive experience

- **criterion:** The user can toggle a view of the agent's tool-calls (what it computed) on or off; a visible indicator shows while the agent is working; and the three-dimensional visualization stays responsive to manipulation while the agent thinks.
- **check:** In the running app, toggle the agent-activity view on and off (it shows the tool-calls when on, hides them when off); confirm a thinking indicator appears during agent work; and confirm the scene still rotates/zooms/pans smoothly while a response is being computed (constraint C-INTERACTIVE).
- **state:** met
- **evidence:** 2026-09-02 — Browser-verified in the running app: clicking "show the agent's tool calls" reveals the trace (interpretation + each tool call with provenance, e.g. "✓ verified · via engine.dynamics.fixed_points, numpy.linalg.eig, scipy.integrate.solve_ivp") and clicking again hides it; a spinner "the agent is thinking…" appears during each request. The render loop runs on `requestAnimationFrame` independently of the (async) agent request, and `window.__ml.bench()` measured 0.367 ms/frame while a scene was loaded, so the scene stays fully manipulable while the agent computes. CHK-012 (`tools/check_agent_transparency.py`, approved in P-0003) is the automated guard: it confirms the trace is inspectable (tool sequence + provenance + verification) and the UI wires the toggle, thinking indicator, and rAF loop ("TRANSPARENT & RESPONSIVE"). Passes under `verify.py`.

## G8 — Polished, unbroken end-to-end flow

- **criterion:** The complete path — pose a problem, have it interpreted, solved, visualized, stepped through, and chatted about — runs end to end across the held-out test set with no crash, no unhandled error surfaced to the user, no dead end, and no placeholder in the interface.
- **check:** Walk the full flow (pose → interpret → solve → visualize → step → chat) for a representative sample of the test set; confirm no crash, no unhandled error reaches the user, and no placeholder or broken state anywhere in the core flow. An automated end-to-end check in `checks/registry.md` exercises the sample.
- **state:** met
- **evidence:** 2026-09-02 — CHK-011 (`tools/check_agent_flow.py`, approved in P-0003) walks pose→interpret→solve→build scene→step→multi-turn chat for five representative problems with no crash and no unhandled error, each scene well-formed (base layer present, every quantity verified) and each chat turn grounded ("FLOW OK"). CHK-005 (`check_e2e.py`) walks the same flow across the full deterministic suite. The server never surfaces a stack trace (`/api/agent` and dispatch catch exceptions and return a clean message), and the agent declines out-of-scope input gracefully rather than dead-ending (CHK-008). Browser-verified end-to-end incl. the Lorenz problem. Both checks pass under `verify.py`.

## G9 — Scope and future expansion are documented

- **criterion:** The repository documents the five supported areas and the planned future expansions — at least PDEs, physics, and higher-than-three-dimensional visualization — distinguishing what is in scope now from what is deferred.
- **check:** Open the scope/expansion documentation in the repository and confirm it states the five supported areas (including dynamical systems / ODEs) and lists the deferred expansions (at least PDEs, physics, and higher-dimensional visualization) clearly enough that a user is not misled about what the tool does.
- **state:** met
- **evidence:** 2026-09-02 — `docs/scope.md` states all five supported areas (scalar fields & surfaces, gradients & optimization, vector fields, linear algebra as geometry, and **dynamical systems / ODEs**) and lists the deferred expansions as first-class items: **PDEs** (the natural extension of the ODE area), **physics**, and **higher-than-three-dimensional visualization**, clearly separated from current scope. CHK-006 (`tools/check_scope_docs.py`, strengthened to require the fifth area + PDEs) confirms this ("SCOPE DOCUMENTED") and passes under `verify.py`.

## G10 — Shapes are drawn on, with a switchable surface reveal

- **criterion:** Each shape in a solved scene appears by being progressively drawn or grown onto the view — building up rather than popping in or cross-fading as an already-finished whole — with supporting overlays (a vector field) fading in behind it and a walkthrough ending framed on the whole finished picture; and a surface is revealed, by default, as a mesh growing from its centre, which the user can switch to a contour view that blooms from the centre and switch back, at will.
- **check:** In the running app, solve a surface problem and watch it appear: the surface builds up from its centre (not a pop or whole-fade), the vector field fades in, and the walkthrough's final step frames the whole scene; then switch the surface's reveal — it becomes contour lines blooming from the centre — and switch back, confirming grow-from-centre is the default for each new problem and the toggle appears only where there is a surface to reveal. `tools/check_draw_on.py` (CHK-013) is the automated guard on the wiring and the reveal's source data.
- **state:** met
- **evidence:** 2026-09-03 — Implemented in `web/app.js`: `buildSurface` orders the surface triangles centre-outward so the progressive draw-range grows the mesh **from its centre**; `buildContours` emits level-set rings ordered centre-outward so they **bloom from the middle**; the top-bar `#contour-toggle` fades the surface out and blooms the contours in, and back, with `surfaceMode` reset to grow-from-centre for every new problem; the vector field fades in (`fadeIn`) and each walkthrough ends on a "The full picture" frame. Browser-verified live (offline brain, localhost:8765): the paraboloid `f = x²+y²` grew from its centre, "Contours" bloomed the nested level rings and "Surface" grew the mesh back — round trip clean at 60 fps; the toggle showed for surface scenes (scalar-fields, optimization) and stayed hidden for vector-fields / linear-algebra (no surface). CHK-013 (`tools/check_draw_on.py`) passes; the full suite CHK-001…013 is green and the 49-test unit suite passes.

---

> **Phase 2 — pedagogical depth (added 2026-09-03).** Criteria G11–G14 open a new phase: the
> agent must genuinely *teach* a complex problem, not just solve and render it. They were
> added when Clara reviewed the tutor on a multi-part Lorenz problem and found the walkthrough
> too coarse, the text hard to read, the pacing too fast, with no way to interrogate an
> individual step or to see chat history without crowding the visual. The goal condition
> re-opens (`state: approved`) until these are met with evidence and the suite is green.

## G11 — Complex problems are taught in small, followable steps, showing the work

- **criterion:** When walked through a complex or multi-part problem, the tutor decomposes it into small steps that each introduce roughly one idea — a big step is broken down rather than delivered whole — and any calculation with several stages is shown as its sequence of intermediate results (not only its final answer), each step carrying the visual that matches it; the reveal and step-to-step pacing is unhurried enough that a first-time learner can follow each step before the next arrives.
- **check:** The automated whole-test-set sweep in `checks/registry.md` (CHK-014) drives **every** case and confirms, per case, that the walkthrough is decomposed into small single-idea steps (not a few dense ones), every multi-stage calculation is shown stage by stage, and each step carries its matching visual — failing if any case falls short. In addition, walk a sample of complex, multi-part problems in the running app (including a full Lorenz problem: find the fixed points, classify their stability from the Jacobian eigenvalues, then integrate and render the trajectory) and confirm the felt pacing is comfortable to follow rather than faster than the eye can track. (Constraint C-STEPWISE.)
- **state:** unmet
- **evidence:**

## G12 — The tutor's explanations are clearly formatted and readable

- **criterion:** Every block of explanatory text the tutor shows is formatted so a learner can parse it: distinct steps and points are visually separated rather than run together, mathematical expressions read as notation a person recognizes rather than as raw machine source, and no explanation is an undifferentiated wall of text.
- **check:** The automated whole-test-set sweep in `checks/registry.md` (CHK-014) confirms, for **every** case, that the tutor's explanatory output carries readable structure — steps/points separated, mathematics rendered as notation rather than raw source, no undifferentiated wall of text — failing if any case is off. Final legibility is confirmed by reading a sample in the running app. (Constraint C-READABLE-OUTPUT.)
- **state:** unmet
- **evidence:**

## G13 — The user can ask follow-up questions about an individual step

- **criterion:** While being walked through a problem, the user can ask a follow-up question about a specific step and get an answer that addresses that step, grounded in that step's computed and verified state (per G1 and G6), without losing their place in the walkthrough.
- **check:** During a walkthrough, ask a question aimed at a particular step (e.g. "why is this eigenvalue negative?" on the stability step); the answer addresses that step's content, is grounded in the verified state and contradicts none of it, and the walkthrough position is preserved afterward. An automated slice in `checks/registry.md` exercises per-step questions.
- **state:** unmet
- **evidence:**

## G14 — Chat history is available without crowding the visualization

- **criterion:** The user can bring up their conversation history and dismiss it through a clean control; when hidden it does not occupy or crowd the visualization, and when shown it is readable — the history never permanently competes with the visual for space.
- **check:** In the running app, toggle the conversation history open and closed: hidden leaves the visualization unobstructed, shown presents the history legibly, and the toggle is clean (no layout breakage, nothing stranded). An automated slice in `checks/registry.md` confirms the history control is wired to show/hide without occupying the visual by default.
- **state:** unmet
- **evidence:**

## G15 — Every case in the test set is on point on every output dimension

- **criterion:** Completion is judged by driving the whole test set — not a hand-picked few — and confirming, for each case, that all four output dimensions are on point: the answer is tool-computed and verified, the explanation is broken into small readable steps that show the work, the visualization is well-formed and correct for its area, and the entrance animation reveals every element with the right draw-on behaviour. A single case that is wrong or weak on a single dimension fails this; a passing spot-check does not satisfy it.
- **check:** `tools/check_suite_quality.py` (CHK-014) drives every case in the test set and, per case, asserts the answer is verified, the explanation meets the step/readability bar (enforcing C-STEPWISE / C-READABLE-OUTPUT — including bite-sized single-idea steps and staged calculations, not merely non-blank text), the scene is well-formed and correct for its area, and every layer has its correct entrance; it exits nonzero if any case is off on any dimension. This criterion is met only once that sweep enforces the full step/readability bar and passes over the whole set, and a representative sample has been confirmed in the running app. (Constraint C-SUITE-QUALITY.)
- **state:** unmet
- **evidence:** In progress. CHK-014 already drives all 16 canonical cases and passes on the answer, visual (well-formed scene), and animation (every layer has a defined entrance) dimensions, plus a shallow explanation check (no blank steps). It is **not yet met**: the explanation assertions must be deepened to enforce the bite-sized-step and readable-formatting bar (G11/G12) across every case, which is Phase-2 work.
