# Governance: who may change the rules

The failure mode this exists to catch: an agent that cannot satisfy a constraint quietly
edits the constraint instead, and the project passes because the bar moved.

So the rules are not the agent's to change. It can *propose*. Clara approves.

Two constraints carry this — `C-GOVERNED-CHANGE` and `C-WAIVER-SIGNOFF` — and three
mechanisms back them up. Read the last section before you trust any of it.

## How it works

**Proposals live apart from approved state.** An agent that wants a constraint changed
writes `proposals/P-000N-slug.md`. Nothing reads `proposals/` as state. `brief.py` shows
pending proposals in their own section, labelled inert. `load_constraints()` never
consults them. A proposal changes nothing by existing — not by the agent's restraint, but
because no code path treats it as authority.

**Waivers are inert until approved.** A constraint can say `status: waived`, but the
loader only honours it when `waived-by:` names a proposal id in the approved baseline.
Otherwise the constraint goes back on the binding list, and `brief.py` prints
`[WAIVER PENDING — STILL BINDING]` next to it. This is the strongest link in the chain:
an unapproved waiver does not weaken anything, because the code computing "what binds"
ignores it.

**Approved state has a fingerprint.** `governance/baseline.txt` records a digest of the
governed content, in four areas:

- `constraints` — every constraint's rule, check, status and waiver;
- `goal` — the goal statement, criteria and out-of-scope list, plus the **non-goals** from
  `goals/outcomes.md` (they are the scope guard, so they are governed even though they live
  in the outcomes file);
- `tools` — the source of the checking tools themselves (`constraint_files.py`,
  `validate.py`, `approve.py`, `brief.py`, `status.py`);
- `trust` — `governance/approvers.txt` and `governance/allowed_signers`, the files that
  decide whose approvals and signatures count. Without this, an agent could add its own
  address or key and approve as itself with nothing showing as drift.
- `checks` — the check registry (`checks/registry.md`): each check's id, command, status
  and waiver backing. Not the results (those change every run) — the suite's *definition*.
  Without this, an agent could make verification pass by deleting a failing check or
  rewriting what it runs.

`validate.py` recomputes and compares. Any change to a rule, a criterion, a non-goal, the
checking tools, the trust roots, or the check suite without a matching approval shows up
as an error.

Check waivers work exactly like constraint waivers: a check marked `waived` in the registry
takes effect only when Clara countersigns it with `approve.py --waive-check`, which records
a `WAIVED-CHECK: CHK-00N` commit. Until then the check still has to pass — an
un-countersigned check waiver binds, just as an unapproved constraint waiver does.

The digest deliberately excludes each criterion's `state:` and `evidence:`, and the
goal's own `state:`. Those change constantly during normal work. The finish line is
governed; progress against it is not.

**Approval is a commit.** `tools/approve.py` is Clara's command. It stamps the proposal,
re-records the baseline, and commits with `APPROVED: P-000N` in the message.
`validate.py` then checks, against git history:

- every id in the baseline has a commit claiming to approve it
- those commits were authored by someone in `governance/approvers.txt`
- `governance/baseline.txt` has only ever changed in approval commits
- with signing on, each approval commit's signature verifies

## The loop in practice

1. Agent hits a constraint it believes is wrong or blocking.
2. It writes a proposal: what it targets, what would change, **why**, and what stops
   being protected if approved. Then it keeps working inside the existing constraint, or
   stops and says it is blocked. It does not edit anything governed.
3. `brief.py` surfaces the proposal on every re-grounding, so neither of you forgets it.
4. Clara reads it: `python3 tools/approve.py --status`.
5. If she agrees, she makes the edit (or has the agent make it and reviews `git diff`),
   then runs `python3 tools/approve.py P-000N`. If she doesn't:
   `python3 tools/approve.py --decline P-000N`.
6. Governance re-baselines, and the new state is what binds from then on.

Governance engages when Clara runs `tools/approve.py --baseline`, which requires the goal
condition to be approved. Before that — during intake — everything is fluid, which is
correct: there is no agreed finish line yet to protect.

## Delegated approval

Clara does not have to type the approval command herself every time. She can tell the
agent, in the session, to run it for her — "yes, approve P-0001" — and the agent runs:

```
python3 tools/approve.py P-0001 --on-behalf-of-clara "yes, approve P-0001"
```

This does three things beyond a normal approval:

- it writes her authorization verbatim into the commit body as `ON-BEHALF-OF-CLARA: "…"`;
- it appends a dated entry to `progress/log.md` recording the delegation;
- it makes `validate.py` list the approval, on every run, as **agent-executed on Clara's
  stated authority**, so she can confirm she actually said so.

Be clear-eyed about what this is and is not. It converts approval from something only
Clara's hands can do into something the agent can do **on her explicit say-so** — and it
makes every such approval loud, logged, and flagged rather than silent. That directly
addresses the failure mode at the top of this document: an agent *quietly* moving the bar.
What it does **not** do, in attribution mode, is prove the authorization was real. The
agent writes the quote; a determined agent could fabricate it, exactly as it could forge a
commit author. Delegation makes a dishonest approval visible and reviewable; it does not
make it impossible.

