---
name: a-correction-is-a-claim
description: A retraction offered against the author's own interest gets less scrutiny than the claim it replaces — check a narrowing against the artifact, not the summary
metadata:
  type: feedback
---

When someone volunteers a correction that makes their own earlier work look worse, it reads as
conscientious and therefore gets waved through. That is backwards: the correction is itself a
claim, and it can be wrong in the direction of excessive modesty.

Worked example, 2026-08-19: the static loop told me their register-offset scanner had only ever
covered ov6, narrowing their own accurate "zero candidates anywhere" to something weaker. I
thanked them and recorded the weaker version. It was wrong — `regions()` listed arm9 first, and
`git log` showed the file had exactly ONE commit, so arm9 was covered from the start. They had
narrowed their own correct claim against their MEMORY of the tool without opening it. The real
cause was a documentation mismatch: the commit message said "in ov6" while the code it committed
scanned arm9 first.

**Why:** this is the inverse of refusing to demote a finding because someone's summary conflicts
with it. Here the conflicting summary was the author's own, and authorship makes a claim feel like
knowledge. Politeness compounds it — challenging a self-critical retraction feels like refusing an
apology. See [[verification-must-not-agree-with-itself]] and
[[negative-control-needs-the-stimulus-first]]; same family, different entry point.

**How to apply:** when a peer retracts or narrows something, ask which tool or artifact established
the original, then check THAT — the code, the commit, the raw log — not the description of it. When
retracting my own work, name the artifact and re-run it rather than reasoning from what I remember
the tool doing. Treat a tool's prose description as a claim about the tool, never as the tool.
