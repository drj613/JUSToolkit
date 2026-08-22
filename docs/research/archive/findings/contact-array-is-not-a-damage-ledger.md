# Findings: the contact array is not a damage ledger

Loop-Atlas iteration 59. Static.

Read `0x020823E4`, the sole producer of the value pipeline stage 8 accumulates into the contact array.

**It is fixed-point 2D arithmetic, not damage.** The accumulated quantity is `(r5 + r0) >> 2`, computed
with 16-bit sign-extension, a 303-caller coordinate-packing utility, and **none** of the damage
multipliers this campaign has documented.

The contact array does not connect the collision subsystem to the damage pipeline. Iteration 57's
lead is closed.

---

## 1. The result

One write through the out-pointer, at the very end of 175 instructions:

```
0x02082650  tst r2, #0x20
0x02082654  beq #0x2082678
0x02082658  ldr r2, [pc, #0x3c]      ; = 0x02092E68, a byte table
0x0208265C  ldrb r1, [r2, r1]        ; classify
0x02082660  cmp r1, #2
0x02082664  orreq r1, r6, #4
0x02082668  lsleq r1, r1, #0x10
0x0208266C  lsleq r2, r5, #6         ; r5 * 64
0x02082670  asreq r6, r1, #0x10      ; sign-extend 16-bit
0x02082674  subeq r0, r0, r2, asr #8 ; r0 -= (r5*64) >> 8   == r0 -= r5/4
0x02082678  add r0, r5, r0
0x0208267C  asr r1, r0, #2           ; >> 2
0x02082680  mov r0, r6
0x02082684  str r1, [fp]             ; *out = (r5 + r0) >> 2
0x02082688  pop {...}
```

The routine returns a flags value in `r0` and the accumulated magnitude `*out = (r5 + r0) >> 2`.

`lsl #0x10` then `asr #0x10` is 16-bit sign extension. `lsl #6` then `asr #8` is ×64 then ÷256, net ÷4.

## 2. Instruction mix: shifts, not multiplies

| kind | count | | kind | count |
|---|---|---|---|---|
| `ldr`/`str` | 32 | | `asr #imm` | 7 |
| branch | 25 | | `lsr #imm` | 5 |
| `lsl #imm` | 20 | | `ldrh`/`ldrsb`/… | 5 |
| `cmp #imm` | 13 | | `sub #imm` | 3 |
| `add reg` | 9 | | `mul`/`mla` | **3** |
| | | | `sub reg` | 3 |

32 shifts against 3 multiplies. Power-of-two scaling — this engine's standard geometry arithmetic.

## 3. The two calls

| callee | direct callers ROM-wide | what it is |
|---|---|---|
| `0x0207342C` | **303** (arm9 8, ov0 28, ov1 34, ov2 17, ov3 16, ov4 28, ov5 90, ov6 65, ov7 13, ov12 4) | a core utility — its prologue does `lsl r1,r5,#0x10; lsl r0,r6,#0x10; orr r7,r1,r0,lsr #16`, packing two 16-bit values into one word |
| `0x02031070` | 51 | refcount release — decrements `[r0+0x9c4]` and calls `0x02030F68` at zero |

**303 callers across 10 binaries makes `0x0207342C` library code, not domain logic.** The most-called
function this campaign has found. Tagging it as a utility now saves misreading it later.

Two 16-bit values packed into one word is the standard coordinate-pair representation.

## 4. No damage constants

Every `mov Rd,#imm` in the function: **`0`, `40`, `122`, `256`**.

The campaign's two damage scalars are **`×5`** (jpower `damage1` = displayed damage × 5) and **`×64`**
(HP units). Neither appears; none of the three multiplies uses them. `256` is the fixed-point scale.

The byte table at `0x02092E68` — `01 01 02 02 02 02 02 02 02 02 02 02` then zeros — is a 12-entry
classification (class 1 or 2), read with `ldrb` and compared against `2`. Not a damage table.

## 5. What this settles, and what it does not

**Settled:** the accumulated values are not damage. No `×5` or `×64`, a power-of-two-scaled sum, and a
coordinate-packing utility. The contact array is **not** a per-pair damage ledger.

**Not settled:** what the magnitudes are. Overlap depth, separation distance, and impulse all fit
`(r5 + r0) >> 2` over packed coordinates. Telling them apart requires identifying the two input objects'
`+0xC` fields — a separate thread.

Four wakes of collision work produced a well-mapped subsystem whose output doesn't touch the question
that started the search. Stating the negative plainly so it's on the record.

## Predictions status

| Claim | Verdict |
|---|---|
| The accumulated value is `(r5 + r0) >> 2` | **CONFIRMED_STATIC** — single write at `0x02082684` |
| The producer works in 16-bit fixed point | **CONFIRMED_STATIC** — `lsl #0x10`/`asr #0x10` pairs; 32 shifts vs 3 multiplies |
| The accumulated values are damage figures | **REFUTED** — no `×5` or `×64`; immediates are only `0`, `40`, `122`, `256` |
| The contact array links collision to the damage pipeline | **REFUTED** — closes iteration 57's lead |
| `0x0207342C` is domain logic | **REFUTED** — 303 callers across 10 binaries; a coordinate-packing utility |
| `0x02031070` is math | **REFUTED** — refcount release on `[r0+0x9c4]` |
| The byte table at `0x02092E68` is a damage table | **REFUTED** — 12 entries of class 1/2, read with `ldrb`, compared to `2` |
| The magnitudes are overlap depth specifically | **not claimed** — depth, distance and impulse all fit |

## Next angles, ranked

1. **Identify the two input objects' `+0xC` fields.** `0x020823E4` dereferences both `r0+0xC` and
   `r1+0xC`; naming those would say what geometry is being measured.
2. **Add the alignment check to `struct_fields.py`** (carried from iteration 58) — flag word loads at
   non-4-aligned offsets and halfword loads at odd offsets.
3. **Read collision pipeline stages 1–7** — still seven unexamined functions, each taking the manager once
   per frame.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
