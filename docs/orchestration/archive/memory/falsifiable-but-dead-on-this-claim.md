---
name: falsifiable-but-dead-on-this-claim
description: An arm can be genuinely refutable and still carry zero information about the claim it is cited for; ask what would refute it ON THIS proposition
metadata:
  type: feedback
---

"What result would refute this arm?" is necessary but not sufficient. An arm can be genuinely
falsifiable and still be dead on the specific claim it is cited for.

Instance: my kshape cell-map/bitmap 66/66 set comparison is refutable -- a cell map disagreeing with
its bitmap kills it. But byte *i* corresponds to bit *i* at ANY grid width, so it cannot fail on
WIDTH, which is exactly what I cited it for. The guard passed and the error went through.

**Why:** this is harder to spot than a tautology. There is no degenerate identity to notice, the
100% pass rate is real, and the test is doing honest work -- just on a different question than the
one being argued.

**How to apply:** name the proposition, not the test. Ask "what result would refute this arm ON THE
CLAIM I AM USING IT FOR?" If the answer is "nothing", drop it from the argument even though it is a
valid check of something else. Watch for citing a real arm and a dead one in the same breath, which
launders the dead one.

Related: [[every-arm-must-be-able-to-fail]] (this refines it), [[verification-must-not-agree-with-itself]], [[clean-evidence-skips-the-check]],
[[test-the-definition-not-a-consequence]], [[circular-search-constraints]]
