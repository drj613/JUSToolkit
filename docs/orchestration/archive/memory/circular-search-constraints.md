---
name: circular-search-constraints
description: Constraining a search with the assumption under test removes the answer from the candidate set, and the search still looks methodical
metadata:
  type: feedback
---

Never narrow a search space using a premise that is downstream of the question the search is meant
to answer. It deletes the correct answer from the candidates, and every result is then wrong by
construction -- while the search output looks diligent.

Instance: hunting the kshape.bin record base, I restricted candidates to `= 0x0C mod 0x18` because
"file offset 0x0B4 is a known record". It is a known *bitmap*, and whether the bitmap sits at
record+0x00 or record+0x14 was the open question. The true base 0x40 was never in scope.

**Why:** a wrong number gets rechecked. A wrong search SPACE produces a plausible winner, a
runner-up, and an apparent process, and nothing in the output signals the answer was excluded. The
constraint also feels like free progress -- using a known data point is normally correct.

**How to apply:** before constraining, state what the constraint assumes and check it is independent
of the question. If not, run unconstrained; the extra candidates are usually cheap (here, eleven
bases, one line). Two tells: a residue you have to explain away in *every* candidate, and a
constraint whose source fact would answer the question outright if read differently -- 0x0B4 minus
the `[r0+0x14]` load gives 0x40 in one subtraction.

Related: [[falsifiable-but-dead-on-this-claim]], [[a-prior-is-not-a-check]],
[[record-points-one-representation-away]]
