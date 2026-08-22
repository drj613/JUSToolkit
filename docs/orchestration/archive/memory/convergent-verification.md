---
name: convergent-verification
description: "Two tools agreeing from different representations (relative vs absolute, displacement vs address) is the strongest confirmation — seek this pattern for load-bearing claims"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a920b433-d98e-437c-9c25-49d3b62b62fc
  modified: 2026-08-18T12:44:35.941Z
---

When two independent tools or methods land on the same value from different representations, that's the strongest form of confirmation. Example: Codex decoded EB00034E as a relative branch to A + 0xD40, while query.py reported the absolute target 0x0215305C — and 0x0215231C + 0xD40 = 0x0215305C exactly.

**Why:** Neither tool knows what the other computed. One thinks in displacements, one in absolute addresses. Agreement across representations can't be a shared bias — it's a genuine convergence.

**How to apply:** For load-bearing decodes or address claims, actively seek a second method that uses a different representation. If both agree, the claim is solid. If they disagree, one of them is wrong and the discrepancy tells you which. This is better than running the same tool twice or having a checker confirm from the same angle.

Related: [[codex-cross-checks]]
