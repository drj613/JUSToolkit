# Nature system — canonical spec

Audience: an engineer reimplementing JUS from scratch. This covers both jobs the
nature system does: its contribution to battle damage, and its role in deck
construction. Everything here is mined from the repo's evidence (ROM bytes,
disassembly, and runtime GDB captures) — no new emulator runs. Sources are cited
inline; claims that are not settled are marked **OPEN**.

Primary source: [Nature-System-Consolidated.md](../research/Nature-System-Consolidated.md)
(read its taint banner first — its old headline "nature does not affect damage"
is retracted by bead `jus-nature-is-read-in-damage-path-hbt`).

## 1. The enum and the triangle

| value | nature | notes |
|---|---|---|
| `0` | 力 Power | |
| `1` | 知 Knowledge | |
| `2` | 笑 Laughter | |
| `3` | なし None | doubles as a "no override" sentinel in deck data |

Triangle: 力 > 知 > 笑 > 力. Confirmed from instructions (loop at
`0x02160944`–`0x021609B8` testing the "theirs beats mine" pairs) and corroborated
live ([Nature-System-Consolidated.md §1](../research/Nature-System-Consolidated.md)).

Every nature value in this spec is a 2-bit field; `3` is always the neutral /
none / sentinel value.

---

## 2. Battle-damage role

### 2.1 The factor tables

Two 4×4 tables of signed halfwords in `arm9.bin`, indexed as
`base + row*8 + col*2`. Values are **8.8 fixed point**: `0x0100` = 1.0,
`0x0180` = 1.5. The tables contain no other value above `0x0100`.
Source: bead `jus-nature-is-read-in-damage-path-hbt` (ROM bytes, verifiable by
anyone with the ROM), also
[p216-nature-is-read-in-the-damage-path.md](../research/findings/p216-nature-is-read-in-the-damage-path.md).

```
T @ 0x0209FEF4                     T @ 0x0209FF14
  row0  1.0  1.0  1.5  1.0          row0  1.0  1.5  1.0  1.0
  row1  1.5  1.0  1.0  1.0          row1  1.0  1.0  1.5  1.0
  row2  1.0  1.5  1.0  1.0          row2  1.5  1.0  1.0  1.0
  row3  1.0  1.0  1.0  1.0          row3  1.0  1.0  1.0  1.0
```

Shape: two opposite three-cycles over {力, 知, 笑} plus a fully neutral fourth
row and column (なし). Rule (verified against ROM bytes, comment on bead
`hbt`): `0x0209FEF4` puts the 1.5 at row `(col+1) mod 3`; `0x0209FF14` at
row `(col+2) mod 3`. Row 3 is all 1.0 and column 3 is all 1.0 **in both
tables**, so "none" on either side kills the term regardless of every other
unknown (bead `jus-nature-column-selector-8gk`).

Table selection: `cmp sb, #0` at `0x020824FC`, where `sb` is arg2 — a single
bit taken from `[sl+0x14d]` at call site `0x02081264`. **OPEN**: which game
condition sets that bit (i.e. the semantic difference between the two tables —
presumably "my advantage" vs "their advantage") has not been identified.

### 2.2 Row and column indices

Both fighters carry a packed nature byte at ColPrm-scratch offset `+0x175`
(the scratches are 0x188-stride slots inside Battle_ObjMan, bead `jus-s5q`).
The byte holds **three 2-bit nature slots**: slot A bits 1:0, slot B bits 3:2,
slot C bits 5:4; bits 7:6 are a separate, unaccounted field preserved by
read-modify-write (**OPEN**). Source: beads `jus-nature-column-selector-8gk`,
`jus-one-routine-assembles-both-u24`.

The two sides are asymmetric:

- **Row (defender)**: always `[r8+0x175] & 3` — slot A only. Bits 3:2 and 5:4
  of the defender's byte are never read by the damage routine (verified from
  ROM bytes, comments on bead `hbt`).
