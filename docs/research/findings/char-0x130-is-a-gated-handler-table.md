# Findings: `char+0x130` carries a 16-entry gated handler table

Loop-Atlas iteration 88. Static.

All ten uses of `char+0x130` in the state dispatcher do the same thing: pass the view's
address and a **selector** to a small method. Following one method reveals the view's layout.

`view+0x0C` is a **32-bit enable mask**. Selector `N` runs `table[N]` only when bit `N` is
set. The table lives at `0x0217221C` with exactly **16 entries** — index 16 onward is
ASCII. Iteration 87's "≥ `0xC` bytes" floor was far too low: the view reaches `0x6C`.

---

## 1. The ten uses are one pattern

```
0x0215A004  add r0, r6, #0x130 / mov r1, #0xf / bl #0x215fc78
0x0215A03C  add r0, r6, #0x130 / mov r1, #6   / bl #0x215fc78
0x0215A04C  add r0, r6, #0x130 / mov r1, #0xa / bl #0x215fc78
0x0215A064  add r0, r6, #0x130 / mov r1, #4   / bl #0x215fc78
0x0215A070  add r0, r6, #0x130 /                bl #0x215fcb8
0x0215A078  add r0, r6, #0x130 / mov r1, #0xe / bl #0x215fce4
0x0215A34C  add r0, r6, #0x130 /                bl #0x215fd58
0x0215A364  add r0, r6, #0x130 / mov r1, #0xe / bl #0x215fc78
0x0215A3B8  add r0, r6, #0x130 /                bl #0x215fd48
0x0215A3D0  add r0, r6, #0x130 / mov r1, #0xe / bl #0x215fc78
```

Five distinct methods; selectors `4`, `6`, `0xA`, `0xE`, `0xF`. Surrounding code reads
state bytes `+0xC8`, `+0xCB`, `+0xD2`, `+0xD3` and the entity at `+0x1A8` — firmly inside
the per-character state machine.

## 2. The gate

```
0x0215FC78  push {r3, lr}
0x0215FC7C  ldr r3, [r0, #0xc]       ; view+0x0C = a 32-bit enable mask
0x0215FC80  mov r2, #1
0x0215FC84  tst r3, r2, lsl r1       ; bit N set?
0x0215FC88  popeq {r3, pc}           ; no -> return, do nothing
0x0215FC8C  ldr r2, [pc, #8]         ; -> 0x0217221C
0x0215FC90  ldr r2, [r2, r1, lsl #2] ; table[N]
0x0215FC94  blx r2
```

Seven callers total. A second method at `0x0215FCE4` tests the **same mask bit**, then reads
a halfword from `view + N*2 + 0x16` into `view+0x64`. So `view+0x16` is an `int16` array
indexed by the same selector.

## 3. The table: 16 entries

| index | handler | |
|---|---|---|
| 0–3 | `0x0215FFDC` | one shared entry — a default or no-op |
| 4 | `0x0215FD68` | **selector seen** |
| 5 | `0x0215FD00` | |
| 6 | `0x0215FD7C` | **selector seen** |
| 7 | `0x0215FEAC` | |
| 8 | `0x0215FEE8` | |
| 9 | `0x0215FF4C` | |
| 10 | `0x0215FE14` | **selector seen** |
| 11 | `0x0215FF74` | |
| 12 | `0x0215FF4C` | shares 9's handler |
| 13 | `0x0215FF64` | |
| 14 | `0x0215FF64` | shares 13's handler; **selector seen** |
| 15 | `0x0215FE7C` | **selector seen** |

**The table ends at 16**: the next words are `0x74746142`, `0x435F656C`, `0x61726168`,
`0x6F666E49` — `"Batt"`, `"le_C"`, `"hara"`, `"Info"`. Strings, not pointers. 16 slots,
12 distinct behaviours, 9 unique handler addresses.

Two sample handlers:

