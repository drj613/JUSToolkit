# Findings: the narrowphase pair test, and the alignment guard earns its keep

Loop-Atlas iteration 60. Static. Tool change: `struct_fields.py` gains guard 7 (alignment).

The two objects `0x020823E4` measures are **peer entities from the collision bucket lists**, each with a same-type sub-object at `+0xC` sharing a `+0x40` field.

This completes the collision subsystem's shape: 22 buckets → walk pairs → measure each pair geometrically → accumulate into the contact matrix at `manager+0x154`.

The alignment guard caught a bogus `+0x175` field on its first use.

---

## 1. Guard 7: alignment

From iteration 58. A word `ldr`/`str` at an offset not divisible by 4, or a halfword access at an odd offset, is never a real struct field — no compiler emits one. The tool flags these per-offset and marks the whole map suspect.

It fired immediately. An unguarded walk of the `[arg0+0xC]` object reported:

```
0x02082500  ldr r7,[r8,#0x175]      <- 0x175 is not 4-aligned
```

Guarded scan returns `+0x40` and `+0x44` only. `+0x175` was contamination — the alignment check caught it without a second opinion.

Selftest still passes (same 12 NoteTrack fields).

## 2. The two input objects

`0x020823E4(r0, r1, flag, &out)` dereferences both arguments at `+0xC`:

| source | fields found | anchors |
|---|---|---|
| `[r1+0xC]` (via `r4`) | `+0x40`, `+0x68` | `0x02082414` |
| `[r0+0xC]` (via `r8`) | `+0x40` (×5, `ldr` **and** `str`), `+0x44` (×2) | `0x020824DC`, `0x02082544`, `0x02082574` |

**Both carry a `+0x40` field.** On the `r0` side it is read *and written* — the function mutates one participant's `+0x40` while only reading the other's.

**`r8` is written exactly once in the entire 175-instruction function**, at `0x020823FC` (`ldr r8,[r0,#0xC]`). No reassignment, so every `[r8,#imm]` in the body is a field of that object.

## 3. The arguments are peer entities from a bucket walk

At the call site inside `0x02080F14`:

```
0x02081084  ldr r7, [sl, #0x30]     ; sl = the ColPrm manager; +0x30 = bucket 1 of the 22-bucket array
0x02081088  add r5, sp, #0x3c
0x02081094  ldr r1, [r7, #8]
0x02081098  ldr r6, [r7]            ; walk the bucket list
0x0208109C  ldr r0, [r1, #8]
0x020810A0  ldr r1, [r1, #0xc]
0x020810A4  ldr r0, [r0, #0x1c]
0x020810A8  ldr r1, [r1, #0x1c]
...
0x0208113C  ldr r5, [r2, #0x1C]
0x02081140  ldr r6, [r1, #0x1C]     ; both from +0x1C of different bases
0x0208127C  mov r0, r5
0x02081268  mov r1, r6
0x02081280  bl  #0x20823e4
```

`r7` is `manager+0x30` — **bucket 1** of the 22 list heads at `+0x28` (`0x28 + 1×8 = 0x30`, iteration 55). The routine walks that list; `r5` and `r6` both load from `+0x1C` of different bases, same offset on two objects — peers.

The shape: **pull a pair from a collision bucket, measure it, record the result per (row, column) in the contact matrix.** Textbook broadphase → narrowphase split:

```
22 buckets at manager+0x28        broadphase bins, drained every frame
  -> walk a bucket's pairs
     -> 0x020823E4(a, b, flag, &out)      narrowphase: fixed-point geometry on a+0xC and b+0xC
        -> *out = (r5 + r0) >> 2
           -> accumulated into manager+0x154 [row][col]
```

## 4. What is still not named

The `+0xC` sub-object type is unnamed. Two fields is too thin, and `+0x40`/`+0x44`/`+0x68` match nothing mapped so far. The iteration-58 lesson (two matching byte offsets ≠ layout match) applies just as well to three word offsets.

`+0x1C` on the participants: same offset on both, purpose unknown.

## Predictions status

| Claim | Verdict |
|---|---|
| Guard 7 catches the iteration-58 contamination | **CONFIRMED** — `+0x175` flagged/removed; selftest unchanged |
| `[r0+0xC]` has fields `+0x40` and `+0x44` | **CONFIRMED_STATIC** — `r8` written exactly once, at `0x020823FC` |
| `[r1+0xC]` has fields `+0x40` and `+0x68` | **CONFIRMED_STATIC** — anchor `0x02082414` |
| Both sub-objects share a `+0x40` field | **CONFIRMED_STATIC** — same offset on both |
| `0x020823E4` mutates one participant's `+0x40` | **CONFIRMED_STATIC** — 5 accesses on the `r0` side, `ldr` and `str` |
| The two arguments are peer entities | **CONFIRMED_STATIC** — both loaded from `+0x1C` of different bases |
| `r7` is bucket 1 of the 22-bucket array | **CONFIRMED_STATIC** — `[manager+0x30]`, `0x28 + 8` |
| The subsystem is a broadphase/narrowphase split | **PLAUSIBLE (strong)** — bucket walk feeding a pairwise geometric test |
| The `+0xC` sub-object type is identifiable from these fields | **not claimed** — three word offsets match nothing mapped |

## Next angles, ranked

1. **Read collision pipeline stages 1–7.** Stage 8 is understood end-to-end; the other seven are unexamined. Stage ordering will show where the buckets get *filled* — the remaining half of the broadphase.
2. **Name the `+0x1C` participant field** by finding what else in the ROM reads `+0x1C` off the same objects.
3. **Trace `0x02081A58`** (packed nibbles → row index) — defines the contact matrix's rows.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
