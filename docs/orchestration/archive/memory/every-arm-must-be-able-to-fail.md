---
name: every-arm-must-be-able-to-fail
description: "Naming the rival isn't enough — a two-arm test whose winning arm is a tautology looks two-sided and is one-sided; ask what would refute each arm"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 9114733f-1275-45a1-a6f1-898e950b4c12
---

I had just told static "name the rival and ask what byte it predicts differently" — then ran a
two-arm test where the winning arm **could not fail**, and used it to tell them their correct
answer was wrong.

The case (2026-08-19, kshape.bin geometry). I paired cell-map byte `(word r, index c)` with bitmap
bit `r*4 + c` and scored **1320/1320**. But in a record of five words of four bytes, `4r + c` *is*
the linear byte offset — so that arm was just "byte at offset i matches bit i", which passes at any
width because it encodes no geometry at all. The other arm was a genuine transpose and failed. One
real test plus one tautology, and the tautology scored 100%, so I read the pair as a discriminator.
In the same message I'd told static their 66/66 set comparison was transpose-blind *for exactly this
reason*. I diagnosed the flaw accurately and then ran it.

**Why:** a 100% arm beside a 60% arm *looks* like a clean discrimination. Nothing in the numbers
distinguishes "this arm is right" from "this arm cannot be wrong." And having named the rival, I felt
I'd already paid the rigour tax — the guard I'd just written down made me less likely to apply the
next one.

**How to apply:** of every arm, ask **what result would refute this arm on the claim I'm using it
for?** The unqualified version ("what would refute this arm?") is not enough, and static found the
case that proves it: their cell-map-versus-bitmap 66/66 *can* fail — a cell map disagreeing with its
bitmap refutes it — so the plain question passes and lets the error through. The arm was live on
"is the cell map real" and dead on "how wide is the grid", and they cited it for the second. **An arm
that is live on one question and dead on yours is harder to catch than a tautology**, because there
is no degenerate identity to notice and its 100% pass rate is genuine.

Cheap test for the tautology specifically: re-derive the arm's index arithmetic in the *container's*
own units — if it collapses to the identity (`byte i ↔ bit i`), it carries no information.

When the object has meaning, a **semantic** check beats more byte arithmetic: a koma piece must be a
single connected polyomino, and width 5 gives 66/66 connected against width 4's 30/66. But static
then went one better and it's the real lesson — **the code already said it, and neither of us needed
to run anything**. The validator at `0x02076D70` folds the 20-bit map by OR-ing four slices five bits
apart, masks each to 5 bits, and indexes `row*5`: four rows of five, stated three ways in one
function we had both already read. Connectivity agreeing from a different representation is the
standard we want, but it was confirmation of something the definition had settled. Reach for the
instruction that *defines* the thing before running a test on its consequences —
[[test-the-definition-not-a-consequence]].

The tell I did catch: the one record that came out disconnected. I flagged it as a counter-signal
and chased it, and that's what caught the whole thing — so [[clean-evidence-skips-the-check]] cuts
both ways, and the single ugly datum is worth more than the 65 tidy ones.

A third instance the same day, mine, outside byte-work entirely: I ran `git remote -v | head -2`,
saw only `fork`, and told a peer that `origin` was not configured. Three remotes exist, `origin`
among them, with the same URL as `fork`. **The truncation was my own command**, which is the circular-constraint shape — a search whose
bounds exclude the answer returns a confident wrong result, and nothing in the output says it was
cut. Sibling of static's `≡ 0x0C mod 0x18` constraint built from the very fact that would have
broken it. When a conclusion rests on the *absence* of something, check that the command could have
shown it.

Related: [[prediction-must-be-single-mechanism]], [[verification-must-not-agree-with-itself]],
[[test-the-definition-not-a-consequence]], [[a-correction-is-a-claim]].
