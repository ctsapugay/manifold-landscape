"""Parser and governance helpers for the constraint-base file format.

The format is Markdown with a convention:

    ## ID — Short title
    - **field:** value
    - **other:** value that may
      continue on indented lines

Every ``## `` heading starts a section. If the heading looks like ``ID — title`` (an
uppercase-ish id, a dash, a title) the section gets an id. Bullets of the form
``- **key:** value`` become fields. Everything else is prose and is ignored.

Beyond parsing, this module carries the governance layer: which proposals exist, which
have been approved, and whether the governed content still matches the approved baseline.
See docs/governance.md -- in particular the section on what is actually enforced.

Standard library only, by design. No install step.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONSTRAINT_FILES = [
    ROOT / "constraints" / "defaults.md",
    ROOT / "constraints" / "project.md",
]
GOAL_FILE = ROOT / "goals" / "goal-condition.md"
CRITERIA_FILE = ROOT / "goals" / "criteria.md"
OUTCOMES_FILE = ROOT / "goals" / "outcomes.md"
LOG_FILE = ROOT / "progress" / "log.md"
CHECKS_FILE = ROOT / "checks" / "registry.md"
RESULTS_FILE = ROOT / "checks" / "results.json"

PROPOSALS_DIR = ROOT / "proposals"
GOVERNANCE_DIR = ROOT / "governance"
BASELINE_FILE = GOVERNANCE_DIR / "baseline.txt"
APPROVERS_FILE = GOVERNANCE_DIR / "approvers.txt"
ALLOWED_SIGNERS_FILE = GOVERNANCE_DIR / "allowed_signers"

# Tool sources are governed too: a validator the agent can quietly edit is not a check.
# status.py reports progress Clara reads remotely, so faking it would misrepresent
# "done" -- it is governed alongside the enforcement tools.
GOVERNED_TOOLS = (
    "constraint_files.py",
    "validate.py",
    "approve.py",
    "brief.py",
    "status.py",
    "verify.py",
    "board_server.py",
)

APPROVAL_TOKEN_RE = re.compile(r"\bAPPROVED:\s*([Pp]-\d{3,5}(?:\s*,\s*[Pp]-\d{3,5})*|BASELINE)\b")
# Marks an approval the agent executed on Clara's explicitly stated authority.
ON_BEHALF_RE = re.compile(r'ON-BEHALF-OF-CLARA:\s*"?(?P<text>[^"\n]*)"?')
# Clara's countersignature accepting a failing/skipped check. Like a waiver, it only
# takes effect through this commit token, so an un-countersigned check-waiver still binds.
CHECK_WAIVER_RE = re.compile(r"\bWAIVED-CHECK:\s*(CHK-[A-Za-z0-9-]+(?:\s*,\s*CHK-[A-Za-z0-9-]+)*)\b")

# "## C-LOCAL — Development stays local"  /  "## G1 - Something"
HEADING_RE = re.compile(r"^##\s+(?P<rest>.+?)\s*$")
ID_TITLE_RE = re.compile(r"^(?P<id>[A-Z][A-Za-z0-9-]{0,39})\s+[—–-]\s+(?P<title>.+)$")
FIELD_RE = re.compile(r"^-\s+\*\*(?P<key>[a-zA-Z][a-zA-Z0-9 _-]*):\*\*\s*(?P<value>.*)$")
CONTINUATION_RE = re.compile(r"^\s{2,}(?P<value>\S.*)$")
FENCE_RE = re.compile(r"^\s*```")

PLACEHOLDER_MARKERS = (
    "<!-- INTAKE:",
    "_Not yet",
    "_not yet",
    "_..._",
    "_No project constraints defined yet",
)


# ---------------------------------------------------------------- parsing ----


@dataclass
class Section:
    """One ``## `` heading and the fields under it."""

    heading: str
    id: str | None
    title: str
    fields: dict[str, str] = field(default_factory=dict)
    field_lines: dict[str, int] = field(default_factory=dict)
    line: int = 0
    source_file: Path | None = None

    @property
    def label(self) -> str:
        return self.id or self.title

    def get(self, key: str, default: str = "") -> str:
        return self.fields.get(key, default).strip()

    def where(self, key: str | None = None) -> str:
        name = self.source_file.name if self.source_file else "?"
        lineno = self.field_lines.get(key, self.line) if key else self.line
        return f"{name}:{lineno}"


