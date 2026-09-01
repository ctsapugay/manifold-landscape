#!/usr/bin/env python3
"""Check that constraints and goals are well-formed, outcome-shaped, and unmodified.

    python3 tools/validate.py            # report; exit 1 only on errors
    python3 tools/validate.py --strict   # exit 1 on warnings too
    python3 tools/validate.py --quiet    # only print problems

Three kinds of finding:

ERRORS are structural or governance failures: missing fields, duplicate ids, a criterion
marked met with no evidence, a waiver with no approval, governed content that no longer
matches what Clara approved.

WARNINGS are heuristics for implementation detail leaking into a rule -- library names,
file paths, pattern names, "use X", step sequences. They are guesses. Read the flagged
line and decide. Do not edit this script to silence one; if a flagged line is genuinely
fine, leave it and say why in progress/log.md. (Note that this script's own source is
part of the governed baseline, so editing it after governance is engaged shows up as
drift.)

NOTES are context.

See docs/outcome-vs-implementation.md and docs/governance.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constraint_files import (  # noqa: E402
    CHECKS_FILE,
    CONSTRAINT_FILES,
    CRITERIA_FILE,
    GOAL_FILE,
    OUTCOMES_FILE,
    ROOT,
    approval_commits,
    approvers,
    approved_ids,
    check_waiver_signoffs,
    drift,
    git,
    governance_engaged,
    has_placeholders,
    in_git_repo,
    load_baseline,
    load_checks,
    load_constraints,
    load_goal,
    load_proposals,
    parse_file,
    signing_configured,
    suite_state,
    verify_signature,
)

CONSTRAINT_REQUIRED = ("source", "status", "rule", "check")
CRITERION_REQUIRED = ("criterion", "check", "state")
PROPOSAL_REQUIRED = ("status", "kind", "targets", "because", "change")
VALID_STATUS = ("active", "waived")
VALID_CRITERION_STATE = ("unmet", "met")
VALID_GOAL_STATE = ("draft", "approved", "met")
VALID_PROPOSAL_STATUS = ("proposed", "approved", "declined", "withdrawn")
VALID_PROPOSAL_KIND = ("waiver", "constraint-change", "goal-change", "new-constraint")

GOVERNED_PATHS = (
    "constraints/defaults.md",
    "constraints/project.md",
    "goals/goal-condition.md",
    "goals/criteria.md",
    "goals/outcomes.md",
    "checks/registry.md",
    "governance/baseline.txt",
    "governance/approvers.txt",
    "governance/allowed_signers",
)

CHECK_REQUIRED = ("run", "status")

# --- outcome-shape heuristics -------------------------------------------------

TECHNOLOGIES = (
    "postgres postgresql mysql sqlite mongodb redis memcached elasticsearch kafka "
    "rabbitmq celery docker kubernetes terraform ansible nginx apache aws azure gcp "
    "s3 lambda dynamodb firebase supabase vercel netlify heroku "
    "react vue angular svelte next.js nextjs nuxt tailwind bootstrap jquery "
    "django flask fastapi rails express nestjs spring laravel "
    "pytest unittest jest mocha vitest cypress playwright selenium "
    "numpy pandas sqlalchemy pydantic requests axios lodash webpack vite babel "
    "graphql grpc rest-api openapi swagger "
    "typescript javascript python java golang rust ruby php kotlin swift "
    "node npm yarn pnpm pip poetry cargo maven gradle"
).split()

PATTERNS = (
    "singleton factory observer decorator adapter facade repository-pattern "
    "microservice monolith mvc mvvm hexagonal event-driven pub-sub cqrs "
    "dependency-injection middleware orm dao dto"
).split()

IMPERATIVE_RE = re.compile(
    r"(?:^|\.\s+|;\s+)(use|add|create|build|implement|refactor|restructure|structure"
    r"|install|import|extend|inherit|wrap|split|merge|rename|move)\b",
    re.IGNORECASE,
)
MODAL_IMPERATIVE_RE = re.compile(
    r"\b(?:must|should|shall|will|needs? to|has to|have to)\s+"
    r"(use|add|create|build|implement|refactor|install|import|extend|wrap)\b",
    re.IGNORECASE,
)
PATH_RE = re.compile(
    r"\b[\w.-]+/[\w./-]+|\b\w+\.(?:py|js|jsx|ts|tsx|go|rs|rb|java|json|ya?ml|toml|ini|cfg)\b"
)
SEQUENCE_RE = re.compile(
    r"\bstep\s*\d|\bfirst,|\bfirstly\b|;\s*then\b"
    r"|(?<!until )\bthen\s+(?:the|it|we|you)\b"
    r"|\bafterwards\b|\bfinally,",
    re.IGNORECASE,
)
COVERAGE_RE = re.compile(
    r"\b\d{1,3}\s*%\s*(?:code\s*)?coverage\b|\bcoverage\s+(?:of|above|at least)\s*\d",
    re.IGNORECASE,
)

TECH_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in TECHNOLOGIES) + r")\b", re.IGNORECASE
)
PATTERN_RE = re.compile(
    r"\b(" + "|".join(re.escape(p).replace(r"\-", "[- ]") for p in PATTERNS) + r")\b"
    r"|\b\w+\s+(?:pattern|architecture)\b",
    re.IGNORECASE,
)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def shape_warnings(text: str, has_why: bool) -> list[str]:
    """Heuristic complaints about a rule or criterion that describes *how*."""
    out: list[str] = []
    if not text:
        return out

    tech = TECH_RE.findall(text)
    if tech and not has_why:
        out.append(
            f"names a technology ({', '.join(sorted(set(t.lower() for t in tech)))}) "
            "without a 'why:' field. If it is imposed from outside, add why: saying who "
            "imposes it. Otherwise rewrite as an outcome."
        )

    pat = [m.group(0).strip() for m in PATTERN_RE.finditer(text)]
    if pat:
        out.append(
            f"names a design pattern ({', '.join(sorted(set(p.lower() for p in pat)))}). "
            "Describe the behaviour it is meant to produce instead."
        )

    if PATH_RE.findall(text):
        out.append("mentions a file or directory path. Rules should not prescribe layout.")

    imp = IMPERATIVE_RE.search(text) or MODAL_IMPERATIVE_RE.search(text)
    if imp:
        out.append(
            f"reads as an instruction ('{imp.group(1).lower()}...'). "
            "State what must be true, not what to do."
        )

    if SEQUENCE_RE.search(text):
        out.append("describes a sequence of steps. A rule holds at all times; it has no order.")

    if COVERAGE_RE.search(text):
        out.append("sets a coverage target. Tie the requirement to observable behaviour instead.")

    return out


# --- structural checks --------------------------------------------------------


def check_constraints(report: Report, approved: set[str]) -> None:
    constraints = load_constraints()
    seen: dict[str, str] = {}

    for path in CONSTRAINT_FILES:
        if not path.exists():
            report.error(path.name, "file is missing")

    unbacked = 0
    for c in constraints:
        where = c.where()
        expected_source = "default" if "defaults.md" in str(c.source_file) else "project"

        for key in CONSTRAINT_REQUIRED:
            if not c.get(key):
                report.error(f"{where} [{c.id}]", f"missing required field '{key}:'")

        if c.id in seen:
            report.error(f"{where} [{c.id}]", f"duplicate id, already used at {seen[c.id]}")
        seen[c.id] = where

        source = c.get("source").lower()
        if source and source != expected_source:
            report.error(
                f"{where} [{c.id}]",
                f"source is '{source}' but it lives in {c.source_file.name} "
                f"(expected '{expected_source}')",
            )

        status = c.get("status").lower()
        if status and status not in VALID_STATUS:
            report.error(
                f"{where} [{c.id}]",
                f"status '{status}' is not one of {', '.join(VALID_STATUS)}",
            )

        if status == "waived":
            backing = c.get("waived-by").upper()
            if not backing:
                report.error(
                    f"{where} [{c.id}]",
                    "waived with no 'waived-by:' proposal. A waiver takes effect only "
                    "through a proposal Clara approved (C-WAIVER-SIGNOFF). This "
                    "constraint is still in force.",
                )
                unbacked += 1
            elif backing not in approved:
                report.error(
                    f"{where} [{c.id}]",
                    f"waived by {backing}, which is not in the approved baseline. "
                    "The waiver has no effect and the constraint is still in force "
                    "(C-WAIVER-SIGNOFF).",
                )
                unbacked += 1
            if not c.get("waived"):
                report.warn(f"{where} [{c.id}]", "waived without a 'waived:' reason")

        if status == "active" and c.get("waived-by"):
            report.warn(
                f"{where} [{c.id}]", "has a 'waived-by:' but status is active"
            )

        rule = c.get("rule")
        if rule and len(rule) < 25:
            report.warn(f"{where} [{c.id}]", "rule is very short; is it specific enough to check?")
        if c.get("check") and len(c.get("check")) < 25:
            report.warn(f"{where} [{c.id}]", "check is very short; could someone else run it?")

        for msg in shape_warnings(rule, has_why=bool(c.get("why"))):
            report.warn(f"{where} [{c.id}] rule", msg)

    effective_waived = [
        c
        for c in constraints
        if c.get("status").lower() == "waived" and c.get("waived-by").upper() in approved
    ]
    report.note(
        f"{len(constraints) - len(effective_waived)} constraints in force, "
        f"{len(effective_waived)} effectively waived."
        + (f" {unbacked} waiver(s) claimed but not approved -- those still bind." if unbacked else "")
    )


def check_goal(report: Report) -> None:
    if not GOAL_FILE.exists():
        report.error(GOAL_FILE.name, "file is missing")
        return

    status, criteria, statement = load_goal()

    if status is None:
        report.error(GOAL_FILE.name, "no '## Status' section")
    else:
        state = status.get("state").lower()
        if state not in VALID_GOAL_STATE:
            report.error(
                status.where("state"),
                f"goal state '{state}' is not one of {', '.join(VALID_GOAL_STATE)}",
            )
        if state == "draft":
            report.note(
                "Goal condition is still a draft. Intake is not finished until Clara "
                "approves it (set state: approved, then run tools/approve.py --baseline)."
            )

    if not statement or statement.lower().startswith("_not yet"):
        report.note("Goal condition has no statement yet.")

    if not criteria:
        report.error(
            CRITERIA_FILE.name,
            "no criteria found (expected sections like '## G1 — ...' in goals/criteria.md)",
        )

    seen: dict[str, str] = {}
    for g in criteria:
        where = g.where()
        for key in CRITERION_REQUIRED:
            if not g.get(key):
                report.error(f"{where} [{g.id}]", f"missing required field '{key}:'")

        if g.id in seen:
            report.error(f"{where} [{g.id}]", f"duplicate id, already used at {seen[g.id]}")
        seen[g.id] = where

        state = g.get("state").lower()
        if state and state not in VALID_CRITERION_STATE:
            report.error(
                f"{where} [{g.id}]",
                f"state '{state}' is not one of {', '.join(VALID_CRITERION_STATE)}",
            )
        if state == "met" and not g.get("evidence"):
            report.error(
                f"{where} [{g.id}]",
                "marked met with no 'evidence:'. A criterion is met only after its "
                "check has been run and observed (constraint C-EVIDENCE).",
            )

        check = g.get("check")
        if check and len(check) < 25:
            report.warn(
                f"{where} [{g.id}]",
                "check is very short. Could a skeptic run it without asking questions?",
            )

        for msg in shape_warnings(g.get("criterion"), has_why=bool(g.get("why"))):
            report.warn(f"{where} [{g.id}] criterion", msg)

    if criteria:
        met = sum(1 for g in criteria if g.get("state").lower() == "met")
        report.note(f"{met}/{len(criteria)} goal criteria met.")
        if len(criteria) > 8:
            report.warn(
                GOAL_FILE.name,
                f"{len(criteria)} criteria. More than about seven tends to mean a task "
                "list rather than a finish line.",
            )


def check_proposals(report: Report, approved: set[str]) -> None:
    proposals = load_proposals()
    seen: dict[str, str] = {}
    pending = 0

    for p in proposals:
        where = p.where()
        for key in PROPOSAL_REQUIRED:
            if not p.get(key):
                report.error(f"{where} [{p.id}]", f"missing required field '{key}:'")

        if p.id in seen:
            report.error(f"{where} [{p.id}]", f"duplicate id, already used at {seen[p.id]}")
        seen[p.id] = where

        status = p.get("status").lower()
        if status and status not in VALID_PROPOSAL_STATUS:
            report.error(
                f"{where} [{p.id}]",
                f"status '{status}' is not one of {', '.join(VALID_PROPOSAL_STATUS)}",
            )
        kind = p.get("kind").lower()
        if kind and kind not in VALID_PROPOSAL_KIND:
            report.warn(
                f"{where} [{p.id}]",
                f"kind '{kind}' is not one of {', '.join(VALID_PROPOSAL_KIND)}",
            )

        if status == "approved" and p.id.upper() not in approved:
            report.error(
                f"{where} [{p.id}]",
                "claims status 'approved' but is not in the approved baseline. A "
                "proposal cannot approve itself -- approval is recorded by "
                "tools/approve.py in an approval commit. Treating this as NOT approved.",
            )
        if status == "proposed":
            pending += 1
            if len(p.get("because")) < 40:
                report.warn(
                    f"{where} [{p.id}]",
                    "'because:' is very thin. A proposal to change a standing "
                    "constraint needs a real explanation.",
                )

    if pending:
        report.note(f"{pending} proposal(s) awaiting Clara's sign-off. See tools/approve.py --status.")


# --- governance ---------------------------------------------------------------


def check_governance(report: Report) -> None:
    baseline = load_baseline()

    if not baseline.exists:
        report.note(
            "Governance not engaged: no approved baseline. Constraints and the goal "
            "condition are still freely editable, which is correct during intake. "
            "Run 'python3 tools/approve.py --baseline' once the goal condition is approved."
        )
        return

    mode = "signed" if signing_configured() else "attribution-only"
    report.note(f"Governance engaged, baseline recorded {baseline.updated} ({mode}).")
    if mode == "attribution-only":
        report.note(
            "Approval is identified by commit author, which anything with repo access "
            "can set. This is an audit trail, not a lock -- see docs/governance.md to "
            "turn on signature verification."
        )

    # 1. Has governed content moved away from what was approved?
    for area, (want, got) in sorted(drift().items()):
        report.error(
            f"governance/{area}",
            f"content no longer matches the approved baseline "
            f"(approved {want[:12]}, current {got[:12]}). Either this was changed "
            "without approval -- revert it -- or Clara approved a change and it has "
            "not been recorded with tools/approve.py.",
        )

    if not in_git_repo():
        report.warn(
            "governance",
            "not a git repository, so approvals cannot be checked against history. "
            "The baseline file is taken at face value.",
        )
        return

    # Was signature verification switched off after having been switched on?
    code, out = git("log", "--diff-filter=A", "--format=%H", "--", "governance/allowed_signers")
    if code == 0 and out.strip() and not signing_configured():
        report.error(
            "governance/allowed_signers",
            "this repository used signature-verified approvals and the allowed_signers "
            "file is now gone. Governance has been downgraded to attribution-only. "
            "Restore it, or record deliberately that you turned it off.",
        )

    commits = approval_commits()
    by_id: dict[str, list] = {}
    for commit in commits:
        for pid in commit.ids:
            by_id.setdefault(pid, []).append(commit)

    allowed = approvers()
    if not allowed:
        report.warn(
            "governance/approvers.txt",
            "no approvers listed, so any author counts. Add Clara's commit email.",
        )

    # 2. Does every recorded approval have a real commit behind it?
    for pid in baseline.approved:
        matches = by_id.get(pid, [])
        if not matches:
            report.error(
                "governance/baseline.txt",
                f"{pid} is recorded as approved but no commit says 'APPROVED: {pid}'. "
                "The baseline was edited by hand.",
            )
            continue
        for commit in matches:
            if allowed and commit.author_email not in allowed:
                report.error(
                    f"governance ({commit.sha})",
                    f"approval of {pid} was committed by {commit.author_email}, who is "
                    "not listed in governance/approvers.txt.",
                )
            if signing_configured():
                if commit.signature == "N":
                    # Was signing already in force when this commit was made?
                    code, _ = git(
                        "cat-file", "-e", f"{commit.sha}:governance/allowed_signers"
                    )
                    if code == 0:
                        report.error(
                            f"governance ({commit.sha})",
                            f"approval of {pid} is unsigned, but signature "
                            "verification was already in force at that commit. An "
                            "approval made outside tools/approve.py, or by something "
                            "without the signing key.",
                        )
                    else:
                        report.warn(
                            f"governance ({commit.sha})",
                            f"approval of {pid} predates signature verification being "
                            "turned on. Re-approve it if you want it verifiable.",
                        )
                else:
                    ok, detail = verify_signature(commit.sha)
                    if not ok:
                        report.error(
                            f"governance ({commit.sha})",
                            f"approval of {pid} has a signature that does not verify "
                            f"against governance/allowed_signers ({detail or 'unverified'}).",
                        )

    # 3. Did the baseline file itself only ever change in approval commits?
    approval_shas = {c.sha for c in commits}
    code, out = git("log", "--format=%H", "--", "governance/baseline.txt")
    if code == 0:
        for sha in [line.strip()[:12] for line in out.splitlines() if line.strip()]:
            if sha not in approval_shas:
                report.error(
                    f"governance ({sha})",
                    "governance/baseline.txt was changed in a commit that carries no "
                    "'APPROVED:' token. The record of what Clara approved was edited "
                    "outside the approval path.",
                )

    # 3b. Which approvals did the agent execute on Clara's stated authority?
    #     These are sanctioned, but they are the path a rogue agent would use, so
    #     surface every one for review rather than letting them blend in.
    delegated = [c for c in commits if c.on_behalf is not None]
    if delegated:
        report.note(
            f"{len(delegated)} approval(s) were AGENT-EXECUTED on Clara's stated "
            "authority (not run by Clara directly). Confirm you authorized each:"
        )
        for c in delegated:
            report.note(f'    {c.sha} {", ".join(c.ids)} -- authority: "{c.on_behalf}"')
        if not signing_configured():
            report.note(
                "    Attribution mode: the authority text is written by the agent, so "
                "these are an audit trail, not proof. Enable signing to make delegated "
                "approval un-forgeable."
            )

    # 4. Uncommitted changes to governed files hide from history entirely.
    code, out = git("status", "--porcelain", "--", *GOVERNED_PATHS)
    if code == 0 and out.strip():
        dirty = ", ".join(
            sorted(
                {
                    line.split(maxsplit=1)[1]
                    for line in out.splitlines()
                    if len(line.split(maxsplit=1)) > 1
                }
            )
        )
        report.warn(
            "governance",
            f"uncommitted changes to governed files ({dirty}). Commit or revert them so "
            "the history reflects the real state.",
        )


def check_malformed_ids(report: Report) -> None:
    """A section that looks like a constraint or criterion but has the wrong id shape.

    The loaders only pick up constraint sections whose id starts with 'C-' and
    criteria whose id starts with 'G'. A typo'd id (e.g. 'LOCAL' or '## G 1') makes
    the section vanish from the binding set / finish line with no other symptom.
    Flag any section that carries a tell-tale field but not a matching id.
    """
    for path in CONSTRAINT_FILES:
        for s in parse_file(path):
            if s.get("rule") and not (s.id and s.id.startswith("C-")):
                report.warn(
                    s.where(),
                    f"section '{s.title}' has a 'rule:' field but its id "
                    f"({s.id or 'none'}) is not a 'C-' constraint id. The loader will "
                    "IGNORE it, so it would bind nothing. Give it an id like 'C-LOCAL'.",
                )
    for s in parse_file(CRITERIA_FILE):
        if s.get("criterion") and not (s.id and s.id.upper().startswith("G")):
            report.warn(
                s.where(),
                f"section '{s.title}' has a 'criterion:' field but its id "
                f"({s.id or 'none'}) is not a 'G' criterion id. The loader will IGNORE "
                "it, so it would not count toward the finish line. Give it an id like 'G2'.",
            )
    for s in parse_file(CHECKS_FILE):
        if s.get("run") and not (s.id and s.id.upper().startswith("CHK")):
            report.warn(
                s.where(),
                f"section '{s.title}' has a 'run:' field but its id ({s.id or 'none'}) "
                "is not a 'CHK' id. verify.py will IGNORE it. Give it an id like 'CHK-001'.",
            )


def check_checks(report: Report) -> None:
    if not CHECKS_FILE.exists():
        return
    checks = load_checks()
    signoffs = check_waiver_signoffs()
    seen: dict[str, str] = {}
    active = waived = 0
    for c in checks:
        where = c.where()
        for key in CHECK_REQUIRED:
            if not c.get(key):
                report.error(f"{where} [{c.id}]", f"missing required field '{key}:'")
        if c.id in seen:
            report.error(f"{where} [{c.id}]", f"duplicate id, already used at {seen[c.id]}")
        seen[c.id] = where

        status = c.get("status").lower()
        if status and status not in ("active", "waived"):
            report.error(f"{where} [{c.id}]", f"status '{status}' is not active or waived")
        if status == "waived":
            waived += 1
            if (c.id or "").upper() not in signoffs:
                report.error(
                    f"{where} [{c.id}]",
                    "waived but not countersigned by Clara. A check waiver takes effect "
                    "only through 'approve.py --waive-check' (a WAIVED-CHECK commit); until "
                    "then this check still has to pass.",
                )
            if not c.get("waived"):
                report.warn(f"{where} [{c.id}]", "waived without a 'waived:' reason")
        else:
            active += 1
    if checks:
        report.note(f"{active} active check(s), {waived} waived.")


def report_completion(report: Report) -> None:
    status, criteria, _ = load_goal()
    goal_state = status.get("state").lower() if status else ""
    real = [g for g in criteria if not g.get("criterion", "").startswith("_Not yet")]
    met = sum(1 for g in real if g.get("state").lower() == "met")
    all_met = bool(real) and met == len(real)

    s = suite_state()
    if s["total"] == 0:
        checks_line = "none registered yet" if CHECKS_FILE.exists() else "no check registry yet"
    else:
        parts = [f"{len(s['passing'])} passing"]
        if s["failing"]:
            parts.append(f"{len(s['failing'])} FAILING")
        if s["unrun"]:
            parts.append(f"{len(s['unrun'])} not run")
        if s["waived_ok"]:
            parts.append(f"{len(s['waived_ok'])} waived")
        if s["waived_pending"]:
            parts.append(f"{len(s['waived_pending'])} waiver(s) NOT countersigned")
        checks_line = ", ".join(parts)
        if s["stale"]:
            checks_line += " — STALE, tree changed since last verify; re-run it"

    report.note(f"Completion gate: criteria {met}/{len(real)} met; checks: {checks_line}.")

    if goal_state != "met":
        return  # not claiming done, so the gate is informational

    reasons = []
    if not all_met:
        reasons.append("not every criterion is met")
    if s["total"] > 0 and not s["ran"]:
        reasons.append("checks have not been run (run tools/verify.py)")
    if s["failing"] or s["unrun"]:
        reasons.append("some checks are failing or did not run")
    if s["waived_pending"]:
        reasons.append("a check waiver is not countersigned")
    if s["stale"]:
        reasons.append("check results are stale — re-run tools/verify.py")
    if reasons:
        report.error(
            "goals/goal-condition.md",
            "goal state is 'met' but the completion gate is not satisfied: "
            + "; ".join(reasons) + ".",
        )
    elif s["total"] == 0:
        report.warn(
            "checks/registry.md",
            "goal marked met with no checks registered. The finish line rested on "
            "criteria evidence alone; register checks if it should be re-verifiable.",
        )


def check_placeholders(report: Report) -> None:
    remaining = []
    for path in (ROOT / "constraints" / "project.md", OUTCOMES_FILE, GOAL_FILE, CRITERIA_FILE):
        hits = has_placeholders(path)
        if hits:
            remaining.append((path, hits))
    if remaining:
        total = sum(len(h) for _, h in remaining)
        report.note(
            f"{total} intake placeholder(s) still present in "
            + ", ".join(p.name for p, _ in remaining)
            + " -- intake has not been completed."
        )


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    quiet = "--quiet" in argv

    report = Report()
    approved = approved_ids()
    check_constraints(report, approved)
    check_goal(report)
    check_proposals(report, approved)
    check_checks(report)
    check_governance(report)
    check_malformed_ids(report)
    report_completion(report)
    check_placeholders(report)

    if report.errors:
        print(f"\nERRORS ({len(report.errors)})")
        for line in report.errors:
            print(f"  x {line}")

    if report.warnings:
        print(f"\nWARNINGS ({len(report.warnings)}) -- heuristics, read and judge")
        for line in report.warnings:
            print(f"  ! {line}")

    if report.notes and not quiet:
        print("\nNOTES")
        for line in report.notes:
            print(f"  - {line}")

    if not report.errors and not report.warnings:
        print("\nOK -- constraints and goal condition are well-formed and unmodified.")
    print()

    if report.errors:
        return 1
    if strict and report.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
