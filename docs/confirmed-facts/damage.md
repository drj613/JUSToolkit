# JUS damage calculation — confirmed spec

Canonical reference for reimplementing battle damage in Jump Ultimate Stars
(`jus.nds`, AJUJ). Everything here is backed by static disassembly of
`arm9.bin`/`arm9_ov06.bin` plus live-RAM measurements, cited inline. Beads
(`br show <id>`) hold the raw measurement logs. The routine at the center is
**arm9 `0x020823E4`** (680 bytes), the damage formula.

> Avoid `docs/research/Battle-Engine-Map.md` as a source — parts of it are
> taint-flagged. This spec cites findings journal entries and
> runtime-confirmed beads instead.

---

## 1. Overview

One hit's damage is computed in a single routine, `0x020823E4`, called from
the collision pipeline at `0x02081280` (inside `0x02080F14`) with the result
returned through an out-parameter on the stack
([p208](../research/findings/p208-damage-formula-0x020823E4.md)).

The shape of the computation:

```
base   = signed byte, the move's base damage        (8.8 fixed point after <<8)
r5     = base<<8, scaled by two attacker multipliers and summed with
         a nature term and quarter-step gate terms  (all additive into r0)
out    = (r5 + r0) >> 2                             (8.8 -> raw HP units, 1/64)
```

Key facts an implementer must not get wrong:

- All internal math is **8.8 fixed point** (`0x100` = 1.0).
- Nature bonus and the ±25% gates land in **one accumulator and are
  additive with each other**, not multiplicative. Nature advantage with one
  resist gate is 1.25×, not 1.5 × 0.75
  ([p216](../research/findings/p216-nature-is-read-in-the-damage-path.md)).
- There is **no flat subtraction** anywhere; the historical "flat −2.0"
  reading was an artifact of base 8, where −25% happens to equal −2.0
  ([p209](../research/findings/p209-damage-formula-decoded.md),
  bead `jus-flat-refuted-with-attribution-doi`).
- With nothing armed, **displayed damage equals the base byte exactly**
  (bead `jus-unreduced-baseline-measured-7dj`, 50 stops, 7 distinct bases).

## 2. Data structures (field level)

### 2.1 The hit element (0x2C bytes, `arg1` = `sl`)

The element describing the contact. The move's data hangs off `arg1`; `arg1`
is the attacking side ([p213 §"Which side is r8"](../research/findings/p213-flag-word-is-plus-0x44-ability-10-sets-bit-5.md)).

| offset | type | meaning |
|---|---|---|
| `+0x0C` | ptr | attacker-side ColPrm scratch (start of the `+0x68` walk chain) |
| `+0x10` | ptr | move-data block (see below) |
| `+0x14` | u8 | element flags; `& 0xF0` feeds the bits-6/14 element condition |

Move-data block at `[elem+0x10]`:

| offset | type | meaning |
|---|---|---|
| `+0x00` | u8 | element kind; values 4 or 5 bypass the second test on gates 6/14 |
| `+0x04` | s8 | **base damage byte** (`ldrsb` at `0x02082428`) |
| `+0x0E` | s8 | **class index**, packed byte: low 6 bits = class (range-checked 0..15 by the routine; `0x3F` is the "none" reset sentinel), bit 7 a separate flag ([p214](../research/findings/p214-class-index-is-a-packed-byte.md)). This byte is the collision damageFlags category (bead `jus-class-index-is-damageflags-mx5`). |

The base byte is design-time data: `base = jpower.damage1 / 5` (damage1
stores displayed×5), converging with the file-format formula
([p210](../research/findings/p210-nature-tables-and-prediction-failure.md)).

### 2.2 The ColPrm scratch objects (`r4` = attacker side, `r8` = other side)

`r4` starts at `[elem+0x0C]` and the prologue walks `r4 = [r4+0x68]` while
`[r4+0x68] != 0` and bit 9 of `[r4+0x40]` is clear. `r8` is the participant
not supplying the move; both were named live in one read
(`r4 = 0x0220FC3C`, `r8 = 0x0220FDC4`, bead
`jus-gate-word-read-live-0x2010-nbz`).

