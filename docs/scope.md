# Scope and future expansion

Manifold Landscape is deliberately deep rather than broad: it goes far on the *geometry of
continuous mathematics* instead of shallow on everything. This page states exactly what the
tool does today and what is planned but not yet built, so no one is misled about its reach.

## Supported now — the five areas

The tool solves, visualizes, steps through, and explains problems in five areas:

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
5. **Dynamical systems (ODEs).** An autonomous system ẋ = F(x) as a flow: its equilibria
   (where F = 0), their stability from the Jacobian's eigenvalues (sink, source, saddle,
   spiral, centre), the integral-curve trajectories that flow through the field, and — for a
   chaotic system such as Lorenz — a measured, verified sensitivity to initial conditions.

A user poses a problem however they like — a typed equation, a word problem, or an open
conceptual request ("show me an example of chaos") — and an **AI agent interprets it and
orchestrates the deterministic tools** to solve, visualize, and explain it. Every
mathematical result the tool shows is computed by a tool and independently verified before
it is displayed, or is clearly labelled to the user as model-derived and unverified; the
model computing mathematics itself is a last resort (constraint C-VERIFIED-MATH). The
problems that define the bar for "supported" are the approved representative and held-out
test sets (see `checks/registry.md`); the tool is not expected to handle every conceivable
problem within an area, only to do the core geometry of each one correctly, and to handle
out-of-scope requests gracefully rather than by bluffing.

## Deferred — planned future expansion, not built yet

These are real intended directions, explicitly **out of scope for the current version**.
They are listed here so the boundary is honest, not because work on them has begun.

- **Partial differential equations (PDEs).** The dynamical-systems area covers ordinary
  differential equations (ODEs) — systems that evolve in time. **PDEs** — equations in
  several independent variables, such as the heat, wave, and Laplace equations, and their
  solution surfaces and evolving fields — are the natural extension of that area and are
  **deferred future work**, not supported today.
- **Physics.** Fields, potentials, and dynamics from physics (electromagnetism, mechanics,
  fluid flow) are a natural next domain and are **not supported today**.
- **Higher-than-three-dimensional visualization.** Visualization is three-dimensional.
  Functions of more than two variables, transformations of ℝⁿ for n > 3, and projection
  or slicing techniques for higher-dimensional geometry are **deferred future work**.
- **Broader continuous mathematics** beyond the five areas above (for example differential
  geometry of general manifolds or complex analysis) may follow, but is not part of the
  current tool.

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
