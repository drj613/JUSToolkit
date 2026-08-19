# Findings: post-indexed addressing was not a blind spot — it was decoded wrongly

Loop-Atlas iteration 80. Static.

Iteration 79 said post-indexed addressing was invisible to every scanner.
**Half right, and the wrong half matters.** The regex scanners and `find_field_writers.py`
are blind to it. `struct_fields.py` is not — it decodes raw words, so it *sees* these
instructions and **decodes them wrong**.

Blind means a gap. Wrong means a confident false field. `+0x9A` on the ColPrm record
map from iteration 78 is one: it does not exist.

Three encoding bugs fixed. All three produce wrong output, not missing output.

---

## 1. Post-indexed offsets are strides, not field offsets

```
0x0207CB0C  ldrsh r2, [r6], #2
```

P = 0, so the read happens at **offset 0**, then the base advances by 2. The old
`access()` ignored P and returned offset 2. With `r6` = `record+0x98`, that produced
`+0x9A`.

The real `+0x9A` comes from the loop's **second pass** through the same instruction —
not from an access at that offset. The offset was right by accident and wrong by method.
On any array whose stride differs from its element size, or any loop not starting at the
base, it would have been wrong outright.

**Corrected ColPrm record map: 20 offsets, not 21.** `+0x098` now shows both of its
accesses (`ldrsh/split` and `strh/split`) instead of being split across a real field and
a phantom.

## 2. Base writeback defeated guard 2

Guard 2 stops the walk when the anchor register is reassigned. It exists because
iterations 49 and 50 invented four phantom fields without it.

`writes()` only checked the *destination* register of loads. Post-indexed and
pre-indexed-writeback transfers modify their **base**:

```
str r0, [r4], #4        ; r4 += 4, and it is a STORE, so the old load-only test
                        ; skipped it entirely
```

The walk kept treating `r4` as the struct base after it had moved. New helper
`writes_back(x)` — true when P = 0, or when W = 1 — now covers both loads and stores.

## 3. Down-offsets were reported as up-offsets

U = 0 means the offset **subtracts**. `ldr r0,[r4,#-8]` was reported as `+8`. A negative
offset from a struct base is not a field in this model, so it is now dropped instead of
sign-flipped into something plausible.

## 4. How much code this touches

Counted by encoding, inside ARM function extents, all 16 regions:

| form | count | share |
|---|---|---|
| total immediate-offset transfers | 106359 | 100% |
| P = 0, post-indexed | **456** | 0.4% |
| P = 1, W = 1, pre-indexed writeback | **46** | 0.0% |
| U = 0, negative offset | **625** | 0.6% |

About 1127 instructions, roughly 1%. Small, but every one could produce a wrong field
offset or defeat the reassignment guard — and one already had.

Iteration 79 reported 331 post-indexed sites in arm9 from a *text* regex. The
encoding-based ROM-wide count of 456 supersedes it; the text count only saw what the
disassembler rendered with `[reg], #imm` syntax.

## 5. A note on how this was almost missed twice

The throwaway script that produced §4's table first reported **97.5%** of transfers as
post-indexed — obviously wrong, which is the only reason it got caught. It parsed the
disassembly's hex column with `int(s, 16)` instead of byte-swapping, so every bit test
read the wrong bits. `struct_fields.py` reads the binary directly and was never affected.

The lesson is the ratio, not the bug. An implausible number is a free correctness check;
a *plausible* wrong number would have gone straight into the doc.

## Predictions status

| Claim | Verdict |
|---|---|
| Post-indexed offsets are strides; the access is at offset 0 | **CONFIRMED_STATIC** — P = 0 at `0x0207CB0C`, base `r6` = `record+0x98` |
| `+0x9A` on the ColPrm record is a phantom | **CONFIRMED_STATIC** — produced solely by decoding the stride as an offset |
| Post-indexed addressing is invisible to `struct_fields.py` | **REFUTED** *(iteration 79's framing)* — it was decoded, and decoded wrongly |
| Post-indexed addressing is invisible to the regex-based scanners | **CONFIRMED_STATIC** *(iteration 79, that half stands)* — they match `[base, #imm]` text only |
| Writeback transfers modify the base and defeated guard 2 | **CONFIRMED_STATIC** — `str r0,[r4],#4` writes `r4`; the old test only checked loads' destinations |
| U = 0 offsets were reported with the wrong sign | **CONFIRMED_STATIC** — 625 sites ROM-wide could have been sign-flipped |
| The corrected ColPrm record map has 20 offsets | **CONFIRMED_STATIC** — re-run with the same four anchors |
| The 331 figure from iteration 79 is the post-indexed population | **REFUTED** — it was arm9 text-rendered only; the ROM-wide encoding count is 456 |

## Next angles, ranked

1. **Port the three fixes to `find_field_writers.py`**, which still matches on
   disassembly text and so is blind to all 1127 sites. Its `+0xE8` sweep at iteration 76
   is the load-bearing result that depends on it.
2. **Resolve `record+0x68`** (carried) — the object whose `+0x20` list holds this
   record's bucket nodes.
3. **Re-run the record map with anchors from the eight per-frame collision stages**
   (carried).
4. **Re-audit the map's `char+0xNN` offsets** across the three objects (carried).
