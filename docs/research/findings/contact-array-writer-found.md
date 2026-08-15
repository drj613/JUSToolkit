# Findings: the contact-array writer, and the array is at `+0x154` not `+0x158`

Loop-Atlas iteration 56. Static.

Four wakes spent looking for whatever fills the pair-wise array that query 71 reads. **Found: four
read-modify-write accumulator blocks in arm9 at `0x02081340`, `0x02081388`, `0x020813D0` and
`0x02081418`.**

This also corrects iteration 52: the array base is **`manager+0x154`**, not `+0x158`. The writer
computes that base directly — stronger than inferring it from a read offset.

---

## 1. Excluding the phase table — all 19 entries

Iteration 55 left 16 of 19 phase-table entries unchecked. All 17 distinct functions scanned:

| test | result across all 17 |
|---|---|
| stores at offset `>= 0x150` | **0** |
| `mov Rd,#0xC0` or `#0x30` | **0** |
| register-offset stores | **0** |
| highest offset touched by any of them | **`0xF8`** |

Sizes range from 1 instruction (`bx lr` stubs at `+0xFC`, `+0x100`) to 229 (`+0x104`). Six slots
are two-instruction constant-returners. **The entire ColPrm phase machinery is excluded**, along with
construction and teardown from iteration 54.

## 2. Two searches, one useful

**Offset-only** — stores anywhere in the ROM at an offset inside the array's byte range, non-`r15` base:
**2251 hits** across 13 binaries. Useless — exactly why the early offset scans failed.

**Stride signature** — both `0xC0` and `0x30` as immediates within 8 instructions, query 71's
exact 2D-index shape: **5 hits in the whole ROM.**

| site | notes |
|---|---|
| ov6 `0x02157EE0` | query 71 itself, the reader |
| arm9 `0x02081340` | writer block 1 |
| arm9 `0x02081388` | writer block 2 |
| arm9 `0x020813D0` | writer block 3 |
| arm9 `0x02081418` | writer block 4 |

Four blocks, evenly spaced `0x48` apart. 2251 vs. 5 is the whole argument for scanning by
*computation shape* instead of by offset.

## 3. The accumulators

Block 1 in full:

```
0x02081330  lsr r0, r0, #4            ; index from a nibble
0x02081338  bl  #0x2081a58
0x0208133C  add r2, sl, #0x154        ; the array base
0x02081340  mov r1, #0xc0
0x02081344  mla r1, r0, r1, r2        ; + row * 0xC0
0x02081348  mov r0, #0x30
0x0208134C  mla r2, fp, r0, r1        ; + column * 0x30
0x02081350  ldr r1, [r2, #0x10]
0x02081354  ldr r0, [sp, #0x4c]
0x02081358  add r0, r1, r0
0x0208135C  str r0, [r2, #0x10]       ; element += value
0x02081360  ldr r0, [r2, #0x28]
0x02081364  add r0, r0, r7
0x02081368  str r0, [r2, #0x28]       ; element += value
```

All four blocks share `add r2, sl, #0x154` and the same `0xC0`/`0x30` index arithmetic, differing only in
which element field they accumulate into:

| block | element field written | absolute |
|---|---|---|
| `0x02081340` | `+0x10` (and `+0x28`) | `+0x164`, `+0x17C` |
| `0x02081388` | `+0x0C` | `+0x160` |
| `0x020813D0` | `+0x08` | `+0x15C` |
| `0x02081418` | `+0x04` | `+0x158` |

Each block is preceded by a flag test (`tst r0,#0xc0`) and a nibble extraction (`lsr r0,#4`, `and r0,sb,#0xf`)
feeding `bl 0x02081A58`. The row index comes from packed bits; flags select which block runs.
**Accumulators, not assignments** — every one is load, add, store.

## 4. The `+0x154` correction, and a producer/consumer match

Iteration 52 placed the array at `+0x158` because query 71's two reads (`+0x158`, `+0x170`) had to land
inside one `0x30` element. Sound reasoning, but under-determined — any base putting both reads in one
element would fit.

The writer settles it: **`+0x154`**, computed directly. Against that base, query 71's reads become
element `+0x04` and `+0x1C`. Element fields in use:

```
element (0x30 bytes)
  +0x04   written by block 4   |  READ by query 71
  +0x08   written by block 3
  +0x0C   written by block 2
  +0x10   written by block 1
  +0x1C                        |  READ by query 71
  +0x28   written by block 1
```

**Block 4 writes element `+0x04` and query 71 reads element `+0x04`** — a direct producer/consumer pair
across two binaries. That's what makes this the right array, not a geometric coincidence.

## 5. The one link still unproven

Can't confirm that `sl` (`r10`) holds the ColPrm manager here — nothing in the preceding `0x340` bytes
assigns it, so it arrives as a parameter or is set further back.

The writer accumulates into an array with **identical geometry** (base `+0x154`, rows `0xC0`, elements
`0x30`) and **overlapping element fields** with the one query 71 reads, whose array lives in the
ColPrm manager (iteration 52, via global `0x0214BE10`). Same array: **PLAUSIBLE (strong)**, not
confirmed, until `r10`'s type is established. Leaving the gap open — iteration 45 burned a wake on an
offset that matched for the wrong object.

Incidental: `extract_symbols.py --nearest` names `Battle_ColPrmManCreate` as the closest symbol below this
code, not previously recorded. At `+0x4E80` it's neighbourhood only.

## Predictions status

| Claim | Verdict |
|---|---|
| One of the 19 phase-table entries writes the contact array | **REFUTED** — all 17 distinct functions clean; max offset `0xF8` |
| Offset-range scanning can find the writer | **REFUTED** — 2251 hits |
| The `0xC0`/`0x30` stride signature is discriminating | **CONFIRMED** — 5 sites ROM-wide |
| Four arm9 blocks accumulate into the array | **CONFIRMED_STATIC** — `0x02081340`/`0x02081388`/`0x020813D0`/`0x02081418`, all `add r2,sl,#0x154` |
| The array is based at `manager+0x158` | **REFUTED** *(iteration 52)* — the writer computes `+0x154` |
| Element fields `+0x04`, `+0x08`, `+0x0C`, `+0x10`, `+0x28` are written | **CONFIRMED_STATIC** — one per block, plus `+0x28` |
| Block 4's `+0x04` is the field query 71 reads | **CONFIRMED_STATIC** — same element offset |
| The writes are assignments | **REFUTED** — all four are load-add-store accumulators |
| The writer's array is the ColPrm manager's | **PLAUSIBLE (strong)** — geometry and fields match; `r10`'s type unproven |

## Next angles, ranked

1. **Establish `r10`'s type at `0x02081340`** by finding the enclosing function's entry and its callers.
   That upgrades the last claim and closes the four-wake search properly.
2. **Identify the accumulated values** — `[sp,#0x4c]` and `r7` in block 1. If these are damage figures,
   the array is a per-pair damage ledger tied to the damage pipeline.
3. **Decode `bl 0x02081A58`**, which turns packed nibbles into the row index. It defines what the rows are.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
