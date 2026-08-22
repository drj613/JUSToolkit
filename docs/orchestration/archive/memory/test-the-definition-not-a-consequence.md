---
name: test-the-definition-not-a-consequence
description: "When two candidate readings survive, look for an instruction that DEFINES the thing rather than a prediction it implies — a consequence can be satisfied by a wrong premise, a definition cannot"
metadata:
  type: feedback
---

2026-08-19, JUS: a RAM scan left two candidate base addresses for an object, `A` and `B = A + 0x14`.
Three adjacency predictions were checked and **both bases passed 3/3** — every recipient happened to
occupy a koma spanning both candidate rows, so a one-row shift landed inside the same panel either
way. A side-delta check also passed on both. Four separate corroborations, none discriminating.

The answer was in an instruction already quoted in a bead: `ldr r6,[sl,#0x558]`. That *defines* arg0
as the owner of the chain whose head lives at `+0x558`. One dereference: null on both sides under
`A`, the correct chain head on both sides under `B`. Absolute discrimination, one peek.

**Why:** the failing tests were all **downstream consequences** — grid contents implied by the
model. A consequence can be satisfied by a wrong premise, and a wrong frame doesn't produce noise,
it produces a clean pattern off by a constant (the spurious base was internally consistent at 5/5
on its own regularity, which is what made it arguable). A **definition** cannot be satisfied by a
wrong premise, because it *is* the premise.

**How to apply:** when two readings both survive, stop generating more predictions and ask what
instruction defines the disputed thing — a dereference, a stride multiply, a bound. Prefer the check
that would be *incoherent* under the wrong reading over the check that would merely be *false*. And
if a discriminator is proposed that you can't yet explain, run it anyway: the reason it works may
only be visible once both branches are on the table (I proposed exactly that discriminator, was
argued out of it on principled-sounding grounds, and wrote the objection into my own doc as a lesson
about my error — my agreement then read as confirmation to the other side).

Related: [[prediction-must-be-single-mechanism]], [[record-points-one-representation-away]],
[[sound-substance-wrong-word]], [[when-the-claim-is-a-count-count-it]].
