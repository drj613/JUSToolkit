# Findings: a Thumb disassembler, and what calls `Battle_CharaCreate`

Loop-Atlas iteration 97. Static.

This repo had no Thumb disassembler — `query.py disasm` is ARM-only, and iterations 95–96
showed ov6 carries uncatalogued Thumb code with real calls.

`scripts/decomp/thumb_disasm.py` is committed and selftested against iteration 95's
hand-decoded call site; every instruction matches.

Result: `Battle_CharaCreate` is called **from inside a loop**, with a stack descriptor
built four fields at a time. The `≥0x5F1` struct is still unnamed.

---

## 1. The call

```
0x0214D658  1c28       add r0, r5, #0        ; arg0 = r5, the loop index
0x0214D65A  a912       add r1, sp, #0x48     ; arg1 = the descriptor
0x0214D65C  00ac       lsl r4, r5, #2
0x0214D65E  f009 e9ec  blx #0x02156a38       ; Battle_CharaCreate
0x0214D662  4a01       ldr r2, [pc, #0x4]
0x0214D664  e016       b   #0x0214d694
```

`r5` increments against a bound (`add r5,r5,#1`; `cmp r5,r4`; `blt`), so **characters are
created in a loop** with `arg0` as the index. This matches `strb r6,[r4,#0x1e0]` in the
constructor — iteration 74's entity index, written from `arg0`.

## 2. The descriptor

Built at `sp+0x48`:

| descriptor | filled from |
|---|---|
| `+0x00` (`sp+0x48`) | `r1`, set earlier in the function |
| `+0x04` (`sp+0x4C`) | `[[0x0214D680] +0x0] +0x4` |
| `+0x08` (`sp+0x50`) | return of `blx #0x02173004` — **one of three sources, see the correction below** |
| `+0x0C` (`sp+0x54`) | return of `blx #0x02173014` — **one of three sources, see the correction below** |

> **CORRECTED, iteration 151.** The two rows above are incomplete. `+0x08` and `+0x0C`
> are each filled from **three** alternative function pairs, selected by guards this
> document could not read because `thumb_disasm.py` was decoding every `cmp Rd,#imm` as
> `mov Rd,#imm` (fixed in iteration 150). See
> `findings/chara-setup-loop-has-three-descriptor-paths.md`. The claim "the descriptor's
> first four words come from four distinct sources" holds for `+0x00` and `+0x04` but
> understates `+0x08`/`+0x0C`.

```
0x0214D5F0  9112       str r1, [sp, #0x48]
0x0214D5F2  4923       ldr r1, [pc, #0x8c]  ; = 0x0214D680
0x0214D5F4  6809       ldr r1, [r1, #0x0]
0x0214D5F6  6849       ldr r1, [r1, #0x4]
0x0214D5F8  9113       str r1, [sp, #0x4c]
...
0x0214D614  f025 ecf6  blx #0x02173004
0x0214D618  9014       str r0, [sp, #0x50]
0x0214D626  f025 ecf6  blx #0x02173014
0x0214D62A  9015       str r0, [sp, #0x54]
```

`Battle_CharaCreate` also reads `arg1` at `+0x10`, `+0x14`, `+0x1C`, `+0x1D` (iteration 74),
so the descriptor is at least `0x20` bytes — beyond these four slots.

**`[descriptor+0x00]` is the `≥0x5F1` struct**, installed at `char+0x1b4`. Its origin is
further back in this function.

## 3. The caller is a setup routine

Large and loop-driven, filling several stack buffers before the call:

```
0x0214D536-0x0214D54A   copy an array into sp+0x78, indexed by r5
0x0214D54E-0x0214D554   sp+0x28 [0] = 0, [1] = 1
0x0214D5C6-0x0214D5CE   ldr r3,[r2,#0x158]; cmp r0,r3; blt   -- a count on r2
0x0214D5D4              ldr r0,[r2,#0x104]
0x0214D5D6-0x0214D5DE   add r3,sp,#0x64; add r2,sp,#0x58; blx #0x02162B60
```

`r2` carries a word-indexed struct with a loop bound at `+0x158` and a field at `+0x104`.
Whether `r2` is `[descriptor+0x00]` is **not claimed** — both are large and word-indexed,
which is not evidence.

No `push {…,lr}` appears between `0x0214D400` and `0x0214D5C4`, so the prologue is
earlier still.

## 4. About the disassembler

Covers ARMv4T encodings present in this ROM's Thumb regions. Unrecognized opcodes print
as `.hw <value>` — a wrong decode is worse than a gap.

## Predictions status

| Claim | Verdict |
|---|---|
| Decoder reproduces iteration 95's hand-decoded call site | **CONFIRMED_STATIC** — all six instructions identical, selftest asserts three |
| `Battle_CharaCreate`'s `arg0` is a loop index | **CONFIRMED_STATIC** — `add r0,r5,#0` with `r5` incremented against a bound |
| `arg1` is a stack descriptor at `sp+0x48` | **CONFIRMED_STATIC** — `add r1,sp,#0x48` |
| The descriptor's first four words come from four distinct sources | **CONFIRMED_STATIC** — `sp+0x48`/`0x4C`/`0x50`/`0x54` |
| Descriptor is 4 words | **REFUTED** — constructor reads `arg1+0x10`, `+0x14`, `+0x1C`, `+0x1D`, so ≥ `0x20` bytes |
| `r2` in setup loop is the `≥0x5F1` struct | **not claimed** — both large and word-indexed; not evidence |
| `≥0x5F1` struct is named | **not claimed** — origin is further back in the caller |

## Next angles, ranked

1. **Find the caller's prologue and read it whole.** Starts before `0x0214D400`; it builds
   every argument characters are created from — the highest-value Thumb function in ov6.
2. **Identify `0x02173004` and `0x02173014`** — both past ov6's end at `0x02172960`;
   another overlay or a thunk table.
3. **Catalogue ov6's early Thumb region** (carried) — `functions.json` starts at
   `0x0214DF14`; this function is well below it.
4. **Read `char+0x7c`'s users** `0x02158B20`, `0x021586D0` (carried).
