#!/usr/bin/env python3
"""Clara's approval command. Records what she has signed off on.

    python3 tools/approve.py --status          # pending proposals and any drift
    python3 tools/approve.py --baseline        # engage governance (end of intake)
    python3 tools/approve.py P-0001 [P-0002]   # approve proposals, re-record baseline
    python3 tools/approve.py --decline P-0001  # decline a proposal
    python3 tools/approve.py --waive-check CHK-001 "reason"   # countersign a failing check

This script is FOR CLARA. It is not a lock -- anything with a shell can run it. What it
does is make approval a deliberate, recorded, committed act, so that an approval which
was not hers is visible in git history afterwards rather than invisible. If you want
approval that an agent cannot fabricate, turn on commit signing; see docs/governance.md.

Delegated approval. Clara can let the agent run an approval in her stead, but only when
she has said so explicitly in the session. The agent passes what she said:

    python3 tools/approve.py P-0001 --on-behalf-of-clara "yes, approve P-0001"

That records her words in the commit body (ON-BEHALF-OF-CLARA: ...) and appends an entry
to progress/log.md, and validate.py flags every such approval as agent-executed so she
can review them. In attribution mode this is an honest audit trail, not proof: the agent
writes the quote, so a determined agent could fabricate it -- what it prevents is a
*quiet* self-approval, which is the failure mode governance exists to catch. For approval
the agent genuinely cannot fabricate, turn on signing with a key it cannot use (see
docs/governance.md); then --on-behalf-of-clara still needs a signature only Clara's key
produces.

Standard library only.
"""

from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constraint_files import (  # noqa: E402
    BASELINE_FILE,
    CHECKS_FILE,
    GOVERNANCE_DIR,
    LOG_FILE,
    PROPOSALS_DIR,
    ROOT,
    current_digests,
    drift,
    git,
    in_git_repo,
    load_baseline,
    load_checks,
    load_goal,
    load_proposals,
    signing_configured,
)

TODAY = _dt.date.today().isoformat()


def _fail(msg: str) -> int:
    print(f"\n  x {msg}\n")
    return 1