def parse_file(path: Path) -> list[Section]:
    """Return every ``## `` section in ``path``. Missing file -> empty list."""
    if not path.exists():
        return []

    sections: list[Section] = []
    current: Section | None = None
    last_key: str | None = None
    in_fence = False

    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            last_key = None
            continue
        if in_fence:
            continue

        heading = HEADING_RE.match(raw)
        if heading:
            rest = heading.group("rest").strip()
            match = ID_TITLE_RE.match(rest)
            if match:
                current = Section(
                    heading=rest,
                    id=match.group("id"),
                    title=match.group("title").strip(),
                    line=lineno,
                    source_file=path,
                )
            else:
                current = Section(
                    heading=rest, id=None, title=rest, line=lineno, source_file=path
                )
            sections.append(current)
            last_key = None
            continue

        if current is None:
            continue

        fieldmatch = FIELD_RE.match(raw)
        if fieldmatch:
            key = fieldmatch.group("key").strip().lower()
            current.fields[key] = fieldmatch.group("value").strip()
            current.field_lines[key] = lineno
            last_key = key
            continue

        cont = CONTINUATION_RE.match(raw)
        if cont and last_key:
            current.fields[last_key] = (
                current.fields[last_key] + " " + cont.group("value").strip()
            ).strip()
            continue

        if not raw.strip():
            last_key = None

    return sections


def load_constraints() -> list[Section]:
    """Constraints from both files, in file order."""
    out: list[Section] = []
    for path in CONSTRAINT_FILES:
        for section in parse_file(path):
            if section.id and section.id.startswith("C-"):
                out.append(section)
    return out


def load_criteria() -> list[Section]:
    """The measurable criteria (goals/criteria.md). Missing file -> empty.

    Criteria live here, not in goal-condition.md, so the goal condition can stay a short
    stable contract that points to this list rather than repeating it -- the list grows.
    """
    return [s for s in parse_file(CRITERIA_FILE) if s.id and s.id.upper().startswith("G")]


def load_goal() -> tuple[Section | None, list[Section], str]:
    """Return (status section from goal-condition.md, criteria from criteria.md, statement)."""
    sections = parse_file(GOAL_FILE)
    status = next(
        (s for s in sections if s.id is None and s.title.lower() == "status"), None
    )
    return status, load_criteria(), section_text(GOAL_FILE, "statement")


def load_checks() -> list[Section]:
    """Every check in the registry (checks/registry.md). Missing file -> empty.

    Checks are the executable verification suite. They live here, not in the goal
    condition, so a complex project can register many of them without bloating the
    finish line. Each carries a `run:` command that tools/verify.py executes.
    """
    out: list[Section] = []
    for section in parse_file(CHECKS_FILE):
        if section.id and section.id.upper().startswith("CHK"):
            out.append(section)
    return out


def load_proposals() -> list[Section]:
    """Every proposal in proposals/, sorted by id. TEMPLATE.md is ignored."""
    if not PROPOSALS_DIR.exists():
        return []
    out: list[Section] = []
    for path in sorted(PROPOSALS_DIR.glob("*.md")):
        if path.name.upper().startswith("TEMPLATE"):
            continue
        for section in parse_file(path):
            if section.id and section.id.upper().startswith("P-"):
                out.append(section)
    return sorted(out, key=lambda s: s.id or "")


def section_text(path: Path, heading_prefix: str) -> str:
    """Prose under a ``## <heading_prefix>...`` heading, comments stripped."""
    if not path.exists():
        return ""
    collecting = False
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("## "):
            if collecting:
                break
            collecting = raw[3:].strip().lower().startswith(heading_prefix.lower())
            continue
        if collecting:
            stripped = raw.strip()
            if stripped and not stripped.startswith("<!--"):
                out.append(stripped)
    return " ".join(out).strip()


def has_placeholders(path: Path) -> list[tuple[int, str]]:
    """Lines in ``path`` that still carry intake placeholder markers."""
    if not path.exists():
        return []
    found = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for marker in PLACEHOLDER_MARKERS:
            if marker in raw:
                found.append((lineno, raw.strip()))
                break
    return found


