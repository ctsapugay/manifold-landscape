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

## C-VERIFIED-MATH — Mathematics the user sees is verified, never asserted

- **source:** project
- **status:** active
- **rule:** A mathematical result reaches the user only after a deterministic computation engine produced or checked it and a verification step confirmed it; the language model is never the sole source of a displayed numeric or symbolic value.
- **check:** For any result the interface shows, there is a corresponding engine computation and a passing verification record; tracing the result's origin never lands on model-generated text alone. An automated check in `checks/registry.md` exercises this across the representative problem suite.
- **why:** The whole product rests on trust. A tutor that confidently states wrong mathematics is worse than none, and language models are unreliable at exact computation. This rule is what makes the tool credible rather than a demo.

## C-INTERACTIVE — Visualizations stay responsive under direct manipulation

- **source:** project
- **status:** active
- **rule:** The rendered visualizations respond to direct manipulation — rotating, zooming, panning, and adjusting parameters — continuously and without perceptible lag on Clara's development machine.
- **check:** Open a representative problem and manipulate the view; interaction remains smooth, and a measured sustained frame rate during manipulation stays above the threshold recorded in `checks/registry.md`.

## C-GROUNDED-EXPLANATION — Explanations never contradict the computed result

- **source:** project
- **status:** active
- **rule:** Every explanation, answer, and annotation shown to the user is consistent with the engine's computed results for the current problem, and states nothing those results contradict.
- **check:** For a sample of problems and questions, each explanation's claims are checked against the engine's computed values; none asserts a value or relationship the engine's results contradict.