def _confirm(prompt: str, on_behalf: str | None) -> bool:
    if on_behalf is not None:
        print(prompt)
        print("  Delegated approval, executed by the agent on Clara's stated authority:")
        print(f'    "{on_behalf}"')
        print("  Recorded in the commit and in progress/log.md, and flagged by")
        print("  validate.py as agent-executed. This is NOT Clara running it herself.")
        return True
    if not sys.stdin.isatty():
        print(
            f"{prompt}\n  x Refusing: no terminal, and no delegated authority given.\n"
            '    Run this yourself at a terminal, or pass'
            ' --on-behalf-of-clara "<what Clara said>".'
        )
        return False
    try:
        answer = input(f"{prompt} Type 'approve' to continue: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer == "approve"


def _append_log(first_line: str, on_behalf: str) -> None:
    """Record a delegated approval in progress/log.md so it is never silent."""
    entry = (
        f"\n## {TODAY} — Delegated approval (agent-executed)\n\n"
        f"- {first_line}\n"
        f'- Clara\'s stated authority, verbatim: "{on_behalf}"\n'
        "- Attribution mode makes this an audit record, not proof the authority was "
        "real. Enable signing (docs/governance.md) for approval the agent cannot forge.\n"
    )
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(entry)
    except OSError as exc:
        print(f"  ! Could not append to progress/log.md: {exc}")


def _write_baseline(approved: list[str]) -> None:
    GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
    digests = current_digests()
    lines = [
        "# Approved baseline. Written by tools/approve.py -- do not hand-edit.",
        "# Hand-editing this file is exactly the tampering validate.py looks for.",
        "version 1",
        f"updated {_dt.datetime.now().isoformat(timespec='seconds')}",
        f"constraints {digests['constraints']}",
        f"goal {digests['goal']}",
        f"tools {digests['tools']}",
        f"trust {digests['trust']}",
        f"checks {digests['checks']}",
    ]
    lines += [f"approved {pid}" for pid in approved]
    BASELINE_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _stamp_proposal(section, new_status: str) -> None:
    path = section.source_file
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"^-\s+\*\*status:\*\*.*$",
        f"- **status:** {new_status}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if re.search(r"^-\s+\*\*approved:\*\*", text, flags=re.MULTILINE):
        text = re.sub(
            r"^-\s+\*\*approved:\*\*.*$",
            f"- **approved:** {TODAY}" if new_status == "approved" else "- **approved:**",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    path.write_text(text, encoding="utf-8")


def _stamp_check(check_id: str, reason: str) -> bool:
    """Mark one registry entry waived, in place, without touching other entries."""
    if not CHECKS_FILE.exists():
        return False
    text = CHECKS_FILE.read_text(encoding="utf-8")
    block_re = re.compile(
        rf"(^##\s+{re.escape(check_id)}\s+[—–-].*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = block_re.search(text)
    if not m:
        return False
    block = m.group(1)

    def set_field(b: str, key: str, value: str) -> str:
        fre = re.compile(rf"^-\s+\*\*{key}:\*\*.*$", re.MULTILINE)
        if fre.search(b):
            return fre.sub(f"- **{key}:** {value}", b, count=1)
        return b.rstrip() + f"\n- **{key}:** {value}\n"

    block = set_field(block, "status", "waived")
    block = set_field(block, "waived", reason)
    block = set_field(block, "waived-by", f"countersigned by Clara {TODAY}")
    CHECKS_FILE.write_text(text[: m.start(1)] + block + text[m.end(1) :], encoding="utf-8")
    return True


def _commit(message: str, on_behalf: str | None) -> int:
    first_line = message.splitlines()[0]
    paths = ["constraints", "goals", "governance", "proposals", "checks"]
    if on_behalf is not None:
        message = message + f'\n\nON-BEHALF-OF-CLARA: "{on_behalf}"'
        _append_log(first_line, on_behalf)
        paths.append("progress")  # so the audit entry rides along in the same commit

    if not in_git_repo():
        print("  ! Not a git repository. Baseline written, but not committed.")
        print("    Governance leans on git history; commit this yourself.")
        return 0
    existing = [p for p in paths if (ROOT / p).exists()]
    if existing:
        code, out = git("add", *existing)
        if code != 0:
            return _fail(f"git add failed: {out}")
    args = ["commit", "-m", message]
    if signing_configured():
        args.insert(1, "-S")
    code, out = git(*args)
    if code != 0:
        return _fail(f"git commit failed: {out}")
    print(f"  Committed: {first_line}")
    if on_behalf is not None:
        print("  Recorded as agent-executed on Clara's stated authority.")
    if signing_configured():
        print("  Signed. validate.py will verify it against governance/allowed_signers.")
    else:
        print("  Unsigned -- attribution only. See docs/governance.md to strengthen this.")
    return 0


def cmd_status() -> int:
    baseline = load_baseline()
    proposals = load_proposals()
    pending = [p for p in proposals if p.get("status").lower() == "proposed"]

    print()
    if not baseline.exists:
        print("Governance: NOT ENGAGED (no approved baseline yet).")
        print("  Constraints and the goal condition are still freely editable.")
        print("  Run 'python3 tools/approve.py --baseline' once you approve the goal condition.")
    else:
        print(f"Governance: ENGAGED (baseline recorded {baseline.updated}).")
        print(f"  Approved proposals: {', '.join(baseline.approved) or 'none beyond the baseline'}")
        changed = drift()
        if changed:
            print("\n  ! GOVERNED CONTENT HAS CHANGED SINCE THE LAST APPROVAL:")
            for area in sorted(changed):
                print(f"      {area}")
            print("    Review 'git diff' and either revert it or approve it deliberately.")
        else:
            print("  No drift. Governed content matches the approved baseline.")

    print(f"\nProposals: {len(proposals)} total, {len(pending)} pending your sign-off.")
    for p in pending:
        print(f"\n  [{p.id}] {p.title}   ({p.get('kind') or 'unspecified kind'})")
        print(f"      targets:  {p.get('targets') or '-'}")
        print(f"      because:  {p.get('because') or '(no explanation given -- reject it)'}")
        print(f"      change:   {p.get('change') or '-'}")
        if p.get("risk"):
            print(f"      risk:     {p.get('risk')}")
        print(f"      file:     {p.source_file.name}")
    print()
    return 0


def cmd_baseline(on_behalf: str | None) -> int:
    status, _criteria, _statement = load_goal()
    state = (status.get("state").lower() if status else "")
    if state != "approved":
        return _fail(
            "The goal condition is not approved yet (state is "
            f"'{state or 'missing'}'). Finish intake first: governance protects an "
            "agreed finish line, so there has to be one."
        )
    if load_baseline().exists:
        print("\nA baseline already exists. This will replace it with the current state.")

    print("\nAbout to record the CURRENT contents of:")
    print("  constraints/defaults.md, constraints/project.md, goals/goal-condition.md")
    print("  and the tool sources, as the approved baseline.")
    print("\nReview 'git diff' and read the constraints before you do this.")
    if not _confirm("\nRecord this as approved?", on_behalf):
        return _fail("Cancelled. Nothing written.")

    _write_baseline(load_baseline().approved)
    print(f"  Baseline written to {BASELINE_FILE.relative_to(BASELINE_FILE.parents[1])}")
    return _commit(
        "APPROVED: BASELINE\n\n"
        "Engage governance. Standing constraints and the goal condition are now "
        "changeable only through an approved proposal.",
        on_behalf,
    )


def cmd_approve(ids: list[str], on_behalf: str | None) -> int:
    baseline = load_baseline()
    if not baseline.exists:
        return _fail(
            "No baseline yet. Run 'python3 tools/approve.py --baseline' first, once "
            "the goal condition is approved."
        )

    proposals = {p.id.upper(): p for p in load_proposals() if p.id}
    wanted = [i.upper() for i in ids]

    missing = [i for i in wanted if i not in proposals]
    if missing:
        return _fail(f"No such proposal: {', '.join(missing)}")

    already = [i for i in wanted if i in baseline.approved]
    if already:
        return _fail(f"Already approved: {', '.join(already)}")

    print()
    for pid in wanted:
        p = proposals[pid]
        if not p.get("because"):
            return _fail(
                f"{pid} has no 'because:' field. A proposal without a written "
                "explanation is not reviewable; send it back."
            )
        print(f"[{pid}] {p.title}  ({p.get('kind') or 'unspecified kind'})")
        print(f"    targets: {p.get('targets') or '-'}")
        print(f"    because: {p.get('because')}")
        print(f"    change:  {p.get('change') or '-'}")
        if p.get("risk"):
            print(f"    risk:    {p.get('risk')}")
        print()

    changed = drift()
    if changed:
        print("Governed content currently differs from the approved baseline in:")
        for area in sorted(changed):
            print(f"    {area}")
        print("Approving will record the CURRENT state as approved. Read 'git diff' first.")
    else:
        print("Note: governed content is unchanged from the last baseline. If this")
        print("proposal was meant to change a constraint, the edit has not been made yet.")

    if not _confirm(f"\nApprove {', '.join(wanted)} and re-record the baseline?", on_behalf):
        return _fail("Cancelled. Nothing written.")

    for pid in wanted:
        _stamp_proposal(proposals[pid], "approved")
    _write_baseline(baseline.approved + wanted)

    return _commit(
        f"APPROVED: {', '.join(wanted)}\n\n"
        + "\n".join(f"{pid}: {proposals[pid].title}" for pid in wanted),
        on_behalf,
    )


def cmd_decline(ids: list[str], on_behalf: str | None) -> int:
    proposals = {p.id.upper(): p for p in load_proposals() if p.id}
    wanted = [i.upper() for i in ids]
    missing = [i for i in wanted if i not in proposals]
    if missing:
        return _fail(f"No such proposal: {', '.join(missing)}")
    for pid in wanted:
        _stamp_proposal(proposals[pid], "declined")
        print(f"  Declined {pid}: {proposals[pid].title}")
    # Declining loosens nothing, so it carries no ON-BEHALF marker or log entry.
    return _commit(f"Decline proposal(s): {', '.join(wanted)}", None)


def cmd_waive_check(check_id: str, reason: str, on_behalf: str | None) -> int:
    """Countersign a failing/skipped check as acceptable. Clara's call.

    Loosens the completion gate for one check, so it is a governed act: recorded as a
    WAIVED-CHECK commit that verify.py and validate.py check for. Until this runs, a
    check marked waived by hand keeps binding.
    """
    check_id = check_id.upper()
    ids = {(c.id or "").upper() for c in load_checks()}
    if check_id not in ids:
        return _fail(f"No such check: {check_id}. See checks/registry.md.")
    if not reason.strip():
        return _fail("A check waiver needs a reason. Say why it is acceptable for this "
                     "check not to pass.")

    print(f"\n[{check_id}] waive this check — the completion gate will accept it as")
    print(f"    passing without it running. Reason: {reason}")
    if not _confirm("\nCountersign this waiver?", on_behalf):
        return _fail("Cancelled. Nothing written.")

    if not _stamp_check(check_id, reason):
        return _fail(f"Could not find {check_id} in {CHECKS_FILE.name} to stamp.")
    if load_baseline().exists:
        _write_baseline(load_baseline().approved)

    return _commit(
        f"WAIVED-CHECK: {check_id}\n\n{reason}",
        on_behalf,
    )


def main(argv: list[str]) -> int:
    on_behalf: str | None = None
    if "--on-behalf-of-clara" in argv:
        i = argv.index("--on-behalf-of-clara")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            return _fail(
                'The --on-behalf-of-clara flag needs the authorization text, e.g.\n'
                '    python3 tools/approve.py P-0001 --on-behalf-of-clara "yes, approve P-0001"'
            )
        on_behalf = argv[i + 1].strip()
        if not on_behalf:
            return _fail("--on-behalf-of-clara was given empty authorization text.")
        argv = argv[:i] + argv[i + 2 :]

    args = argv

    if "--waive-check" in args:
        i = args.index("--waive-check")
        rest = [a for a in args[i + 1 :] if not a.startswith("--")]
        if len(rest) < 2:
            return _fail('Usage: python3 tools/approve.py --waive-check CHK-001 "reason"')
        return cmd_waive_check(rest[0], rest[1], on_behalf)

    if not args or "--status" in args:
        return cmd_status()
    if "--baseline" in args:
        return cmd_baseline(on_behalf)
    if "--decline" in args:
        ids = [a for a in args if a != "--decline"]
        if not ids:
            return _fail("Which proposal? e.g. --decline P-0001")
        return cmd_decline(ids, on_behalf)

    ids = [a for a in args if not a.startswith("--")]
    if not ids:
        return _fail("Nothing to do. Try --status.")
    if not PROPOSALS_DIR.exists():
        return _fail("No proposals/ directory.")
    return cmd_approve(ids, on_behalf)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
