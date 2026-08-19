# Findings: what the contact array accumulates, and an unaligned-load tell

Loop-Atlas iteration 58. Static.

Traced the two values stage 8 accumulates into the contact array. **`[sp,#0x4c]` is an out-parameter
filled by `0x020823E4`**, a 175-instruction pairwise routine; **`r7` is a signed byte scaled by 256.**

Whether these are damage figures is **not settled**. The producer's arithmetic (3 multiplies, 20 shifts)
leans geometry, not damage — but that's a lean, not a finding.

Useful byproduct: **a word load at a non-4-aligned offset means your scan is contaminated.** This caught
a bad result of mine in the same wake.

---

## 1. `[sp,#0x4c]` is an out-parameter

`0x02080F14`'s frame is `0x50` bytes (`push` of 10 registers, then `sub sp,sp,#0x50`), so `0x4c` is a
local. **Read 8 times, never stored directly** — the write goes through a pointer:

```
0x0208126C  add r3, sp, #0x4c        ; r3 = &local_4C   (out-parameter)
0x02081270  tst r0, #1
0x02081274  movne r2, #1
0x0208127C  mov r0, r5
0x02081280  bl  #0x20823e4           ; f(r0, r1=r6, r2=flag, r3=&out)
...
0x020812CC  ldr r3, [sp, #0x4c]      ; read the result back
0x020812D4  add r3, ip, r3
0x020812DC  str r3, [r8, r0, lsl #2] ; also accumulated into a second, word-indexed array
```

`0x020823E4` computes the accumulated value. It lands in **two** places: the word array at `[r8, r0*4]`
here, and the contact array via the four accumulator blocks.

## 2. `r7` is a signed byte × 256

```
0x02081298  ldr   r1, [r6, #0x10]
0x020812A0  ldrsb r1, [r1, #5]
0x020812AC  str   r1, [sp, #0x38]
0x020812B0  ldr   r2, [sp, #0x38]
0x020812C0  lsl   r7, r2, #8
```

Signed byte from `[r6+0x10]+5`, shifted left 8 — fixed-point 8.8, matching the `×64`/`×256` scaling
seen elsewhere in this engine.

## 3. The object at `[r6+0x10]` — two byte fields, and no claim

Guarded scan (`struct_fields.py`, anchors `0x020812A0:1` and `0x0208125C:0` — both sites where the
register provably holds `[r6+0x10]`) finds **exactly two** accesses:

| offset | kind |
|---|---|
| `+0x05` | `ldrsb` |
| `+0x0E` | `ldrsb` |

These offsets match `DurationMult` and `DamageFlags` in `CollisionEntry`. **Not claimed**: any 20-byte
struct has bytes at `+0x05` and `+0x0E`, and two hits is not evidence of a shared layout. Iteration 50's
`+0x1a` near-miss on `prmData` was the same shape.

## 4. The unaligned-load tell

Before the guarded scan I ran an inline walk — register-write stops only, no branch handling. It reported
**six** offsets off `[r6+0x10]`, including `ldr` (word) loads at `+0x01`, `+0x02`, `+0x10` and `+0x11`.

**A word load at a non-multiple-of-4 offset is a contradiction.** ARM will execute it (with rotation), but
no compiler emits one for a struct field. `ldr [rX,#1]` means the scan is contaminated or the struct
assumption is wrong.

It was contamination: the guarded scan gives 2 offsets, not 6, both `ldrsb`. The four bogus ones came from
crossing branches into code where the register held something else.

Cheap post-hoc check for any field map: **flag every `ldr`/`str` at an offset not divisible by 4, and
every `ldrh`/`strh` at an odd offset.** Real structs are aligned; violations mean a broken scan. Adding
this to `struct_fields.py` is queued.

## 5. The value producer

`0x020823E4`, **175 instructions** (extent checked first, per iteration 57's lesson):

```
0x020823E4  push 0x4FF8
0x020823E8  mov r10, r1
0x020823EC  ldr r4, [r10, #0xC]
0x020823F0  mov r9, r2               ; the flag
0x020823F4  mov r11, r3              ; the out-pointer
0x020823F8  add r7, r4, #0xA4
0x020823FC  ldr r8, [r0, #0xC]
0x02082404  ldr r0, [r1, #0x40]
0x02082414  ldr r1, [r4, #0x68]
0x02082420  ldr r1, [r10, #0x10]
```

Pairwise: two objects (`r0` and `r1`), each dereferenced at `+0xC`, plus a flag and an out-pointer.
Arithmetic across the body: **3 `mul`/`mla` and 20 `lsl`-by-immediate**.

Shift-heavy, multiply-light math over two positioned objects looks like **overlap or distance geometry**,
not damage (damage would more likely be a table lookup or short multiply chain). That's a lean, not a
finding; settling it needs the body read properly.

## Predictions status

| Claim | Verdict |
|---|---|
| `[sp,#0x4c]` is an out-parameter of `0x020823E4` | **CONFIRMED_STATIC** — `add r3,sp,#0x4c` then `bl`, read back after |
| `[sp,#0x4c]` is written by a direct `str` in `0x02080F14` | **REFUTED** — 8 reads, 0 direct stores |
| `r7` = signed byte at `[r6+0x10]+5`, scaled ×256 | **CONFIRMED_STATIC** — `ldrsb` then `lsl #8` |
| The accumulated value also feeds a second array | **CONFIRMED_STATIC** — `str r3,[r8,r0,lsl #2]` at `0x020812DC` |
| `[r6+0x10]` is a `CollisionEntry` | **not claimed** — only 2 byte offsets match; insufficient |
| My inline scan's 6 offsets off `[r6+0x10]` | **REFUTED** — unaligned word loads exposed contamination; the guarded scan gives 2 |
| The accumulated values are damage figures | **still open** — producer is 3 muls / 20 shifts, leaning geometry |

## Next angles, ranked

1. **Read `0x020823E4` properly** — 175 instructions, the sole producer of the accumulated value. This is
   the whole question now, and it's bounded.
2. **Add the alignment check to `struct_fields.py`** — flag word loads at non-4-aligned offsets and
   halfword loads at odd offsets. Caught a real error this wake.
3. **Identify the second array** at `[r8, r0*4]`, indexed by `0x02081A58`'s output.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
