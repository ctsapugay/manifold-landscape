# Project constraints

Constraints specific to this project. Written during intake, edited by hand whenever.
Defaults live in `defaults.md` and are inherited automatically — do not copy them here.

Before adding an entry, read `docs/outcome-vs-implementation.md`. A constraint says what
must remain true. It does not say how to build anything.

Use the same entry format as `defaults.md`:

```
## ID — Short title
- **source:** project
- **status:** active | waived
- **rule:** One sentence. What must remain true.
- **check:** How anyone can tell, from the outside, whether the rule held.
- **why:** Optional. Required when the rule names a specific technology.
```

IDs are `C-` plus a short slug, unique across both constraint files.

---

## C-VERIFIED-MATH — Mathematics the user sees is tool-computed and verified, or honestly labelled

- **source:** project
- **status:** active
- **rule:** The deterministic tool set is the primary source of every mathematical result the user sees, and a result is shown as verified only after an independent check (a second computation, a residual, or a back-substitution) confirms it; deriving a result with the model itself is a **last resort**, permitted only where no deterministic tool can produce or check it, and any such result is clearly labelled to the user as model-derived and unverified — never presented as if it were verified.
- **check:** For any result the interface shows, either it traces to a deterministic tool computation carrying a passing verification record, or it is explicitly marked model-derived/unverified; no unverified value is ever styled or stated as if it were verified, and model-derived results are rare rather than routine. An automated check in `checks/registry.md` exercises this across the test set.
- **why:** The whole product rests on trust. A tutor that confidently states wrong mathematics is worse than none, and language models are unreliable at exact computation — so the tools do the math and a verification step confirms it. When a gap is found, the expectation is to **extend the toolset to close it** (a new solver, or model-generated code that is executed deterministically and verified) rather than lean on the model; model-derived results stay a rare, clearly-labelled last resort, and the honest label is what protects the trust.

## C-INTERACTIVE — Visualizations stay responsive under direct manipulation, even while the agent thinks

- **source:** project
- **status:** active
- **rule:** The rendered visualizations respond to direct manipulation — rotating, zooming, panning, and adjusting parameters — continuously and without perceptible lag on Clara's development machine, including while the agent is computing a response.
- **check:** Open a representative problem and manipulate the view, including during agent processing; interaction remains smooth, and a measured sustained frame rate during manipulation stays above the threshold recorded in `checks/registry.md`.

## C-GROUNDED-EXPLANATION — The tutor never contradicts the computed result

- **source:** project
- **status:** active
- **rule:** Every explanation, answer, and annotation the tutor shows is consistent with the current problem's computed results and states nothing those results contradict, and every quantitative claim traces to a computed result or is presented as model-derived and unverified per C-VERIFIED-MATH.
- **check:** For a sample of problems and questions, each answer's claims are checked against the engine's computed values; none asserts a value or relationship the results contradict, and any claim that is not backed by a computed result is labelled as model-derived rather than stated as fact.

## C-DRAW-ON — Shapes are revealed by drawing them on, not by popping or whole-fading in

- **source:** project
- **status:** active
- **rule:** A shape enters the scene by being progressively drawn or grown onto it — building up from a point or an edge — rather than appearing all at once or cross-fading in as an already-finished whole; supporting overlays such as a vector field may fade in behind the shape; a walkthrough ends framed on the whole finished picture; and where a shape is offered in more than one reveal style, one style is always active by default and the user can switch between the styles and back without re-posing the problem.
- **check:** Open a representative problem and watch it appear: the shape builds up progressively rather than popping in or fading in whole, any vector field fades in, and a walkthrough's final step frames the entire scene; where alternate reveal styles exist for a shape, a default is always in effect and the user can switch styles and switch back. An automated check in `checks/registry.md` confirms the interface wires these behaviours.
- **why:** The tool is judged partly as portfolio craft, and a scene whose pieces snap into existence reads as unfinished; drawing each shape on is what makes the geometry feel constructed and understandable. This constrains the *experience* (things are drawn on, a default is always present, the user is never stranded mid-switch), not the technique used to achieve it.

## C-STEPWISE — A walkthrough teaches in small, single-idea steps, showing its work

