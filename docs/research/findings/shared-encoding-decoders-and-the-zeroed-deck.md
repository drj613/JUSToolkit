# Findings: shared encoding decoders, and the deck block starts zeroed

Loop-Atlas iteration 112. Static.

Four mask bugs in one campaign is a process failure. Fix: `struct_fields.py` now
exports **tested decoders** for the three problem encodings, each hand-verified in the
selftest against a real instruction.

Result: the deck block is **`memset` to zero at creation**, and no identified writer
sets the ID table base `+0x30` or its count `+0x18EC`. If that holds, add-entry can
never succeed — but 96 candidate stores remain unattributed, so not yet a claim.

---

## 1. The decoders

`is_bl`, `is_ldr_pc`, `is_mov_imm` — the three encodings that produced silent zeros
at iterations 46, 47, 89 and 111. The selftest checks each against a hand-read
instruction **and** against something it must reject:

| decoder | accepts | rejects |
|---|---|---|
| `is_ldr_pc` | `0x02076CB4` → `(r0, 0x20)` | `0x02076CC0`, a non-pc load |
| `is_mov_imm` | | `0x02076CD0`, a **conditional** `movlo` |
| `is_bl` | `0x02076EB4` → `0x02076C98` | `0x02076CA4`, a `bxeq lr` |

Rejections matter more: every one of the four bugs was a mask that matched *nothing*
— a positive-only test would have passed.

## 2. The deck block is zeroed at creation

```
0x0207602C  ldr r3, [pc, #0x388]   ; -> 0x0214BD80
0x02076030  ldr r2, [pc, #0x37c]   ; -> 0x00001914
0x02076034  mov r1, #0
0x02076038  str r0, [r3]           ; the global
0x0207603C  bl  #0x20517fc         ; memset(deck, 0, 0x1914)
```

So `deck+0x30` and `deck+0x18EC` both start at **0**.

## 3. No identified writer of either field

| search | result |
|---|---|
| word stores to `+0x30` in `ComicDeck.cpp` | 0 (iteration 110) |
| word stores to `+0x30` in any of the 55 deck-global holders | **0** |
| stores resolving to `+0x18EC` ROM-wide (`add` + `str` split) | **0** |

`0x18EC` exceeds a 12-bit immediate, so it *must* be split — making `add`+`str` the
right search shape.

## 4. What would follow, and why it is not claimed

With count at 0, `0x02076C98` rejects every id (`id >= count`), so `0x02076D30`
always fails and add-entry always returns `0x10000000`.

**Not claimed.** There are **96** word stores to `+0x30` across ov5, arm9, ov6 and
ov11 — none in a function that loads the deck global, but a function receiving the
deck **as an argument** would not load it. Those 96 are the unexcluded case.

Also unswept: register-offset stores, `stm`, and Thumb (ov5 has 1 Thumb function,
arm9 has 313).

## Predictions status

| Claim | Verdict |
|---|---|
| `ComicDeckCreate` zeroes the whole `0x1914` block | **CONFIRMED_STATIC** — `mov r1,#0`; `bl #0x20517fc` with `r2` = `[0x020763B4]` = `0x1914` |
| `deck+0x30` and `deck+0x18EC` start at 0 | **CONFIRMED_STATIC** — follows from the memset |
| Some deck-global holder writes `+0x30` | **REFUTED** — 0 of 55 |
| Any ARM `add`+`str` pair writes `+0x18EC` | **REFUTED** — 0 ROM-wide |
| A mask test that only checks positive cases catches these bugs | **REFUTED** — all four bugs matched nothing; only a rejection case or an implausible count exposes them |
| Add-entry can never succeed | **not claimed** — 96 `+0x30` stores are unattributed, and a caller passing the deck would not load the global |
| The deck-entry system is a fifth vestigial system | **not claimed** — follows only if the 96 are excluded |

## Next angles, ranked

1. **Attribute the 96 `+0x30` stores.** For each, check whether the base register traces
   to a parameter that a caller sets from the deck global. That decides the vestigial
   question outright.
2. **Sweep `+0x30` and `+0x18EC` in Thumb** using `find_thumb_callers.py`'s halfword
   machinery.
3. **Read `KomaList_Create` `0x0214F5C4`** (carried) — the largest ov5 allocation.
4. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
