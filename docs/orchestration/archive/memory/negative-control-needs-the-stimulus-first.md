---
name: negative-control-needs-the-stimulus-first
description: A control whose PASS condition is "no effect" passes trivially when the stimulus never arrived — establish the stimulus lands before suppressing it
metadata:
  type: feedback
---

When a positive control's success looks like **absence** (damage goes to zero, the effect stops,
the value never changes), it cannot tell "the mechanism worked" from "my stimulus never landed."
Order fixes it: prove the stimulus lands FIRST, then suppress it, then restore and show it comes
back.

Worked example, 2026-08-19: my JUS auto-guard control set ability bit 4 on the opponent and *then*
walked into attack range. With bit 4 set the target was immune, so the range-finder could never
detect a hit, and the control printed "control PASSES: bit 4 drives damage to zero" on a run where
`x=None` — it never connected once. The reordered version finds range clean, lands hits, sets bit 4,
then clears it and requires damage to RETURN.

**Why:** this is a third variant of the family in [[verification-must-not-agree-with-itself]] and
[[taint-rules-can-over-apply]] — one accepts something false, one discards something true, this one
manufactures a pass out of a failed setup. All three are invisible because none produces an error.
A null result is only evidence if the same rig demonstrably produces a non-null one.

**How to apply:** write suppression controls as a triple — baseline, suppressed, restored — and make
the restore step a hard requirement, not a nicety. If the baseline can't be established, report
"never connected", not "passed". Prefer a control that fails loudly when the stimulus is absent over
one that reports the outcome you were hoping for.
