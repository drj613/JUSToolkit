# Findings: all 16 handlers read — and `char+0x1b4` is the `+0x56c` struct

Loop-Atlas iteration 91. Static.

All 16 handler slots read. The key finding is a pointer chain, not a handler:

**`[char+0x1b4]` owns the `+0x56c` gauge.** Unnamed since the earliest GDB work;
`0x0215FE14` reaches it in two instructions.

Also: three counters, two new `char+0x7c` fields, and a correction — **11** unique
handlers, not the 9 reported twice.

---

## 1. `[char+0x1b4]` owns the gauge

Selector `0xA` handler:

```
0x0215FE14  push {r3, r4, r5, lr}
0x0215FE18  mov  r5, r0
0x0215FE1C  ldr  r0, [r5]              ; view+0x00 = [char+0x1b4]
0x0215FE24  ldr  r0, [r0, #0x56c]      ; the gauge
0x0215FE28  ldrh r2, [r5, #0x56]
0x0215FE2C  ldrsh r3, [r0, #0x18]
```

GDB-proven anchor:

```
0x020784E4  push {r4, lr}
0x020784E8  ldr  r4, [r0, #0x56c]
0x020784EC  ldrsh r2, [r4, #0x16]
```

Same field, same gauge, both then read a signed halfword (`+0x16` there, `+0x18` here).
So `0x020784E4`'s `arg0` is `[char+0x1b4]`, and the chain is:

**ov6 battle character (`0x1F0`) → `+0x1b4` → the `≥0x570` struct → `+0x56c` → the gauge.**

Iteration 74 established the `+0x56c` object is *not* the battle character. Now we know
where it sits: one pointer away, at `+0x1b4`.

## 2. All 16 slots

| slot | handler | what it does |
|---|---|---|
| 0–3 | `0x0215FFDC` | never issued (iteration 89) |
| 4 | `0x0215FD68` | `+0x5A += +0x62` |
| 5 | `0x0215FD00` | `+0x5A += arr16[N]`; `+0x5C += arr16[N]` |
| 6 | `0x0215FD7C` | `+0x5A = +0x56`; `+0x5C = +0x58`; then if `[char+0x7c + 0x4D] >= 3`, add `arr16[N]` to both |
| 7 | `0x0215FEAC` | counter `+0x10`, cap `0x120`; then apply |
| 8 | `0x0215FEE8` | if `[char+0x7c + 0x5B] >= 3`, apply via `+0x64` |
| 9, 12 | `0x0215FF4C` | SP-apply `arr16[N]` |
| 10 | `0x0215FE14` | the gauge path above |
| 11 | `0x0215FF74` | counter `+0x14`, cap `0x2D0`; then `arr36[N]` |
| 13, 14 | `0x0215FF64` | SP-apply `+0x64` if non-zero |
| 15 | `0x0215FE7C` | counter `+0x12`, cap `0x1B0`; then `arr16[N]` |

Recurring shape: **accumulate into `+0x5A`/`+0x5C`**, or **apply outward** via SP-apply
or the gauge.

## 3. Three counters, adjacent, different caps

| field | cap | frames at 60 fps |
|---|---|---|
| `+0x10` | `0x120` | 288 = 4.8 s |
| `+0x12` | `0x1B0` | 432 = 7.2 s |
| `+0x14` | `0x2D0` | 720 = 12 s |

Three consecutive halfwords, each guarding a different slot. Each counts while below its
cap, then falls through to the apply path.

## 4. `char+0x7c` gets its first fields

Two handlers read through `view+0x04` = `&char+0x7c`:

| offset | access | test |
|---|---|---|
| `+0x4D` | `ldrb` | `cmp #3`, skip if lower |
| `+0x5B` | `ldrsb` | `cmp #3`, skip if less than |

`char+0x7c` is at least `0x5C` bytes; both fields are thresholds compared against `3`.

## 5. Correction: 11 unique handlers, not 9

Iterations 88 and 89 both reported "9 unique handlers". Actual count:
`0x0215FFDC` ×4, `0x0215FF4C` ×2, `0x0215FF64` ×2, and eight singletons — **11 distinct
addresses across 16 slots**. Arithmetic slip, not a decoding error; the slot-to-handler
mapping in both docs was correct.

## Predictions status

| Claim | Verdict |
|---|---|
| `[char+0x1b4]` is the struct owning the `+0x56c` gauge | **CONFIRMED_STATIC** — `0x0215FE1C`/`0x0215FE24`, matching `0x020784E8`'s `ldr r4,[r0,#0x56c]` |
| `0x020784E4`'s `arg0` is `[char+0x1b4]` | **CONFIRMED_STATIC** — same field read, same gauge, both followed by a signed halfword load |
| The view has three counters with distinct caps | **CONFIRMED_STATIC** — `+0x10`/`0x120`, `+0x12`/`0x1B0`, `+0x14`/`0x2D0` |
| `char+0x7c` has fields at `+0x4D` and `+0x5B` | **CONFIRMED_STATIC** — `ldrb`/`ldrsb` through `view+0x04`, both `cmp #3` |
| `char+0x7c` is at least `0x5C` bytes | **CONFIRMED_STATIC** — highest field is a byte at `+0x5B` |
| The table has 9 unique handlers | **REFUTED** *(iterations 88 and 89, mine)* — 11 |
| `+0x56` and `+0x58` are unaccounted | **REFUTED** *(iteration 90)* — they are the sources slot 6 copies into `+0x5A`/`+0x5C` |
| The `+0x5A`/`+0x5C` pair is the view's main accumulator | **PLAUSIBLE** — 4 of 12 live handlers write it; the rest apply outward |
| The three caps correspond to game-visible durations | **not claimed** — 4.8 s, 7.2 s and 12 s at 60 fps, but no runtime check |

## Next angles, ranked

1. **Find who fills `arr16` at `view+0x16` and `arr36` at `view+0x36`** (carried) — the
   amounts every apply path uses.
2. **Find who sets `view+0x0C`** (carried) — the mask gates all twelve.
3. **Name the `≥0x570` struct at `[char+0x1b4]`** — now reachable from ov6, not only from
   an arm9 GDB anchor; much better handle than the census gave.
4. **Read `char+0x7c`'s users** `0x02158B20` and `0x021586D0` for more fields.
