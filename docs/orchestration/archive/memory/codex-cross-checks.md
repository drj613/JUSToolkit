---
name: codex-cross-checks
description: Owner wants Codex used for cross-checking load-bearing arithmetic/encoding claims — spreads usage across subscriptions
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0808c5dd-b8f4-4066-a3c4-01ed6013065c
  modified: 2026-08-18T23:05:26.524Z
---

Use Codex cross-checks for validating load-bearing arithmetic and ARM encoding claims in RE work. The owner specifically wants this to spread usage across multiple subscriptions.

**Why:** Codex independently re-derived 7 of atlas's ARM encoding claims and caught a real gap — cheap and effective validation. Also distributes API costs.

**How to apply:** When a session produces arithmetic formulas, struct-size inferences, or instruction-encoding claims that downstream work depends on, run them through Codex for independent verification before treating them as ground truth. If Codex is erroring out, note it and retry later — don't skip.

**The owner has observed this being under-used, repeatedly.** Treat it as a default step, not an option. It also applies to *verification designs*, not just arithmetic: the most expensive bug of 2026-08-18 was a pixel check that compared against a reference captured in the very state it was meant to detect, and a second opinion on the check's design would have cost minutes and saved two sessions of contaminated measurements. See [[verification-must-not-agree-with-itself]].

**Frame Codex neutrally — never lead it with your hypothesis (owner rule, 2026-08-18).** Give it context and the raw question, not the answer you expect. "Confirm X is the battle root" invites agreement and wastes the call; "here are the reads/xrefs — what is this?" lets it conclude independently, then you reconcile the two. Agreement between independently-reached conclusions is the real signal (same basis as [[convergent-verification]]); disagreement shows which side is wrong. This is now codified in `docs/orchestration/COORDINATION-PROTOCOL.md` (§Leverage /codex) so sessions get it without reminding. See [[cross-session-coordination]].
