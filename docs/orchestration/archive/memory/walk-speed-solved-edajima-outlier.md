---
name: walk-speed-solved-edajima-outlier
description: "JUS walk speed IS solved (chr_b statC, threshold-based); Edajima outlier explained by innate passive, not statC"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6d7aafe0-df0d-47b9-bff3-f694adbdd4a3
---

Walk speed storage is SOLVED per DJ (2026-07-01): chr_b.bin `statC` field, threshold/tier-based (not linear). Testing sessions comparing characters aligned with expectations.

**Edajima** (heaviest, slowest-moving character) is the known outlier: his statC is a normal value, but an **innate character passive** slows him — this confounded earlier analysis and drove the false "NOT in chr_b.bin" conclusion recorded in docs/research/Research-Status.md (which still wrongly lists walk speed as UNKNOWN). AI-ASSISTANT-GUIDE.md's "SOLVED MYSTERIES" entry is the correct one.

Still open (JUS-n3p): exact threshold values / number of tiers — mechanism known, boundaries not.

**Why:** Research-Status.md contradicts the guide on this; the guide wins. Prevents re-investigating a solved mystery or "reconciling" in the wrong direction.

**How to apply:** When cleaning docs, update Research-Status.md walk-speed section to CONFIRMED (statC + Edajima passive caveat), and treat passive effects as a confounder class in future stat-vs-behavior tests. See [[character-mapping-completeness]].