- **Column (attacker)**: one of the three slots of `[r4+0x175]`, chosen **per
  move** by bits 7:6 of the move's word at `[arg1+0x18]` (decoded at
  `0x02082488`–`0x020824D8`):
  - `(word & 0xC0) == 0` → slot A (bits 1:0)
  - bit 6 set → slot B (bits 3:2)
  - bit 6 clear, bit 7 set → slot C (bits 5:4)

  This decode is runtime-confirmed: a live `[sl+0x18] = 0x41` resolved through
  it to column 0, predicting the measured term `r0 = 0`
  (bead `jus-nature-not-bypassed-selector-confirmed-zh2`).

**Bypass**: if bit 30 (`0x40000000`) of either `[r8+0x40]` or `[r4+0x40]` is
set, `0x020824F4` forces the factor to `0x100` (1.0) and the tables are never
read (bead `hbt`). Both bits were observed clear in normal training play, so
the bypass is real but not the default (bead `zh2`). **OPEN**: what sets
bit 30.

### 2.3 The arithmetic — additive in one accumulator

The nature term and the resist/class gate terms land in the **same
accumulator** `r0` and are **additive over the base**, not multiplicative with
each other. Source: bead `hbt` (instruction trace) and the live composed
observation in bead `jus-bit5-fired-and-nature-observed-w5n`.

With `r5` = base damage in 8.8 (base byte × 0x100) and `cell` = the table
value:

```
nature term = (r5 * (cell - 0x100)) >> 8      ; 0 for a 1.0 cell, r5/2 for 1.5
r0          = nature term + gate terms         ; gates: ±quarter-steps of r5
out (raw)   = (r5 + r0) >> 2
displayed   = out / 64
```

Instruction trace (bead `hbt`):

```
0x02082568  sub r1, r3, #0x100     ; r3 = table cell, e.g. 0x180 -> 0x80
0x0208256C  mul r1, r5, r1
0x02082578  add r0, r0, r1, asr #8 ; nature term joins the accumulator
0x02082678  add r0, r5, r0
0x0208267C  asr r1, r0, #2
```

Consequence for the formula: nature advantage plus one 25% resist gate is
`(1 + 0.5 - 0.25)` = **1.25×**, not `1.5 × 0.75 = 1.125×`. "×0.75 per gate"
and "×1.5 for nature" are only correct in isolation.

The nature term can be read at breakpoint `arm9 0x02082584`, where `r0` holds
the nature adjustment and nothing else (verified by enumerating every write to
`r0` from its zeroing at `0x020824AC`; comment on bead `hbt`). Note the
formula breakpoint fires on non-hit events too, so it is not a hit oracle
(bead `jus-formula-bp-not-a-hit-oracle-ve6`).

Distinct site, do not conflate: the ×1.20 percentage scale at
`0x02158DC4`–`0x02158DD0` in ov6 (`×120/100` through a divide) was once
labelled "nature ×1.5" and that label is **refuted**. Different address,
different value, different arithmetic convention (decimal percentage vs 8.8).
Both facts are true of different code (comments on bead `hbt`).

### 2.4 Test vectors

All runtime-confirmed.

