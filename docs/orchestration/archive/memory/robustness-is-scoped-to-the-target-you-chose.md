---
name: robustness-is-scoped-to-the-target-you-chose
description: "A test property like \"this cannot return an uninformative null\" only holds inside the target you picked — it says nothing about whether the target is right"
metadata:
  type: feedback
---

The runtime loop widened a memory diff specifically so it could not return a bare null, and
counted that as protection. The field it was diffing (`+0x175`) turned out to be *derived* — only
rewritten when an assembler routine re-runs — so a training-menu press that correctly updated the
real source bytes would leave it untouched. A clean, stable, unambiguous reading was the expected
observation under the very hypothesis being tested. The wider net was still around the wrong field.

**Why:** properties like "cannot return a bare null", "has a positive control", "pre-registered",
"3/3 reproducible" are all *internal* to a chosen target and readout. None of them is evidence the
target is the thing the mechanism actually writes. Worse, they feel like general rigour, so they
displace the one question that would have caught it.

**How to apply:** before running a measurement, ask what writes the field you are about to read —
by name and address, from the instruction stream — and whether the value is stored or derived. A
derived value changes only when its producer runs, so the timing of the producer is part of the
experiment. Then ask the pair of questions together: *what would this readout look like if my
hypothesis is false, and what would it look like if it is true but the field is derived?* If those
two look the same, the target is wrong, however robust the readout is.

Corollary for shared-address targets: a breakpoint on an overlay address can fire on whatever code
later occupies it. Verify the instruction bytes at the stop, not just that the stop happened.

Related: [[verification-must-not-agree-with-itself]], [[prediction-must-be-single-mechanism]],
[[clean-evidence-skips-the-check]], [[negative-control-needs-the-stimulus-first]].
