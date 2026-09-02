## P-0001 — Representative problem suite (the bar for G1–G5)

- **status:** proposed
- **kind:** new-constraint
- **targets:** G1–G5 (criteria that reference "the representative suite"); checks/registry.md (CHK-001)
- **proposed:** 2026-09-01
- **because:** Criteria G1–G5 are all judged "for every problem in the approved
  representative suite." Until that suite exists and is approved, those criteria have no
  concrete referent — "done" is undefined, and there is nothing to build the engine
  against. `goals/criteria.md` says the suite is *defined and registered in
  `checks/registry.md` at the start of goal mode and approved by Clara — so it is governed
  content the agent cannot quietly weaken to pass.* This proposal defines that suite and
  registers the check (CHK-001) that runs it, so that the bar for the whole project is
  fixed by Clara's approval rather than by the agent's later convenience. Nothing is built
  against the suite until this is approved (per the checkpoint and C-SURFACE-AMBIGUITY):
  the suite composition changes what Clara ends up with, so it is hers to sign off.

- **change:** Approve the representative suite below (12 problems, 3 per beachhead area)
  as the bar for G1–G5, and register **CHK-001** in `checks/registry.md` (already written
  there, pending this approval) which runs every suite problem through the engine, compares
  each displayed quantity against an independently-computed reference, and confirms each
  carries a passing verification record — failing (nonzero exit) if any problem is missing,
  any value disagrees with its independent reference, or any result traces to model text
  alone (C-VERIFIED-MATH). Approving re-records the baseline to include the new check.

  The suite is representative, **not exhaustive** (`goals/criteria.md`): it fixes the
  standard the four areas are held to, not every problem they could handle.

  **Area 1 — Scalar fields & surfaces** (f: ℝ²→ℝ; surface z=f(x,y), level sets, critical
  points via gradient and Hessian):
  - **S1** Paraboloid `f = x² + y²` — convex bowl; single minimum at origin; circular level
    sets. Exercises: gradient field, one critical point classified as a minimum (Hessian
    positive-definite).
  - **S2** Saddle `f = x² − y²` — saddle point at origin; hyperbolic level sets. Exercises:
    gradient field, a critical point classified as a saddle (Hessian indefinite).
  - **S3** `f = sin(x)·cos(y)` — a periodic surface with several critical points of mixed
    type. Exercises: trigonometric gradient/Hessian, multiple critical points with distinct
    classifications (max, min, saddle).

  **Area 2 — Gradients & optimization landscapes** (gradient as steepest ascent; descent
  trajectories; constrained optimization):
  - **O1** Anisotropic bowl `f = x² + 3y²` — gradient descent from a fixed start converges
    to the minimum at (0,0), visibly zig-zagging under the anisotropy. Exercises: gradient,
    a descent trajectory whose objective decreases monotonically to the minimum.
  - **O2** Rosenbrock `f = (1−x)² + 100(y−x²)²` — the classic curved-valley landscape;
    global minimum at (1,1), f=0. Exercises: a hard optimization landscape, minimum
    location and value, gradient zero and Hessian positive-definite there.
  - **O3** Constrained: minimize `f = x² + y²` subject to `g = x + y − 1 = 0` — Lagrange
    multipliers; optimum at (½,½), tangency ∇f = λ∇g. Exercises: the constrained-optimum
    and the Lagrange condition.

  **Area 3 — Vector fields** (F: ℝ²→ℝ² or ℝ³→ℝ³; divergence, curl, field lines):
  - **V1** Rotation `F = (−y, x)` — divergence 0, curl +2 (about z); closed circular field
    lines. Exercises: a purely rotational field (curl without divergence).
  - **V2** Source `F = (x, y)` — divergence +2, curl 0; radial field lines. Exercises: a
    purely divergent field (divergence without curl).
  - **V3** 3-D `F = (−y, x, z)` — divergence 1, curl (0,0,2); rotation about z with vertical
    stretch. Exercises: divergence and curl of a genuinely three-dimensional field, curl
    shown as a vector.

  **Area 4 — Linear algebra as geometry** (matrices as transformations of space; eigen-
  structure, determinant, SVD):
  - **L1** Symmetric `A = [[2,1],[1,2]]` — eigenvalues 3 and 1, orthonormal eigenvectors;
    maps the unit circle to an ellipse aligned with the eigenvectors; det 3. Exercises:
    real eigen-decomposition, eigenvectors as invariant directions, determinant as area
    scaling.
  - **L2** Shear `A = [[1,1],[0,1]]` — determinant 1 (area-preserving), a single (defective)
    eigenvalue 1 with eigenvector (1,0). Exercises: a non-diagonalizable transform,
    determinant as area scaling, the limit of eigen-analysis.
  - **L3** General 3×3 `A = [[1,2,0],[0,1,2],[2,0,1]]` — singular-value decomposition; the
    unit sphere maps to an ellipsoid whose semi-axes are the singular values and whose
    axis directions are the singular vectors. Exercises: SVD, verified by reconstruction
    (A = UΣVᵀ) and orthonormality residuals, and the singular values as ellipsoid axes.

  **Verification methodology (implementation, summarized so Clara can judge the bar).**
  Each displayed quantity is produced by the deterministic engine and confirmed by an
  independent step before it is shown (C-VERIFIED-MATH): symbolic derivatives are
  cross-checked numerically (finite differences) *and* against hand-derived closed forms
  stored with each problem; critical points and optima are confirmed by back-substitution
  (residual ≈ 0) and Hessian eigenvalue signs; eigen/SVD by residual identities
  (‖Av−λv‖, ‖A−UΣVᵀ‖, orthonormality) rather than by trusting a single routine. No
  displayed number originates from a language model.

- **risk:** Fixing the suite fixes the bar, so it is what the project will be judged and
  optimized toward — a suite that is too easy would let a shallow engine pass G1–G5, and
  one locked too rigidly would make a reasonable later addition (say, a fourth scalar-field
  problem) a governed change rather than a free improvement. Mitigations: the problems are
  standard, canonical cases chosen to exercise the *core* geometric operation of each area
  (so passing them means the real capability exists, not a memorized answer), and the suite
  is explicitly the representative bar, not exhaustive — adding *more* coverage later is
  always allowed and only *weakening* it needs re-approval, which is the asymmetry
  governance is meant to enforce. Approving this does not commit Clara to these exact
  problems forever; it commits the agent to not lowering the bar without her.

- **approved:**