The old `--yes` flag, which approved with no authorization trail at all, has been removed.
Approval now has exactly two shapes: Clara at a terminal typing `approve`, or the agent
with `--on-behalf-of-clara "<her words>"`. In a non-interactive context with neither,
`approve.py` refuses.

**What makes delegation un-forgeable** is signing with a key the agent cannot use (below).
With signing on, an `--on-behalf-of-clara` approval still has to carry a signature that
only Clara's key produces, so the agent can prepare the approval but cannot complete it
without her. Note the practical cost: a signing-key passphrase prompt appears in the local
terminal and does not forward to a phone, so un-forgeable approval means Clara is at the
machine, not approving from Remote Control.

## Turning on signing (recommended)

Attribution mode identifies approvals by commit author email, which anything with repo
access can set. Signing raises the bar a lot:

```
# use your own signing key path in place of the example below
git config gpg.format ssh
git config user.signingkey ~/.ssh/id_ed25519.pub
git config commit.gpgsign true
printf '%s %s\n' 'ctsapugay@gmail.com' "$(cat ~/.ssh/id_ed25519.pub)" > governance/allowed_signers
git config gpg.ssh.allowedSignersFile "$(pwd)/governance/allowed_signers"
```

That last line matters: without `gpg.ssh.allowedSignersFile` set, git cannot verify SSH
signatures, so `git log`'s signature field reports a validly signed commit as *unsigned*
and `validate.py` would wrongly flag it. (`validate.py` also passes the file explicitly
when reading history, so it stays correct even in a fresh clone where you have not set the
config yet — but set it, so your own `git log --show-signature` works too.)

Once `governance/allowed_signers` exists, `approve.py` signs automatically and
`validate.py`:

- errors on an approval commit whose signature does not verify
- errors on an *unsigned* approval commit made at a point where `allowed_signers` was
  already in the tree — i.e. an approval that bypassed `approve.py`
- warns, rather than errors, on approvals that predate signing being turned on, since
  those genuinely cannot be verified. Re-approve them if you want a clean report.
- errors if `allowed_signers` was ever present and has since been deleted, so quietly
  downgrading back to attribution mode is itself a finding

## What this actually enforces

Be clear-eyed about this. The repository is plain files and the agent has a shell. There
is no sandbox here, and this document is not going to pretend otherwise.

**Genuinely enforced, by construction:**

- An unapproved waiver does not reduce the constraint set. The code that computes what
  binds does not look at unapproved waivers. Nothing has to remember to honour this.
- A proposal has no effect. There is no code path that reads `proposals/` as state.
- A hand-edited `baseline.txt` is caught, because approvals are cross-checked against
  commit messages in git history, not just against the file.

**Detectable after the fact, not prevented:**

- Editing a constraint, a non-goal, or the goal condition. The agent can do it.
  `validate.py` will report drift the next time it runs, and `git diff` shows it. This is
  an alarm, not a lock.
- Adding itself as an approver or a signer. `governance/approvers.txt` and
  `governance/allowed_signers` are in the `trust` digest, so appending an address or a key
  moves the digest and shows as drift. Editing them is possible; doing it invisibly is not.
- Editing the tools to disable the alarm. The tool sources are in the digest, so this
  also shows as drift — but only to a validator that has not itself been replaced. A
  self-hashing checker cannot detect its own subversion. For that case, run
  `bash tools/selfcheck.sh`, which uses git alone (no repo Python) to diff the tools and
  governed files against the last approved commit, or run `git diff` against a known-good
  commit yourself.
- The authenticity of a delegated approval in attribution mode. `validate.py` flags every
  `--on-behalf-of-clara` approval for review and records the stated authority, but cannot
  prove the agent was actually told to run it. Signing closes this; see below.

**Not enforced at all in attribution mode:**

- Authorship of an approval commit. `git -c user.email=ctsapugay@gmail.com commit` is
  available to anything with a shell. Attribution mode gives you an audit trail — the
  forged approval is a visible commit, in history, pushed to GitHub, with a timestamp —
  but it does not stop the forgery.

Signing closes that last one properly: an unsigned approval made while signing is in
force is an error, not a warning, so forging authorship no longer works. The remaining
gap is the key itself. If your signing key sits unencrypted at `~/.ssh/id_ed25519` and
the agent has a shell on the same machine, it can sign as you. A passphrase-protected
key held in the agent, or a hardware key, is what actually closes it — and at that point
you are relying on your key hygiene, not on this repository.

**The honest summary:** governance makes the sanctioned path easy, makes unsanctioned
changes visible, and makes one specific category — waivers — structurally impossible to
self-grant. It does not make an agent unable to modify files it can write to. Treat
`validate.py` output and `git log` as the real check, and read the diff on anything under
`constraints/`, `goals/`, or `governance/` before you approve it.

## Files

| Path | What it is |
|---|---|
| `proposals/P-000N-*.md` | Requests. Inert. Written by the agent. |
| `proposals/TEMPLATE.md` | The format, and how to write a proposal worth approving. |
| `governance/baseline.txt` | Digest of approved content + approved proposal ids. Written only by `approve.py`. |
| `governance/approvers.txt` | Whose commits count as approvals. |
| `governance/allowed_signers` | Optional. Enables signature verification. |
| `tools/approve.py` | Clara's command. Approve, decline, re-baseline, check status. |
