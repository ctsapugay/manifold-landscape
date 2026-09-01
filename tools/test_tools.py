#!/usr/bin/env python3
"""Tests for the constraint-base tools.

    python3 tools/test_tools.py            # run them
    python3 -m unittest tools.test_tools   # or this

The whole value of this repo is that validate.py correctly detects a weakened
constraint, a hand-edited baseline, a forged-looking approval, and a smuggled
implementation detail. If that detection silently breaks, nothing else here is worth
anything. These tests are the guard on the guard.

Two layers:
  * pure-function unit tests (parsing, digests, shape heuristics) -- fast, no git;
  * integration tests that scaffold a throwaway repo, run the real tools as
    subprocesses, and assert on exit codes and output -- the behaviour that matters.

Standard library only.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))

import constraint_files as cf  # noqa: E402
import validate as vd  # noqa: E402


# --------------------------------------------------------------- unit tests ----


class ParserTests(unittest.TestCase):
    def _parse(self, text: str):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write(text)
            path = Path(fh.name)
        self.addCleanup(path.unlink)
        return cf.parse_file(path)

    def test_fields_and_id_title(self):
        [sec] = self._parse("## C-X — A title\n- **rule:** stays true\n")
        self.assertEqual(sec.id, "C-X")
        self.assertEqual(sec.title, "A title")
        self.assertEqual(sec.get("rule"), "stays true")

    def test_continuation_lines_join(self):
        [sec] = self._parse("## C-X — T\n- **rule:** one\n  two\n  three\n")
        self.assertEqual(sec.get("rule"), "one two three")

    def test_code_fence_is_ignored(self):
        secs = self._parse(
            "## C-X — T\n- **rule:** real\n\n```\n## C-Y — fake\n- **rule:** nope\n```\n"
        )
        self.assertEqual([s.id for s in secs], ["C-X"])

    def test_prose_heading_gets_no_id(self):
        [sec] = self._parse("## Entry format\nsome prose\n")
        self.assertIsNone(sec.id)

    def test_load_constraints_filters_to_c_prefix(self):
        secs = self._parse(
            "## C-A — a\n- **rule:** r\n## NOTE — n\n- **rule:** r\n## G1 — g\n- **rule:** r\n"
        )
        # parse_file returns all three; load_constraints would keep only C-.
        kept = [s for s in secs if s.id and s.id.startswith("C-")]
        self.assertEqual([s.id for s in kept], ["C-A"])


class ShapeHeuristicTests(unittest.TestCase):
    def test_technology_without_why_flagged(self):
        self.assertTrue(vd.shape_warnings("Store data in PostgreSQL.", has_why=False))

    def test_technology_with_why_not_flagged(self):
        # A technology named with a why: is the sanctioned exception.
        msgs = vd.shape_warnings("Must run on Node 18.", has_why=True)
        self.assertFalse([m for m in msgs if "technology" in m])

    def test_path_flagged(self):
        self.assertTrue(
            any("path" in m for m in vd.shape_warnings("Put routes in src/api/.", False))
        )

    def test_imperative_flagged(self):
        self.assertTrue(
            any("instruction" in m for m in vd.shape_warnings("Use a retry decorator.", False))
        )

    def test_pattern_flagged(self):
        self.assertTrue(
            any("pattern" in m for m in vd.shape_warnings("Apply the singleton pattern.", False))
        )

    def test_sequence_flagged(self):
        self.assertTrue(
            any("sequence" in m for m in vd.shape_warnings("First, parse; then, the writer runs.", False))
        )

    def test_outcome_shaped_line_is_clean(self):
        clean = "Data written by one run is readable by the next and survives a restart."
        self.assertEqual(vd.shape_warnings(clean, has_why=False), [])


class DashboardTests(unittest.TestCase):
    def test_body_and_head_split(self):
        import status
        s = status.collect()
        self.assertIn("<style>", status.page_head())
        body = status.render_body(s)
        self.assertTrue(body.strip().startswith("<main"))
        self.assertNotIn("<style>", body)  # styles belong to the head, not the fragment

    def test_full_page_has_root_and_poll(self):
        import board_server
        page = board_server.full_page()
        self.assertIn('id="root"', page)
        self.assertIn("/fragment", page)  # the polling endpoint the browser hits


class DigestAndRegexTests(unittest.TestCase):
    def test_digest_is_deterministic(self):
        self.assertEqual(cf.digest("abc"), cf.digest("abc"))
        self.assertNotEqual(cf.digest("abc"), cf.digest("abd"))

    def test_approval_token_variants(self):
        find = lambda s: cf.APPROVAL_TOKEN_RE.findall(s)  # noqa: E731
        self.assertEqual(find("APPROVED: P-0001"), ["P-0001"])
        self.assertEqual(find("APPROVED: BASELINE"), ["BASELINE"])
        self.assertTrue(cf.APPROVAL_TOKEN_RE.search("APPROVED: P-0001, P-0002"))

    def test_on_behalf_regex(self):
        m = cf.ON_BEHALF_RE.search('ON-BEHALF-OF-CLARA: "yes do it"')
        self.assertEqual(m.group("text"), "yes do it")


# -------------------------------------------------------- integration tests ----

DEFAULTS = """\
# Default constraints

