# Findings: `Battle_CharaCreate`'s only caller is Thumb — and the dead-table residual closes

Loop-Atlas iteration 95. Static.

**`Battle_CharaCreate` has zero ARM callers ROM-wide.** Its only caller is **Thumb** code
at ov6 `0x0214D65E` — every prior caller scan in this campaign was ARM-only.

The same Thumb scan against the view's arm function found **nothing**, closing the
residual from iteration 94.

The `[char+0x1b4]` struct's floor tightens from `0x570` to **`0x5F1`**.

---

## 1. The Thumb caller

Scanning `bl`/`blx` in Thumb encoding across all 16 regions gives one hit:

```
ov6 0x0214D65E  thumb blx -> 0x02156A38 (Battle_CharaCreate)
```

Verified as genuine Thumb (not a byte-pattern coincidence):

```
0x0214D650  1c28   add r0, r5, #0
0x0214D652  f6d3 e94c   blx (another call)
0x0214D656  9015   str r0, [sp, #0x54]
0x0214D658  1c28   add r0, r5, #0
0x0214D65A  a912   add r1, sp, #0x48     ; arg1 = a stack descriptor
0x0214D65C  00ac   lsl r4, r5, #2
0x0214D65E  f009 e9ec   blx -> 0x02156A38
0x0214D662  4a01   ldr r2, [pc, #4]
0x0214D666  46c0   nop                   ; Thumb alignment padding
0x0214D668  02172960                     ; literal pool
```

The `46c0` padding and literal pool settle it — the same bytes read as nonsense in ARM.

`arg1` is `sp+0x48`, a stack descriptor, so `[char+0x1b4]` is copied from a local, not
allocated by the constructor.

**The caller is not in `functions.json`.** ov6's earliest catalogued Thumb function is
`0x0214DF14`, well past this — uncatalogued Thumb code exists in ov6.

## 2. The residual from iteration 94 closes

Iteration 94 concluded the view's 16-slot handler table is dead, with one residual:
the enumeration was ARM-only, and 18 of ov6's 752 functions are Thumb.

Scanning for Thumb callers of `0x0215FC20` across all regions: **none**. The dead-table
conclusion holds.

The scan found a Thumb caller where one exists and none where ARM analysis said none —
the expected cross-check behavior.

## 3. `[char+0x1b4]` is at least `0x5F1` bytes

```
0x02156B04  ldr  r1, [r5]            ; r5 = arg1, the stack descriptor
0x02156B08  str  r1, [r4, #0x1b4]    ; install into the character
0x02156B0C  strb r6, [r1, #0x5f0]    ; ...and immediately write +0x5F0 on it
```

Previous floor was `0x570` (the `+0x56c` gauge pointer). `+0x5F0` raises it to **`0x5F1`**.

Still unnamed. Two routes excluded:

- **not tagged-allocated** — the census has nothing between `0x570` and `0x1040`
- **not memset wholesale** — the only block write covering `+0x5F0` is
  `Battle_ColJointManCreate`'s `0x1040`, a different object

Same profile as ColPrm: reached by pointer, sized only by field usage.

## 4. The parameter table is runtime-only

`[[0x02172984]+0xC]` cannot be read statically. **ov6 spans `0x0214CD20`–`0x02172960`**,
so `0x02172984` is past the end — a BSS global holding a runtime pointer. The 16
`{u16, u16}` entries aren't at a computable ROM address.

Blocked by the static-only constraint.

## Predictions status

| Claim | Verdict |
|---|---|
| `Battle_CharaCreate` has no ARM caller anywhere in the ROM | **CONFIRMED_STATIC** — raw word and `bl` scan over all 16 regions, 0 hits |
| It is called from Thumb at ov6 `0x0214D65E` | **CONFIRMED_STATIC** — `f009 e9ec` decodes to `blx 0x02156A38`; surrounding `46c0` padding and literal pool confirm Thumb |
| That hit is a byte-pattern coincidence | **REFUTED** — the ARM reading of the same bytes is nonsense; the Thumb reading is a coherent call sequence |
| The Thumb caller is catalogued in `functions.json` | **REFUTED** — ov6's earliest catalogued Thumb function is `0x0214DF14` |
| A Thumb caller exists for the view's arm function `0x0215FC20` | **REFUTED** — 0 hits across all regions; iteration 94's residual closes |
| `[char+0x1b4]` is at least `0x5F1` bytes | **CONFIRMED_STATIC** — `strb r6,[r1,#0x5f0]` at `0x02156B0C` |
| `[char+0x1b4]` is allocated by `Battle_CharaCreate` | **REFUTED** — it arrives as `[arg1+0x0]`, `arg1` = `sp+0x48` in the Thumb caller |
| `[char+0x1b4]` is tagged-allocated or wholesale-memset | **REFUTED** — nothing in the census between `0x570` and `0x1040`; the only covering block write is a different object |
| The table at `[[0x02172984]+0xC]` can be read statically | **REFUTED** — `0x02172984` is past ov6's end at `0x02172960`; a BSS global |
| Other functions have Thumb-only callers | **not claimed** — two targets scanned; the campaign's caller analysis has been ARM-only throughout |

## Next angles, ranked

1. **Re-run Thumb caller scan against every "0 callers" function.** At least `0x0207D440`,
   `0x021570EC` and `0x0215FB64` were characterised that way — one already had a Thumb caller.
2. **Follow the Thumb caller at `0x0214D65E` upward** — it builds the descriptor whose
   `+0x0` is the `≥0x5F1` struct; best remaining handle on naming it.
3. **Read `char+0x7c`'s users** `0x02158B20`, `0x021586D0` (carried).
4. **Map `BattleCol.cpp`** (carried).
