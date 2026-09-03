#!/usr/bin/env python3
"""CHK — agentic, tool-orchestrated solving (criterion G3).

Confirms, from the recorded agent trace, that solving is genuinely agentic:

  * the agent CHOOSES and SEQUENCES tool calls in response to the input — different inputs
    drive different tool sequences (not one fixed pipeline);
  * every displayed mathematical value came from a tool call (each successful solve records
    engine provenance and a passing verification), and none is unlabelled model-derived.

Runs the offline brain (no network — C-LOCAL). Backs criterion G3.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent import build_agent  # noqa: E402

# a spread of inputs that SHOULD drive distinct tool sequences
INPUTS = [
    "f = x^2 - y^2",
    "minimize x^2 + y^2 subject to x + y = 1",
    "F = (-y, x)",
    "[[2,1],[1,2]]",
    "show me an example of chaos",
    "minimize x^2 + 3y^2 starting at (3,2)",
]


def main() -> int:
    errs = []
    sequences = []
    for text in INPUTS:
        agent = build_agent(force="offline")
        r = agent.run(text)
        seq = r.trace["tool_sequence"]
        sequences.append(tuple(seq))
        if r.declined or not seq:
            errs.append(f"{text!r}: no tools were orchestrated")
            continue
        # every successful solve call must carry engine provenance and be verified
        for call in r.trace["calls"]:
            if not call["ok"] or not call["produced"]:
                continue
            if not call["verified"]:
                errs.append(f"{text!r}: tool {call['tool']} produced an unverified value")
            for prov in call["provenance"]:
                if not prov or prov == "model":
                    errs.append(f"{text!r}: tool {call['tool']} value had no engine provenance")
        if r.model_derived:
            errs.append(f"{text!r}: displayed an unlabelled model-derived value")
        print(f"  ok    {text[:44]:46} → {seq}")

    # different inputs must drive different tool sequences (not a fixed pipeline)
    distinct = len(set(sequences))
    print(f"\n{distinct} distinct tool sequences across {len(INPUTS)} inputs")
    if distinct < 4:
        errs.append(f"only {distinct} distinct tool sequences — looks like a fixed pipeline")

    if errs:
        for e in errs:
            print(f"  FAIL  {e}")
        print(f"\nNOT AGENTIC — {len(errs)} issue(s).")
        return 1
    print("AGENTIC — the agent chose and sequenced tools from the input; every value tool-produced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
