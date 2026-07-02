# Combat Research Status

Current understanding of Jump Ultimate Stars combat mechanics and data
structures.

---

## 2026-07-02 — Static RE Campaign (Battle-Engine-Map)

A static reverse-engineering campaign mapped 9 battle-engine subsystems
directly from `arm9.bin` + overlay disassembly (no emulator/GDB execution),
with every claim machine-verified against the disassembly database and run
through three adversarial verification lenses. Full detail, per-claim
confidence labels, refuted-hypotheses lists, and open questions live in
**[docs/research/Battle-Engine-Map.md](Battle-Engine-Map.md)**; every
`PLAUSIBLE`/`SPECULATIVE` claim has a one-breakpoint validation card in
**[docs/research/GDB-Validation-Queue.md](GDB-Validation-Queue.md)**.

**Subsystem statuses:** damage-pipeline, jpower-indirect, projectile-entities,
hitstun-timers, movement, weight-hunt, and collision-data are `PARTIAL`;
hitbox-priority and physics-writers are `PARTIAL` but flagged in loop-state as
still `TRACING` (least-resolved of the nine — see their sections in the Map
for why). None reached `EXHAUSTED`.

**Headline CONFIRMED discoveries this campaign:**

- **Gauge system** — `char+0x56c` is a generic clamp-accumulator gauge
  (`+0x16` max / `+0x18` current), with accessors `0x02078488`
  (`ApplyDeltaToCurrent`) and `0x020784B8` (`GrowMax`, capped `0x4000`). The
  GDB seed anchor `0x020784FC` is this gauge's "is current ≤ 25% of max"
  desperation check, **not** the per-hit damage formula. The previously
  unexplained ×1.20 scale at `0x02158DC4` is now read as the documented
  universal `attack_boost`, causally gated by that same 25%-gauge check
  (its old "nature ×1.5" label is refuted). See
  [Battle-Engine-Map.md § damage-pipeline](Battle-Engine-Map.md#subsystem-damage-pipeline)
  and [§ Cross-Cutting Structures](Battle-Engine-Map.md#cross-cutting-structures).
- **chr_b record access confirmed** — `*(0x0214BD80)+0x40`, stride `0x3C`,
  statA/B/C at record `+8`/`+0xA`/`+0xC`, indexed by the koma's `PassiveIndex`
  (a nuance: not confirmed identical to chr_b's own on-disk `CharId`). See
  [§ movement](Battle-Engine-Map.md#subsystem-movement).
- **jpower loading is ov5-only** — `jpower.bin` is opened and indexed
  (304-byte stride, exact `311×304` file-size match) exclusively inside the
  `ov5` menu/Jump-Galaxy overlay; since `ov5`/`ov6` share an overlay window
  and are mutually exclusive, the live battle overlay cannot read this blob
  directly. All 147 nonzero `damage1` values are multiples of 5 — the likely
  reason no runtime ÷5 instruction was ever found near combat code. See
  [§ jpower-indirect](Battle-Engine-Map.md#subsystem-jpower-indirect).
- **Entity pool** — global pooled-entity allocator/free pair
  (`0x020834D4`/`0x02083648`) with a 3-anchor free/active/pending list
  manager, confirmed for projectile spawn/despawn. See
  [§ projectile-entities](Battle-Engine-Map.md#subsystem-projectile-entities)
  *(note: that section's evidence is machine-verified but adversarial-lens
  verification is still pending)*.
- **Hitstun scaling formula** — `ov6 0x02158ED0`:
  `newDuration = floor(duration/10) × [table+0x4c] × 2 + duration`. The table
  index is a transient per-object hit-type/element byte
  (`object+0x1e0`), **not** a per-character weight constant — this closes off
  weight-hunt's primary lead as a dead end. See
  [§ weight-hunt](Battle-Engine-Map.md#subsystem-weight-hunt).
- **Refuted anchors** (previously load-bearing addresses, now corrected):
  `0x020784FC` is a gauge-threshold check, not the damage formula;
  `0x020924B0` is a char-ID ASCII string table, not a collision-blob pointer
  table (see the correction note on this same claim further down this
  document); `0x0208D4A0` is a plain ASCII case-folding table, unrelated to
  chr_b; no inlined or subroutine-based ÷5 division idiom exists anywhere in
  the ROM near combat code. See each subsystem's "Refuted hypotheses"
  subsection in the Map for full detail.

---

## ✓ CONFIRMED (High Confidence)

### Damage Calculation Formula

**Formula (confirmed 2026-01-30):**

```
damage = (jpower.damage1 ÷ 5) + (tier - 2)
actual_damage = floor(damage × nature_multiplier)
```

**Key insight:** The formula uses `damage1` (first component), NOT
`totalDamage`!

**Tier Modifiers:**

- tier=1: -1 damage (e.g., Bankai Ichigo)
- tier=2: +0 damage (most characters)
- tier=3: +1 damage (e.g., Caramelman)

**Nature Multipliers:**

- Neutral: 1.0x
- Advantage: 1.5x
- Disadvantage: 1.0x (no penalty - bonus-only system)

**Verified B move damages (2026-01-30):**

| Character     | tier | B Damage | Required d1 | d1 exists?   |
| ------------- | ---- | -------- | ----------- | ------------ |
| Nami          | 2    | 6        | 30          | ✓ 27 entries |
| Train         | 2    | 7        | 35          | ✓ 4 entries  |
| Goku          | 2    | 8        | 40          | ✓ 16 entries |
| Luffy         | 2    | 8        | 40          | ✓            |
| Robin         | 2    | 8        | 40          | ✓            |
| Franky        | 2    | 8        | 40          | ✓            |
| Naruto        | 2    | 8        | 40          | ✓            |
| Buu           | 2    | 9        | 45          | ✓ 3 entries  |
| Bankai        | 1    | 9        | 50          | ✓ 5 entries  |
| Ichigo        | 2    | 10       | 50          | ✓            |
| Caramelman    | 3    | 13       | 60          | ✓ 1 entry    |
| Kyuubi Naruto | 1    | 8        | 45\*        | ✓            |

\*Kyuubi has tier=1 but B=8, implying he uses d1=45 entry (45/5-1=8), not d1=40
like base Naruto

**What's confirmed:** The calculation formula works - all tested damages match
jpower entries with the correct d1 value.

**What's NOT confirmed:** How collision files SELECT which jpower entry to use.
See "jpower Entry Selection" in UNKNOWN section below.

#### Previous Mysteries - EXPLAINED (merged from Damage-Formula-Predictions.md)

**"Goku B=8 Mystery"**

- Old assumption: formula uses `total = damage1+damage2+damage3`
- Problem: Block 0 has total=50 entries, which would give 10 damage, not 8
- Solution: formula uses `damage1` only. Goku B uses an entry with damage1=40

**"Buu B=9 Anomaly"**

- Old assumption: no jpower entry has total=45
- Solution: Buu uses an entry with damage1=45 (45/5+0=9)

**"Divisor ÷5 vs ÷7"**

- Old assumption: some characters use ÷7 (Goku Y=14 from total=100)
- Solution: ALL characters use ÷5 on `damage1`. Goku Y uses damage1=70 →
  70/5=14

---

### Damage Types

Three damage types with character resistances:

| Type                | jpower Field | Examples         |
| ------------------- | ------------ | ---------------- |
| Punch/Kick (Impact) | damage1      | Physical strikes |
| Energy/Ki           | damage2      | Energy blasts    |
| Blade               | damage3      | Sword slashes    |

**Special case:** `hitProperties=1` in collision data forces blunt damage
regardless of weapon visual.

**Verified:** Kenshin uses sword visually but deals punch/kick damage (tested vs
Naruto and Luffy with different resistances).

---

### chr_b.bin → Collision File Mapping

**Source:** ARM9.bin offset 0x0924B0 contains pointer table to collision file
names in exact chr_b.bin order.

> **[CORRECTED 2026-07-02]:** Static disassembly of `0x020924B0` shows this is
> an 8-byte-stride table of `{ASCII char-ID C-string, packed word}` records
> (74 entries), consumed at load time to build a resource key — **not** a
> table of raw collision-file pointers. The one traced consumer of the
> string half was found building a sprite-archive (`.aar`)/ending-credits key,
> not a collision-file path; no code path from this table to collision-file
> loading was confirmed. The file-name-order correspondence documented below
> may still hold empirically, but the *mechanism* ("pointer table to
> collision file names") is disproven. See
> [Battle-Engine-Map.md § hitbox-priority](Battle-Engine-Map.md#subsystem-hitbox-priority)
> for full detail and refuted-hypotheses.

**Complete mapping:** See docs/research/chr_b-Complete-Mapping.md

**Verified:**

- db_b_01 (Goku): 25 collision entries ✓
- dt_b_04 (Taizo): 1 collision entry ✓
- bl_b_01/bl_b_02 collision counts match ✓

---

### chr_b.bin → jpower.bin Linkage

**Formula:**

```
jpower_attack_block_index = chr_b.classId & 0xFF
```

The low byte of `classId` points to a jpower ATTACK block containing move
parameters.

**Structure:**

- jpower.bin: 311 entries organized into 43 ATTACK blocks
- ATTACK blocks contain actual move data (damage, hitstun)
- DATA blocks (type1=0) separate ATTACK blocks

**Verified:**

- db_b_01 (Goku): classId=256 → Block 0 with damages [7,7,7,7,7,7,7,14,14] ✓
- Multiple characters can share blocks but have DIFFERENT movesets
- **Critical:** jpower blocks are template libraries, not 1:1 movesets
  - Goku/SSJ/Majin Buu all use Block 0 but only Goku/SSJ share moveset
  - Selection mechanism within blocks is unknown

---

### charId = Stat Templates (NOT Character IDs)

chr_b.bin has only **29 unique charIds** for **74 characters**.

**Examples of shared charIds:**

- charId=16: **Nami and Franky** (completely opposite weight/speed but identical
  chr_b entry)
- charId=7: Goku family (9 characters)
- charId=3: All Bleach characters + Lenalee

**Conclusion:** charId groups characters by stat template, not individual
identity.

---

### Character Mapping (Identity Only)

**All 74 battle characters identity-mapped** — every collision filename is
matched to a confirmed character name.

**Source:** Character-Mapping.md verified via in-game deck order checks.

**Note:** This is filename → character *identity* mapping only. Full
per-character kit maps (moves, damages, collision entries) exist only for Goku
(complete) and Ichigo (unverified); the rest of `docs/characters/*.md` are
partial or stubs — see the `Map status` header in each file.

---

### Walk Speed (chr_b.bin `statC`)

**Confirmed:** Walk speed IS stored in chr_b.bin, in the `statC` field.
It is **threshold/tier-based**, not linear:

- Zoro (statC=33) = slowest tier
- Luffy (statC=82) = middle tier
- Ichigo (statC=225) = fastest tier
- Lenalee (statC=153) and Killua (statC=300) share the same speed tier

**Edajima outlier (resolved confounder):** Edajima is the heaviest/slowest
character yet has a normal statC value — an **innate character passive** slows
him. This outlier confounded the earlier Nami/Franky comparison and led to the
now-retracted conclusion that walk speed was "NOT in chr_b.bin".

**Still open:** Only the exact threshold/tier boundary values remain unknown —
see ticket **JUS-n3p**.

---

### Projectile System Categories

Four distinct projectile types identified via collision data and gameplay:

1. **True Projectiles** - Travel across screen (Goku fwd Y, Zoro fwd Y)
2. **Extended Hitboxes** - Large area, minimal travel (Goku down B)
3. **Summons** - Separate entities (Yugi, Dio's Stand)
4. **Persistent/Traps** - Remain after switch-out (Yugi fwd B, Dr. Mashirito)

**Verified:** Confirmed via collision type values and in-game observation.

---

### Buff System

**Buff groups exist:**

- Group A: Yusuke, Ichigo (compatible)
- Group B: Fuusuke, Raoh (compatible)
- Groups A and B cannot share buffs

**Technical:** damageFlags=64 (0x40) triggers buff, modifier sub-records contain
2x damage.

**Verified:** In-game buff transfer testing confirmed compatibility matrix.

---

## ⚠️ LIKELY TRUE (Medium Confidence)

### Deck koma.bin Structure

- Entry size: 12 bytes (0x0C)
- Offset 4: letters (series index)
- Offset 5: number (character index within series)
- 890 total koma entries (helpers + supports + all battle panel variants)

**Evidence:** Koma-Research.md documentation and file size match.

**Uncertainty:** Haven't fully traced koma → chr_b linkage.

---

### Universal Frame Data

From user testing:

- Landing lag: 16 frames
- Dash: 15 frames
- Jump: 19 frames

**Uncertainty:** Measured via video recording, not from binary data. Not
verified in data files.

---

### Collision `frameStart` Meaning

`frameStart` appears to be when hitbox becomes active within animation, NOT full
startup frames.

**Evidence:** User-measured startup frames don't match collision frameStart
values with consistent offset.

**Uncertainty:** Could be animation-specific or have external modifiers.

---

### Series Order in Deck Builder

42 series in specific order from Eyeshield 21 to Meta/Debug.

**Source:** User-provided list documented in Deck-System.md.

**Uncertainty:** Not verified against binary data, but matches observed file
prefixes.

---

### HP Formula

```
HP = base_hp + (deck_koma_size - 1) * 16
```

**Evidence:** User tested 5+ characters, all followed +16 HP per koma pattern.

**Exception:** Ichigo's 6→7 koma transition maintains same HP (form change).

**Uncertainty:** Base HP values not found in chr_b.bin or other files yet.

---

## ❓ UNKNOWN (No Confidence)

### Character Weight

**NOT stored in:**

- chr_b.bin battleParams (proven via Nami/Franky test)
- Collision files (all reserved fields = 0)
- ARM9 file name table region

**Known from gameplay:**

- HEAVY: Raoh, Edajima, Franky
- LIGHT: Lenalee, Nami
- STANDARD: Goku, Dio, Gon, Momotaro

**Possible locations:**

- Hardcoded in game executable by character index
- Effect files (chr/effect/\*.bin) - only 21/74 characters have these
- Overlays or other code sections
- Calculated from undiscovered formula

**Note:** Weight was previously assumed co-located with walk speed. Walk speed
is now **confirmed** in chr_b.bin `statC` (see CONFIRMED section); weight
remains unknown and must be tracked separately.

---

### battleParams Field Meaning

12 bytes in chr_b.bin with unknown purpose.

**Known:**

- NOT weight (bytes 8-10 don't correlate)
- NOT walk speed
- Values range from 0-100 typically
- Nami and Franky have identical values despite opposite properties

**Speculation:** Could be stat modifiers, hitstun resistance, or other combat
parameters.

---

### komaSize Field Meaning

chr_b.bin `komaSize` values (2-6) do NOT match deck koma sizes (4-8).

**Evidence:** Raoh has deck komas 6,7,8 but chr_b komaSize=6.

**Possibilities:**

- Minimum deck koma
- Tier indicator
- Base template size
- Unknown encoding

---

### jpower Entry-to-Move Mapping

**Known:**

- classId points to jpower ATTACK block (confirmed)
- Blocks contain damage values for moves
- **jpower blocks are template libraries** - characters select subset of entries
- Characters sharing same block can have completely different movesets (Goku ≠
  Majin Buu, Luffy ≠ Robin, Nami ≠ Franky)

**NEW DISCOVERY (2026-01-30): Collision damageFlags can be global jpower index**

For Ichigo (bl_b_01):

- damageFlags values (2, 3, 5, 7, 8, etc.) = **direct jpower array indices**
- Example: damageFlags=2 → jpower[2] (ID=6, total=50) → 50/5=10 damage ✓
- Most Ichigo collision entries have non-zero damageFlags

For Goku (db_b_01):

- Almost all damageFlags=0 (different pattern from Ichigo)
- damageFlags=0 does NOT simply mean "use jpower[0]"
- Goku B=8 requires damage1=40 (at indices 146, 195, 218) but damageFlags=0

**Entries with jpower damage1=40:**

| Array Index | jpower ID | linkCategory | Notes                       |
| ----------- | --------- | ------------ | --------------------------- |
| 146         | 379       | 1            | First entry with damage1=40 |
| 195         | 539       | 1            | Same linkCategory           |
| 218         | 604       | 1            | Same linkCategory           |

**NEW DISCOVERY (2026-01-30): Two distinct damage reference systems**

Characters fall into two categories:

1. **Direct jpower reference** (Ichigo pattern): damageFlags = global jpower
   array index
   - Ichigo: 19/20 collision entries have damageFlags > 0
   - damageFlags=2 → jpower[2] (total=50) → 50/5=10 damage ✓

2. **Indirect/ARM9 lookup** (Goku pattern): damageFlags mostly 0
   - Goku: Only 2/25 collision entries have damageFlags > 0
   - Most moves use damageFlags=0 → triggers unknown lookup mechanism
   - Somehow accesses jpower entries with damage1=40 (indices 146, 195, 218)

**Verified damage values (2026-01-30):**

| Character  | tier | B Damage | Required d1 | Status                  |
| ---------- | ---- | -------- | ----------- | ----------------------- |
| Ichigo     | 2    | 10       | 50          | ✓ Confirmed             |
| Bankai     | 1    | 9        | 50          | ✓ Confirmed (50/5-1=9)  |
| Goku       | 2    | 8        | 40          | ✓ Entries exist         |
| Naruto     | 2    | 8        | 40          | ✓ Entries exist         |
| Buu        | 2    | 9        | 45          | ✓ Entries exist         |
| Caramelman | 3    | 13       | 60          | ✓ Confirmed (60/5+1=13) |

> **NOTE:** Buu was previously listed as "anomaly" because we looked for
> `total=45`. **RESOLVED:** Formula uses `damage1` only, and entries with
> `damage1=45` DO exist.

**Still Unknown:**

- How damageFlags=0 resolves to jpower entries (ARM9 lookup table?)
- Which jpower entry within a block corresponds to which move (B, fwd B, Y,
  etc.)
- How multi-hit moves work (Y combo 4+4+6, up B 3+3)
- Why only some collision entries have damageFlags>0 while most use 0

---

### Knockback Physics

**Known from jpower.bin:**

- knockback field exists (0-255 values)

**NEW: Character Struct Region (2026-02-03 GDB session):**

- Physics/velocity data is in `+0x006A` to `+0x00BA` region (not 0x00-0x40 as
  originally hypothesized)
- Fields `+0x006A/6C`, `+0x0072/74`, `+0x007A/7C` show large deltas during
  knockback
- Exact velocity field not yet isolated - comparing light vs heavy characters
  showed differences but position/timing variations made isolation difficult

**Observed:**

- Different characters have different knockback distances with same attack
- Nami (light) visually travels farther than Raoh (heavy) from same attack
- Light characters may have shorter hitstun duration (recover faster)

**Still Unknown:**

- Exact byte offset containing knockback velocity
- How jpower knockback value translates to velocity
- How character weight affects knockback received
- Formula for applied knockback

---

### Hitstun Mechanics

**Known from jpower.bin:**

- hitstun field exists (values: 0, 5, 10, 50+)

**NEW: Character Struct Findings (2026-02-03 GDB session):**

- `+0x0078 [ground_air] = 0xC0 (192)` indicates **LAUNCHED/HITSTUN state**
  - Distinct from 0x00 (air/jumping) and 0x22 (ground)
  - This is a state FLAG, not a timer
- **Timer region `+0x0098` to `+0x00BA`** contains countdown timers
  - Decrements in -5/-3 alternating pattern (suggests 32-bit values read as 16-bit)
  - Fields: +0x0098/9A, +0x00A0/A2, +0x00A8/AA, +0x00B0/B2, +0x00B8/BA
  - These timers run during hitstun/recovery
- Heavier characters (Raoh) show longer timer activity than lighter characters (Nami)

**Still Unknown:**

- Exact mapping of jpower hitstun values to timer initial values
- Which specific timer field controls hitstun vs recovery vs other states
- How hitstun affects combo potential
- Blockstun mechanics

---

### Gravity and Launch Physics

**Observed:**

- All characters jump same height
- Knockback has both horizontal and vertical components

**Unknown:**

- Gravity value
- Fall speed
- Launch trajectory calculations
- How knockback vs knockup differ

---

### Combo System

**Unknown:**

- What determines true combos vs escapable sequences
- How hitstun links to combo windows
- Move priority/clash resolution

---

### Flash Dash Mechanics

**Observed:**

- Standard dash: 15 frames, consistent length
- Flash dash: character disappears/reappears, variable distance
- Dr. Mashirito has unique air dash with vertical momentum

**Unknown:**

- What determines flash vs regular dash
- Where dash distances/properties are stored

---

### Form Changes

**Observed:**

- Some characters transform during specials (temporary)
- Some have permanent form changes (SSJ, Bankai)
- Shinsetsu Bo-bobo has form change with extra collision entries after
  terminator

**Unknown:**

- How form changes are triggered
- Where transformation data is stored
- Why Shinsetsu has 5 entries after collision terminator

---

### Nature Type Storage

**Observed:**

- Same character can have different natures (Power, Laughter, Knowledge)
- Nature affects special attacks
- Naruto has Power (4-koma vertical) and Laughter (4-koma square) variants

**Unknown:**

- Where nature is stored per koma panel
- How nature affects special move selection

---

### AI System

**Known:**

- AI files: LZSS compressed AIPM format
- ~6 parameters per character
- Template-based (explains "bad" AI)

**Unknown:**

- Actual AI parameters and behavior
- How complexity varies by character

---

### Support Characters (chr_s.bin)

**Known:**

- 140+ support characters
- Similar format to chr_b.bin (3860 bytes total)

**Status:** Not investigated yet.

---

## Next Research Priorities

### High Value

1. **jpower subType mapping** - How collision entries select jpower moves
2. **Multi-hit move mechanics** - nextId chains and combo system
3. **Weight location** - Critical for physics understanding (walk speed is
   solved: chr_b `statC`; only tier thresholds remain — JUS-n3p)

### Medium Value

4. **HP formula verification** - Find base HP in data files
5. **battleParams decoding** - 12 unknown bytes per character
6. **Hitstun frame data** - Convert jpower hitstun values to frames

### Lower Value

7. **Support characters** - chr_s.bin structure
8. **AI parameters** - Decompress and analyze AIPM files
9. **Effect files** - 21 character-specific effect files
