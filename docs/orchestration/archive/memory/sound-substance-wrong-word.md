---
name: sound-substance-wrong-word
description: "This project's dominant failure is a correct finding carried into the record under a word stronger than the evidence — assert only what you inspected"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9114733f-1275-45a1-a6f1-898e950b4c12
  modified: 2026-08-19T23:09:38.357Z
---

The JUS sessions' most frequent error is not wrong findings. It is **right findings stated in a
word the evidence doesn't support**, which then propagates because the substance holds up when
anyone spot-checks it. Five instances in one day (2026-08-19), across two sessions — note the fifth is a
**retraction** overstating, which is the same failure pointing the other way:

- "Robin's record is **byte-identical** to Luffy's" — from a five-byte read; 16 of 60 bytes differ
- "eleven records are **absent** from the index" — from a parse; the rows existed and were blank
- "**gated by** a one-shot flag `[sl+0xf8]`" — the instruction is a store; it *arms* the flag
- inferring from "the exporter names +0x03 `charId`" that the byte is therefore **not an ability**
  — a name change asserted as a function change. (The original "five-slot ability array" was
  *right*: the loader at `0x02077768` walks five slots, `cmp sb,#5`. The wrong word was in the
  retraction, not the claim.)
- offering a **confirmation** whose predicted value was zero, reachable by every rival mechanism

**Why:** each had sound substance underneath, so re-checking the *claim* confirms it while the
*wording* stays wrong. And the wrong word is always the stronger one — byte-identical, absent,
gated, confirmed, *not an ability*.

The two directions hide for different reasons, which is why both need naming. An overstated
**claim** hides because overstating reads as confidence. An overstated **retraction** hides because
withdrawing reads as rigour — and a retraction gets *less* scrutiny than the claim it withdraws,
since nobody audits someone for being too hard on themselves. The retraction instance above cost
two commits and a round trip precisely because it arrived looking like the careful move.

**How to apply:** assert only the scope you actually inspected. Five bytes read licenses "identical
ability window", never "byte-identical". A parse licenses "my parse found none", never "there are
none" — read one raw row. A store is not a gate. And when restating a partner's claim in your own
record, **re-derive it rather than transcribing it**: their wording is the thing most likely to be
wrong. Cheapest defence, and it caught every one of the five above.

Related: [[record-points-one-representation-away]], [[prediction-must-be-single-mechanism]],
[[stale-claim-above-its-own-correction]], [[a-correction-is-a-claim]].
