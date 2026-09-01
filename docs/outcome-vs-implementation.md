# Outcomes, not implementations

This is the rule the whole repository exists to protect.

**A constraint says what must remain true. A goal says what must become true. Neither
ever says how to build anything.**

The agent has full freedom of judgment over architecture, file layout, libraries,
patterns, and sequencing. The constraint system defines the boundaries and the finish
line, and then gets out of the way. Every time a "how" leaks into a constraint, the
system loses the thing that makes it worth having: an agent that can find a better route
than the one you would have specified.

This is not a style preference. A constraint file full of implementation detail is a bad
design document wearing a constraint's clothes — it will go stale, it will conflict with
what the agent learns, and it will make the goal condition unfalsifiable.

## Three tests

Apply these to any line before it goes into `constraints/` or `goals/`.

**1. The substitution test.** Could two competent engineers satisfy this with completely
different builds? If yes, it is outcome-shaped. If every satisfying implementation looks
the same, you have written a spec, not a constraint.

**2. The black-box test.** Can you verify it without reading the source? Constraints are
checked from the outside: by running the thing, reading its output, inspecting the diff,
timing it, breaking it on purpose. If the only way to check is "open the file and see if
they did it that way", it is implementation.

**3. The obsolescence test.** If the agent finds a better approach halfway through, does
this line still hold? A real constraint survives a rewrite. "Data survives a restart"
survives switching storage engines. "Use SQLite" does not.

## Good and bad, side by side

| Smuggled implementation | Outcome-shaped |
|---|---|
| Use PostgreSQL for storage. | Data written by one run is readable by the next, and survives the process being killed. |
| Put API routes in `src/api/` and handlers in `src/handlers/`. | Every HTTP endpoint's request and response shape is documented, and the documentation is generated from the same source the server uses, so it cannot drift. |
| Write unit tests with pytest, aim for 80% coverage. | Every outcome in `goals/outcomes.md` has an automated check that fails when that outcome stops holding. |
| Use React and Tailwind. | The interface is usable in current Chrome and Safari at 375px and 1440px wide, with no horizontal scrolling and no clipped controls. |
| Cache results in Redis with a 60s TTL. | A repeated identical query returns in under 50ms, and never returns data more than a minute stale. |
| Add a retry decorator with exponential backoff to all network calls. | A transient network failure does not surface as an error to the user, and does not produce duplicate side effects. |
| Structure the CLI with subcommands and argparse. | Someone who has never seen the tool can accomplish the main task from `--help` alone, without reading the source. |
| Log to stdout in JSON with a request ID field. | Given a user report of a failure and a rough timestamp, the responsible request can be located in the logs in under a minute. |
| Refactor `sync.py` into smaller modules. | A change to how one record type syncs does not require touching code for any other record type. |
| Use a worker queue for the import. | Importing a 100k-row file does not block the interface, and a failed import can be resumed without re-importing rows already committed. |

Notice what the right-hand column buys you: every one of them is falsifiable, and none of
them tells the agent what to type.

## The tells

A line is probably smuggling implementation if it contains:

- a library, framework, service, or product name
- a file path, directory name, module name, class name, or function name
- a design pattern by name — factory, singleton, hexagonal, MVC, event-driven
- a numeric target attached to an internal mechanism rather than an observable result
  (coverage percentage, module size, number of layers)
- the words "use", "add", "create", "refactor", "structure", "implement", "make sure to"
- a sequence: first this, then that

`tools/validate.py` flags these as warnings. Warnings are heuristics, not verdicts — read
the flagged line and decide.

## The legitimate exception

Sometimes a technology *is* the outcome, because it was imposed from outside:

- the deliverable is a library her team will import, and it must be importable from Python 3.11
- it has to run on a machine that only has Node 18
- it must read a file format she does not control
- her employer requires a specific runtime

These are real constraints. Name the technology, and add a `why:` field stating the
external requirement that forces it. The validator requires `why:` on any constraint that
names a technology, precisely so that "I would rather build it this way" cannot pass
itself off as "this is required."

The distinction is: **is this imposed on the project from outside, or is it a preference
about how to build?** Preferences do not belong in constraints. If Clara has a strong
preference, she can say it in the session — that is direction, not a constraint, and it
does not bind future sessions.

## Rewriting a bad constraint

When you catch one, do not delete it. Ask what it was protecting.

> "Use a worker queue for the import."

What was that protecting? Probably: the UI froze last time, and a half-finished import
left a mess. So:

> **rule:** Importing a large file leaves the interface responsive, and an import that
> fails partway can be resumed without duplicating rows already committed.
> **check:** Start an import of a 100k-row file, confirm the interface still responds
> during it, kill the process midway, restart the import, and confirm the final row
> count matches the input exactly.

Now the agent can use a queue, a thread, a subprocess, or chunked commits — and the
constraint still catches the failure Clara actually cared about.

Do this for every constraint that fails a test. The question is always: **what bad
outcome was this "how" trying to prevent?** Write that instead.

## One apparent exception: the governance rules

`C-GOVERNED-CHANGE` and `C-WAIVER-SIGNOFF` look like process instructions — "write a
proposal", "get sign-off". They are not exceptions to the rule on this page, and it is
worth seeing why, because the distinction is the same one you apply everywhere else.

They constrain the *agent's* conduct, not the project's implementation. What must remain
true is: the rules the work is judged against are the ones Clara agreed to. That is an
outcome, and it is checkable from outside — `validate.py` compares the current rules to
the approved baseline, and git history shows who changed what. The proposal mechanism is
the check, in the same way "run the importer on samples/" is a check. It is not
architecture for the thing being built.

The test that separates them: **does this constrain what the agent produces, or how it
produces it?** Governance rules constrain neither — they constrain what counts as the
standard. A rule about the constraint system itself is legitimate. A rule about the
project's code structure is not.

Note also that `C-GOVERNED-CHANGE` carries a `why:`. It should: it is the one default
whose reasoning an agent is most likely to try to argue past, and the reasoning is the
part that makes it stick.

## And the thing this page is really for

You will, at some point, be stuck against a constraint. The rewrite advice above is for
authoring good constraints, not for escaping ones you find inconvenient. If a rule is
blocking you and governance has engaged, the honest move is a proposal that states the
blockage and what it would cost to lift the rule — not a "clarification" that quietly
converts a binding rule into a softer one. `docs/governance.md` covers that path.
