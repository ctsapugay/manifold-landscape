# Outcomes

The problem, who it is for, what becomes true when the project exists, and what is
deliberately out of scope. Written at intake; the goal condition is distilled from this.

## Problem

People learning and working with the geometry of continuous mathematics — multivariable
calculus, vector fields, linear algebra as geometry, optimization landscapes, dynamical
systems — struggle to build the *intuition* behind it. Textbooks and static figures cannot
convey how a surface bends, how a gradient points, how a linear map deforms space, or how a
system flows and settles. Existing tools split the gap badly: answer engines return a
result with no geometric intuition, and plotting tools require you to already know what to
draw. Nothing takes a problem *however a learner phrases it* — an equation, a word problem,
or an open request like "show me an example of chaos" — solves it correctly, *constructs the
geometry step by step, and tutors you through it*, pointing at the visualization as it
explains, so that a learner ends up understanding rather than just holding an answer.

This project is built to do that, and to do it as an **AI tutor agent**: an agent that
interprets what the user asks, orchestrates a set of deterministic mathematical and
visualization tools to solve and draw it, and teaches — moving and transforming the picture
to point at what matters and answering follow-up questions grounded in the real computed
state. It is meant to show off both a passion for mathematics and skill with agentic AI, to
a portfolio standard.

## Who it is for

Primarily **visual learners — students and self-learners** building intuition in continuous
math; the design leans toward scaffolding, tutoring, and pointing-at-the-picture explanation
for them. Secondarily **engineers and mathematicians** who want to see or sanity-check a
problem geometrically. Single user, running locally, for now; a fresh user brings a problem
in any form and leaves understanding it.

## Outcomes

When this exists, the following are true that are not true today:

1. A user can **pose a problem however they like** — a typed equation, a word problem, or an
   open conceptual request ("show me a saddle", "explain chaos with an example") — and the
   tool interprets it, asking a clarifying question when the request is genuinely ambiguous.
2. An **AI agent solves it by orchestrating deterministic tools**: it decides which
   computations to run and in what order, so every result the user sees is either
   tool-computed and verified, or clearly labelled as model-derived (constraint
   C-VERIFIED-MATH). Computing a result with the model itself is a **last resort** — gaps
   are closed by extending the tools, not by leaning on the model.
3. Coverage spans **five areas** — scalar fields & surfaces, gradients & optimization
   landscapes, vector fields, linear algebra as geometry, and **dynamical systems (ODEs)** —
   and handles a broad range of problems within them, not a fixed list.
4. **By default the user gets the answer plus an interactive three-dimensional visualization**
   they can rotate, zoom, and pan — nothing forced; if all they want is the answer and the
   picture, that is what they get.
5. **The step-by-step walkthrough is optional.** When the user wants to understand *how* — a
   button or toggle — the tool **tutors**: it builds the visualization in sync, step by step,
   and **drives it** (zooming to a minimum, highlighting a saddle, transforming a surface) to
   point at what it is explaining.
6. The user can **ask the tutor questions** whenever they want and get answers grounded in
   the problem's actual computed state, contradicting nothing the engine found. The explanation
   and the chat are **one conversation** — the walkthrough's steps are messages in the same
   thread the user talks in — and a follow-up is answered by **the agent itself**, not a canned
   template, grounded in the relevant step's verified state. Clickable **suggested prompts**
   (including advancing to the next step) keep common moves a click away; the conversation opens
   from a single **start state** that a **new chat** returns to, and can be **collapsed** so the
   visualization takes the full space. Where a visualization is drawn over a domain, the user can
   **expand its bounds** and see the geometry re-computed (still tool-verified) over more space.
7. The experience is **transparent and responsive**: the user can toggle a view of the
   agent's tool-calls (what it computed) — and that view **reliably reflects the tools that
   ran**, consistently across a solve, a follow-up, or a simulation — a visible indicator shows
   while the agent works, and the visualization stays smooth while it thinks.
8. Chat sessions are **saved automatically** and are the user's to manage: a past session can
   be reopened (restoring its conversation and the visualization it explored) and deleted, all
   locally on the user's machine.
9. The agent can **drive motion**: through its tools it triggers step-by-step playback and
   animation in the 3-D — playing a trajectory, animating a process — both to illustrate its
   explanations and on request; and it can **run a simulation or sweep** relevant to the problem
   (e.g. a multi-start descent sweep to see which basin wins most often) and play the actual runs
   back animated, with every reported outcome tool-computed and verified or labelled model-derived
   (C-VERIFIED-MOTION).
10. The whole thing reads as a **polished product** that demonstrates mathematical depth and
    agentic-AI craft — of a standard Clara is glad to show a recruiter.

## Non-goals

Explicitly out of scope. An agent in goal mode does not start on these, even with time to
spare.

- A general symbolic-math or answer engine (a Wolfram Alpha replacement). The tool goes
  deep on the geometry spine, not shallow on everything.
- **PDEs (partial differential equations).** A documented future expansion of the dynamical-
  systems area, not built in this version.
- **Physics.** Documented as a future expansion, not built now.
- **Higher-than-three-dimensional visualization.** Documented future work; visualization is
  three-dimensional.
- Discrete mathematics, formal proofs, statistics, or probability.
- A native mobile application.
- Multiple users, accounts, or classroom-management features.
- Deployment, hosting, billing, subscriptions, or anything that takes the tool off Clara's
  machine. Calling an LLM API over the network is expected (the tutor is an AI agent) and is
  not deployment; productization is a deliberate future decision, governed by C-LOCAL until
  she makes it.

## Open questions

Decisions not yet made. Each has an assumption the agent works under until Clara says
otherwise; none can be reversed later in a way that discards completed work.

- **Delivery form.** Assumption: a graphical application Clara runs locally on her machine
  (a local web app), which calls an LLM API for the agent. The exact form is an
  implementation decision.
- **LLM provider/model.** Assumption: Anthropic's Claude, configured from an API key the user
  supplies via a gitignored `.env` (with a committed `.env.example` template). The specific
  model is an implementation decision.
- **Timeline.** Soft, not a finish-line criterion. Aim for a demonstrable slice of the
  agentic tutor working within a few weeks, without cutting the finish line to hit a date.
- **Future productization.** Deployment, security, and billing are explicitly deferred; when
  Clara decides to make this deployable, that opens a separate round of intake.
- **Scope discipline.** The five areas above are this version. Everything else — PDEs,
  physics, higher-than-three-dimensional visualization — is documented expansion, out of the
  finish line.