## C-LOCAL — Development stays local
- **source:** default
- **status:** active
- **rule:** Nothing leaves this machine unless Clara says so explicitly in the session.
- **check:** Every outward command appears in progress/log.md next to her approval.

## C-EVIDENCE — Completion claims carry evidence
- **source:** default
- **status:** active
- **rule:** Nothing is reported done on reasoning alone; the check must have been run.
- **check:** Each completion claim names the check that was run and what it printed.
"""

PROJECT = """\
# Project constraints

_No project constraints defined yet._
"""

GOAL = """\
# Goal condition

## Status
- **state:** approved
- **approved:** by test

## Statement

The tool prints the current date when run.

## What completion requires

Complete only when every criterion in goals/criteria.md is met, tools/verify.py is green,
and every constraint in constraints/ held throughout.

## Out of scope for "done"

- Time zones other than local.
"""

CRITERIA_MD = """\
# Criteria

## G1 — Prints a date
- **criterion:** Running the tool prints today's date in ISO form.
- **check:** Run the tool and confirm the printed date matches the system date exactly.
- **state:** unmet
- **evidence:**
"""

OUTCOMES = """\
# Outcomes

## Problem

Dates are typed by hand.

## Outcomes

1. The date is printed automatically.

## Non-goals

- Parsing dates from arbitrary text.

## Open questions

- None.
"""

LOG = "# Progress log\n\n---\n\n## 2020-01-01 — Created\n\n- Scaffolded.\n"

CHECKS = """\
# Check registry

## CHK-001 — trivially true
- **run:** true
- **status:** active