| scenario | inputs | expected | source |
|---|---|---|---|
| Neutral cell | base byte 8 (`r5=0x800`), cell 1.0, no gates | raw 512, displayed 8.000 | bead `hbt` |
| Advantage | base byte 8, cell 1.5, no gates | term +1024; raw 768, displayed 12.000 | bead `hbt` (matches owner's live 8→12) |
| Neutral + gate 5, class 2 | base byte 4 (`r5=0x400`), cell 1.0, bit-5 quarter-step −256 | raw 192, displayed 3.000 (3/3 stops) | bead `jus-bit5-fired-and-nature-observed-w5n` |
| Advantage + gate 5, class 2 | base byte 4, cell 1.5 (term +512), −256 | raw 320, displayed 5.000 (6/6 stops) | bead `w5n` |
| Selector live read | `[sl+0x18]=0x41`, col byte `0x20`, row byte `0x00` | column = bits 3:2 = 0, row 0 → cell 1.0 → `r0 = 0` (measured 0) | bead `zh2` |
| Zero-gate baseline | gate word 0, nature term 0, base bytes 3/5/4 | displayed = base exactly | bead `jus-nature-menu-not-in-these-modes-43m` §4, `jus-unreduced-baseline-measured-7dj` |

The composed check: 4.000 unreduced + 2.000 (1.5 nature on base 4) − 1.000
(quarter-step) = 5.000, observed live with the nature term unpoked (bead
`w5n`). The 1.5 cell has been observed exactly once in play; which table/column
produced it is not attributable because the defender's row byte churns between
respawn cycles in that mode (bead `w5n` comment).

### 2.5 How the packed nature byte is populated

One ov6 routine, `0x02157114`, assembles **both** load-time derived values on
the ColPrm scratch: the ±25% gate word at `+0x44` and the packed nature byte at
`+0x175`. Source: bead `jus-one-routine-assembles-both-u24` (static, decoded
from ov6 bytes) and bead `jus-nature-menu-not-in-these-modes-43m` (runtime,
breakpoint fired once per fighter with matching values).

The assembler (`0x021571C4`–`0x02157208`) packs three consecutive source bytes
into the three slots:

```
r5 = [[[battleObj+0x1a0]+0x174]+8]      ; = char_struct + 0x10
slot A (bits 1:0) <- [r5+3] & 3          ; char+0x13
slot B (bits 3:2) <- [r5+4] & 3          ; char+0x14
slot C (bits 5:4) <- [r5+5] & 3          ; char+0x15
bits 7:6 preserved (read-modify-write of [scratch+0x175])
```

So each fighter carries **three natures** in its per-character slot, three
bytes below HP (`char+0x16` max HP s16, `+0x18` current HP s16, `+0x1A` ability
count, `+0x1B...` ability ids — live-verified layout, bead `u24` comments).
Slot A is what the fighter *defends* with; the move picks which slot it
*attacks* with.

`0x02157208` is the **only** store in the ROM that assembles this byte: an
imm-`0x175` sweep found 8 stores ROM-wide and the other seven are initialisers
or booleans (bead `u24`). Pre-assembler value is `0x3C` (slot A = 0, slots
B/C = 3 "none"), observed live; the byte is rewritten whenever the assembler
re-runs, which happens per KO/respawn cycle, so it **churns** in active play —
sample it where the consumer reads it, not before (bead `u24` comments,
`jus-gate-word-assembled-after-load-68g`).

**OPEN**: what writes the three source bytes at `char+0x13..0x15`. The shape —
three per-character natures with the move selecting one — matches the owner's
ground truth that natures are per-panel and a deck contributes several, so the
leading hypothesis is that deck/koma loading fills them (base nature + panel
natures). Located, not confirmed (beads `u24`, `8gk`). Also **OPEN**: no
invoker of `0x02157114` is findable statically (zero xrefs; computed call),
and whether the move-side selector bits 7:6 of `[element+0x18]` actually vary
between moves has never been observed (beads `u24`, `zh2` §5, `w5n` comment).

---

## 3. Deck-construction role

### 3.1 Per-panel nature resolution

Every deck panel (koma) has a nature, resolved by the deck-editor accessor at
`0x0214E480` in **ov05** — a sentinel-and-fallback scheme, not a lookup table.
Source: [nature-SOLVED.md](../research/findings/nature-SOLVED.md), summarised
in [Nature-System-Consolidated.md §2](../research/Nature-System-Consolidated.md);
wording fix in bead `jus-yw8m` (nature *is* per-panel; what doesn't exist is a
per-panel table).

Inputs are fields of the panel's `koma.bin` record (`+0x7` abilityId, `+0xB`
flags) plus the character tables `chr_b.bin` (74 records, 60-byte stride) and
`chr_s.bin` (193 records, 20-byte stride):

```
helper  (panelType 2) -> 3 (なし), short-circuit, flags ignored
battle  (panelType 0) -> nib = (flags[0xB] >> 4) & 0xF
                         nature = nib                        if nib != 3
                         nature = chr_b[abilityId*60 + 0x00] if nib == 3
support (panelType 1) -> nature = chr_s[abilityId*20 + (kshapeGroup-1)*8]
```

