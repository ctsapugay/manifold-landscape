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
