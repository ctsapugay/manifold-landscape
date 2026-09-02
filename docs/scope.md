# Scope and future expansion

Manifold Landscape is deliberately deep rather than broad: it goes far on the *geometry of
continuous mathematics* instead of shallow on everything. This page states exactly what the
tool does today and what is planned but not yet built, so no one is misled about its reach.

## Supported now — the four beachhead areas

The tool solves, visualizes, steps through, and explains problems in four areas:

1. **Scalar fields and surfaces.** A function f(x, y) as a surface z = f(x, y): its
   gradient field, its Hessian, and its critical points classified as minima, maxima, or
   saddles.
2. **Gradients and optimization landscapes.** The gradient as the direction of steepest
   ascent; gradient-descent trajectories down a landscape to a minimum; and constrained
   optimization by Lagrange multipliers.
3. **Vector fields.** Fields F(x, y) and F(x, y, z), with their divergence (local
   expansion) and curl (local rotation), shown as arrow glyphs with the scalar fields those
   operators produce.
4. **Linear algebra as geometry.** A matrix as a transformation of space: its determinant
   as an area/volume scale factor, its eigenvalues and eigenvectors as invariant directions,
   and its singular value decomposition as the unit sphere deformed into an ellipsoid.

Every mathematical result the tool shows is computed by a deterministic engine and
independently verified before it is displayed; nothing shown comes from a language model
(see the verification note in the README and constraint C-VERIFIED-MATH). The problems that
define the bar for "supported" are the approved representative suite (see
`checks/registry.md`); the tool is not expected to handle every conceivable problem within
an area, only to do the core geometry of each one correctly.

## Deferred — planned future expansion, not built yet

These are real intended directions, explicitly **out of scope for the current version**.
They are listed here so the boundary is honest, not because work on them has begun.

- **Physics.** Fields, potentials, and dynamics from physics (electromagnetism, mechanics,
  fluid flow) are a natural next domain and are **not supported today**.
- **Higher-than-three-dimensional visualization.** Visualization is three-dimensional.
  Functions of more than two variables, transformations of ℝⁿ for n > 3, and projection
  or slicing techniques for higher-dimensional geometry are **deferred future work**.
- **Broader continuous mathematics** beyond the four areas above (for example differential
  geometry of general manifolds, complex analysis, or PDE solution surfaces) may follow, but
  is not part of the current tool.

## Deliberately out of scope (not planned as expansion)

These are non-goals recorded at intake (`goals/outcomes.md`) — not deferred features, but
things the tool is intentionally not:

- A general symbolic-math or answer engine (a Wolfram Alpha replacement).
- Discrete mathematics, formal proofs, statistics, or probability.
- A native mobile application.
- Multiple users, accounts, or classroom-management features.
- Deployment, hosting, billing, or anything that takes the tool off a single local machine.

If and when deployment, multi-user, or productization is taken up, that opens a separate
round of design covering security and accounts; it is not smuggled into the current tool.
