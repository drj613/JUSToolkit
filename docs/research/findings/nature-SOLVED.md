# NATURE SOLVED — and three of my earlier claims were wrong

Loop-Atlas iteration 11. Static. This closes the last unknown in the koma system.

Nature isn't stored per panel. It's computed through a sentinel-and-fallback scheme — which is exactly why my table searches couldn't find it.

## The rule

From the deck-editor accessor at **`0x0214E480`** (overlay disassembled in `jus_files/analysis/disasm/ov5.txt`; copy in `arm9.txt` at `0x02076F70` / `0x02078CB8`). `r0` = pointer to a `koma.bin` record.

```
helper  (panelType 2) -> 3 (なし), short-circuit on type, flags ignored
battle  (panelType 0) -> nib = (flags >> 4) & 0xF
                         nature = nib               if nib != 3
                         nature = chr_b[abilityId + 0x00]   if nib == 3
support (panelType 1) -> nature = chr_s[abilityId*20 + (kshapeGroup-1)*8]
```

**Nature enum: `0` = 力 Power, `1` = 知 Knowledge, `2` = 笑 Laughter, `3` = なし Neutral.**

The trick: **`3` in the high nibble is a "no override" sentinel**, not a value. When present, the code falls through to the character's base nature. Any other nibble value *is* the nature directly — no lookup table involved.

```asm
0x0214E48C  ldrb   r1, [r0, #0xb]   ; flags
0x0214E490  asr    r1, r1, #4       ; high nibble
0x0214E498  cmp    r1, #3           ; sentinel?
0x0214E49C  bne    #0x214e4bc       ; no -> nibble IS the nature
0x0214E4A0  ldr    r1, [pc, #0x50]  ; -> 0x0214BD80
0x0214E4A4  ldrb   r2, [r0, #7]     ; abilityId
0x0214E4AC  mov    r0, #0x3c        ; stride 60
0x0214E4B4  ldr    r1, [r1, #0x40]  ; chr_b base
0x0214E4B8  ldrb   r1, [r1, r0]     ; chr_b[abilityId] + 0x00  = BASE NATURE
```

Implemented in `scripts/analysis/dump_koma.py` (`resolve_natures`).

## Verification

All nine Naruto panels match the owner's observed table:

| koma | size | type | flags | nibble | computed | owner |
|---|---|---|---|---|---|---|
| 497 | 1 | helper | `0x30` | 3 | なし | なし ✓ |
| 498 | 2 | support | `0x30` | 3 | 笑 | 笑 ✓ |
| 499 | 3 | support | `0x30` | 3 | 力 | 力 ✓ |
| 500 | 4 | battle | `0x30` | 3 | 力 | 力 ✓ |
| 501 | 4 | battle | `0x20` | 2 | 笑 | 笑 ✓ |
| 502 | 5 | battle | `0x30` | 3 | 力 | 力 ✓ |
| 503 | 6 | battle | `0x30` | 3 | 力 | 力 ✓ |
| 504 | 7 | battle | `0x30` | 3 | 力 | 力 ✓ |
| 505 | 8 | battle | `0x30` | 3 | 力 | 力 ✓ |

**9 of 9.** CONFIRMED.

Whole-game distribution across 890 panels: **力 226, 知 183, 笑 169, なし 312**.

| type | distribution |
|---|---|
| battle (206) | 力 96, 知 57, 笑 53 |
| support (372) | 力 130, 知 126, 笑 116 |
| helper (312) | なし 312 |

The split looks designed, not accidental. All 372 supports and all 312 helpers carry nibble `3`. Only **32** battle panels carry an explicit override (nibbles `{0: 12, 1: 7, 2: 13}`).

## Corrections — three claims of mine were wrong

### 1. "Nature is not in `koma.bin`" (iteration 4) — WRONG

It is. The high nibble of byte `+0xB` carries it for 32 battle panels.

I reasoned that Naruto's size-2 panel is 笑 and his size-3 is 力, and both records were "byte-identical except image, shape, and ordinal" — so no field could encode nature. **The mistake was dismissing the differing fields.** `kshapeGroup` differs between those records, and the support path indexes `chr_s` at `(kshapeGroup-1)*8`. The field I waved away was doing the work.

Lesson: "the differing fields are incidental" is a claim that needs evidence, not a safe default.

### 2. "Exhaustively REFUTED: no per-koma nature table" (iterations 9–10) — OVERSTATED

I searched for a dedicated table — whole-byte, nibble-packed, or 2-bit-packed, at every offset, across arm9 + 26 `bin/` files + 14 overlays. That search was correct as stated: no dedicated table exists.

But I called it "exhaustive," and it wasn't. It never tested *a nibble of an existing field combined with a sentinel and a fallback*. The word claimed more coverage than the method delivered.

### 3. P1d: "bit `0x10` clear marks the override" (iteration 10) — REFUTED in mechanism

The real test is `high nibble == 3`, not a single bit. My test caught nibbles `0` and `2` (25 records) but missed nibble `1` (7 records) — so it landed near the right answer for the wrong reason. There are **32** override panels, not the 26 I reported.

P1d's *shape* — base nature with a per-panel override — was right, and it correctly predicted why no table existed. The mechanism was wrong.

## What actually cracked it

My searches couldn't have worked, and it's worth saying exactly why. I was looking for nature as **stored data**. It's **computed**, and two of its three inputs (`panelType`, `kshapeGroup`) were fields I'd already decoded for other purposes. No value-space search over files can find a function.

What worked: another session's overlay-residency test identified which overlay to read, then I read the accessor directly. Static value search found every *table* in this system — sizes, shapes, types, abilities, names, HP — then failed on the one property that isn't a table.

## Corollary: `chr_s` offsets `0x00` and `0x08` are per-size nature slots

The support path indexes `chr_s[abilityId*20 + (kshapeGroup-1)*8]`, so a support character's 2-koma and 3-koma panels read offsets `0x00` and `0x08` of the same record. Both are nature slots. That's why `chr_s` offset `0x00` showed a near-even 3-way split — it was a nature column, just one of two.

## Predictions status — final

| ID | Prediction | Verdict |
|---|---|---|
| P1 | Nature is a 4-value enum in `koma.bin` | **partly CONFIRMED** — a 4-value enum, in a nibble, for 32 panels |
| P1b | Dedicated per-koma nature table in the binaries | **REFUTED** (correctly) |
| P1c | Compacted 578-entry table | **REFUTED** (correctly) |
| P1d | Base nature + per-panel override | **shape CONFIRMED, mechanism REFUTED** |

## Open follow-ups

- The **low** nibble of `+0xB` is still unknown (maps to runtime struct `+0x12`; the high nibble maps to `+0x13`).
- `chr_s` offset `0x10` unidentified.
- `[0x0214BD80]` is a global table-pointer block: `+0x40` = `chr_b` base, `+0x48` = `chr_s` base, `+0x54` = a 12-byte-stride table worth identifying.
- Consumers at ov5 `0x0214D998` / `0x0214DC50` do `addne r0, r0, r1, lsl #10` — likely a palette/tile-attribute merge for drawing the glyph.
- `arm9` `0x02078CB8` is a pure "has explicit nature?" predicate in the **battle** engine — so nature is read during combat despite `Deck-System.md` implying it's deck-only. Worth chasing when the loop moves to the combat phase.
