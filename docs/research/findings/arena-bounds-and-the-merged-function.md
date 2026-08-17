# Findings: `0x0207DD40` is eight functions, and it hands us the arena bounds

Loop-Atlas iteration 125. Static.

Read all 540 bytes of `0x0207DD40` — the phase-table target that iteration 124 showed backs seven of the
17 slots. Two results:

1. The `functions.json` record **`0x0207DD40 size=540` is not one function.** It is one list-walking
   routine plus **seven independent leaf routines**, each ending in its own `bx lr`. The detector merged
   them because nothing branches between them — they are only reached through the phase table.
2. Those leaves are **arena-boundary code**. They pin down three constants that recur across the
   whole set: **`0x4000`**, **`0x3C000`**, **`0x20000`**.

---

## 1. The eight bodies inside one record

`0x0207DD40 + 540 = 0x0207DF5C`, exactly where a literal pool starts. The record's size is right; its
granularity is wrong.

| start | end | terminator | what it does |
|---|---|---|---|
| `0x0207DD40` | `0x0207DDD0` | `pop {r4,r5,r6,pc}` | the list walker (below) |
| `0x0207DDD4` | `0x0207DE04` | `bx lr` | predicate → `0`/`1` |
| `0x0207DE08` | `0x0207DE38` | `bx lr` | classifier → `3`/`0`/`1`/`2`/`-1` |
| `0x0207DE3C` | `0x0207DE40` | `bx lr` | `mov r0,#0x20000; bx lr` |
| `0x0207DE44` | `0x0207DE48` | `bx lr` | `mov r0,#0; bx lr` |
| `0x0207DE4C` | `0x0207DE7C` | `bx lr` | classifier → `2`/`3`/`1`/`0` |
| `0x0207DE80` | `0x0207DE84` | `bx lr` | `mov r0,#0; bx lr` |
| `0x0207DE88` | `0x0207DF58` | `bx lr` ×5 | the rect getter, 4-case jump table |

Two of the eight are the same two-instruction routine `mov r0,#0; bx lr` at different addresses. The
table needs two distinct pointers for the same behaviour, so the compiler emitted it twice.

## 2. The walker: two wall flags on a list

```
0x0207DD44  ldr r4, [r0, #0xb0]      ; list head at arg0+0xB0
0x0207DD4C  ldr r5, [r4, #8]         ; node -> element
0x0207DD50  ldr r0, [r5, #8]         ; element+0x08 = object A
0x0207DD54  ldr ip, [r5, #0xc]       ; element+0x0C = object B
0x0207DD58  ldrsh r3, [r0, #0x30]    ; A+0x30 = half-extent
0x0207DD5C  ldrsh r1, [r0, #0x2c]    ; A+0x2C = centre
0x0207DD60  ldr r0, [ip, #0x5c]      ; B+0x5C -> object C
0x0207DD64  ldr r2, [r0, #0xc]       ; C+0x0C = base coordinate
0x0207DD68  sub r0, r1, r3           ; centre - half
0x0207DD6C  add r1, r1, r3           ; centre + half
0x0207DD70  add r0, r2, r0, lsl #8   ; lo = base + (centre-half) << 8
0x0207DD78  add r6, r2, r1, lsl #8   ; hi = base + (centre+half) << 8
0x0207DD74  cmp r0, #0x4000
0x0207DD7C  bge #0x207dd9c           ; skip unless lo <  0x4000
0x0207DD80  ldr r0, [ip, #0x30]
0x0207DD84  bl  #0x206cf28
0x0207DD88  cmp r0, #0
0x0207DD8C  ldrne r1, [r5, #0xc]     ; NE
0x0207DD94  orrne r0, r0, #0x1000000
0x0207DD98  strne r0, [r1, #0x78]    ; B+0x78 |= 0x1000000
0x0207DD9C  cmp r6, #0x3c000
0x0207DDA0  ble #0x207ddc4           ; skip unless hi >  0x3c000
0x0207DDAC  bl  #0x206cf28
0x0207DDB4  ldreq r1, [r5, #0xc]     ; EQ  <-- opposite condition
0x0207DDBC  orreq r0, r0, #0x2000000
0x0207DDC0  streq r0, [r1, #0x78]    ; B+0x78 |= 0x2000000
0x0207DDC4  ldr r4, [r4]             ; next
0x0207DDCC  bne #0x207dd4c
```

The `<< 8` is the giveaway: a 16-bit centre and half-extent are shifted into the same scale as the base
coordinate, so the comparison constants are in **24.8 fixed point**. `0x4000 >> 8 = 64`,
`0x3C000 >> 8 = 960`, `0x20000 >> 8 = 512`.

