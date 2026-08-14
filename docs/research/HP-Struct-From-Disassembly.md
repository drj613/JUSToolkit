# The HP fields, from ARM9 disassembly

**Status:** read from disassembly of `arm9.bin` (uncompressed, maps 1:1 at
`0x02000000`), cross-checked against live RAM. This supersedes the guesswork in
`HP-And-Damage-Runtime-Findings.md` about which field is which.

## Two HP fields, not one

Two small functions sit right before the address our notes call
`fn_health_calc` (`0x020784FC`), and together they name the fields.

### `0x020784B8` — add to MAX HP, clamped

```asm
0x020784B8  ldr   r2, [r0, #0x56c]   ; r2 = character struct
0x020784BC  ldrsh r0, [r2, #0x16]    ; load field +0x16 as SIGNED HALFWORD
0x020784C0  cmp   r0, #0x4000
0x020784C4  movge r0, #0
0x020784C8  bxge  lr                 ; already at the cap -> return 0
0x020784CC  add   r0, r0, r1         ; += argument
0x020784D0  cmp   r0, #0x4000
0x020784D4  movgt r0, #0x4000        ; clamp
0x020784D8  strh  r0, [r2, #0x16]    ; store back
0x020784DC  mov   r0, #1
```

### `0x020784E4` — is current HP below a percentage of max?

```asm
0x020784E8  ldr   r4, [r0, #0x56c]
0x020784EC  ldrsh r2, [r4, #0x16]    ; MAX
0x020784F0  mul   r0, r2, r1         ; max * pct
0x020784F4  mov   r1, #0x64          ; 100
0x020784F8  bl    0x0200d12c         ; divide -> (max * pct) / 100
0x020784FC  ldrsh r1, [r4, #0x18]    ; CURRENT
0x02078500  lsl   r0, r0, #0x10
0x02078504  cmp   r1, r0, asr #16
0x02078508  movle r0, #1             ; current <= pct% of max
0x0207850C  movgt r0, #0
```

So:

| struct offset | size | field |
|---|---|---|
| `+0x16` | s16 | **max HP** |
| `+0x18` | s16 | **current HP** |
| `+0x41` | u8 | `chr_b` index |

Both HP fields are loaded with `LDRSH` — **signed halfwords**. That settles the
16-bit question from the code itself, not from arithmetic on observed values.

## The 0x4000 cap confirms the 1/64 scale and the +8 bonus model

Max HP is clamped to `0x4000` = 16384. At 1/64 units that is **256.0 displayed
HP**.

The highest base HP anywhere in `chr_b.bin` is **224**. The maximum bonus is
**+32** (four stacking `Ｊ魂最大値＋` sources: leader plus three relationship
adjacencies). `224 + 32 = 256`.

The hardcoded engine cap is exactly the theoretical maximum the data can
produce. Three independently-derived numbers — the 1/64 scale, the 224 table
maximum, and the 4×8 bonus — meet at `0x4000`. That is strong mutual
confirmation, and it also identifies `0x020784B8` as the routine that applies
the `Ｊ魂最大値＋` ability.

## The offsets cross-check the RAM scan exactly

The runtime scan (`scripts/emu/find_battle_structs.py`) locates slots by
treating **current HP as the slot base**, and finds the `chr_b` index at
**`+0x29`** from there.

The disassembly puts current HP at struct `+0x18` and the index at struct
`+0x41`:

`0x18 + 0x29 = 0x41` ✓

So the scanner's "base" is `struct + 0x18`, and the two methods describe the
same structure. That arithmetic agreeing is not something two wrong models do.

**Therefore max HP is at `scan_base − 2`.** Verified live: at full health a
character reads 10240 at both `base` and `base − 2`, as it must.

## chr_b lookup, confirmed in code

Two accessors just below use the index to reach `chr_b`:

```asm
0x02078514  ldr   r2, [pc, #0x1c]    ; -> 0x0214BD80
0x02078518  ldrb  r3, [r0, #0x41]    ; chr_b index
0x0207851C  ldr   r2, [r2]
0x02078520  mov   r0, #0x3c          ; 60 = chr_b record size
0x02078524  ldr   r2, [r2, #0x40]    ; -> chr_b table base
0x02078528  mla   r0, r3, r0, r2     ; record = base + index*60
0x0207852C  add   r0, r0, r1, lsl #1
0x02078530  ldrh  r0, [r0, #0x24]    ; halfword array at record+0x24
```

A second variant at `0x0207853C` reads a **byte** array at `record + 0x2C`.

This confirms independently that `chr_b` records are **60 bytes** and are indexed
by that per-character id, and it surfaces two per-record arrays we had not
catalogued: halfwords at `+0x24` and bytes at `+0x2C`, both indexed by a
caller-supplied value.

The table pointer is reached via `[[0x0214BD80] + 0x40]`. Note `0x0214BD80` sits
just *below* `0x0214CD20`, the address ten overlays share, so it is in the
always-resident region and safe to reference. See
`Overlay-Residency-In-Battle.md`.

## Still open

The **resistance magnitude** is not in these functions. `0x020784B8` and
`0x020784E4` handle max-HP growth and a threshold test; neither applies damage.
The subtraction site — and whether blunt resistance is a multiply or a
subtraction — has not been located yet. Battle code lives in `arm9.bin` **and
overlay ov06** (154KB, confirmed resident during combat), so ov06 is the next
place to look.
