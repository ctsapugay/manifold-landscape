#!/usr/bin/env python3
"""Print the constraints, the goal condition, pending proposals, and recent progress.

    python3 tools/brief.py             # everything
    python3 tools/brief.py --goal      # just the goal condition and criteria
    python3 tools/brief.py --rules     # just the constraints
    python3 tools/brief.py --pending   # just governance: proposals and drift

Run this at the start of a session, and again periodically during a long run: after
finishing a chunk of work, before a decision that would be expensive to reverse, or
whenever you notice you have been going a while without checking. It is the re-grounding
call -- read the output, then ask whether what you are about to do stays inside the rules
and moves toward the finish line.

A waiver that Clara has not approved is shown as NOT in effect, and the constraint it
targets is listed among the rules that bind. That is not a courtesy; it is how the
loader computes the list.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constraint_files import (  # noqa: E402
    approved_ids,
    current_checkpoint,
    drift,
    governance_engaged,
    load_baseline,
    load_constraints,
    load_goal,
    load_proposals,
    open_blockers,
    recent_log_entries,
    signing_configured,
    suite_state,
)

WIDTH = 88


def rule(char: str = "=") -> None:
    print(char * WIDTH)


def wrap(text: str, indent: str = "    ") -> str:
    return textwrap.fill(text, width=WIDTH, initial_indent=indent, subsequent_indent=indent)


def _partition(approved: set[str]):
    """Split constraints into those that bind and those genuinely waived."""
    binding, waived, claimed = [], [], []
    for c in load_constraints():
        if c.get("status").lower() != "waived":
            binding.append(c)
        elif c.get("waived-by").upper() in approved:
            waived.append(c)
        else:
            binding.append(c)
            claimed.append(c)
    return binding, waived, claimed


def show_constraints() -> None:
    approved = approved_ids()
    binding, waived, claimed = _partition(approved)

    rule()
    print(f"CONSTRAINTS -- {len(binding)} in force")
    rule()
    print(
        wrap(
            "These bound the work. They say what must remain true; they never say how "
            "to build anything. Implementation is your judgment. You may not change "
            "them yourself -- propose, and Clara approves.",
            indent="",
        )
    )
    print()

    for c in binding:
        origin = "default" if c.get("source").lower() == "default" else "project"
        flag = "  [WAIVER PENDING -- STILL BINDING]" if c in claimed else ""
        print(f"  [{c.id}] {c.title}  ({origin}){flag}")
        print(wrap(c.get("rule"), indent="      "))
        if c.get("check"):
            print(wrap(f"check: {c.get('check')}", indent="      "))
        print()

    if claimed:
        print(wrap(
            f"! {len(claimed)} constraint(s) carry a waiver Clara has not approved. "
            "An unapproved waiver has no effect. Do not act as though it does.",
            indent="  ",
        ))
        print()

    if waived:
        print(f"  Waived with approval ({len(waived)}):")
        for c in waived:
            print(f"    [{c.id}] {c.title} -- {c.get('waived') or 'no reason recorded'}"
                  f" (via {c.get('waived-by')})")
        print()


def show_goal() -> None:
    status, criteria, statement = load_goal()
    state = status.get("state") if status else "unknown"

    rule()
    print(f"GOAL CONDITION -- {state}")
    rule()

    if statement:
        print(wrap(statement, indent=""))
    else:
        print("  (no statement yet)")
    print()

    if state.lower() == "draft":
        print(wrap(
            "! Still a draft. Clara has not approved it. Finish intake before starting "
            "work -- see docs/intake.md.",
            indent="  ",
        ))
        print()

    met = 0
    for g in criteria:
        gstate = g.get("state").lower()
        mark = "x" if gstate == "met" else " "
        met += gstate == "met"
        print(f"  [{mark}] {g.id} -- {g.title}")
        print(wrap(g.get("criterion"), indent="      "))
        print(wrap(f"check: {g.get('check')}", indent="      "))
        if gstate == "met":
            print(wrap(
                f"evidence: {g.get('evidence') or '(NONE -- this is a problem)'}",
                indent="      ",
            ))
        print()

    su = suite_state()
    if su["total"]:
        bits = [f"{len(su['passing'])} passing"]
        if su["failing"]:
            bits.append(f"{len(su['failing'])} FAILING")
        if su["unrun"]:
            bits.append(f"{len(su['unrun'])} not run")
        if su["waived_ok"]:
            bits.append(f"{len(su['waived_ok'])} waived")
        if su["waived_pending"]:
            bits.append(f"{len(su['waived_pending'])} waiver(s) not countersigned")
        line = "  checks: " + ", ".join(bits)
        if su["stale"]:
            line += "  [STALE -- re-run tools/verify.py]"
        print(line)
        print()

    if criteria:
        all_met = met == len(criteria)
        gate_ok = all_met and su["gate_ok"] and (su["ran"] or su["total"] == 0)
        print(f"  {met}/{len(criteria)} criteria met.")
        if all_met and not gate_ok:
            print(wrap(
                "! Criteria are all met but the completion gate is NOT satisfied -- the "
                "check suite is failing, stale, or unrun. Run 'python3 tools/verify.py'. "
                "Not done until it is green.",
                indent="  ",
            ))
        elif gate_ok:
            print(wrap(
                "All criteria met and the check suite is green. The work is finished -- "
                "stop here rather than looking for more to improve.",
                indent="  ",
            ))
        print()


def show_governance() -> None:
    baseline = load_baseline()
    proposals = load_proposals()
    pending = [p for p in proposals if p.get("status").lower() == "proposed"]
    changed = drift()

    rule()
    print("GOVERNANCE -- " + (
        f"engaged {baseline.updated}" if baseline.exists else "not engaged (intake phase)"
    ))
    rule()

    if not baseline.exists:
        print(wrap(
            "No approved baseline yet, so constraints and the goal condition are still "
            "being written. Once Clara approves the goal condition she runs "
            "'python3 tools/approve.py --baseline' and they stop being yours to edit.",
            indent="  ",
        ))
        print()
    else:
        if not signing_configured():
            print(wrap(
                "Mode: attribution-only. Approvals are identified by commit author. "
                "Real, but forgeable -- see docs/governance.md.",
                indent="  ",
            ))
        else:
            print(wrap("Mode: signed. Approval commits are signature-verified.", indent="  "))
        print()

    if changed:
        print(wrap(
            "! GOVERNED CONTENT DIFFERS FROM WHAT CLARA APPROVED: "
            + ", ".join(sorted(changed))
            + ". If you changed it, revert it and raise a proposal instead. Run "
              "'python3 tools/validate.py' for detail.",
            indent="  ",
        ))
        print()

    if pending:
        print(f"  {len(pending)} proposal(s) awaiting Clara's sign-off -- inert until she approves:")
        print()
        for p in pending:
            print(f"    [{p.id}] {p.title}  ({p.get('kind') or 'unspecified'})")
            print(wrap(f"targets: {p.get('targets') or '-'}", indent="        "))
            print(wrap(f"because: {p.get('because') or '(no explanation -- fix this)'}",
                       indent="        "))
            print()
        print(wrap(
            "Mention these to Clara. Do not act as though any of them were approved.",
            indent="  ",
        ))
        print()
    elif baseline.exists:
        print("  No pending proposals.")
        print()


def show_working_state() -> None:
    """The live working state: current checkpoint and any open blockers.

    The checkpoint is the overwritten "resume here" card; blockers are the fronts that are
    stuck. Both are progress, not governed content. Surfacing them here means the
    re-grounding call always shows where the work stands and what is waiting on Clara.
    """
    checkpoint = current_checkpoint()
    blockers = open_blockers()

    rule()
    print("WORKING STATE -- checkpoint and open blockers")
    rule()

    if checkpoint:
        print("  Checkpoint (progress/checkpoint.md):")
        for line in checkpoint.splitlines():
            print(f"  {line}" if line.strip() else "")
        print()
    else:
        print("  (no checkpoint yet -- write progress/checkpoint.md at the next break)")
        print()

    if blockers:
        print(f"  {len(blockers)} OPEN BLOCKER(S) -- progress/blockers.md:")
        for b in blockers:
            print(f"    [{b.id}] {b.title}")
            if b.get("blocks"):
                print(wrap(f"blocks: {b.get('blocks')}", indent="        "))
            if b.get("needs"):
                print(wrap(f"needs: {b.get('needs')}", indent="        "))
        print()
        print(wrap(
            "Keep working every front that is not blocked. Surface all open blockers to "
            "Clara together only when every front is blocked.",
            indent="  ",
        ))
        print()
    else:
        print("  No open blockers.")
        print()


def show_progress(limit: int = 3) -> None:
    entries = recent_log_entries(limit)
    rule()
    print(f"RECENT PROGRESS -- last {len(entries)} log entr{'y' if len(entries) == 1 else 'ies'}")
    rule()
    if not entries:
        print("  (progress/log.md is empty)")
        print()
        return
    for entry in entries:
        for line in entry.splitlines():
            print(f"  {line}" if line.strip() else "")
        print()


def main(argv: list[str]) -> int:
    if "--goal" in argv:
        show_goal()
        return 0
    if "--rules" in argv:
        show_constraints()
        return 0
    if "--pending" in argv:
        show_governance()
        return 0

    show_constraints()
    show_goal()
    show_governance()
    show_working_state()
    show_progress()
    rule("-")
    print("Full detail: constraints/, goals/, proposals/, progress/log.md.")
    print("Well-formedness and tamper check: python3 tools/validate.py")
    if governance_engaged():
        print("To change a constraint or the goal: write a proposal. Clara approves it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