def recent_log_entries(limit: int = 3) -> list[str]:
    """The last ``limit`` ``## `` entries of the progress log, newest last."""
    if not LOG_FILE.exists():
        return []
    text = LOG_FILE.read_text(encoding="utf-8")
    if "\n---\n" in text:
        text = text.split("\n---\n", 1)[1]
    chunks: list[str] = []
    current: list[str] = []
    for raw in text.splitlines():
        if raw.startswith("## "):
            if current:
                chunks.append("\n".join(current).strip())
            current = [raw]
        elif current:
            current.append(raw)
    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if c][-limit:]


# ------------------------------------------------------------- governance ----


@dataclass
class Baseline:
    """The approved state, as recorded by tools/approve.py."""

    exists: bool = False
    updated: str = ""
    digests: dict[str, str] = field(default_factory=dict)
    approved: list[str] = field(default_factory=list)


def load_baseline() -> Baseline:
    if not BASELINE_FILE.exists():
        return Baseline(exists=False)
    baseline = Baseline(exists=True)
    for raw in BASELINE_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        key, value = parts[0].lower(), parts[1].strip()
        if key == "updated":
            baseline.updated = value
        elif key == "approved":
            baseline.approved.append(value.upper())
        elif key in ("constraints", "goal", "tools", "trust", "checks"):
            baseline.digests[key] = value
    return baseline


def approved_ids() -> set[str]:
    """Proposal ids the recorded baseline says are approved.

    This is the only thing that makes a waiver take effect. A proposal file that
    claims ``status: approved`` but is absent here counts as NOT approved -- which
    is what makes an unapproved waiver inert without relying on anyone's good
    behaviour. Whether the baseline itself is honest is a separate question that
    validate.py answers against git history.
    """
    return set(load_baseline().approved)


def _norm(text: str) -> str:
    return " ".join(text.split())


def canonical_constraints() -> str:
    """Governed constraint content, in a stable form.

    Includes every field that changes what a rule means or whether it binds.
    """
    lines = []
    for c in load_constraints():
        lines.append(
            "|".join(
                _norm(x)
                for x in (
                    c.id or "",
                    c.title,
                    c.get("source"),
                    c.get("status"),
                    c.get("waived-by"),
                    c.get("rule"),
                    c.get("check"),
                    c.get("why"),
                )
            )
        )
    return "\n".join(lines)


def canonical_goal() -> str:
    """Governed goal content.

    Deliberately excludes each criterion's ``state:`` and ``evidence:``, and the
    goal's own ``state:``. Those change constantly during normal work; the finish
    line itself is what is governed.
    """
    _status, criteria, statement = load_goal()
    lines = [_norm(statement)]
    for g in criteria:
        lines.append(
            "|".join(
                _norm(x)
                for x in (g.id or "", g.title, g.get("criterion"), g.get("check"))
            )
        )
    lines.append(_norm(section_text(GOAL_FILE, "out of scope")))
    # The completion contract is part of the finish line: it defines "done" by reference
    # to the criteria, the checks, and the constraints. Governed so it can't be softened.
    lines.append(_norm(section_text(GOAL_FILE, "what completion requires")))
    # Non-goals are the scope guard -- they stop an agent expanding the project on
    # its own initiative -- so they are governed too, even though they live in
    # outcomes.md rather than goal-condition.md.
    lines.append(_norm(section_text(OUTCOMES_FILE, "non-goals")))
    return "\n".join(lines)


def canonical_tools() -> str:
    """Source of the tools that do the checking."""
    parts = []
    for name in GOVERNED_TOOLS:
        path = ROOT / "tools" / name
        parts.append(f"### {name}\n" + (path.read_text(encoding="utf-8") if path.exists() else ""))
    return "\n".join(parts)