```
0x0215FCB8  ldrh r1,[r0,#0x5a] / strh r1,[r0,#0x66]
            ldrh r1,[r0,#0x5c] / strh r1,[r0,#0x68]     ; snapshot a pair
0x0215FD68  ldrh r2,[r0,#0x5a] / ldrh r1,[r0,#0x62]
            add r1,r2,r1       / strh r1,[r0,#0x5a]     ; +0x5A += +0x62
```

Halfword slots doing accumulate-and-snapshot — consistent with per-frame counters or positional
deltas.

## 4. The view's size, bounded two ways

Known fields: `+0x00`, `+0x04`, `+0x08` (constructor, iteration 87), `+0x0C` (mask),
`+0x16` (`int16` array), plus halfwords at `+0x5A`, `+0x5C`, `+0x5E`, `+0x62`, `+0x64`,
`+0x66`, `+0x68`, `+0x6A`. Highest is `+0x6A`, so the view ends at `+0x6C`.

**Upper bound: `0x70`.** `char+0x1A0` is confirmed (8 accesses in `Battle_CharaCreate`),
and `0x1A0 - 0x130 = 0x70`. The view spans `char+0x130`–`char+0x19F` at most — the known
fields fill it to within 4 bytes.

This rules out an obvious misreading. `Battle_CharaInfoCreate` (`0x0215FFF4`,
`BattleCharaInfo.cpp`) allocates `0xAC` bytes, and the handler table sits in that module's
code band — entries 0–3 point at `0x0215FFDC`, `0x18` bytes before the constructor. But
`0xAC` at `char+0x130` would reach `char+0x1DC`, colliding with confirmed fields `+0x1A0`,
`+0x1A4`, `+0x1A8` and `+0x1B4`. **The embedded view is not the `0xAC` heap object**, even
though both belong to `BattleCharaInfo.cpp`.

## Predictions status

| Claim | Verdict |
|---|---|
| `view+0x0C` is a 32-bit enable mask gating a handler table | **CONFIRMED_STATIC** — `ldr r3,[r0,#0xc]`; `tst r3,r2,lsl r1`; `popeq` at `0x0215FC78`–`0x0215FC88` |
| The table is at `0x0217221C` and has 16 entries | **CONFIRMED_STATIC** — index 16 onward is the ASCII `"Battle_CharaInfo"` |
| Indices 0–3 share one handler | **CONFIRMED_STATIC** — all four are `0x0215FFDC` |
| `view+0x16` is an `int16` array indexed by the same selector | **CONFIRMED_STATIC** — `add r1,r0,r1,lsl#1`; `ldrh r1,[r1,#0x16]` at `0x0215FCE4` |
| The state dispatcher exercises selectors 4, 6, `0xA`, `0xE`, `0xF` | **CONFIRMED_STATIC** — five `mov r1,#N` sites |
| The view is `≥ 0xC` bytes | **REFUTED** *(iteration 87's floor)* — fields reach `+0x6A` |
| The view is at most `0x70` bytes | **CONFIRMED_STATIC** — bounded by the confirmed `char+0x1A0` |
| The view is `Battle_CharaInfoCreate`'s `0xAC` object | **REFUTED** — `0xAC` would collide with `+0x1A0`/`+0x1A4`/`+0x1A8`/`+0x1B4` |
| The view belongs to `BattleCharaInfo.cpp` | **PLAUSIBLE** — its methods and table live in that band, but no tag binds the embedded instance |
| All 16 handlers are reachable | **not claimed** — 5 selectors observed from one caller; `0x0215FC78` has 7 callers |

## Next angles, ranked

1. **Enumerate all 7 callers of `0x0215FC78`** and collect every selector. That pins down
   the live-slot set, same approach as the 73-case dispatcher.
2. **Read the 9 unique handlers** — small (16–100 bytes), operating on the `+0x5A`–`+0x6A`
   halfword block (the view's payload).
3. **Find who sets `view+0x0C`.** The mask controls which handlers run; a writer names the
   feature set.
4. **Size `char+0x7c`** (carried) — damage-side users `0x02158B20`, `0x021586D0`.
