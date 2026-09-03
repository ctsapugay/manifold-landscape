# Manifold Landscape

A locally-run, **AI-tutored** tool for building intuition in the geometry of continuous
mathematics. Pose a problem however you like — a typed equation, a word problem, or an open
request like *"show me an example of chaos"* — and an AI agent interprets it, orchestrates a
set of deterministic tools to solve it, and shows you the answer as an interactive
three-dimensional scene you can rotate, zoom, and explore. Ask for a walkthrough and it
tutors: it builds the visual in sync, drives the camera to what matters, and answers
follow-up questions at any step — every number tool-computed and independently verified, or
clearly labelled as model-derived.

It covers five areas:

- **Scalar fields & surfaces** — a function `f(x, y)` as a surface; its gradient, critical
  points, and the shape of its landscape.
- **Gradients & optimization** — gradient descent across a landscape, and constrained
  optima via the Lagrange condition.
- **Vector fields** — flow, divergence, and curl in two and three dimensions.
- **Linear algebra as geometry** — a matrix as a transformation: determinant, eigen-
  decomposition, and the singular-value ellipsoid.
- **Dynamical systems (ODEs)** — flow fields, integrated trajectories, equilibria and their
  stability from the Jacobian, and chaos (the Lorenz attractor).

PDEs, physics, and higher-than-three-dimensional visualization are **documented future
expansions**, not part of the current tool. See `docs/scope.md`.

## What makes it trustworthy

A tutor that confidently states wrong mathematics is worse than none, and language models
are unreliable at exact computation. So the mathematics is done by a **deterministic engine**
(`engine/`, built on numpy / sympy / scipy), and every result is shown as verified only after
an **independent check** confirms it — a second computation, a residual, or a back-
substitution. The model's job is to *interpret* the request and *orchestrate* the tools, not
to do the arithmetic. On the rare occasion no tool applies, a result may be model-derived —
and then it is clearly labelled as model-derived and unverified, never dressed up as fact.
This is the project's core rule, `C-VERIFIED-MATH`.

## How it works

```
you ─▶ AI agent ─▶ picks & sequences deterministic tools ─▶ verified results ─▶ 3-D scene + tutor
        (agent/)         (engine/)                            (each checked)      (web/)
```

- **The agent** (`agent/`) interprets your input and decides which tools to call and in what
  order — different problems drive different tool sequences; it is not a fixed pipeline. It
  runs against the Anthropic (Claude) API, and falls back to a deterministic offline
  interpreter when no key is present, so the whole thing works offline.
- **The engine** (`engine/`) is the deterministic tool set. Each tool returns a verified
  quantity carrying its provenance and a passing verification record.
- **The web app** (`web/`) renders the interactive 3-D scene with Three.js (vendored locally —
  no runtime CDN) and hosts the tutor. Shapes are **drawn on** rather than popped in: a
  surface grows from its centre, point markers grow in, curves and trajectories draw
  themselves, and the vector field fades in behind them. A surface can be switched — via the
  top-bar toggle — from the grown mesh to its **level-set contours blooming from the centre**,
  and back. The agent's tool calls are inspectable behind a toggle, a thinking indicator shows
  while it works, and the scene stays responsive the whole time.

## Running it

The tool runs locally for a single user; there is no deployment, no accounts, no hosting.

```bash
# Offline (deterministic interpreter — no API key needed):
python3 web/server.py            # then open http://127.0.0.1:8765

# Live Claude agent (put your key in .env — never commit it):
./.venv/bin/python web/server.py
```

The live path uses an isolated virtualenv (`.venv`, gitignored) because it needs a clean
HTTP stack for the Anthropic client. The offline engine and the whole check suite run on a
plain `python3`. Your API key lives in `.env` (gitignored — see `.env.example`); it is never
written into a tracked file (`C-SECRETS`).

```bash
python3 -m pytest tests/ -q      # the engine unit suite
python3 tools/verify.py          # the full check battery (the completion gate)
```

## Layout

```
engine/     the deterministic math tools (scalar fields, optimization, vector fields,
            linear algebra, dynamical systems) + verified-quantity plumbing and the explainer
agent/      the tool-orchestrating agent: intake, the brain (Claude + offline), the tool
            layer, the trace, and the grounding gate
web/        the server, the interactive 3-D app (app.js), and the vendored Three.js
suite/      the held-out test set (protected core + freely-appendable coverage)
tests/      the engine unit suite
tools/      the project's check scripts (run by tools/verify.py) — and the constraint-system
            tooling described below
docs/       scope and future expansions (docs/scope.md)
```

## How this project is governed

This repository is built on **constraint-base**: a small set of plain-Markdown files that
fix the boundaries the work must stay inside and the finish line it works toward, plus a
governance layer so an agent working on it over a long run cannot quietly redefine what
"done" means. The constraints (e.g. *math the user sees is verified or honestly labelled*,
*visualizations stay responsive*, *shapes are drawn on*), the outcomes, the measurable
criteria (`goals/criteria.md`), and the executable check suite (`checks/registry.md`) are all
in the repo and are **governed content** — changeable only with the owner's recorded sign-off.

If you are (or are pointing an agent at) this repo to continue development, start with
`CLAUDE.md` — it is the entry point — then run `python3 tools/brief.py` to see the active
constraints, the goal condition, and recent progress. `progress/checkpoint.md` is the
"resume here" card. The full governance model is in `docs/governance.md`.

## Status

The five areas, the tool-orchestrating agent (live Claude + offline), the interactive 3-D
tutor with the draw-on animation system, grounded multi-turn chat, and the transparency
controls are **built and working**: all ten criteria (G1–G10) are met with recorded
evidence, `python3 tools/verify.py` is green (CHK-001…013), and every constraint has held.
