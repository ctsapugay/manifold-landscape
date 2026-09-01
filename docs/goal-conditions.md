# Writing a goal condition

A goal condition is the answer to "how will we know this is finished?" — written so
precisely that an agent, working alone for hours, can decide for itself whether it is
done, and be right.

It is the single most important artifact in the repo. A vague one turns goal mode into
drifting. A prescriptive one turns it into following orders.

## The standard

**Concrete.** Every criterion names something that exists in the world: a command with an
output, a file with contents, a behaviour someone can trigger.

**Verifiable by someone else.** A skeptic with access to the machine but not to the
conversation can run the checks and reach the same verdict. If confirming it requires
trusting the agent's account of its own work, it is not verifiable.

**Falsifiable.** There is a describable state of the world in which the criterion is
false. "The code is well organized" has no such state. "Adding a new record type requires
changing exactly one file" does.

**Bounded.** It can be met, and once met, work stops. If satisfying it more fully is
always possible, it is a direction, not a finish line.

**Silent on how.** It says what is true at the end, never what happens in between. Same
rules as `docs/outcome-vs-implementation.md`.

## Three files, one finish line

The goal condition itself is short and stable, and it does **not** contain the criteria or
the checks — it points to them. The finish line is three files together:

- **`goals/goal-condition.md`** — a plain overview of the project, plus the *completion
  contract*: a standing "what completion requires" section that defines done **by
  reference** — every criterion met, the check suite green, every constraint upheld — and
  cites the constraint system so the work can't be judged against a softened bar. It does
  not list criteria or checks, because those grow long.
- **`goals/criteria.md`** — the measurable criteria: the few, human-meaningful statements
  of what done means (aim for three to seven), each with a prose `check:` and a `state:`.
  A criterion's `state:` is a claim, recorded once when it was first confirmed.
- **`checks/registry.md`** — the executable checks `tools/verify.py` runs, which pass or
  fail on real behaviour every time. There can be dozens; keeping them out of the goal
  condition is what stops the finish line becoming a task list.

The completion contract binds them: done only when every criterion is met *and* `verify.py`
is green (each check passing or waived with Clara's countersignature) *and* the constraints
held. The criteria say what done means; the checks prove it still holds at the end, not
just when a box was first ticked — a regression that breaks a passing check turns the suite
red and re-opens the finish line. Don't enumerate criteria or checks in the goal condition;
put them in their files and let the contract require them.

## Aspirational vs. checkable

| Aspirational | Checkable |
|---|---|
| The importer is reliable. | Running the importer on each of the three sample files in `samples/` exits zero and produces row counts matching the file line counts, three times in a row. |
| The tool is easy to use. | Someone who has not seen it before completes the main task using only `--help`, without asking a question. |
| Good test coverage. | Each outcome in `goals/outcomes.md` has at least one automated check; deliberately breaking that outcome makes the check fail. |
| It's fast enough. | A 10k-row query returns in under 200ms on this machine, measured three times, warm. |
| The docs are complete. | Following the README from a fresh clone gets a working local run with no step that requires knowledge not in the README. |
| Errors are handled gracefully. | Every failure the tool can produce prints a message naming what failed and what to do next; no stack trace reaches the user. |

The right-hand column is longer. That is the cost, and it is worth paying — those are the
sentences an agent can actually check at hour six.

## Shape

Three to seven criteria. Fewer, and it is too coarse to guide anything. More, and it is a
task list that will go stale.

Each criterion gets a `check:` — the specific thing to run or look at. Write the check
before you trust the criterion. If you cannot write a check, the criterion is not ready.

Each criterion gets `state:` and `evidence:`. `evidence:` stays empty until the check has
actually been run; then it records what was run and what it showed, with a date. Empty
evidence on a criterion marked `met` is a bug — `tools/validate.py` catches it.

## The "out of scope for done" section

List what will still be imperfect when the goal condition is met, and that is fine. No
Windows support. No tests for the CLI parsing. Slow on files over a million rows.

This section is what makes the finish line a *line*. Without it, an agent in goal mode
that meets every criterion will keep finding things to improve.

## Approval

Clara approves or edits before goal mode starts. An unapproved goal condition
(`state: draft`) means intake is not finished, and `tools/validate.py` will say so.

Once she approves, `python3 tools/approve.py --baseline` engages governance and the goal
condition stops being the agent's to edit. Criterion `state:` and `evidence:` stay
freely updatable — those are progress, not the finish line.

Changing a criterion mid-project needs a proposal and her re-approval. Record it in
`progress/log.md` too. A goal condition that quietly moves is worse than none, and an
agent that can move it has no finish line at all.
