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

## 2026-07-02 — Phase-0 Gap-Closing Loop (addendum)

A follow-up loop (`docs/design/Static-RE-Phase0.md`) closed every
"verification pending"/never-traced gap the campaign above left open, without
any emulator/GDB execution. Full detail in the same
**[Battle-Engine-Map.md](Battle-Engine-Map.md)** (new/updated sections) and
**[GDB-Validation-Queue.md](GDB-Validation-Queue.md)** (regenerated).

- **Collision data re-mined at full-roster scale (round 2):** coverage went
  from 4/74 (5.4%) to 281/281 files (74 battle + 206 support + 1 item). This
  **broke several round-1 findings at scale**, not just weakened them: the
  `projectileId=-32` "fixed sentinel" hypothesis is refuted (15 distinct
  nonzero values in battle files, 25 in support); the `collisionType=4`
  necessary-for-`projectileId` framing is refuted (the real rule is
  `collisionType ∈ {4,5}`, 97.87% coverage); the `collisionType=5→hitTier=3`
  and `collisionType=3→hitTier=1` correlations both weaken to near-coin-flip;
  and round 1's own CONFIRMED_STATIC "`hitModifier` constant at 0" claim is
  overturned (9/2047 entries are nonzero). See
  [§ collision-data](Battle-Engine-Map.md#subsystem-collision-data).
- **projectile-entities fully verified:** the prior campaign's "adversarial
  lens verification pending" caveat is resolved — 4/5 claims are now
  CONFIRMED_STATIC (entity-pool alloc/free, spawn dispatch, spawn+ownership
  including a second character-struct back-pointer at wrapper`+0x18`); the
  despawn function is capped PLAUSIBLE (cannot be statically proven
  projectile-specific vs. a shared spawned-effect routine). See
  [§ projectile-entities](Battle-Engine-Map.md#subsystem-projectile-entities).
- **Guard/SP gauge coverage (new, spec B12):** no second *fixed* character-struct
  offset analogous to `+0x56c` (HP) was found; the leading guard/SP candidate
  is a dynamically-linked Meter-node list at `char+0x558`. A previously
  invisible sibling **drain** trampoline (`0x020783B8`) was discovered
  adjacent to the known HP trampoline — a concrete demonstration that
  `xrefs-to`/`pool-values` cannot see `bx ip`-style indirect jumps. See
  [§ guard-sp-gauges](Battle-Engine-Map.md#subsystem-guard-sp-gauges).
- **chr_b singleton reframed (new, spec B14):** `0x0214BD80` is a "battle
  resource manager" singleton owning ~15 tables/resources, of which chr_b's
  own record array is one; all 97 ROM-wide xref hits (not the ~87 previously
  estimated) are now classified, and the complete 60-byte record map is
  built, including a confirmed schema mismatch (`CharId`+`Flags` are 5
  independent ability-ID bytes, not a `charId` byte + a `flags` u32). Whether
  the `+0x558` per-technique node feeding this cache is the *same* object
  `charPtr+0x56c` points to for hit-resolution is the campaign's **top open
  dispute** — the two adversarial lenses disagree, and it is deliberately left
  unresolved pending one GDB breakpoint (queue card #1). See
  [§ chrb-catalog](Battle-Engine-Map.md#subsystem-chrb-catalog).

---

## ✓ CONFIRMED (High Confidence)

### chr_b Runtime Access — Battle Resource Manager Singleton

**Confirmed 2026-07-02 (Phase-0, spec B14):** `*(0x0214BD80)` is a "battle
resource manager" singleton, not a chr_b-specific pointer — chr_b's own
60-byte-record array (manager`+0x40`, stride `0x3C`) is one of roughly 15
tables/resources the same singleton owns (koma, kshape, chr_s, an
ability/passive-effect lookup table, several still-unidentified fixed-size
tables, a match-config sub-struct). All 97 ROM-wide references to the
singleton are classified (only 13 touch chr_b's own array). The complete
record map is built, confirming `statA`/`statB`/`statC` (`+8`/`+0xA`/`+0xC`),
`BattleParams` (`+0x24`, read **live** by the Battle-AI overlay `ov11` — the
only confirmed live, uncached chr_b read at battle time), and `TextIds`
(`+0x30`, character name + 5 per-technique names). One confirmed schema
mismatch against the exported `chr_b.json`: on-disk `CharId`+`Flags`
(`+3..+7`) are consumed as **5 independent ability-ID bytes**, never as a
combined `charId` byte + `flags` u32. See
[Battle-Engine-Map.md § chrb-catalog](Battle-Engine-Map.md#subsystem-chrb-catalog).

**Not yet settled:** whether chr_b's `CombatStatN` value, cached into a
per-technique struct at setup time, is the same struct ov6's hit-resolution
code later reads via `charPtr+0x56c` — see the Map's "TOP OPEN DISPUTE"
subsection (one GDB breakpoint away from resolution).

### Entity Pool (Projectiles / Spawned Hitbox-Effects)

**Confirmed 2026-07-02 (3-lens verified, Phase-0):** a global pooled-entity
allocator/destructor pair (`0x020834D4`/`0x02083648`) with a 3-anchor
free/active/pending list manager (singleton at RAM literal `0x0214BE14`)
backs projectile and other spawned-hitbox/effect entities. Spawn is
dispatched from a 13-way ov6 event switch (`0x021574CC`) through an
ownership-wrapper allocator (`0x02168CF4`) that records **two** back-pointers
to the attacking character: the MoveInfo pointer at wrapper`+0xc` and the
raw character-struct pointer at wrapper`+0x18`. See
[§ projectile-entities](Battle-Engine-Map.md#subsystem-projectile-entities).

### Collision Data at Full-Roster Scale

**Confirmed 2026-07-02 (round 2, 281/281 files, Phase-0):** the collision
(23-field) and jpower (20-field) schemas still share zero field names at
full scale; `damageFlags==0` occurs on 46.86% of battle entries (a near
coin-flip, not the 57.1% "majority" round 1's 4-file sample suggested); and
`hitModifier` is **not** constant at 0 (9/2047 entries are nonzero,
corroborated across the item and support populations too) — this directly
overturns round 1's own CONFIRMED_STATIC claim to the contrary. Several other
round-1 correlations (the `-32` `projectileId` sentinel, `collisionType=4`
necessity, `collisionType=5→hitTier=3`/`3→hitTier=1` skews) did **not**
survive full-roster scale and are now SPECULATIVE — see
[§ collision-data](Battle-Engine-Map.md#subsystem-collision-data) for the
complete round-2 table.

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

12 bytes in chr_b.bin with unknown *value* meaning (per-field semantics still
undecoded), but its *consumer* is now identified.

**Known:**

- NOT weight (bytes 8-10 don't correlate)
- NOT walk speed
- Values range from 0-100 typically
- Nami and Franky have identical values despite opposite properties

> **[UPDATED 2026-07-02, Phase-0 spec B14]:** `BattleParams` (chr_b record
> offset `+0x24`) is read **live** (not cached) exclusively by the
> Battle-AI overlay `ov11`, via two getters read with two *different* element
> sizes (`ushort[6]` for the first 8 bytes, `byte[]` for the last 4) — the
> first getter builds a per-technique "availability" bitmask, the second a
> per-slot AI range/facing table used in threshold comparisons. This is the
> only chr_b field confirmed read live at battle time; everything else
> chr_b-derived that reaches battle code is cached at technique-setup instead
> (see `Battle-Engine-Map.md` § chrb-catalog). The exact per-byte stat
> meaning is still undecoded — "stat modifiers / hitstun resistance" remains
> speculation — but "used by CPU decision-making, not a cosmetic/UI field" is
> now confirmed.

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

## 2026-08-14 — Loop-Atlas: koma sprint COMPLETE, flipping to combat phase

Eleven iterations of the self-paced Atlas loop, run alongside a second session that built an
agent-drivable melonDS harness. The koma/deckbuilding system is now fully decoded and the design
brief is written (`../design/Koma-System-Design-Brief.md`).

**Solved this sprint:**

- `koma.bin` — all 12 bytes of 890 records; `kshape.bin` — all 66 shapes as 4x5 footprints, and
  panel size is the occupied-cell count (group index + 1), never a stored field
- Panel type derived from size (Helper 1, Support 2-3, Battle 4-8); 312 characters, one Helper each
- `komatxt.bin` holds per-panel display names, which is why sizes 7-8 can rename
- All 57 abilities named from `ability.bin` + `ability_t.bin`, including all ten IDs the
  cheat-code table listed as Unknown. Ｊ魂 (J-soul) = HP; 必殺魂 = SP gauge
- Per-character-per-size HP for all 74 playable characters, plus the bonus model
  (`+8` per source, four sources, `256` engine cap = the exact maximum the data can produce)
- **Nature** — the last unknown. It is computed, not stored: high nibble of `koma.bin` `+0xB`, with
  `3` as a no-override sentinel falling back to a base nature in `chr_b`/`chr_s`

**Three claims of mine were wrong and are now corrected in place**, each with a banner on the
original doc: "nature is not in koma.bin" (I dismissed a differing field that was a lookup input),
"exhaustively refuted" (the search only covered dedicated tables), and the bit-`0x10` override
mechanism (the real test is a nibble sentinel; my version was right for the wrong reason).

**Method lesson worth carrying into the combat phase.** Static value search found every *table* in
this system and then failed completely on the one property that is a *function*. Two of nature's
three inputs were fields already decoded for other purposes. A value search cannot find a
computation — reach for the disassembly sooner.

**Also produced:** `scripts/analysis/dump_koma.py` (panel dump with resolved natures),
`scripts/analysis/extract_overlays.py` (all 14 ARM9 overlays, an ~1.4 MB blind spot nobody had
extracted), and five harness cards in `Human-Testing-Queue.md` of which two closed statically.

**Combat-phase handoff.** `0x02078CB8` is a "has explicit nature?" predicate living in the battle
engine, so nature is read during combat despite being a deck-building property — a likely home for
the nature matchup multiplier. Combat code is `arm9.bin` + overlay ov06 only; `bl 0x020783CC`
(the HP-delta apply) appears 8 times in ov06 and zero times in `arm9.bin`.

## 2026-08-14 — Loop-Atlas: melee damage producer marked STUCK

Five iterations of the combat phase went at "where does melee damage come from". The negatives are
solid and worth keeping; the answer is not found, and I'm marking it rather than spending a third
consecutive wake.

**Established:** HP changes only via a store to `+0x18`, and every such store with clamp context is
enumerated — 17 sites across 8 arm9 functions, plus one ov6 field serialiser that isn't a writer. The
core apply `0x02078488` has 14 callers, all classified (6 Thumb heals, 2 status ticks, 2 script
wrappers, 3 arg-passing dispatchers, 1 accumulator flush). Damage demonstrably happens —
`7168 → 6784` = 384 raw = 6.000 displayed, reproducibly.

**Refuted along the way:** the pending-damage accumulator at `[r6+0x1A8]->+0x10->+0x140` (breakpoint
logged `r1 = 0` on every hit); `0x02078660`/`0x020785B8` as damage paths (they're HP/SP restore
utilities taking boolean flags and a percentage).

**The blocker is tooling, not reasoning.** The remaining candidates are the three arg-passing
dispatchers, reached through pointer tables. Every technique available here — value search, offset
scan, constrained offset scan, cross-binary caller enumeration — has been applied, and three of them
produced confident false positives on the way. The next step needs indirect-call resolution:
Tier-2 task **D0.3** (headless Ghidra import) is already specified and is exactly the missing
capability. A pointer-table scanner would be the cheap version.

Not spending the charter's codex second opinion: codex hung for an hour on this same damage path for
the emulator-harness session, and the gap is tool capability rather than analysis.

**Method lessons from this phase, all earned the hard way:**

1. An offset-only scan over these binaries is not evidence about a specific struct. `+0x18` gave 226
   hits; `+0x140` gave a vtable initialiser that mimicked the exact pattern I predicted.
2. Constraining a scan isn't sufficient — constrain it enough to **read every hit**. 17 readable
   sites caught an error that 226 would have hidden.
3. A tool that only handles ARM will silently invent negatives. Two wrong conclusions came from that.
4. Overlays sharing a load address create phantom cross-overlay callers. `find_callers.py` now warns.
5. A coincidence that mirrors the structure you predicted is more dangerous than a random one,
   because the resemblance itself feels like confirmation.

---

## 2026-08-18 — Handoff, Loop-Atlas iterations 157–164

I can speak for **157–164 only**. For anything earlier, read the findings directory — don't trust any summary, including mine.

### 1. Current state

Iteration **164**, phase **combat**. Branch `loop/battle-engine-atlas`, tree **clean**, **8 commits** (`7ad111d..c8da30a`). Nothing pushed — that's the owner's call.

State file `scripts/analysis/loop-state-atlas.json` is current at iteration 164, 95 queue entries. Canon doc `docs/research/Battle-Engine-Map.md` has a `P157`–`P164` update block per wake. Eight findings added (`docs/research/findings/p157-*` … `p164-*`), each voice-passed through `claude -p --model claude-opus-4-6` with a numeric-token diff. All clean.

`docs/orchestration/COORDINATION-PROTOCOL.md` and `Charter-Atlas-additions.md` **don't exist in this worktree yet**. They weren't deleted — they haven't landed.

### 2. What got settled

**The dream-attack chain multiplier isn't in the status/effect subsystem.** `CONFIRMED_STATIC`, three wakes, three angles. P157: all ten HP-adjust `bl` sites carry only constant shifts (`lsl #6`, `lsl #8`). P158: the writer of `[param+0x4]` stores a **pointer** into static table data — the amount is a constant. P159: effect selection is a byte-table lookup plus a negated byte. Combined with C6b's earlier "no melee damage reaches this subsystem", the question is closed. A dream attack is a *move*, so the hunt belongs to the move script system (`move_script_location_UNKNOWN`).

This was a **productive negative**: it yielded the dispatcher `0x02158ED0`, the complete 42-entry effect-id table, the on-hit flush, and the duration formula.

**The one non-constant formula in the engine** (P158, ov6 `0x02158F78`): `duration = base + (base/10) * (V*2)`. `V` is **unidentified** — see §4.

**The battle root** is `[0x02172960]`, a 368-byte (`0x170`) heap object with a two-write lifecycle. `0x0214D928` is a literal **pool word**, not a global. Root map extended 11 → 14 slots (`+0x4C`, `+0x158`, `+0x15C`).

**The match-settings struct is `0x020AFE90`**, and the whole ルールセレクト screen is mapped to it — six settings, three booleans. Time limit `+0x1C` is a **frame count**. The mode classifier lives in **ov1 `0x0216446C`**, reading a 16-byte-per-mode descriptor table — time conversion is data-driven.

### 3. Next task and queue shape

**Top of queue: read ov1 `0x021643A4`.** Its return value is the `ctx` whose `[ctx+4]` is the mode table base. That gives us the table, all three modes' `+0xC` values, and finally explains the `144` in the second time-limit branch. Small, bounded, decisive.

Then: dump the 16-byte mode records and **re-check every campaign address in the `0x0214CD20` window** the way P164 did (five-way disassembly + boundary + coherence). That sweep isn't hygiene anymore — P164 caught a load-bearing address attributed to the wrong overlay in a doc I'd written **one iteration earlier**.

### 4. Retractions and live taint

| retracted | what it was | still tainting? |
|---|---|---|
| `root+0x4C` = "per-character stat" (P158, retracted P160) | the term `V` in the only non-constant formula | **YES.** The formula's arithmetic is verified three ways and stands. Its *meaning* doesn't. Don't describe it as stat-scaled. `jus-wic` settles it. |
| effect table `+0x5` = "the table's key" (P157, refuted P158) | promoted a gapless `0x00`–`0x1F` permutation to a structural role before finding the indexing code | No — the index is the caller's `id`. Fixed in the map. |
| "chain scaling must live where `[param+0x4]` is written" (P157, refuted P158) | that field is static table data | No. |
| "global `0x0214D928`" (campaign-wide, fixed P161) | a literal pool word | **Partly.** Fixed in the map, the P156 handoff, and the chara-setup finding. Raw `; = 0x0214D928` disassembly comments left alone — the tool's output is correct on its own terms. |
| P154 struct base at `0x0214CCF8` (before me; refuted by its author) | — | No. Only `+0x00` exists. |

**Unfixed root cause (will bite again):** `query.py`'s ARM listing prints a literal's **value** in its `; = 0x...` comment; `thumb_disasm.py` prints the **pool address**. Same shape, opposite meaning. That's how one pool word became "the battle root global" across four documents. Queued as a tool fix.

**Process failure I made twice in five wakes.** P157 drafted an already-documented census as new. P160 spent a whole wake reaching `PLAUSIBLE` on something `findings/battle-add-root-object-map.md` already had at `CONFIRMED_STATIC`. Charter rule added: `grep -rl` the claim's key address through `findings/` **and** `Battle-Engine-Map.md` before drafting — and **not** via the state file, which is hundreds of keys of my own summaries and is exactly where I kept re-finding my own questions instead of the record's answers.

### 5. Open threads with the runtime loop

The runtime loop is **`justoolkit-ed`** (resolved via `ListAgents`). Four `coord` beads carry the reachability basis, expected shape, one-line test, and failure signature:

- **`jus-wic`** (P1) — the `root+0x4C` dump. Owed **to** us; accepted, queued behind owner emulator work. Settles the only multiplier we have.
- **`jus-vrz`** (P1) — falsification cards for **every** address I handed them, with confidence labels. Two runtime-confirmed, two confirmed-by-elimination, **two `PLAUSIBLE` only** (`0x020AFEA0` mode, `0x020AFEC3` COM count) — don't treat those as confirmed.
- **`jus-qsh`** (P2) — the ObjShot kind-byte walk. Owed **to** us, long-queued, now re-aimed: their gimmick discovery means stage hazards may occupy kinds in that table — a candidate explanation for the six entity-less kinds.
- **`jus-q4b`** (P2) — the Thumb writer of `[0x020AFE90+0x28]`. ARM search exhausted; only a *clearing* store exists.

**What I sent them:** the `0x0214D928` correction (unprompted); the six rule-select addresses with per-address confidence; the warning that their `rules_off()` clears **two of three** booleans (`0x020AFEBD` untouched); and that four of six rules have never been varied in any runtime data, since all of it is training-mode.

**What they gave us:** the items/gimmick toggle addresses, which named the `0x020AFE90` struct that had been open for dozens of iterations. Also, against their own interest: **every damage measurement in their last two sessions ran with a projectile-spawning gimmick live**. Our "damage is flat" synthesis leans on their numbers, so treat any single-run figure from those sessions as having an unmodelled source in the room. P157–P159's clearing of the status subsystem is static and unaffected.

**The coordination failure, stated plainly:** I treated them as a service to call when blocked, not as a party to my conclusions. I put a formula into the canon doc with its key term labelled on no evidence and didn't ask for the one dump that would settle it — for four wakes, until the owner prompted. Two mechanisms fix most of it, and the incoming protocol encodes both: retractions get **pushed** the same wake naming every dependent, and every measurement carries its environment while every address carries its reachability basis.

### 6. Codex usage — keep this

It earns its place, and it has been wrong. That's the point.

**The pattern:** hand it **raw instruction hex, an address-free frame, and no hypothesis** — and do it **before** forming a conclusion. Never a second run of my own tool; a genuinely different representation.

What that bought across eight wakes: it caught a special case I read straight past (`0x02078428` sets HP to **1** on every living character when its `r1` argument is 0); it proved from displacement arithmetic alone that a `free` and a null-store hit the same pool word, with no address knowledge; it independently computed a literal at blob offset `0x019A` from PC alignment — which is what confirmed the pool-word fact underpinning the whole root map; and it refused to answer when I mangled a prompt and omitted the data, rather than inventing a decode.

**It was also flatly wrong once** (P158): it swapped `Rn` and `Rs` in an `mla`, which would have made the duration formula dimensionally incoherent. Settled by a **third** representation — the encoding bits (`0xE0223290`: `Rd`=r2, `Rn`=r3, `Rs`=r2, `Rm`=r0; ARM `MLA` is `Rd = Rm*Rs + Rn`). **Codex is not an oracle. When it disagrees on a decode, go to the bits.**

**Operational notes:** `codex exec "<prompt>"` **reads stdin even with a positional prompt** and hangs on an open terminal — one wake burned 560s for 39 bytes. A **backgrounded** call dies when the turn ends at `ScheduleWakeup`; "dispatch it and read it next wake" always comes back empty. The only reliable form is **foreground, `< /dev/null`, generous timeout.**
## 2026-08-19 — Loop-Atlas, iterations 165–174: effect subsystem mapped

Progress note covering iterations **165–174 only**. For earlier work, read the findings directory. For other branches, read those branches (see §5).

### 1. Current state

Iteration **174**, combat phase. Branch `loop/battle-engine-atlas`, tree clean. Ten findings added (`findings/p165-*` … `p174-*`), each voice-passed through `claude -p --model claude-opus-4-6` with a hex-token diff. `Battle-Engine-Map.md` has a block per wake.

Coordination docs (`COORDINATION-PROTOCOL.md`, `Charter-Atlas-additions.md`, the outbox-gate hook) landed at the start of this run. Runtime is `justoolkit-fa`; ledger is `justoolkit-dc` (identity `justoolkit-87`); `justoolkit-ba` is the owner's interactive session, **not a loop**.

### 2. What got settled

**The status/effect subsystem is mapped end to end.** From the dispatcher outward:

| piece | address | note |
|---|---|---|
| dispatcher | ov6 `0x02158ED0` | `(battleObj, id)`; indexes two parallel stride-8 arrays |
| handler table | ov6 `0x02171168` | 42 entries × 8; `+0x7` is the status opcode |
| **param table** | **`bin/state.bin`** | 336 bytes = 42 × 8. `+0x2` base duration, `+0x4` signed amount, `+0x0` flags. Live base `[[0x02172984]+4]` |
| **cancel gate** | ov6 `0x0215986C` → `0x02158EB0` | `(Mem32[battleObj+0x120 + 4*(op>>5) + 8] >> (op & 0x1F)) & 1`; set bit zeroes the duration and the handler retires |
| **the bitset** | `battleObj+0x128` | the **cached ability bitset** — a per-ability behaviour switchboard, not resistance |
| **tick driver** | ov6 `0x02158C68`–`0x02158D60` | second half of `0x02158B20`; decrements `node+0xE` by 1 at `0x02158C88`, calls `node+0x0` at `0x02158CF0`, 2 slots at stride `0x18` |
| expiry | ov6 `0x0215911C` | installed stub + `(battleObj, slot)`; **unread** |
| apply worker | arm9 `0x02078488` | `+delta` into `char_struct+0x18`, clamped `[0, max]` |

**Term V is 0 in ordinary play.** The campaign's only non-constant formula never varies. Confirmed by reading the formula's stored output at `node+0xE` across **ten** effect ids — `duration == base` every time.

**Two channels, not one.** Route B stages effect ids on the entity and the flush applies them: `X+0x172` carries the **gauge** family, `X+0x173` (stored negated) carries the **statuses**. 28 attributed dispatches, zero crossover.

**Ability bits are behaviours.** Two bits measured to distinct effects with their own negative controls — bit 4 gives total damage immunity (384 raw → 0), bit 8 doubles effect decay (confirmed to the frame). The gate reads the same word indexed by status opcode, so a third consumer exists at bit 14.

**Rule modes.** `0x020AFEA0` indexes a **31-entry** handler table in ov6 (`0x02170EAC`, 12-byte records); the 22 described modes live in `bin/rulemess.bin`, the extra nine are story mode (owner-confirmed). `0x020AFEAC` is the time limit in frames, `(じかん+1)*144-1` for versus modes, confirmed end to end across a whole match.

**Format correction with campaign-wide reach:** pointers in JUS `bin/*.bin` text files are **self-relative**, not absolute — 1,347 of 1,347 verified across six files.

### 3. Open questions, by priority

1. **The KO path** — hunting the owner's 1-HP floor. The entire DoT path is mapped and nothing on it clamps to 1.
2. `0x0215911C` — the expiry handler, last unread function on the effect lifecycle.
3. `0x021613C4(battleObj+0x1C, 0xF, 2)` — the second route to faster decay.
4. The staging writers of `X+0x172`/`X+0x173`. No immediate-offset store in the ROM writes them; needs a watchpoint or register-offset-aware static tool. Blocked behind `jus-fun`.
5. The active-character swap. Live lead: the ability bitset's *contents* changed within one savestate.

### 4. Retractions

Eleven this run. The ones that matter going forward:

- **The ov12 "staging setters"** were `ALTextDS.cpp` text-widget fields. An immediate-offset search finds every struct in the ROM at that offset. Lesson: **name the containing function before believing an offset hit.**
- **The opcode-based family boundary** — refuted by a single counterexample; the id-range boundary I replaced was correct. My "refinement" was the error.
- **`char+0x56C` is not HP** — it is. I had a clamp-to-0 and the owner's stated floor of 1, and resolved the conflict by demoting my own derivation. Lesson: **when two facts conflict, hold both open.**
- **"Bit 29 is set, so the effect was cancelled"** — computed from a word already retracted. Lesson: **a retraction isn't transitive; re-derive everything downstream.**
- **The `+0x6A`–`+0xBA` physics window** handed to the runtime loop — measured, doesn't move. I passed along a documented offset without checking whether anyone had ever tested it.

### 5. Process changes that earned their keep

- **Check the record across branches.** `HP-Struct-From-Disassembly.md` and `Ability-Bitset-Is-Not-Resistance.md` both live on other branches and both answered questions I was re-deriving from scratch. A worktree-local grep only checks a fraction of the record.
- **Don't reprice priorities off a partner's explanation.** I moved the same scheduling decision twice on successive accounts of a yield, both later withdrawn.
- **Owner questions go in `jus-law`** as confirm/deny with a stated break condition; the ledger surfaces them. One line from the owner has repeatedly beaten a wake of measurement — the freeze attribution, the story-mode answer, and the DoT floor all came that way.

### 6. Instrument rules

Ten now, nearly all self-caught by the runtime loop. The load-bearing ones for a static reader:

- The shape of a number is not a test.
- An independent-agreement claim is only as independent as its weaker half, and the receiver is least motivated to audit it.
- Instrument liveness and stimulus occurrence are different preconditions; a null needs both.
- When a treatment looks decisive, add the condition that would produce the same result without your mechanism.
- A rate averaged over a long window cannot see a one-event difference at the start.

The pattern behind most of this run's errors on both sides: *a plausible mechanism sitting in front of you is more dangerous than none at all, because it ends the search.*

**Addendum, same day (P174 close).** `jus-eml` is measured: a synthetic id-19 node with the player's ability bit
29 set comes back **stubbed and zeroed**, with an inert-bit control and a second-treatment control (bit 8, which
decays faster) in the same experiment. So **status immunity is an ability**, and **effect opcode == ability ID** is
measured rather than composed from two premises about the same word. **Three** bits of `battleObj+0x128` now carry
distinct measured behaviours with controls — bit 4 total damage immunity, bit 8 doubled decay, bit 29 effect
cancellation. Nothing in §3's open list changes; the expiry handler `0x0215911C` is still the last unread function
on the effect lifecycle, and the KO path still owes us the owner's 1-HP floor.

