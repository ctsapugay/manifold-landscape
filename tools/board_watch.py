#!/usr/bin/env python3
"""Block until the board's state changes — the change signal for `/board watch`.

    python3 tools/board_watch.py                 # print the current fingerprint and exit
    python3 tools/board_watch.py --once          # wait until the board changes, then exit 0
                                                 #   (exit 2 if --timeout seconds pass first)
    python3 tools/board_watch.py --once --timeout 50 --interval 3

The fingerprint is a hash of status.py's JSON view — criteria states and evidence, the
check suite's results, drift, governance mode, the log count. Anything that would move the
dashboard moves the fingerprint. The `/board watch` loop uses this so the agent re-publishes
the phone Artifact only when something actually changed, not on a blind timer.

This does not run checks or touch any state; it only reads. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import status  # noqa: E402


def fingerprint() -> str:
    blob = json.dumps(status.collect(), sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Wait until the board state changes.")
    ap.add_argument("--once", action="store_true", help="wait for one change, then exit")
    ap.add_argument("--timeout", type=float, default=50.0, help="give up after N seconds")
    ap.add_argument("--interval", type=float, default=3.0, help="poll every N seconds")
    args = ap.parse_args(argv)

    start = fingerprint()
    if not args.once:
        print(start)
        return 0

    deadline = time.time() + args.timeout
    while time.time() < deadline:
        time.sleep(args.interval)
        if fingerprint() != start:
            print("changed")
            return 0
    print("timeout")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
