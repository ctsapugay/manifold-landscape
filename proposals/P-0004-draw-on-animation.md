## P-0004 — Record the draw-on animation constraint, criterion, and check

- **status:** approved
- **kind:** new-constraint
- **targets:** a new project constraint (`C-DRAW-ON` in `constraints/project.md`), a new
  criterion (`G10` in `goals/criteria.md`), and a new check (`CHK-013` in
  `checks/registry.md` → `tools/check_draw_on.py`).
- **proposed:** 2026-09-03
- **because:** Clara directed a visual/animation change this phase: shapes should be *drawn
  on* rather than popped in or cross-faded as a finished whole, with a surface growing from
  its centre by default and a user toggle that blooms level-set contours from the centre and
  switches back. The feature is built and browser-verified. Governance is already engaged
  (baseline recorded 2026-09-02), so the standing constraints, criteria, and check suite are
  no longer freely editable — adding this constraint, criterion, and check is a governed act
  that has to be recorded, or `validate.py` reports it as drift and the new draw-on
  experience rests on no executable evidence (C-EVIDENCE). `--baseline` is the intake-time
  engage command and refuses once the goal is `met`, so the proposal path is the correct
  route. This records the appends Clara has approved.
- **change:** Record as approved the current contents of the three governed files, which now
  contain these additions:
  - `constraints/project.md` — **C-DRAW-ON**: "A shape enters the scene by being
    progressively drawn or grown onto it — building up from a point or an edge — rather than
    appearing all at once or cross-fading in as an already-finished whole; supporting overlays
    such as a vector field may fade in behind the shape; a walkthrough ends framed on the
    whole finished picture; and where a shape is offered in more than one reveal style, one
    style is always active by default and the user can switch between the styles and back
    without re-posing the problem."
  - `goals/criteria.md` — **G10 — Shapes are drawn on, with a switchable surface reveal**
    (marked `met`, with browser + suite evidence): each shape appears by drawing/growing on;
    the field fades in; a walkthrough ends framed on the whole scene; a surface grows from its
    centre by default and the user can switch it to a contour bloom and back.
  - `checks/registry.md` — **CHK-013** (`covers: G10, C-DRAW-ON`,
    `run: python3 tools/check_draw_on.py`, `status: active`): guards the draw-on wiring and
    that a surface scene carries the height grid the contour reveal is built from.
- **risk:** Adds a standing rule and a criterion to the finish line, so future work must keep
  shapes drawing-on (not just popping in) and must keep the switchable surface reveal working,
  or CHK-013 fails and the goal can no longer be honestly marked met. This is intended — it is
  the guard that stops the animation quality regressing. It does not touch or weaken any
  existing constraint, criterion, check, or protected-core problem; it is purely additive.
- **approved:** 2026-09-03
