# Collision subType vs jpower selection — the doc's claim doesn't hold simply

Loop-Atlas iteration 37. One micro-hypothesis of mine refuted, one existing claim questioned.

## jpower ID lives at record +0x00

`jpower-Mapping.md` lists a "jpower ID" column for block 0: `0, 3, 6, 9, 12, 15, 18, 21, 23`. That matches **byte `+0x00`** of each 304-byte record exactly. CONFIRMED — this completes the record layout alongside `damage1` at `+0x0C` (found two iterations ago).

The IDs aren't array indices. Entry `n` has ID `3n` for the first seven, then 21 and 23. "jpower ID" and "jpower entry index" are different numbering, which matters for any lookup.

## The subType→jpower claim is shaky

`jpower-Mapping.md` says *"Collision `subType` selects which jpower entry to use from the block."* Tested on Goku (`db_b_01.bin`, 25 records, `chr_b[0]` → jpower block 0, 9 entries):

- subType values: `{0:2, 1:6, 2:13, 5:2, 6:1, 7:1}` — max 7, so it *could* index a 9-entry block.
- But **13 of 25 records share subType 2.** A one-to-one move selector wouldn't pile half the records on one value.
- subType is **not** the jpower ID: block 0's IDs are `0, 3, 6, …, 23`, while subTypes include `1, 2, 5, 7` — none of which appear in block 0's ID list.

So subType is at most a block-*relative* index, and the skew argues against it picking a distinct move per record. Marking this **questioned**, not refuted — I've only tested one character, and the claim may hold under some reading of "entry" I haven't tried.

## My type-correlation idea: refuted

In Goku's 25 records, `+0x10` looked like a function of `+0x00` (type) — every type-5 record had `+0x10 = 3`, every type-3 had `1` or `2`. If true, `+0x10` would be derived rather than independent, which would weaken it as a `hitTier` candidate.

Tested across all **2837** records:

| | result |
|---|---|
| types where `+0x10` is fully determined | **1 of 8** |
| predicting `+0x10` from type alone | **50.3%** correct |
| predicting `+0x11` from type alone | **48.7%** correct |

Every type spreads across multiple values of both fields. **The pattern was a 25-record artefact.** `+0x10` (4 values) and `+0x11` (7 values) remain independent and survive as `hitTier`/`hitProperties` candidates — still candidates, not claims.

Worth noting the shape of that near-miss: a clean pattern in 25 records that vanishes at 2837. Same failure mode as my `chr_b +0x30` over-fit, caught earlier this time because I checked before writing it up.

## One assumption I almost made

Goku's record 22 is **all zeros**, which looked like a terminator convention. Across the full corpus there's exactly **one** all-zero record — that one. It's not a convention, and code shouldn't treat a zero record as end-of-list.

## Next

The productive direction is the unopened half: `chr/shot/*` (184 files) is the projectile-entities subsystem's data, and `chr/ai/*` (269 files, plus `ai_param.bin`) belongs to ov11, the battle-AI overlay. Both are newly available and neither carries a prior campaign's worth of demoted claims.