- **source:** project
- **status:** active
- **rule:** When the tutor walks a user through a problem, it decomposes the work into small steps that each introduce roughly one idea, so a big or multi-part problem is broken down rather than delivered whole; a calculation with several stages is shown as its sequence of intermediate results — not only its final value — with the visual that matches each stage; and the reveal and step-to-step pacing is unhurried enough that a first-time learner can follow what is happening before the next step arrives.
- **check:** Walk a representative complex, multi-part problem: the walkthrough advances in small single-idea steps rather than a few dense ones, any multi-stage calculation is shown stage by stage rather than jumping to the answer, each step carries the matching visual, and the animation/transition pace is comfortable to follow rather than faster than the eye can track. An automated slice in `checks/registry.md` guards the structure (step scoping, staged calculations, per-step visuals); the felt pacing and clarity are confirmed in the running app.
- **why:** The whole point of the tutor is understanding. A correct answer delivered in one dense step, or a long derivation collapsed to its result, teaches nothing — the learner cannot see where it came from. Breaking the work down and showing each stage, at a pace they can follow, is what turns a solved problem into an understood one. This constrains the *pedagogy* (small steps, work shown, followable pace), not how it is implemented.

## C-READABLE-OUTPUT — The tutor's text is formatted to be read, not dumped

- **source:** project
- **status:** active
- **rule:** Every block of explanatory text the tutor shows is formatted so a reader can parse and follow it: distinct steps and points are visually separated rather than run together, mathematical expressions are presented so they read as notation a person recognizes rather than as raw machine source, and no explanation is delivered as a single undifferentiated wall of text.
- **check:** Read the tutor's output for a sample of problems: steps and points are visually distinguishable, mathematics is rendered legibly as notation rather than raw source, and no answer is an unbroken block a reader has to untangle. An automated slice in `checks/registry.md` checks the output carries readable structure; legibility is confirmed by reading it in the running app.
- **why:** Understanding is lost the moment the reader has to fight the formatting. Notation shown as raw source, or three steps mashed into one paragraph, buries the very structure the tutor is trying to teach. This constrains the *legibility of what the user reads*, not the format or toolkit used to achieve it.

## C-SUITE-QUALITY — Quality is judged across the whole test set, per case, on every output dimension

- **source:** project
- **status:** active
- **rule:** The tutor's quality is judged by driving **every** case in the test set — not a hand-picked few — and checking, for each case, that **all four** output dimensions are on point: the answer (tool-computed and verified), the explanation (broken down and readable per C-STEPWISE and C-READABLE-OUTPUT), the visualization (well-formed and correct for its area), and the entrance animation (every element revealed by the right draw-on behaviour). A single case that is wrong or weak on a single dimension means the bar is not met; a passing spot-check of a few problems does not satisfy it.
- **check:** An automated check in `checks/registry.md` drives every case in the test set and, per case, confirms the answer is verified, the explanation meets the step/readability bar, the scene is well-formed and correct for its area, and every layer has its correct entrance; it fails if any case is off on any dimension. Felt pacing and genuine clarity — the parts a machine cannot fully judge — are confirmed by walking a representative sample in the running app and recorded as evidence.
- **why:** "It works on the examples I tried" is exactly the failure this whole repo exists to prevent. A tutor can look right on a paraboloid and fall apart on a multi-part Lorenz problem; the only honest bar is that every case in the set is on point on every dimension a user experiences. This constrains *how completion is judged* (whole set, per case, all dimensions), not how the tutor is built.

## C-VERIFIED-MOTION — Animations and simulations play back verified computation

- **source:** project
- **status:** active
- **rule:** Any animated playback or simulation the tool shows is a faithful visualization of tool-computed, independently verified state — a trajectory that was actually integrated, a sweep whose runs were actually computed — so its motion, and any outcome it reports (a count, a winner, a rate), traces to a verified computation or is clearly labelled to the user as model-derived and unverified; the tool never fabricates motion or invents simulation results and presents them as real.
- **check:** For any animation or simulation the interface plays, the frames follow from a tool-computed, verified quantity (an integrated trajectory, a computed sweep), and any reported outcome traces to a passing verification record or carries a model-derived label; nothing animated or simulated is presented as authoritative unless it is verified. An automated check in `checks/registry.md` exercises this.
- **why:** Animation and simulation are a new surface where a language model could invent motion or "results" that look authoritative — a moving path that no integrator produced, a "basin B wins 63%" that no sweep computed. The same trust guarantee that protects every displayed number (C-VERIFIED-MATH) has to extend to displayed motion and simulated outcomes, or the tool teaches confident fiction. This constrains what a shown animation/simulation must *rest on* (verified computation, or an honest label), not how it is rendered.