## CHK-002 — goal file exists
- **run:** test -f goals/goal-condition.md
- **status:** active
"""

GITIGNORE = "checks/results.json\n"


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="cbase-test-"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self._scaffold()

    # -- helpers --

    def _write(self, rel: str, text: str):
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def _scaffold(self):
        self._write("constraints/defaults.md", DEFAULTS)
        self._write("constraints/project.md", PROJECT)
        self._write("goals/goal-condition.md", GOAL)
        self._write("goals/criteria.md", CRITERIA_MD)
        self._write("goals/outcomes.md", OUTCOMES)
        self._write("checks/registry.md", CHECKS)
        self._write(".gitignore", GITIGNORE)
        self._write("governance/approvers.txt", "test@example.com\n")
        self._write("progress/log.md", LOG)
        (self.dir / "proposals").mkdir(parents=True, exist_ok=True)
        (self.dir / "tools").mkdir(parents=True, exist_ok=True)
        for name in ("constraint_files.py", "validate.py", "approve.py", "brief.py",
                     "status.py", "verify.py", "board_server.py"):
            shutil.copy(TOOLS_DIR / name, self.dir / "tools" / name)
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "scaffold")

    def _git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.dir), *args],
            capture_output=True, text=True,
        )

    def _run(self, tool: str, *args):
        env = dict(os.environ, GIT_AUTHOR_EMAIL="test@example.com",
                   GIT_COMMITTER_EMAIL="test@example.com")
        return subprocess.run(
            [sys.executable, str(self.dir / "tools" / tool), *args],
            capture_output=True, text=True, cwd=str(self.dir), env=env,
        )

    def _baseline(self):
        # No tty in a subprocess, so approve via the delegated path.
        r = self._run("approve.py", "--baseline", "--on-behalf-of-clara", "approve baseline")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self._git("add", "-A")  # sweep in anything the tool left uncommitted
        self._git("commit", "-q", "-m", "post-baseline tidy")
        return r

    # -- tests --

    def test_clean_repo_validates(self):
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unapproved_waiver_still_binds(self):
        self._write("constraints/project.md", PROJECT + textwrap.dedent("""\
            ## C-EXTRA — Waived without approval
            - **source:** project
            - **status:** waived
            - **rule:** This constraint would be off if the waiver were real.
            - **check:** N/A for the test.
            - **waived:** because the test says so
            - **waived-by:** P-9999
            """))
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("still in force", r.stdout)
        # brief must list it among the binding rules, not the waived ones.
        b = self._run("brief.py", "--rules")
        self.assertIn("WAIVER PENDING", b.stdout)

    def test_baseline_then_clean(self):
        self._baseline()
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Governance engaged", r.stdout)

    def test_delegated_approval_is_flagged(self):
        self._baseline()
        r = self._run("validate.py")
        self.assertIn("AGENT-EXECUTED", r.stdout)
        # and the authority text was recorded in the commit body
        log = self._git("log", "--format=%B").stdout
        self.assertIn("ON-BEHALF-OF-CLARA", log)

    def test_constraint_edit_is_drift(self):
        self._baseline()
        self._write("constraints/defaults.md", DEFAULTS.replace("Nothing leaves", "Anything may leave"))
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no longer matches the approved baseline", r.stdout)

    def test_adding_an_approver_is_drift(self):
        # Weakness 2: the trust root is governed now.
        self._baseline()
        (self.dir / "governance/approvers.txt").write_text(
            "test@example.com\nattacker@evil.example\n", encoding="utf-8"
        )
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("trust", r.stdout)

    def test_nongoal_edit_is_drift(self):
        # Weakness 5: non-goals in outcomes.md are governed.
        self._baseline()
        self._write("goals/outcomes.md", OUTCOMES.replace(
            "Parsing dates from arbitrary text.", "Nothing is out of scope."
        ))
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("goal", r.stdout)

    def test_handedited_baseline_is_caught(self):
        self._baseline()
        bp = self.dir / "governance/baseline.txt"
        bp.write_text(bp.read_text() + "approved P-0002\n", encoding="utf-8")
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("edited by hand", r.stdout)

    def test_malformed_constraint_id_warns(self):
        # Minor: a rule: under a non-C- id would be silently ignored by the loader.
        self._write("constraints/project.md", PROJECT + textwrap.dedent("""\
            ## LOCAL — Missing the C- prefix
            - **source:** project
            - **status:** active
            - **rule:** This looks like a constraint but the loader will drop it.
            - **check:** N/A for the test.
            """))
        r = self._run("validate.py")
        self.assertIn("IGNORE", r.stdout)

    # -- checks layer --

    def test_verify_green_when_checks_pass(self):
        r = self._run("verify.py")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("GREEN", r.stdout)
        self.assertTrue((self.dir / "checks/results.json").exists())

    def test_failing_check_blocks_verify(self):
        self._write("checks/registry.md", CHECKS + textwrap.dedent("""\
            ## CHK-003 — always fails
            - **run:** false
            - **status:** active
            """))
        r = self._run("verify.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", r.stdout)
        self.assertIn("CHK-003", r.stdout)

    def test_registry_change_is_drift(self):
        self._baseline()
        self._write("checks/registry.md", CHECKS.replace("test -f goals/goal-condition.md", "true"))
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("checks", r.stdout)

    def test_waived_check_needs_countersign(self):
        # Mark CHK-002 waived by hand — no countersign yet: still required.
        self._write("checks/registry.md", CHECKS.replace(
            "## CHK-002 — goal file exists\n- **run:** test -f goals/goal-condition.md\n- **status:** active\n",
            "## CHK-002 — goal file exists\n- **run:** test -f goals/goal-condition.md\n"
            "- **status:** waived\n- **waived:** not needed for the test\n",
        ))
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not countersigned", r.stdout)
        # Now countersign it, and the error clears.
        r2 = self._run("approve.py", "--waive-check", "CHK-002", "not needed for the test",
                       "--on-behalf-of-clara", "ok")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self._git("add", "-A"); self._git("commit", "-q", "-m", "tidy")
        r3 = self._run("validate.py")
        self.assertNotIn("not countersigned", r3.stdout)

    def test_signed_approval_verifies(self):
        # Signing mode: a signed approval must validate, not be flagged unsigned.
        # Guards the %G? / allowed-signers wiring in approval_commits.
        keydir = Path(tempfile.mkdtemp(prefix="cbase-key-"))
        self.addCleanup(shutil.rmtree, keydir, ignore_errors=True)
        key = keydir / "id"  # kept OUTSIDE the repo so the private key isn't committed
        kg = subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(key), "-q", "-C", "test"],
            capture_output=True, text=True,
        )
        if kg.returncode != 0:
            self.skipTest("ssh-keygen unavailable")
        pub = (keydir / "id.pub").read_text().strip()
        self._write("governance/allowed_signers", f"test@example.com {pub}\n")
        self._git("config", "gpg.format", "ssh")
        self._git("config", "user.signingkey", str(keydir / "id.pub"))
        self._git("config", "gpg.ssh.allowedSignersFile",
                  str(self.dir / "governance/allowed_signers"))
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "enable signing")

        self.assertEqual(
            self._run("approve.py", "--baseline", "--on-behalf-of-clara", "ok").returncode, 0)
        self._write("proposals/P-0001-x.md", textwrap.dedent("""\
            ## P-0001 — test waiver
            - **status:** proposed
            - **kind:** waiver
            - **targets:** C-EVIDENCE
            - **because:** A long enough explanation so approve.py accepts it in this test.
            - **change:** Would waive C-EVIDENCE; not actually applied here.
            - **risk:** Only here to exercise a signed approval commit.
            - **approved:**
            """))
        r = self._run("approve.py", "P-0001", "--on-behalf-of-clara", "ok")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        v = self._run("validate.py")
        self.assertNotIn("unsigned", v.stdout)
        self.assertEqual(v.returncode, 0, v.stdout)
        self.assertIn("signed", v.stdout)

    def test_completion_gate_blocks_met_goal(self):
        # Goal claimed met and its one criterion has evidence, but the checks were
        # never run -> the completion gate errors.
        self._write("goals/goal-condition.md", GOAL.replace("- **state:** approved",
                                                             "- **state:** met"))
        self._write("goals/criteria.md", CRITERIA_MD.replace(
            "- **state:** unmet\n- **evidence:**",
            "- **state:** met\n- **evidence:** 2020-01-02 ran it, ok",
        ))
        r = self._run("validate.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("completion gate is not satisfied", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
