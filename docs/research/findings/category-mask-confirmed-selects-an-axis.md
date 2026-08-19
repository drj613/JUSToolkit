# Findings: `+0x38` confirmed as a bitmask that picks which axis gets a 50% adjustment

Loop-Atlas iteration 142. Static.

Iteration 141 rated `record+0x38` as a category mask, **PLAUSIBLE**, based on four call sites. It predicted
one consumer would settle things. This iteration found four consumer sites inside a single function.
**Confirmed** — and they show what the bits actually choose.

---

## 1. The confirmation

Inside `0x02081DDC` (992 bytes, 1 caller), the same pattern repeats four times:

```
0x02081EFC  tst fp, #0x200
0x02081F04  beq #0x2081f18
0x02081F08  ldr ip, [r7, #0xc]
0x02081F0C  ldr ip, [ip, #0x38]      ; the mask
0x02081F10  tst ip, #0x4000          ; <-- BIT-TESTED
0x02081F14  addne r3, r3, r1, lsl #7

0x02081F18  tst fp, #0x100
0x02081F20  ldr ip, [r7, #0xc]
0x02081F24  ldr ip, [ip, #0x38]
0x02081F28  tst ip, #0x8000          ; <-- BIT-TESTED
0x02081F2C  addne sb, sb, r2, lsl #7

0x02081F30  tst fp, #0x20000
0x02081F38  ldr ip, [r7, #0xc]
0x02081F3C  ldr ip, [ip, #0x38]
0x02081F40  tst ip, #0x4000
0x02081F44  subne r3, r3, r1, lsl #7

0x02081F48  tst fp, #0x10000
0x02081F50  ldr r1, [r7, #0xc]
0x02081F54  ldr r1, [r1, #0x38]
0x02081F58  tst r1, #0x8000
```

`+0x38` is always read and **`tst`ed** — never compared as a whole number. The tested bits are exactly
`0x4000` and `0x8000`, two of the three bits that real callers were seen writing in iteration 141 (`0x8000` at
`0x02164F0C`, `0x4000` at `0x02164F48`). The values written and the values tested match, from opposite ends
of the chain. That upgrades this from PLAUSIBLE to **CONFIRMED_STATIC**.

## 2. What the bit picks: an axis

Each mask bit maps to a different accumulator:

| mask bit | accumulator | adjustment |
|---|---|---|
| `0x4000` | `r3` | `± r1 << 7` |
| `0x8000` | `sb` | `± r2 << 7` |

The gating flags come in **sign pairs**:

| flag bit | effect |
|---|---|
| `0x200` | `r3 +=` |
| `0x20000` | `r3 -=` |
| `0x100` | `sb +=` |
| `0x10000` | `sb -=` |

The flags pick a direction; the category bit picks which axis is allowed to move. Two independent gates on
one adjustment.

## 3. Where the values come from — signed bytes, scaled to 24.8

```
0x02081EE4  ldr r2, [r7, #0x10]
0x02081EEC  ldrsb r1, [r2, #4]      ; a SIGNED byte
0x02081EF0  ldrsb r2, [r2, #5]      ; a SIGNED byte
0x02081EF4  ldr fp, [r3, #0x44]     ; r3 = [r6+0xC] -- the flags word
0x02081EF8  lsl r3, r1, #8          ; base = byte << 8
0x02081F00  lsl sb, r2, #8
```

A pair of signed bytes at `+0x4`/`+0x5` become the base offset via `<< 8` — **24.8 fixed point**, the same
format iteration 125 proved for the arena bounds. This is the second place that format appears.

The adjustment uses `byte << 7`, exactly **half** of `byte << 8`. So the full operation is: take a signed
byte offset, scale it, then add or subtract **50%** of it when both the direction flag and the axis's category
bit are set.

## 4. Two things deliberately not claimed

**`sl+0x48` is not necessarily MoveMan's link array.** The function opens with `ldr r5, [sl, #0x48]`, then
`ldr r6, [r5]` and `ldr sb, [r5, #8]` — a next-pointer-and-payload walk off `+0x48`, exactly matching
iteration 137's MoveMan link shape. But `+0x48` sits on the conventional-offset list, and `sl` is just this
function's `arg0`. **Not claimed.**

**`fp` is at `+0x44`, not `+0x40`.** Earlier iterations put the ColPrm record's flags at `+0x40` (bit
`0x200` = free, `0x800` gates delta application, `0x100` set on detach). This flags word lives at `+0x44` on
a different base (`[[r6+0xC]+0x44]`). It also uses bits `0x100` and `0x200`, but the meanings here are
directional. Adjacent offset, overlapping bit values, **different field** — noted so a later iteration doesn't
merge them by mistake.

One observation with no claim attached: iteration 140 found `record+0x3C` always receiving `0x20C000`, which
contains `0x8000 | 0x4000` — the same two bits tested here as categories. Bit values are reused freely in
this codebase, so this may mean nothing.

## Predictions status

| Claim | Verdict |
|---|---|
| `record+0x38` is a category/layer bitmask | **CONFIRMED_STATIC** *(was PLAUSIBLE, iteration 141)* — `tst` against `0x4000`/`0x8000` at four sites |
| `+0x38` is ever compared as a number | **REFUTED** — every consumer site uses `tst` |
| Writer values and reader tests agree | **CONFIRMED_STATIC** — `0x8000`/`0x4000` passed at `0x02164F0C`/`0x02164F48`, tested at `0x02081F10`/`0x02081F28` |
| The mask bit selects which accumulator is adjusted | **CONFIRMED_STATIC** — `0x4000`→`r3`, `0x8000`→`sb` |
| The gating flags form sign pairs | **CONFIRMED_STATIC** — `0x200`/`0x20000` on `r3`, `0x100`/`0x10000` on `sb` |
| The base offsets are signed bytes scaled by `<< 8` | **CONFIRMED_STATIC** — `ldrsb` at `+0x4`/`+0x5`, `lsl #8` |
| The adjustment is half the base | **CONFIRMED_STATIC** — `lsl #7` against a `lsl #8` base |
| This module uses 24.8 fixed point | **PLAUSIBLE** — `<< 8` on a signed byte matches iteration 125's format, in a different function |
| `sl+0x48` is MoveMan's link array | **not claimed** — `+0x48` is conventional and `sl` is untraced |
| `fp` at `+0x44` is the record's `+0x40` flags word | **REFUTED** — different offset, different base; only the bit *values* overlap |
| `record+0x3C`'s `0x20C000` relates to the category bits | **SPECULATIVE** — shares `0x4000\|0x8000`, but bit reuse is common here |
| What `0x800` (the third observed category bit) selects | **not claimed** — no consumer site tests it |

## Next angles, ranked

1. **Find a consumer that tests `0x800`.** Two of three category bits now have an axis; the third doesn't,
   and it's the one the `0x02168E44` caller passes.
2. **Identify `0x02081DDC`** — 992 bytes, 1 caller, the first function found that reads the category mask.
   Its caller would name the whole pass.
3. **Trace `0x02083624`'s caller** (carried) — settles whether the installer's `0x400000` branch is dead.
4. **Read `0x0201899C`** (carried) — the call whose output iteration 140 proved is thrown away.
