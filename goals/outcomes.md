# Outcomes

The problem, who it is for, what becomes true when the project exists, and what is
deliberately out of scope. Written at intake; the goal condition is distilled from this.

## Problem

People learning and working with the geometry of continuous mathematics — multivariable
calculus, vector fields, linear algebra as geometry, optimization landscapes — struggle to
build the *intuition* behind it. Textbooks and static figures cannot convey how a surface
bends, how a gradient points, or how a linear map deforms space. Existing tools split the
gap badly: answer engines return a result with no geometric intuition, and plotting tools
require you to already know what to draw. Nothing takes a problem, solves it correctly, and
*constructs the geometry step by step while explaining why*, so that a learner ends up
understanding rather than just holding an answer.

## Who it is for

Primarily **students and self-learners** building intuition in continuous math — the design
leans toward scaffolding and explanation for them. Secondarily **engineers and
mathematicians** who want to see or sanity-check a problem geometrically. Single user,
running locally, for now; a fresh user brings a problem and leaves understanding it.

## Outcomes

When this exists, the following are true that are not true today:

1. A user can pose a problem in the supported geometry domain and receive a **correct,
   verified** solution — the answer is produced and checked by a computation engine, never
   an unverified guess.
2. The solution appears as an **interactive three-dimensional visualization** the user can
   rotate, zoom, pan, and adjust in real time.
3. The user can **step through the solution**, and the visualization is constructed in sync
   — each piece of geometry appearing at the step it belongs to.
4. The user can **ask questions at any point** and get an explanation grounded in the
   problem's actual computed state.
5. The core experience reads as a **polished product** — the whole flow works end to end
   with no broken or placeholder states — of a standard Clara is glad to show a recruiter.

## Non-goals

Explicitly out of scope. An agent in goal mode does not start on these, even with time to
spare.

- A general symbolic-math or answer engine (a Wolfram Alpha replacement). The tool goes
  deep on the geometry spine, not shallow on everything.
- **Physics.** Documented as a future expansion, not built in v1.
- Discrete mathematics, formal proofs, statistics, or probability.
- A native mobile application.
- Multiple users, accounts, or classroom-management features.
- Deployment, hosting, billing, subscriptions, or anything that takes the tool off Clara's
  machine. These are a deliberate future decision (see Open questions), governed by
  C-LOCAL until she makes it.

## Open questions

Decisions not yet made. Each has an assumption the agent works under until Clara says
otherwise; none can be reversed later in a way that discards completed work.

- **Delivery form.** Assumption: a graphical application Clara runs and interacts with
  locally on her machine. The exact form is an implementation decision.
- **Timeline.** Soft, not a finish-line criterion. Assumption: aim to have a demonstrable
  slice of the agentic and mathematical parts working within a few weeks, without cutting
  the finish line down to hit a date.
- **Future productization.** Deployment, security, and billing are explicitly deferred.
  Assumption: when Clara decides to make this deployable, that opens a separate round of
  intake covering security, multi-user, and billing — it is not smuggled in now.
- **Scope discipline.** The four beachhead areas (scalar fields & surfaces, gradients &
  optimization landscapes, vector fields, and linear-algebra-as-geometry) are v1.
  Everything else — physics, higher-than-three-dimensional visualization — is documented
  expansion, out of the finish line.
