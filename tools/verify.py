#!/usr/bin/env python3
"""Run the check suite and record whether the project still verifies.

    python3 tools/verify.py            # run all active checks, record results, report
    python3 tools/verify.py --quiet    # summary and failures only
    python3 tools/verify.py --json     # machine-readable result

This answers the question the goal condition's completion gate asks: is every registered
check passing right now, or waived with Clara's countersignature? A criterion's `state:`
is a claim frozen when it was written; a check is re-run every time this runs, so a
regression that breaks a previously-passing check turns the suite red again. That is the
whole point of separating the two.

Exit 0 only when the suite is GREEN and current: every active check passed this run, and
every waived check is countersigned. Otherwise exit 1. verify.py also stamps the working
tree's fingerprint into the results, so status.py and validate.py can tell you when the
code has changed since the last run and the suite needs re-running.

Checks run through the shell, in the repo root. The registry is governed content, so what
runs is what Clara approved. This is a local-development tool (constraint C-LOCAL) and does
not sandbox commands; keep each `run:` deterministic and offline.

Standard library only.
"""

from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from constraint_files import (  # noqa: E402
    RESULTS_FILE,
    ROOT,
    check_waiver_signoffs,
    git,
    in_git_repo,
    load_checks,
    suite_state,
    tree_state,
)

OUTPUT_CAP = 2000  # keep results.json small; enough to see why a check failed
TIMEOUT = 600      # a single check that hangs should not hang the whole run forever


def _run_one(command: str) -> dict:
    try:
        proc = subprocess.run(
            command, shell=True, cwd=str(ROOT),
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        out = (proc.stdout + proc.stderr).strip()
        return {
            "passed": proc.returncode == 0,
            "exit": proc.returncode,
            "output": out[-OUTPUT_CAP:],
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "exit": None, "output": f"timed out after {TIMEOUT}s"}
    except OSError as exc:
        return {"passed": False, "exit": None, "output": f"could not run: {exc}"}


def run_suite() -> dict:
    checks = load_checks()
    signoffs = check_waiver_signoffs()
    results: dict[str, dict] = {}

    for c in checks:
        if c.get("status").lower() == "waived":
            continue  # waived checks are not run; countersignature is what clears them
        cmd = c.get("run")
        if not cmd:
            results[c.id] = {"passed": False, "exit": None, "output": "no run: command"}
            continue
        r = _run_one(cmd)
        r["ran_at"] = _dt.datetime.now().isoformat(timespec="seconds")
        results[c.id] = r

    payload = {
        "ran_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "head": git("rev-parse", "HEAD")[1] if in_git_repo() else "",
        "tree_state": tree_state(),
        "results": results,
        "waived": {
            c.id: {"countersigned": (c.id or "").upper() in signoffs, "reason": c.get("waived")}
            for c in checks if c.get("status").lower() == "waived"
        },
    }
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv
    as_json = "--json" in argv

    run_suite()
    s = suite_state()  # read back through the shared reader everyone else uses

    if as_json:
        print(json.dumps(s, indent=2))
        return 0 if s["gate_ok"] else 1

    total = s["total"]
    print()
    print(f"CHECK SUITE — {len(s['passing'])}/{len(s['passing']) + len(s['failing']) + len(s['unrun'])} "
          f"active checks passing" + (f", {len(s['waived_ok'])} waived" if s["waived_ok"] else ""))

    if not quiet:
        for cid in s["passing"]:
            print(f"  ok    {cid}")
    for cid in s["failing"]:
        print(f"  FAIL  {cid}")
    for cid in s["unrun"]:
        print(f"  ?     {cid} (did not run)")
    for cid in s["waived_ok"]:
        print(f"  waived {cid} (countersigned)")
    for cid in s["waived_pending"]:
        print(f"  STILL REQUIRED  {cid} (waiver not countersigned — run "
              f"approve.py --waive-check {cid})")

    print()
    if total == 0:
        print("No checks registered. Register the project's checks in checks/registry.md.")
        return 0
    if s["gate_ok"]:
        print("GREEN — every active check passed and every waiver is countersigned.")
        return 0
    print("NOT GREEN — the completion gate is not satisfied.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