High nibble `3` means "no override — inherit the character's base nature",
which lives at `chr_b` record offset `+0x00` (3-valued across all 74 records:
{0: 35, 1: 22, 2: 17};
[nature-base-plus-override.md](../research/findings/nature-base-plus-override.md)).
Support panels index `chr_s` by the panel's kshape group, so one support
character can present different natures at different panel shapes.

Verification: all 9 Naruto panels match the owner's observed natures
(9/9, [nature-SOLVED.md](../research/findings/nature-SOLVED.md)).

Whole-game distribution across 890 panels: 力 226, 知 183, 笑 169, なし 312.
All 312 helpers are なし; all 372 supports inherit; only **32** battle panels
carry an explicit override (nibbles {0: 12, 1: 7, 2: 13}).

The character's *base* nature (chr_b `+0x00`) is also what special attacks
keep using even on an alternate-nature panel, per
[Deck-System.md](../research/Deck-System.md) — a character property distinct
from the panel nature.

### 3.2 In-battle consumers of panel nature

Two confirmed in-battle reads besides the damage tables
([Nature-System-Consolidated.md §3](../research/Nature-System-Consolidated.md),
static leg — these two findings survive the taint):

- **Triangle counter**: the loop at `0x02160944`–`0x021609B8` compares natures
  pairwise over the triangle and accumulates a **count** into `[r7, #0x60]`.
  **OPEN**: what consumes that counter (candidates: SP gain, a deck bonus, an
  AI heuristic).
- **Sprite selection**: an explicit-nature panel loads the `_b.aar` sprite
  archive with a `0x005F2000` VRAM allowance instead of `.aar`/`0x005F1000` —
  alternate-nature panels have different artwork.

**OPEN**: the exact deck-level bonus rules the game's UI attributes to nature
matchups (the reason nature matters when building a deck) have not been traced
to code; the triangle counter above is the best candidate mechanism.
**OPEN**: low nibble of koma flags byte `+0xB`, and `chr_s + 0x10`
([Nature-System-Consolidated.md §6](../research/Nature-System-Consolidated.md)).

---

## 4. Reimplementation checklist

1. Store per character: base nature (2 bits) plus two more nature slots
   (sources **OPEN**, likely deck-derived); defend with slot A.
2. Store per move: a 2-bit column selector (bits 7:6 of the move's `+0x18`
   word) choosing which attacker slot applies.
3. Damage: look up `table[defender_slotA][selected_attacker_slot]` in one of
   two 8.8 tables (selection bit **OPEN**); cells are 1.0 or 1.5 per the
   three-cycle rules in §2.1; add `(base * (cell - 1.0))` into the same
   accumulator as the ±25% resist gates; then `(base + acc) >> 2`, display
   `/64`.
4. Honour the bit-30 bypass on either fighter's `+0x40` word.
5. Deck editor: resolve each panel's nature by the §3.1 rules; helpers are
   always none; sentinel nibble 3 inherits `chr_b[+0x00]`.

## 5. Provenance key

Beads (claim ledger, `br show <id>`): `jus-nature-is-read-in-damage-path-hbt`
(tables, arithmetic, retraction), `jus-nature-column-selector-8gk` (selector,
row-3 shortcut), `jus-one-routine-assembles-both-u24` (assembler, char-struct
layout), `jus-nature-not-bypassed-selector-confirmed-zh2` (bypass clear, live
selector), `jus-bit5-fired-and-nature-observed-w5n` (first live 1.5, additive
composition), `jus-nature-menu-not-in-these-modes-43m` (per-fighter assembler,
zero-gate baseline), `jus-yw8m` (per-panel wording), `jus-s5q` (ColPrm
scratches), `jus-nature-does-not-affect-damage-0c6` (tainted — superseded).

Docs: [Nature-System-Consolidated.md](../research/Nature-System-Consolidated.md),
[findings/nature-SOLVED.md](../research/findings/nature-SOLVED.md),
[findings/nature-base-plus-override.md](../research/findings/nature-base-plus-override.md),
[findings/p216-nature-is-read-in-the-damage-path.md](../research/findings/p216-nature-is-read-in-the-damage-path.md).
