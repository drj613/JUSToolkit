---
name: self-authored-prompts-are-unreviewed
description: Addressing detail belongs in a bead, not in the wake prompt you write for yourself — a self-authored prompt is unreviewed by construction
metadata:
  type: feedback
---

Never carry addresses, registers, or deref chains in the `/loop` prompt you write for your
own next wake. Put them in a bead. The runtime loop's own prompt told next-wake-them to
read the scratch via `r5` with the object in `r0`; the correct register was `r4`, and both
of their choices were wrong at the sites they were about to break on.

**Why:** next-wake-you trusts the prompt without re-deriving it, and nobody else ever sees
it. A bead is visible to the partner, so a wrong register gets corrected before it becomes
four confident void measurements. Their case was the dangerous kind — no HP signal would
have revealed the reads were nonsense, unlike the earlier version of the same bug that got
caught because the numbers looked wrong.

**How to apply:** the prompt carries role, discipline, and pointers. Anything falsifiable
goes in the ledger. Same failure shape as [[record-check-spans-branches]] and the
superseded-table rule: stale instructions that look authoritative because you wrote them.
Related: [[verification-must-not-agree-with-itself]], [[convergent-verification]].
