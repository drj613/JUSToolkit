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
`Overlay-Residency-By-Mode.md`.

## HP initialization proves the ×64 scale in code

At `0x02077C50`:

```asm
0x02077C4C  strb  r3, [r1, #0x49]   ; regen rate (set from a conditional above)
0x02077C50  ldrb  lr, [r4, #0x10]   ; BYTE at record +0x10  <-- chr_b HP field
0x02077C58  lsl   lr, lr, #6        ; x64
0x02077C5C  strh  lr, [r1, #0x16]   ; max HP
0x02077C60  ldrsh lr, [r1, #0x16]
0x02077C64  strh  lr, [r1, #0x18]   ; current HP = max
```

This is conclusive on two points that were previously inferred:

1. **`chr_b` record offset `0x10` holds displayed HP as a byte** — exactly the
   field identified from the data side.
2. **Runtime HP = that byte `<< 6` = × 64.** The 1/64 scale is not a
   reverse-engineered guess; it is a shift instruction.

A second copy of the same pattern sits at `0x02077CF4`.

## The single HP-delta application function

**`0x02078488`** is where every HP change lands:

```asm
0x02078488  ldrsh r2, [r0, #0x18]   ; current
0x0207848C  adds  r1, r1, r2        ; delta + current
0x02078490  ldrsh r2, [r0, #0x16]   ; max
0x02078494  movmi r1, #0            ; negative -> clamp to 0
0x02078498  cmp   r1, r2
0x0207849C  movgt r1, r2            ; over max -> clamp to max
0x020784A0  strh  r1, [r0, #0x18]   ; store
0x020784A4  ldrsh r0, [r0, #0x18]
0x020784AC  movne r0, #1            ; return 1 = still alive
0x020784B0  moveq r0, #0            ; return 0 = dead
```

So: `HP = clamp(current + delta, 0, max)`, returning whether the character
survived. **Damage is simply a negative delta.**

`0x020783CC` is the public entry point — a thunk that dereferences `[r0, #0x56C]`
to reach the character struct and tail-calls the above (the `.word` at
`0x020783D8` is `0x02078488`, which the disassembler renders as a bogus `andeq`).
`0x020783DC` is a list variant that applies one delta to every non-KO'd
character in a linked list.

### The damage callers are all in ov06

`bl 0x020783CC` appears **8 times in ov06 and 0 times in arm9.bin**.

This is the concrete payoff of identifying the battle overlay: anyone searching
only `arm9.bin` cannot find a single damage site. (That is exactly what happened
to a one-hour automated attempt at this before the overlay was known.)

Call sites: `0x02157DC0`, `0x021582C4`, `0x02158BC0`, `0x02159274`,
`0x021592D0`, `0x0215952C`, `0x02159668`, `0x0215A318`.

**Where resistance is NOT.** The delta arrives at these call sites already
computed — one of them loads it straight out of an effect record
(`ldrsh r1, [r1, #4]`). So blunt/slash resistance is applied *upstream* of the
apply function, in whatever computes the delta. That still isn't located, but the
search space is now "the producers of r1 at those 8 sites" rather than all of
battle code.

## Other HP writers, characterized

| address | what it does |
|---|---|
| `0x02077DA4` | `current += [+0x49] * 2`, clamp to max — **regeneration** |
| `0x02077E08` | `current += [+0x4A]`, clamp to max — a second regen rate |
| `0x02077E50` | `current += [+0x49]`, clamp to max |
| `0x02078474` | `current = max * r7 / 100` — set HP to a percentage |
| `0x02078604` | `smulbb` then divide then store — a multiplicative HP change |
| `0x02078778` | `add r2, r2, r2, lsr #31; asr r2, #1` — signed **halve HP** |
| `0x021595F8`, `0x0215C4D0` | store **0** to current HP — KO / reset |
| `0x020784D8` | add to **max** HP, clamp `0x4000` — the `Ｊ魂最大値＋` ability |

The regen entries are almost certainly the training-mode auto-heal measured from
the emulator (~64 raw units per ~2 frames): if `[+0x49]` is 32, then `32 × 2 =
64` per tick matches exactly. Note `[+0x49]` is written at init
(`0x02077C4C`), so it is per-character configuration, not a mode flag — the
mode presumably selects the rate.

## The 8 call sites are a script-effect dispatcher, not the melee path

Traced with `scripts/find_callers.py`, which decodes the ARM `BL` encoding
directly out of every extracted binary instead of grepping a partial text
disassembly. It confirms exactly 8 callers of `0x020783CC`, all in ov06.

Each is a small handler of the same shape:

```asm
0x02159264  ldr   r1, [r1, #4]     ; effect record
0x0215926C  ldrsh r1, [r1, #4]     ; signed halfword parameter from data
0x02159270  lsl   r1, r1, #6       ; x64  (displayed -> raw)
0x02159274  bl    0x020783CC       ; apply
```

Two useful facts fall out:

- **`lsl #6` here means damage/heal values are authored in *displayed* units** and
  scaled to the 1/64 representation at the last moment. A sibling at
  `0x02159290` uses `lsl #8` into a different stat, so this is a family of
  "apply data parameter to stat X" handlers.
- The measured **1.250** damage (80 raw) is *not* a multiple of 64, so it did
  **not** come through a `lsl #6` handler. At least one damage path computes a
  genuine sub-integer value.

The remaining sites take their delta from a register supplied by the enclosing
dispatcher (`0x02157DC0` sits in a switch with `b 0x02157f90` after each case) or
from a config field (`0x0215A318`). **None of the 8 contains resistance math.**

So the resistance magnitude lives upstream, in whatever resolves a hit into a
damage value before invoking this dispatcher. Still not located — but the
architecture is now mapped rather than guessed at.

## Nature is NOT resolved during battle

Worth recording because the opposite is an easy and tempting inference.

The panel-nature predicate at `0x02078CB8`
(`nib = (koma.flags[0xB] >> 4) & 0xF; return nib != 3`) sits in `arm9.bin`, and
the nature resolver is at `0x0214E480`. An exhaustive BL scan over `arm9.bin`
plus all 14 overlays gives:

| function | callers |
|---|---|
| `0x02078CB8` nature predicate | **1**, in ov05 (`0x02156C70`) |
| `0x0214E480` nature resolver | **2**, both in ov05 |
| `0x020783CC` HP apply | 8, all in ov06 |

**Zero callers in ov06.** Nature is resolved only while ov05 is resident, never
in the battle overlay. There is also no function-pointer reference to either
address anywhere, so it isn't reached indirectly.

The general trap: **`arm9.bin` is the always-resident image and contains code
for every mode.** A function being in `arm9.bin` says nothing about which mode
runs it — only the caller does. `0x02078CB8` operates on a *koma record*
(deck data), not on a battle character struct, which fits.

Consequence: do not expect a nature multiplier in the damage path on the strength
of that function's location. If the nature triangle affects damage, it has to
surface some other way.

Note also that the resolver at `0x0214E480` exists **only in overlay 05** — not
in ov01, which is the overlay actually resident on the deck-editor screen
(see `Overlay-Residency-By-Mode.md`). Which mode loads ov05 is still unidentified,
so addresses in that window need the resident overlay named alongside them.

## Still open

The **resistance magnitude** is not in these functions. `0x020784B8` and
`0x020784E4` handle max-HP growth and a threshold test; neither applies damage.
The subtraction site — and whether blunt resistance is a multiply or a
subtraction — has not been located yet. Battle code lives in `arm9.bin` **and
overlay ov06** (154KB, confirmed resident during combat), so ov06 is the next
place to look.
