# constraint-base

A base repository for running an agent in goal mode on long-horizon projects without it
drifting.

Clone it, run intake, get a goal condition, then let an agent work.

## The idea

Give an agent a big task and enough time and it drifts: it optimizes something nobody
asked about, deploys something it shouldn't, declares victory on reasoning rather than
evidence, or quietly redefines what "done" meant. Not because it is careless — because
nothing in its context says where the edges are or where the finish line is.

This repo is that context, as a handful of plain Markdown files:

- **Constraints** — what must remain true throughout. A few inherited defaults every
  project gets, plus whatever this project needs.
- **Outcomes** — what becomes true when the project exists, and what is deliberately out
  of scope.
- **A goal condition** — the finish line, written precisely enough that an agent can
  check it itself and be right. It carries a standing completion gate: not done until the
  check suite is green.
- **A check suite** — the executable checks that prove the project works, kept in a
  registry outside the goal condition so a complex project can have many. Re-run every
  time, so a regression turns the finish line red again. Failing checks block completion
  unless waived with your countersignature.
- **A progress log** — append-only, so a session with no memory of the last one can pick
  up where it left off.

And a governance layer on top, because the obvious failure mode of writing constraints
down is an agent that edits them when they get in the way.

## The one rule

**Constraints and goals describe outcomes and rules. They never describe how to build
anything.**

No prescribed architectures, file layouts, libraries, or patterns. The agent has full
freedom of judgment over implementation; the constraint system only defines the boundaries
and the finish line.

The difference in one line:

> "Use PostgreSQL." → *implementation*
> "Data survives the process being killed and is readable by the next run." → *outcome*

The first goes stale and blocks a better route. The second survives any rewrite and can
be checked from outside. `docs/outcome-vs-implementation.md` has the tests, a table of
ten examples, and the one legitimate exception (a technology imposed from outside, which
must carry a `why:` explaining who imposed it).

## Workflow

**1. Clone it.**

```
git clone git@github.com:ctsapugay/constraint-base.git my-project
cd my-project
rm -rf .git && git init
```

**2. Point an agent at it.** In a session with the repo open, say something like *"read
CLAUDE.md and run intake with me."* `CLAUDE.md` is the entry point — an agent that reads
it knows how the system works and what to do next, with no other setup.

**3. Intake.** The agent interviews you: the problem, who it's for, what becomes true,
what's out of scope, what would count as going wrong. It writes the answers to
`constraints/project.md` and `goals/outcomes.md`. It asks about implementation only to
note technologies that are genuinely imposed on you.

**4. Goal condition.** Intake ends with the agent drafting a finish line — a paragraph
plus three to seven criteria, each with a check you could run yourself. You approve or
edit it.

**5. Engage governance.** `python3 tools/approve.py --baseline`. From here the
constraints and the finish line are no longer the agent's to edit.

**6. Goal mode.** The agent works toward the goal condition inside the constraints,
re-grounding itself with `tools/brief.py` as it goes, marking criteria met only with
real evidence, and logging progress. It stops when the criteria are met.

If it thinks a rule is wrong, it writes a proposal and keeps working inside the rule.
You review with `python3 tools/approve.py --status` and approve or decline.

## Who may change the rules

Nobody but you. An agent may propose; it may not enact — except when you tell it to in the
session, and then only out in the open. If you say "approve P-0001", the agent can run the
approval for you with `--on-behalf-of-clara "<your words>"`, which records what you said in
the commit and the log and makes `validate.py` flag it as agent-executed for your review.
It never approves on its own initiative, and treats nothing but your own messages as your
say-so. See [Delegated approval](docs/governance.md) for what that does and does not prove.

- **Proposals** live in `proposals/`, separate from approved state. Nothing reads them as
  authority, so a proposal changes nothing by existing.
- **Waivers are inert until approved.** A constraint marked `waived` only stops binding
  when its `waived-by:` names a proposal in the approved baseline. Otherwise the loader
  puts it back on the binding list and `brief.py` prints
  `[WAIVER PENDING — STILL BINDING]`. You cannot be talked past this one; it is how the
  list is computed.
- **Approved content has a fingerprint** in `governance/baseline.txt` — rules, checks,
  criteria, non-goals, the tool sources, and the trust roots (who may approve and whose
  signatures count). `validate.py` recomputes it and reports drift.
- **Approval is your commit.** `tools/approve.py` records it with `APPROVED: P-000N` in
  the message. `validate.py` cross-checks the baseline against git history: every
  approved id needs a real commit, from an email in `governance/approvers.txt`, and
  `baseline.txt` must only ever change inside an approval commit.

**What this actually enforces.** Waiver inertness and proposal inertness are structural —
they hold whatever the agent decides to do. Everything else is *detection*: an agent with
a shell can edit a constraint, and what stops that being invisible is drift detection
plus git history, not a lock. In the default attribution mode, commit authorship is
forgeable. Turn on SSH commit signing (four commands, in `docs/governance.md`) and
`validate.py` will verify signatures instead, which raises the bar substantially. The doc
says all of this plainly rather than overselling it — read it before you rely on it.