def canonical_trust() -> str:
    """The root-of-trust files: who may approve, and whose signatures verify.

    These files decide whether an approval counts at all, so they are governed
    like everything else. If they were not, an agent could append its own address
    to approvers.txt (attribution mode) or its own key to allowed_signers (signed
    mode) and then approve as itself, with nothing showing as drift. Governing
    them turns that into a visible finding: adding an approver or a signer moves
    this digest, which validate.py reports.

    Comments and blank lines are ignored so reformatting the files is not drift;
    a change to who is trusted is.
    """
    parts = []
    for path in (APPROVERS_FILE, ALLOWED_SIGNERS_FILE):
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        meaningful = "\n".join(
            _norm(line)
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
        parts.append(f"### {path.name}\n{meaningful}")
    return "\n".join(parts)


def canonical_checks() -> str:
    """The check suite's definition -- what must pass for the task to be complete.

    Governs each check's id, title, what it covers, the command it runs, its status,
    and its waiver backing. Deliberately excludes results (pass/fail/output/time),
    which live in checks/results.json and change every run. The suite is governed so
    an agent cannot make verification pass by deleting a failing check or quietly
    rewriting what it runs.
    """
    lines = []
    for c in load_checks():
        lines.append(
            "|".join(
                _norm(x)
                for x in (
                    c.id or "",
                    c.title,
                    c.get("covers"),
                    c.get("run"),
                    c.get("status"),
                    c.get("waived-by"),
                )
            )
        )
    return "\n".join(lines)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def current_digests() -> dict[str, str]:
    return {
        "constraints": digest(canonical_constraints()),
        "goal": digest(canonical_goal()),
        "tools": digest(canonical_tools()),
        "trust": digest(canonical_trust()),
        "checks": digest(canonical_checks()),
    }


def drift() -> dict[str, tuple[str, str]]:
    """Governed areas whose current digest differs from the baseline.

    Returns {area: (baseline_digest, current_digest)}. Empty when clean.
    """
    baseline = load_baseline()
    if not baseline.exists:
        return {}
    current = current_digests()
    out = {}
    for area, want in baseline.digests.items():
        got = current.get(area, "")
        if want != got:
            out[area] = (want, got)
    return out


def governance_engaged() -> bool:
    """Governance binds once Clara has approved a baseline.

    During intake everything is still being written, so there is nothing to protect
    yet. The moment she approves the goal condition and runs ``approve.py --baseline``,
    the standing constraints and the finish line stop being the agent's to edit.
    """
    return load_baseline().exists


# ------------------------------------------------------------------- git -----


def git(*args: str) -> tuple[int, str]:
    """Run a git command in the repo. Returns (returncode, combined output)."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def in_git_repo() -> bool:
    code, out = git("rev-parse", "--is-inside-work-tree")
    return code == 0 and out.strip() == "true"


def approvers() -> list[str]:
    """Email addresses whose commits count as approvals."""
    if not APPROVERS_FILE.exists():
        return []
    out = []
    for raw in APPROVERS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(line.lower())
    return out


def signing_configured() -> bool:
    """True when signature verification is available -- the stronger mode."""
    return ALLOWED_SIGNERS_FILE.exists()


@dataclass
class ApprovalCommit:
    sha: str
    author_email: str
    signature: str  # git's %G? code: G good, U good/untrusted, B bad, N none, E error
    subject: str
    ids: list[str]
    on_behalf: str | None = None  # set when the agent approved on Clara's stated authority

    @property
    def signed_ok(self) -> bool:
        return self.signature in ("G", "U")


def approval_commits() -> list[ApprovalCommit]:
    """Commits whose message carries an ``APPROVED:`` token."""
    if not in_git_repo():
        return []
    sep = "\x1f"
    # Record separator goes FIRST: an empty %b would otherwise leave a ragged tail.
    fmt = f"--format=%x1e%H{sep}%ae{sep}%G?{sep}%s{sep}%b"
    args = ["log", "--no-merges", fmt]
    # %G? only reports a verdict for SSH signatures when the allowed-signers file is
    # configured; without it a validly signed commit shows as 'N'. Pass it so the
    # signed/unsigned distinction validate.py relies on is correct in signed mode.
    if ALLOWED_SIGNERS_FILE.exists():
        args = ["-c", f"gpg.ssh.allowedSignersFile={ALLOWED_SIGNERS_FILE}"] + args
    code, out = git(*args)
    if code != 0:
        return []
    commits: list[ApprovalCommit] = []
    for record in out.split("\x1e"):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split(sep)
        if len(parts) < 4:
            continue
        sha, email, sig, subject = parts[0], parts[1], parts[2], parts[3]
        body = "\n".join(parts[4:])
        ids: list[str] = []
        for match in APPROVAL_TOKEN_RE.finditer(f"{subject}\n{body}"):
            ids.extend(part.strip().upper() for part in match.group(1).split(","))
        if ids:
            on_behalf_match = ON_BEHALF_RE.search(body)
            on_behalf = on_behalf_match.group("text").strip() if on_behalf_match else None
            commits.append(
                ApprovalCommit(
                    sha=sha[:12],
                    author_email=email.lower(),
                    signature=sig or "N",
                    subject=subject,
                    ids=ids,
                    on_behalf=on_behalf,
                )
            )
    return commits


def verify_signature(sha: str) -> tuple[bool, str]:
    """Verify a commit signature against governance/allowed_signers."""
    if not ALLOWED_SIGNERS_FILE.exists():
        return False, "no allowed_signers file"
    code, out = git(
        "-c",
        f"gpg.ssh.allowedSignersFile={ALLOWED_SIGNERS_FILE}",
        "verify-commit",
        "--raw",
        sha,
    )
    return code == 0, out.splitlines()[0] if out else ""


def check_waiver_signoffs() -> set[str]:
    """Check ids Clara has countersigned as waived, from ``WAIVED-CHECK:`` commits.

    This is the analogue of ``approved_ids`` for checks: a check marked ``waived`` in
    the registry only stops blocking completion if its id appears here. An
    un-countersigned waiver has no effect -- the check still has to pass. As with
    approvals, attribution mode makes the countersignature forgeable (an audit trail);
    signing makes it a lock.
    """
    if not in_git_repo():
        return set()
    code, out = git("log", "--no-merges", "--format=%x1e%s%x1f%b")
    if code != 0:
        return set()
    ids: set[str] = set()
    for record in out.split("\x1e"):
        if not record.strip():
            continue
        subject, _, body = record.partition("\x1f")
        for match in CHECK_WAIVER_RE.finditer(f"{subject}\n{body}"):
            ids.update(part.strip().upper() for part in match.group(1).split(","))
    return ids


def load_results() -> dict:
    """The last recorded check run (checks/results.json), or {} if none/unreadable."""
    if not RESULTS_FILE.exists():
        return {}
    try:
        return json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def tree_state() -> str:
    """A fingerprint of the current working tree, for staleness detection.

    Recorded when verify.py runs and recomputed later: if it differs, the code has
    changed since the checks last ran, so their results may no longer hold and verify
    should be re-run. Covers committed state (HEAD) and staged + unstaged content;
    it does not track edits to untracked files. Empty outside a git repo.
    """
    if not in_git_repo():
        return ""
    parts = []
    for args in (("rev-parse", "HEAD"), ("status", "--porcelain"), ("diff",), ("diff", "--cached")):
        _code, out = git(*args)
        parts.append(out)
    return digest("\x1e".join(parts))


def suite_state() -> dict:
    """Read-only summary of the check suite from the last recorded run.

    The single source of truth that verify.py, status.py and validate.py all agree on,
    so the completion gate reads the same everywhere. Computes from the registry, the
    stored results, and the countersignatures -- it does not run anything.
    """
    checks = load_checks()
    results = load_results()
    res = results.get("results", {}) if isinstance(results, dict) else {}
    signoffs = check_waiver_signoffs()

    active = [c for c in checks if c.get("status").lower() != "waived"]
    waived = [c for c in checks if c.get("status").lower() == "waived"]

    passing, failing, unrun = [], [], []
    for c in active:
        r = res.get(c.id)
        if not isinstance(r, dict):
            unrun.append(c.id)
        elif r.get("passed"):
            passing.append(c.id)
        else:
            failing.append(c.id)

    waived_ok = [c.id for c in waived if (c.id or "").upper() in signoffs]
    waived_pending = [c.id for c in waived if (c.id or "").upper() not in signoffs]

    ran = bool(results)
    # Staleness only matters when there are checks whose results could go out of date.
    stale = ran and len(checks) > 0 and results.get("tree_state", "") != tree_state()
    green = not failing and not unrun and not waived_pending

    return {
        "total": len(checks),
        "passing": passing,
        "failing": failing,
        "unrun": unrun,
        "waived_ok": waived_ok,
        "waived_pending": waived_pending,
        "ran": ran,
        "ran_at": results.get("ran_at", "") if isinstance(results, dict) else "",
        "stale": stale,
        # The suite passes its part of the completion gate when it is green AND the
        # results reflect the current tree. Vacuously green when no checks exist.
        "gate_ok": green and not stale,
    }
