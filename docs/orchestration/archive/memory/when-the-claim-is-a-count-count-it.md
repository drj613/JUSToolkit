---
name: when-the-claim-is-a-count-count-it
description: "Both JUS loops shipped a wrong summary of data they had already captured — glancing at your own output instead of querying it is the cheapest error class here"
metadata:
  type: feedback
---

Two instances in one session (2026-08-19), one per loop, both on already-captured data:

- I reported the jpower base-2 partner split as "20 with damage2=40, 3 with damage3=40". It is
  18 / 4 / 1. The odd entry (idx 199, `damage2=90`) was printed in **my own script output** and I
  eyeballed the split instead of counting it. The corrected version was the stronger claim —
  23/23 paired, an invariant rather than a tendency — so the miscount undersold my own finding.
- The runtime loop wrote "bases 8, 7 and 2 all agree with proportional" as supporting evidence.
  Base 8's margin between the competing models is exactly **zero** — one subtraction away from
  data it already had. It was reciting the coincidence the retracted reading had rested on.

**Why:** neither needed new evidence, a tool, or a second opinion. Both were summaries of output
already on screen. This is distinct from [[clean-evidence-skips-the-check]] — there the *evidence*
looked tidy; here the evidence was fine and the **summary of it** was never checked against it.
It is also the cheapest error class in this project to fix: one line of code, no partner, no run.

**How to apply:** when a claim is a count, count it. When a claim is a margin, compute it. When a
claim is "all" or "never", assert it programmatically over the whole set rather than over the rows
you happened to read. A glance at your own output is not a query, and confidence in it is
unearned in exactly the way that feels safest.

Related: [[clean-evidence-skips-the-check]], [[convergent-verification]],
[[record-points-one-representation-away]].