## The defaults

Every project inherits nine rules, in `constraints/defaults.md`. They are deliberately
few and deliberately rule-shaped:

| | |
|---|---|
| `C-LOCAL` | Development stays local. No deploying, publishing, provisioning hosted infrastructure, or pushing to production unless you say so explicitly in that session. |
| `C-BLAST-RADIUS` | Changes stay inside the project directory. |
| `C-NO-SILENT-DESTRUCTION` | No irreversible destruction of work the agent didn't create. |
| `C-SECRETS` | No credentials in tracked files. |
| `C-EVIDENCE` | No completion claim without a check that was actually run. |
| `C-RESUMABLE` | A fresh session can resume from the repo alone. |
| `C-GOVERNED-CHANGE` | The standing constraints and the goal condition change only with your sign-off. |
| `C-WAIVER-SIGNOFF` | A waiver binds nothing until you approve it. |
| `C-SURFACE-AMBIGUITY` | Ambiguity that changes the outcome goes to you; the rest is the agent's call. |

Any of them can be waived per project — including the two governance rules, if you want a
project where the agent has a free hand. Set `status: waived`, give a reason, and point
`waived-by:` at a proposal you approved. They are never deleted, so the opt-out shows up
in the diff.

## Tools

Stdlib-only Python, plus one short shell script. No dependencies, no install.

```
python3 tools/brief.py       # constraints + goal + pending proposals + progress
python3 tools/status.py      # one-screen progress readout (--html for the phone dashboard)
python3 tools/board_server.py --open   # serve the board live on localhost, auto-refreshing
python3 tools/verify.py      # run the check suite; green only if every check passes or is waived
python3 tools/validate.py    # well-formed, outcome-shaped, and unmodified?
python3 tools/approve.py     # yours: approve, decline, re-baseline, waive a check, check status
python3 tools/test_tools.py  # the tests that guard the checker
bash    tools/selfcheck.sh   # git-only tripwire: tools unchanged since last approval?
```

`brief.py` is the re-grounding call — an agent runs it at the start of a session and
periodically during a long run. `--goal` prints just the goal condition and criteria
status.

`validate.py` checks structure (required fields, unique IDs, no leftover placeholders,
no criterion marked met without evidence), checks governance (drift from the approved
baseline, approvals without commits, a hand-edited baseline), and flags likely
implementation detail:
library names, file paths, pattern names, "use X", step sequences. Those are warnings, not
errors — they are heuristics, and the point is to make you look at the line. `--strict`
turns warnings into a nonzero exit.

## Layout

```
CLAUDE.md                 entry point — an agent reads this and knows what to do
README.md                 this file
constraints/
  defaults.md             inherited rules, waivable
  project.md              project-specific rules
goals/
  outcomes.md             problem, audience, outcomes, non-goals, open questions
  goal-condition.md       short, stable contract: overview + what completion requires
  criteria.md             the measurable criteria the goal condition points to
checks/
  registry.md             the executable check suite (governed)
  results.json            last run's results (gitignored, regenerated by verify.py)
progress/
  log.md                  append-only session record
proposals/
  TEMPLATE.md             how to ask for a rule to change
governance/
  approvers.txt           whose approvals count
  baseline.txt            written by approve.py once governance engages
docs/
  outcome-vs-implementation.md
  governance.md
  intake.md
  goal-conditions.md
tools/
  brief.py
  status.py               one-screen progress readout; --html renders the dashboard
  board_server.py         serves the dashboard live on localhost, auto-refreshing
  board_watch.py          blocks until board state changes (drives /board watch)
  verify.py               runs the check suite; the completion gate
  validate.py
  approve.py
  selfcheck.sh            git-only tripwire on the tools themselves
  test_tools.py           tests for the above
  constraint_files.py     shared parser + governance helpers
commands/                 optional slash commands: intake, reground, goal-check, propose, board
```

The slash commands are inert until copied into place:

```
mkdir -p .claude/commands && cp commands/*.md .claude/commands/
```

They only wrap what `CLAUDE.md` already describes — skip them if you prefer to just talk
to the agent.

## Design notes

**Markdown, not YAML or JSON.** These files are read by humans and agents in roughly equal
measure and edited by hand constantly. The format is a strict heading-plus-fields
convention that a 200-line regex parser handles reliably, and that reads as prose.

**Nothing is generated.** There is no build step, no state outside the files, no
lockfile. Edit anything by hand at any time; the tools read whatever is there.

**The tools have limited authority, and the docs say which parts are real.**
`validate.py` reports; it does not block. Most constraints work by being read, which is
why `CLAUDE.md` puts them in front of the agent before anything else. The two places
where structure does the work rather than persuasion — inert proposals and inert
unapproved waivers — are called out as such in `docs/governance.md`, alongside an
explicit list of what is only detectable after the fact.