| offset | type | side used | meaning |
|---|---|---|---|
| `+0x40` | u32 | both | status flag word. Bit 30 = nature bypass (either side forces nature factor to 1.0); bit 25 tested in prologue; bit 9 stops the `+0x68` walk. Dynamic during a hit (read `0x01000018` mid-hit vs `0x00000008` at rest). |
| `+0x44` | u32 | `r8` | **the gate word** — the ±25% mask (see §4). Note: `+0x44`, not `+0x40` (bead `jus-gate-word-is-r8-0x44-fnz`). |
| `+0x68` | ptr | `r4` | chain link for the prologue walk |
| `+0xA4` | array | `r4` | per-frame contribution accumulator array (the formula's out-param is accumulated here by the caller, [p208](../research/findings/p208-damage-formula-0x020823E4.md)) |
| `+0x175` | u8 | both | packed **nature byte**: three candidate 2-bit fields (bits 1:0, 3:2, 5:4). Column = selected field of `[r4+0x175]` (selector by flags at `0x020824A4`/`0x020824B4`); row = `[r8+0x175] & 3`. |
| `+0x184` | u16 | `r4` | multiplier **f1**, 8.8 (measured 1.0 = `0x100` in all captures) |
| `+0x186` | u16 | `r4` | multiplier **f2**, 8.8 (measured 1.0) |

### 2.3 The character struct (HP lives here, not in the scratch)

From [HP-Struct-From-Disassembly.md](../research/HP-Struct-From-Disassembly.md):

| offset | type | meaning |
|---|---|---|
| `+0x16` | s16 | **max HP**, clamped to `0x4000` (= 256.0 displayed) |
| `+0x18` | s16 | **current HP** |
| `+0x41` | u8 | `chr_b` index |
| `+0x49` | u8 | regen byte (poke to 0 to disable regen in tests) |

Reached from the battle object as `char = [battleObj+0x56C]`
(p173, cited in that doc).

## 3. HP encoding

- HP and damage are stored in **raw units of 1/64 displayed HP**:
  `displayed = raw / 64`. Confirmed two ways: the `0x4000` max-HP cap = 256.0,
  and the routine's own `asr #6` scale appearing in the arithmetic
  ([HP-Struct-From-Disassembly.md](../research/HP-Struct-From-Disassembly.md),
  [p208](../research/findings/p208-damage-formula-0x020823E4.md)).
- Inside the formula the working unit is 8.8 fixed point (`raw × 4`); the
  final `>> 2` converts 8.8 → raw/64.
- Both HP fields are loaded with `LDRSH` — signed 16-bit.
- Damage is applied by negation: `0x020783B8` is a trampoline doing
  `rsb r1, r1, #0` then tail-calling the HP-apply function
  ([Damage-Path-Codex-Findings.md](../research/Damage-Path-Codex-Findings.md)).
- Known runtime HP addresses for the default dm_battle setup:
  opponent current HP `0x021DF7F0`, player `0x021DF1D4`; read 2 bytes **at**
  the address. `0x021DF7EE` is max HP — reading it looks like a working
  measurement at full health and cost four sessions
  (bead `jus-reading-max-hp-not-current-2jo`,
  [docs/memory/jus-hp-address-current-vs-max.md](../../docs/memory/jus-hp-address-current-vs-max.md)).

## 4. The algorithm, step by step (`0x020823E4`)

Arguments at the call site `0x02081280`: `r0` = element list, `r1` = the
0x2C hit element, `r2` = one bit from `[ColPrmMan+0x14D]` (selects which
nature table), `r3` = `&out` on the caller's stack
([p208](../research/findings/p208-damage-formula-0x020823E4.md)).

### Step 1 — prologue: resolve scratches, load base

```
0x020823E8  mov   sl, r1            ; the hit element
0x020823EC  ldr   r4, [sl, #0xc]    ; attacker-side scratch
            ; walk: while [r4+0x68] != 0 && !(bit9 of [r4+0x40]): r4 = [r4+0x68]
0x02082420  ldr   r1, [sl, #0x10]
0x02082428  ldrsb r5, [r1, #4]      ; BASE, signed byte
```

### Step 2 — base to 8.8, two scratch multipliers

```
0x0208247C  add  r0, r4, #0x100
0x02082480  ldrh r2, [r0, #0x84]    ; f1 = [r4+0x184]
0x02082484  ldrh r0, [r0, #0x86]    ; f2 = [r4+0x186]
0x0208248C  lsl  r3, r5, #8         ; r3 = base << 8   (8.8)
0x02082490  sub  r2, r2, #0x100     ; f1 - 1.0
0x02082494  mul  r2, r3, r2
0x02082498  add  r2, r3, r2, asr #8 ; r2 = base * f1 / 256
0x0208249C  sub  r0, r0, #0x100     ; f2 - 1.0
0x020824A0  mul  r0, r2, r0
0x020824A8  add  r5, r2, r0, asr #8 ; r5 = r2 * f2 / 256
```

i.e. `r5 = (base<<8) * f1/256 * f2/256`. Each multiplier is applied as
`x + x*(f-1)/256`, which is exact for 8.8 factors
([p209](../research/findings/p209-damage-formula-decoded.md)). Both factors
have measured 1.0 in every capture to date; their writer is where
rules/buffs would land (unidentified — see §8).

### Step 3 — nature term (additive, into `r0`)

Selection: column = one of three 2-bit fields of `[r4+0x175]` (bits 1:0,
3:2 or 5:4, chosen by flags at `0x020824A4`/`0x020824B4`); row =
`[r8+0x175] & 3`. Table = `0x0209FF14` if `arg2` (`ColPrmMan+0x14D` bit 0)
is set, else `0x0209FEF4` (`cmp sb, #0` at `0x020824FC`).
**Bypass:** if bit 30 of `[r8+0x40]` or `[r4+0x40]` is set, `0x020824F4`
forces the cell to `0x100` and the tables are never read
([p210](../research/findings/p210-nature-tables-and-prediction-failure.md),
[p216](../research/findings/p216-nature-is-read-in-the-damage-path.md)).

```
0x02082538  ldrsh r3, [r2, r1]      ; cell = s16 table[row*8 + col*2]
0x02082568  sub   r1, r3, #0x100    ; cell - 1.0
0x0208256C  mul   r1, r5, r1
0x02082578  add   r0, r0, r1, asr #8  ; r0 += r5 * (cell - 1.0) / 256
```

Every cell is `0x100` (1.0) or `0x180` (1.5) — the nature system is
**bonus-only**; advantage adds +50% of `r5`, disadvantage adds nothing.
Observed live: `r0 = 512` at `r5 = 1024`
(bead `jus-bit5-fired-and-nature-observed-w5n`).

Nature tables (8.8, row = defence category of `r8`, col = attack category
of `r4`; row stride 8 bytes, col stride 2):

```
Table B @ 0x0209FEF4 (arg2 clear)      Table A @ 0x0209FF14 (arg2 set)
      atk0  atk1  atk2  atk3                 atk0  atk1  atk2  atk3
def0  1.0   1.0   1.5   1.0            def0  1.0   1.5   1.0   1.0
def1  1.5   1.0   1.0   1.0            def1  1.0   1.0   1.5   1.0
def2  1.0   1.5   1.0   1.0            def2  1.5   1.0   1.0   1.0
def3  1.0   1.0   1.0   1.0            def3  1.0   1.0   1.0   1.0
```

The two tables are inverse 3-cycles of the 力/知/笑 triangle with なし
(category 3) inert. Category values follow the nature enum in
[Nature-System-Consolidated.md](../research/Nature-System-Consolidated.md)
(0 力, 1 知, 2 笑, 3 なし).

### Step 4 — quarter-step gates (additive, into `r0`)

The gate word is `r2 = [r8+0x44]`, loaded once at `0x02082574` and not
rewritten before the last gate. The class index is
`r1 = ldrsb [[sl+0x10]+0x0E]`, range-checked `0 <= r1 <= 15`; outside that
range **all four class gates are skipped** (legitimate no-class states:
sentinel `0x3F` reads 63, bit 7 set reads negative). The class table at
`0x02092E68` (16 bytes) maps index → category:

```
01 01 02 02 02 02 02 02 02 02 02 02 00 00 00 00
```

Indices 0–1 → category 1, 2–11 → category 2, 12–15 → category 0 (immune to
class gates). Six gates, each adding or subtracting exactly **25% of `r5`**
(`(r5 << 6) >> 8 = r5/4`), all conditional
([p213](../research/findings/p213-flag-word-is-plus-0x44-ability-10-sets-bit-5.md)):

| gate addr | bit of `[r8+0x44]` | extra condition | effect on `r0` |
|---|---|---|---|
| `0x020825A8` | 14 (`0x4000`) | element cond.* | **+** r5/4 |
| `0x020825DC` | 6 (`0x40`) | element cond.* | **−** r5/4 |
| `0x02082608` | 12 (`0x1000`) | class table byte == 1 | **+** r5/4 |
| `0x02082624` | 13 (`0x2000`) | class table byte == 2 | **+** r5/4 |
| `0x0208264C` | 4 (`0x10`) | class table byte == 1 | **−** r5/4 |
| `0x02082674` | 5 (`0x20`) | class table byte == 2 | **−** r5/4 |

\* element condition: fires if `[[sl+0x10]+0]` is 4 or 5 (bypasses the
second test), otherwise requires `[sl+0x14] & 0xF0`.

Gate arithmetic, verbatim:

```
0x02082644  lsleq r4, r5, #6
0x0208264C  subeq r0, r0, r4, asr #8   ; r0 -= r5/4
```

Live confirmations: bit 4 with category 1 fired for −512 at `r5 = 2048`
while an armed bit 13 was correctly **blocked** by the category mismatch
(bead `jus-gate-word-read-live-0x2010-nbz`); bit 5 with category 2 fired at
the pre-registered value (bead `jus-bit5-fired-and-nature-observed-w5n`).

The routine also builds a **result flag word** alongside: `orreq r3, r6, #4`
/ `lsleq r3, r3, #0x10` at `0x0208263C` sets bit 2 = "resisted", returned in
`r0` at `0x02082680`. Do not mistake it for a damage value
([p211](../research/findings/p211-damage-formula-end-to-end.md)).

### Step 5 — final combine and output

```
0x02082678  add r0, r5, r0     ; scaled base + (nature term + gate terms)
0x0208267C  asr r1, r0, #2     ; 8.8 -> raw/64
0x02082684  str r1, [fp]       ; the out-parameter
```

So: **`out_raw = (r5 + r0) >> 2`**, where `r0` is the signed sum of the
nature term and every gate that fired. The caller accumulates `out` into a
per-frame array at `scratch+0xA4` (cleared every frame), from which the HP
drain is eventually applied
([p208](../research/findings/p208-damage-formula-0x020823E4.md)).

### Control-flow summary

1. Resolve `r4` via the `+0x68` walk; test bit 25 of `[r4+0x40]`.
2. Load base; `r5 = (base<<8) * f1/256 * f2/256`.
3. Nature: bit-30 bypass check → selector flags → 2-bit row/col → table
   pick by `arg2` → additive term into `r0`.
4. Load gate word `[r8+0x44]` and class index; range-check 0..15.
5. Six conditional ±r5/4 adjustments into `r0`; build result flags.
6. `*out = (r5 + r0) >> 2`; return flag word.

## 5. How the gate word gets filled (load time)

Abilities never reach the damage routine directly — they are compiled into
`[+0x44]` bits once, which is why every mid-battle ability-array poke
measured zero effect ([p213](../research/findings/p213-flag-word-is-plus-0x44-ability-10-sets-bit-5.md),
[Damage-Path-Codex-Findings.md §2](../research/Damage-Path-Codex-Findings.md)):

- On-disk ability list: `chr_b` record `+0x03`, five sparse bytes
  (bead `jus-ondisk-ability-list-at-chrb-0x03-kfc`).
- Load-time loader `0x0215FB3C` caches ability IDs as a **bitset** at
  `battleObj+0x128` (bit index = ability ID).
- ov6 `0x02157114` reads that bitset once and assembles **both** the gate
  word and the packed nature byte (from record bytes `+3/+4/+5`)
  (bead `jus-one-routine-assembles-both-u24`). It drives helper
  `arm9 0x02083BE0`: `[target+0x44] |= tbl[variant-1][maskIdx]` (or clears
  both variants when `variant == 0`), with mask tables
  `0x02092E78` = bits 4..9 (subtract) and `0x02092E90` = bits 12..17 (add).
- The ability→(maskIdx, variant) mapping is a 12×3-byte table at ov6
  `0x021710BC` — six subtract/add couples, e.g. ability 9 → bit 4, ability
  12 → bit 13. Confirmed end-to-end live: bitset for abilities
  [9, 25, 12, 14] predicted `[r8+0x44] = 0x00002010`, and it read exactly
  that; writer object and the routine's `r8` are the same object
  (bead `jus-gate-word-read-live-0x2010-nbz`).
- Timing: the gate word is assembled ~30–80 frames **after** load, not at
  frame 0 (bead `jus-gate-word-assembled-after-load-68g`).

Note the damage routine reads only mask indices 0–2 (bits 4/5/6 and
12/13/14); bits 7–9 / 15–17 are consumed elsewhere (unlocated).

## 6. Edge cases

- **Base is a signed byte.** Bases are integral by construction; a base of
  0 is real (measured, produces 0 damage).
- **Class index out of 0..15** (sentinel `0x3F`, or bit 7 set → negative):
  all class gates skipped; not an error state
  ([p214](../research/findings/p214-class-index-is-a-packed-byte.md)).
- **Class categories 0 (indices 12–15)** match neither gate pair — immune
  to both class-gated resist and weakness.
- **Nature bypass:** bit 30 of either scratch's `+0x40` forces factor 1.0.
- **Multi-contact moves:** the routine runs once per contact. Goku's UP+B
  is two contacts of base 3, summing to 4.500 displayed
  (bead `jus-flat-refuted-with-attribution-doi`).
- **The formula only runs on landed hits** — 4 hits → 4 stops, 7 misses →
  0 stops; a breakpoint at `0x02082584` is a hit oracle
  (bead `jus-first-attributed-measurement-d6u`; the earlier contrary claim
  `jus-formula-bp-not-a-hit-oracle-ve6` is retracted).
- **Downstream of the formula**, on the pending-damage consumer path
  (`0x0215AC00`): the magnitude at `obj+0x134` is **halved** (`asr #1`)
  when either of two unidentified predicates (`0x02159A10`,
  `0x021598D0` — guard/defensive-status candidates) is true; and a scripted
  path at `0x021518D6` applies a hardcoded 32.0 displayed
  ([Damage-Path-Codex-Findings.md](../research/Damage-Path-Codex-Findings.md)).
- **No 1-HP floor** on the drain path: HP reaches raw 0 and a KO follows
  (bead `jus-r3i`).
- **Max HP** adds are clamped to `0x4000` (256.0); the adder returns 0 if
  already at cap ([HP-Struct-From-Disassembly.md](../research/HP-Struct-From-Disassembly.md)).

## 7. Test vectors (CROSS_CONFIRMED measurements)

All from live RAM with items/gimmick/team = 0, regen disabled, values read
at breakpoint `0x02082584` and cross-checked against actual HP drops at
`char+0x18`. f1 = f2 = 1.0 throughout.

| # | base | r5 | nature term | gates fired | out raw | displayed | source bead |
|---|---|---|---|---|---|---|---|
| 1 | 8 | 2048 | 0 | none (gate word 0) | 512 | 8.000 | `jus-unreduced-baseline-measured-7dj` |
| 2 | 8 | 2048 | 0 | bit 4, cat 1: −512 (bit 13 armed, blocked by cat) | 384 | **6.000** | `jus-gate-word-read-live-0x2010-nbz`, `jus-first-attributed-measurement-d6u` |
| 3 | 3 | 768 | 0 | none | 192 | 3.000 | `jus-unreduced-baseline-measured-7dj` |
| 4 | 3 | 768 | 0 | bit 4, cat 1: −192 | 144 | 2.250 (×2 contacts = 4.500 measured) | `jus-flat-refuted-with-attribution-doi` |
| 5 | 4 | 1024 | 0 | none | 256 | 4.000 | `jus-unreduced-baseline-measured-7dj` |
| 6 | 4 | 1024 | 0 | bit 5, cat 2: −256 | 192 | 3.000 | `jus-bit5-fired-and-nature-observed-w5n` |
| 7 | 4 | 1024 | +512 (1.5 cell) | bit 5, cat 2: −256 | 320 | 5.000 | `jus-bit5-fired-and-nature-observed-w5n` |
| 8 | 7 | 1792 | 0 | one −25% gate | 336 | **5.250** (3 identical reps) | `jus-reading-max-hp-not-current-2jo` |
| 9 | 0,2,5,28 | base<<8 | 0 | none | base<<6 | = base exactly | `jus-unreduced-baseline-measured-7dj` |

Static-only worked example for nature at full strength
([p216](../research/findings/p216-nature-is-read-in-the-damage-path.md)):
base 8, advantage cell 1.5, no gates → `r0 = (2048·0x80)>>8 = 1024`,
`out = (2048+1024)>>2 = 768` = **12.000** — matching the owner's live-play
8 → 12 observation.

Note on vector 8: the move is unattributed (base inferred as 7 from
5.250/0.75 being integral), but the drop was measured three times under
controlled conditions; it is the vector that refuted the flat model on
integrality alone.

Degeneracy warning for test authors: base 8 is the point where
"−25%" and "flat −2.0" coincide (both give 6.000). Use base 3 or 4 vectors
to discriminate models.

## 8. Open questions

Marked **OPEN** deliberately — do not treat as settled, do not guess:

- **OPEN — what sets the gate bits in `[r8+0x44]` beyond the ability path.**
  The ability→bit chain via ov6 `0x02157114` / `0x02083BE0` is confirmed for
  the observed bits, but only 2 of the 12 table rows have been exercised
  (bit 4 naturally, bit 5 poked); ability 10 → bit 5 specifically is
  untested (`jus-bit5-ability-10-untested-mvk`, cited in
  [p213 appendix](../research/findings/p213-flag-word-is-plus-0x44-ability-10-sets-bit-5.md)),
  and whether anything other than abilities (rules, koma adjacency, status)
  writes gate bits is unknown.
- **OPEN — which gate produced the −25% observation** in vector 8 (the
  5.250 reps): the character/move was never attributed, so bit 4 vs bit 6
  vs another −25% source is unresolved.
- **OPEN — the ability→damage-flag load-time link** as a single end-to-end
  observation: the natural route (ability arrives via koma append, bit
  arms, gate fires on a matching-class element in one capture) has not been
  demonstrated; the poked-gate and natural-bit halves exist separately
  (bead `jus-bit5-fired-and-nature-observed-w5n`).

Other loose ends (not required for reimplementation of the core formula):
what writes the `+0x184`/`+0x186` multipliers (never observed ≠ 1.0); which
nature-table *cell* the selector picks (the 1.5 value is confirmed by the
term, not by reading the inputs — bead
`jus-nature-not-bypassed-selector-confirmed-zh2` confirmed the selector
decode but the per-cell map is inferred); the two halving predicates on the
consumer path; consumers of gate bits 7–9/15–17; what writes `elem+0x0E`.

### Footnoted retractions (do not resurrect)

- "Nature does not affect damage" (`jus-nature-does-not-affect-damage-0c6`,
  tainted): the byte-poke null had scope problems; nature **is** read, as a
  2-bit field on the scratch copy
  ([Nature-System-Consolidated.md banner](../research/Nature-System-Consolidated.md)).
- "Flat −2.0 reduction" ([Damage-Reduction-Is-Flat.md](../research/Damage-Reduction-Is-Flat.md)):
  superseded by the proportional −25% gates
  (bead `jus-reduction-is-quarter-multiplier-xk1`).
- "Gate word at `[r8+0x40]`": corrected to `+0x44`
  (bead `jus-gate-word-is-r8-0x44-fnz`).
- "Class-1 gate is unconditional": all six gates are conditional
  ([p213](../research/findings/p213-flag-word-is-plus-0x44-ability-10-sets-bit-5.md)).
- "Formula breakpoint is not a hit oracle"
  (`jus-formula-bp-not-a-hit-oracle-ve6`): retracted; the evidence was a
  max-HP read (`jus-reading-max-hp-not-current-2jo`).
