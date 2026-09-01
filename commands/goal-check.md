---
description: Test each goal criterion against reality and update its state and evidence
---

Run `python3 tools/brief.py --goal`.

For each criterion, actually run its `check:`. Not a mental simulation, not an inference
from the code — run the command, open the thing, trigger the behaviour, and observe the
result. This is constraint C-EVIDENCE and it is the one most easily fudged.

Then update the criterion in `goals/criteria.md`:

- Criterion passed → `state: met`, and fill `evidence:` with what you ran and what it
  output, with today's date.
- Criterion failed → leave it `unmet` and say what specifically fell short.
- Check could not be run → say why. Do not mark it met.

Update `state:` and `evidence:` only. The criterion text and its check are governed —
if a criterion turns out to be unmeetable or wrongly worded, that is a proposal
(`commands/propose.md`), not an edit. Rewording a criterion so the work passes is the
exact failure this system exists to prevent.

Then run the executable suite: `python3 tools/verify.py`. The goal condition's completion
contract requires it to be green (every check passing, or waived with Clara's
countersignature) on top of every criterion being met — a met criterion whose check later
regresses will show up here.

Run `python3 tools/validate.py` afterwards. It will flag any drift in the governed goal
condition, criteria, or checks.

Report: how many criteria are met, whether `verify.py` is green, what is left, and the
next step.

The goal condition is satisfied only when every criterion is met with real evidence **and**
`verify.py` is green. Then say so and stop — do not start improving things that are out of
scope for done.