An element's span is tested against a **left bound at 64 and a right bound at 960**. Crossing either
sets a bit in `B+0x78` — `0x1000000` for the left wall, `0x2000000` for the right.

**Recorded as observed, not smoothed over:** the two arms use *opposite* conditions on the same
`0x0206CF28` result — `ne` for the left wall, `eq` for the right. Either `0x0206CF28` is asymmetric by
design or one arm is a bug. Nothing here decides which, and I am not guessing.

## 3. The rect getter confirms all three constants

`0x0207DE88` switches on `r1` (0–3) and fills four words at `r2`:

| case | `[r2]` | `+0x4` | `+0x8` | `+0xC` | returns |
|---|---|---|---|---|---|
| 0 | `0` | `0x20000` | `0x3FF` | `0x3FF` | `1` |
| 1 | `0` | `0` | `0x4000` | `0x20000` | `2` |
| 2 | `0x3C000` | `0` | `0xFFFC43FF` | `0x20000` | `2` |
| 3 | `0` | `0` | `0x3FF` | `0` | `3` |
| else | — | — | — | — | `-1` |

Case 2's `+0x8` is `mvn r0,#0x3bc00`, i.e. **`-(0x3C000 - 0x3FF)`**. That settles the layout: `+0x8`/`+0xC`
are a **signed extent**, not a second corner. Case 1 sits at `0` and extends *right* to `0x4000`;
case 2 sits at `0x3C000` and extends *left* by the same span inverted. They are the **left and right wall
regions**, using the same constants the walker tests against — two independent uses of `0x4000`
and `0x3C000`, which is what makes them bounds rather than coincidence.

`0x20000` (512) appears as the vertical extent in three of the four cases.

## 4. The `0x0207DF5C` gap, resolved

Queue item "uncatalogued gap `0x0207DF5C`–`0x0207DFD7`" — identity settled:

- `0x0207DF5C` is a **one-word literal pool** holding `0x000003FF`, loaded twice by the rect getter
  (`pc+0x9C` from `0x0207DEB8`, `pc+0x18` from `0x0207DF3C` — both resolve to `0x0207DF5C`).
- `0x0207DF60` is a **real function the detector missed** — `cmp r2,#6; addls pc,pc,r2,lsl #2`, a 7-case
  jump table whose cases 2, 3, 4 and 5 all branch to one target (`0x0207DF9C`). It is referenced from the
  phase table and from a literal load at `0x0207C734`.

Iteration 124 called this a "7-case jump table at `0x0207DF60`" and put three phase slots in the gap. The
jump table is right. **The gap is not three slots of unknown code** — it is one literal word plus one
undetected function.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x0207DD40 size=540` is one function | **REFUTED** — 8 bodies, 8 terminators; `+540` lands on a literal pool |
| Iteration 124's "interior entry points" are separate functions | **CONFIRMED_STATIC** — each ends in its own `bx lr` |
| `0x4000` and `0x3C000` are arena left/right bounds | **CONFIRMED_STATIC** — tested in the walker, emitted as wall rects in the getter |
| The bounds are 24.8 fixed point | **CONFIRMED_STATIC** — `add r0, r2, r0, lsl #8` at `0x0207DD70` |
| `64`/`960`/`512` are the screen or stage extent in pixels | **PLAUSIBLE** — the arithmetic is certain, the unit is inferred |
| `+0x8`/`+0xC` of the rect are a second corner | **REFUTED** — case 2 stores `-(0x3C000-0x3FF)`; they are a signed extent |
| The gap holds three uncatalogued phase slots | **REFUTED** — one literal word, one undetected function |
| The two wall arms use the same condition | **REFUTED** — `ne` left, `eq` right, same callee |
| Two phase slots point at byte-identical code | **CONFIRMED_STATIC** — `0x0207DE44` and `0x0207DE80` |

## Next angles, ranked

1. **Read `0x0207DF60` whole** — an undetected function, phase-table target, and the four-cases-one-target
   shape suggests a default-heavy classifier.
2. **Name `B+0x78`'s other bits.** Two of 32 are known (`0x1000000`, `0x2000000`). The same
   write-sites-across-lifetime method that cracked `record+0x40` applies.
3. **Read `0x0206CF28`** — the callee both wall arms consult, and the reason their conditions differ.
4. **Re-audit `functions.json` for other merged records** among phase-table targets. If one 540-byte record
   hid eight functions, sizes elsewhere in this module are suspect too.
