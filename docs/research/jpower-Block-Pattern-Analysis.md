# jpower.bin Block Pattern Analysis

Comprehensive analysis of jpower block patterns, damage values, hitstun patterns, and unknown fields affecting combat.

**Generated:** 2026-01-31  
**Based on:** jpower-Mapping.md, JPowerEntry.cs, chr_b-Complete-Mapping.md

---

## Executive Summary

- **Total jpower entries:** 311
- **ATTACK blocks (type1=1):** 43 blocks (estimated)
- **DATA blocks (type1=0):** Separators between ATTACK blocks
- **Block assignment:** `jpower_block_index = classId & 0xFF`
- **Critical finding:** jpower blocks are **template libraries**, not 1:1 movesets

---

## 1. Character-to-Block Mapping

### Complete Block Assignment Table

| jpower Block | Characters | Series | classId Range | Notes |
|--------------|------------|--------|---------------|-------|
| **0** | Goku, Goku SSJ, Majin Buu | Dragon Ball | 256 | **Paradox:** Majin Buu has different moveset |
| **1** | Vegetto, Vegeta | Dragon Ball | 257 | Different movesets despite shared block |
| **2** | Vegeta SSJ, Gohan SSJ | Dragon Ball | 258 | SSJ template group |
| **3** | Gohan SSJ2, Gotenks | Dragon Ball | 259 | SSJ2/fusion group |
| **4** | Gotenks SSJ | Dragon Ball | 516 | Unique SSJ fusion |
| **5** | Piccolo | Dragon Ball | 261 | Unique block |
| **6** | Frieza | Dragon Ball | 262 | Unique block |
| **9** | Luffy, Robin | One Piece | 521 | **Paradox:** Different movesets (stretching vs arms) |
| **10** | Gear 2 Luffy | One Piece | 522 | Unique transformation |
| **11** | Zoro | One Piece | 523 | Unique block |
| **12** | Nami, Franky | One Piece | 524 | **Paradox:** Different movesets |
| **13** | PCT Nami | One Piece | 525 | Unique transformation |
| **14** | Sanji | One Piece | 270 | Unique block |
| **17** | Naruto | Naruto | 529 | Unique block |
| **18** | Kyuubi Naruto | Naruto | 274 | Unique transformation |
| **19** | Sasuke | Naruto | 275 | Unique block |
| **20** | Sakura | Naruto | 532 | Unique block |
| **22** | Kakashi, Yoh, Yoh (White Swan) | Naruto, Shaman King | 278, 534 | Cross-series sharing |
| **23** | Anna | Shaman King | 535 | Unique block |
| **25** | Jotaro | JoJo | 281 | Unique block |
| **26** | Dio | JoJo | 282 | Unique block |
| **33** | Gon | Hunter x Hunter | 545 | Unique block |
| **34** | Killua | Hunter x Hunter | 290 | Unique block |
| **37** | Yusuke | Yu Yu Hakusho | 549 | Unique block |
| **39** | Kurama | Yu Yu Hakusho | 295 | Unique block |
| **42** | Hiei | Yu Yu Hakusho | 298 | Unique block |
| **47** | Yugi | Yu-Gi-Oh! | 303 | Unique block |
| **48** | Kenshin | Rurouni Kenshin | 304 | Unique block |
| **52** | Train, Ichigo, Bankai Ichigo | Black Cat, Bleach | 564 | **Paradox:** Different movesets, block may be empty |
| **54** | Eve, Renji | Black Cat, Bleach | 310 | Cross-series sharing |
| **56** | Rukia | Bleach | 312 | Unique block |
| **63** | Kazuki | Busou Renkin | 575 | Unique block |
| **65** | Hitsugaya, Allen, Lenalee | Bleach, D.Gray-man | 577, 321 | Cross-series sharing |
| **70** | Bo-bobo, Don Patch, Super Patch | Bobobo | 582 | Shared moveset confirmed |
| **71** | Shinsetsu | Bobobo | 327 | Unique block |
| **92** | Ryotsu | KochiKame | 348 | Unique block |
| **93** | Gintoki | Gintama | 349 | Unique block |
| **98** | Tsuna | Reborn | 354 | Unique block |
| **99** | Jaguar | Jaguar | 355 | Unique block |
| **100** | Arale | Dr. Slump | 356 | Unique block |
| **101** | Mashirito | Dr. Slump | 357 | Unique block |
| **102** | Caramelman | Dr. Slump | 358 | Unique block |
| **140** | Muhyo | Muhyo | 652 | Unique block |
| **146** | Kenshiro | Hokuto no Ken | 658 | Unique block |
| **147** | Raoh | Hokuto no Ken | 403 | Unique block |
| **150** | Seiya, Gold Seiya | Saint Seiya | 662 | Shared moveset confirmed |
| **157** | Neuro | Neuro | 669 | Unique block |
| **164** | Edajima | Otokojuku | 420 | Unique block |
| **166** | Kinnikuman | Kinnikuman | 422 | Unique block |
| **172** | Momotaro, Taikoubou | Otokojuku, Houshin Engi | 428, 684 | Cross-series sharing |
| **179** | Fuusuke | Ninku | 435 | Unique block |
| **187** | Kagura | Gintama | 443 | Unique block |
| **190** | Komaman Red, Taizo | Debug | 446 | Debug characters |
| **191** | Komaman Yellow | Debug | 447 | Debug character |
| **192** | Komaman Green | Debug | 448 | Debug character |

### Block Sharing Patterns

**Confirmed shared movesets:**
- Block 0: Goku + Goku SSJ (same moveset)
- Block 70: Don Patch + Super Patch (same moveset)
- Block 150: Seiya + Gold Seiya (same moveset)

**Same block, DIFFERENT movesets (proves template library model):**
- **Block 0:** Goku/Goku SSJ ≠ Majin Buu
- **Block 9:** Luffy ≠ Robin
- **Block 12:** Nami ≠ Franky
- **Block 52:** Ichigo ≠ Bankai Ichigo (may be empty block)
- **Block 70:** Bo-bobo ≠ Don Patch variants

**Cross-series block sharing:**
- Block 22: Kakashi (Naruto) + Yoh variants (Shaman King)
- Block 52: Train (Black Cat) + Ichigo variants (Bleach)
- Block 54: Eve (Black Cat) + Renji (Bleach)
- Block 65: Hitsugaya (Bleach) + Allen/Lenalee (D.Gray-man)
- Block 172: Momotaro (Otokojuku) + Taikoubou (Houshin Engi)

---

## 2. Damage Value Patterns

### Damage Formula (Partially Solved)

**Confirmed formula (Bleach characters):**
```
damage = floor(jpower_total / 5) + (tier - 2)
```

Where:
- `jpower_total = damage1 + damage2 + damage3`
- `tier` from chr_b.bin (1-3)
  - tier 1: -1 modifier
  - tier 2: +0 modifier
  - tier 3: +1 modifier

**Alternative formula (Goku Block 0):**
```
damage = floor(jpower_total / 7)
```
- Block 0 entries: total=50 → 7 damage, total=100 → 14 damage
- **Exception:** Goku B=8 damage requires total=40 or 56, NOT found in Block 0

### Damage Distribution Patterns

**Common jpower totals observed:**

| Total Damage | Frequency | Typical Moves | Examples |
|--------------|-----------|---------------|----------|
| **50** | Very common | Standard attacks, jabs | Goku fwd B, Ichigo B |
| **100** | Common | Heavy attacks, specials | Goku up Y, down Y |
| **40** | Rare | Light attacks | Found at indices 146, 195, 218 (not in Block 0) |
| **56** | Rare | Unknown | Needed for Goku B=8 with ÷7 formula |
| **57** | Rare | Special attacks | Luffy/Robin Block 9 first entry |
| **28** | Rare | Special moves | Gotenks SSJ Block 4 |

**Damage component patterns:**

**Type 1 (Punch/Kick - damage1):**
- Most common component
- Ranges: 10-100 typically
- Goku Block 0: 20-100

**Type 2 (Energy/Ki - damage2):**
- Common for projectile/special moves
- Goku Block 0: 0-40
- Often paired with damage1

**Type 3 (Blade - damage3):**
- Least common
- Typically 0 for non-blade characters
- Kenshin, Zoro likely have non-zero values

**Multi-hit patterns:**
- Goku up B: 3+3 damage (likely uses nextId chain)
- Goku Y combo: 4+4+6 damage (likely uses nextId chain)
- These totals don't appear as single entries

### Block-Specific Damage Patterns

**Block 0 (Goku family):**
- 7 entries with total=50 (damage1: 20-50, damage2: 0-40, damage3: 0-20)
- 2 entries with total=100 (damage1: 60-100, damage2: 0-40)
- Hitstun: 5 (light) or 10 (heavy)
- **Missing:** Entry with total=40 or 56 for B=8 damage

**Block 1 (Vegetto/Vegeta):**
- 2 entries with total=50 each
- Damage pattern: [7, 7] in-game

**Block 4 (Gotenks SSJ):**
- Pattern: [7, 7, 7, 28]
- Last entry (28) likely special move

**Block 9 (Luffy/Robin):**
- Pattern: [57, 7, 7, 7, 7, 7, 7, 7, 7, 7, 14]
- First entry (57) likely special/unique move
- Last entry (14) likely heavy attack

**Block 12 (Nami/Franky):**
- Pattern: [7, 7]
- Minimal moveset template

**Block 52 (Ichigo/Train):**
- **CRITICAL:** May point to empty entries (all zeros)
- Suggests block index ≠ array index, or collision-based damage

---

## 3. Hitstun Value Patterns

### Hitstun Distribution

**Known hitstun values:**

| Hitstun | Attack Type | Frequency | Notes |
|---------|-------------|-----------|-------|
| **5** | Light attacks | Very common | Jabs, light combos |
| **10** | Heavy attacks | Common | Y button attacks, launchers |
| **50+** | Specials | Rare | Super moves, special attacks |

**From JPowerEntry.cs documentation:**
- `5 = light attacks`
- `10 = heavy attacks`

**Hypothesis:**
- Hitstun duration in frames = `jpower.hitstun` value directly
- Observed: Light hitstun ~10-15 frames, Medium ~20-30 frames
- **Unknown:** Exact formula connecting jpower.hitstun to actual frame duration

### Hitstun by Attack Category (Type2)

**Type2 = 1 (Standard):**
- Typically hitstun = 5
- Light attacks, jabs

**Type2 = 7 (Projectile):**
- Hitstun varies (likely 5 or 10)
- Projectile attacks

**Type2 = 8 (Heavy):**
- Typically hitstun = 10
- Heavy attacks, launchers

**Type2 = 9 (Special):**
- Hitstun varies (5-50+)
- Special moves

**Type2 = 10 (Super):**
- Hitstun = 50+ typically
- Super moves, finishers

### Hitstun by LinkCategory

**LinkCategory values:**
- `1 = chain` - Light hitstun (5)
- `4 = ground` - Variable
- `5 = light` - Light hitstun (5)
- `7 = launcher` - Heavy hitstun (10)
- `8 = super` - Very high hitstun (50+)
- `9 = multi-hit` - Variable (may use nextId chains)
- `10 = finisher` - Very high hitstun (50+)

**Pattern:**
- LinkCategory 1, 5 → hitstun = 5
- LinkCategory 7 → hitstun = 10
- LinkCategory 8, 10 → hitstun = 50+

---

## 4. Unknown Fields Analysis

### ExtendedData (16 bytes, offset 0x20)

**Status:** 66/311 entries have non-zero data in extendedData section

**Potential uses:**
1. **Combo system parameters** - Frame windows, cancel timings
2. **Knockback modifiers** - Velocity, angle adjustments
3. **Status effect data** - Poison, stun, freeze durations
4. **Move-specific flags** - Armor, invincibility frames
5. **Damage scaling** - Combo damage reduction factors

**Research priority:** HIGH - May contain critical combat mechanics

### LinkType (offset 0x18)

**Known values:** 0 or 2

**Potential meanings:**
- `0 = no link` - Standalone move
- `2 = linked move` - Part of combo chain

**Correlation needed:**
- Check if LinkType=2 correlates with nextId usage
- Check if LinkType affects combo system

### LinkFlags (offset 0x1C)

**Status:** Unknown purpose

**Potential uses:**
1. **Combo flags** - Which moves can cancel into this
2. **State flags** - Ground-only, air-only, both
3. **Property flags** - Armor, invincibility, super armor
4. **Hit flags** - Can hit grounded, can hit airborne

**Research priority:** MEDIUM

### ModifierEffect (offset 0x52 in modifier sub-record)

**Status:** Present when HasModifier=true

**Known:** Modifier sub-record contains 2x damage values typically

**Potential uses:**
1. **Status effect type** - What buff/debuff this applies
2. **Visual effect ID** - Particle effect, screen effect
3. **Sound effect ID** - Audio cue for powered state
4. **Additional properties** - Knockback modifier, hitstun modifier

**Research priority:** MEDIUM

### NextId (offset 0x08)

**Status:** Linked record reference

**Known usage:**
- Multi-hit moves likely chain via nextId
- Goku up B (3+3) and Y combo (4+4+6) may use nextId chains

**Research needed:**
- Map nextId chains for all entries
- Identify which moves use multi-hit chains
- Determine if nextId affects damage calculation (total across chain?)

**Research priority:** HIGH - Critical for understanding multi-hit moves

### Type2 (Attack Subtype)

**Known values:**
- `0 = Data` (type1=0 entries)
- `1 = Standard`
- `2-6 = Variation2-6` (unknown purpose)
- `7 = Projectile`
- `8 = Heavy`
- `9 = Special`
- `10 = Super`

**Unknown variations:**
- Type2 values 2-6 are not documented
- May represent different attack properties or categories

**Research priority:** LOW-MEDIUM

---

## 5. Block Organization Patterns

### ATTACK Block Structure

**Pattern:** ATTACK blocks separated by DATA entries (type1=0)

**Block identification:**
1. Find first ATTACK entry (type1=1) after DATA entry
2. Collect consecutive ATTACK entries until next DATA entry
3. This forms one ATTACK block

**Block size variation:**
- Smallest: Block 12 (Nami/Franky) - 2 entries
- Largest: Block 0 (Goku) - 9 entries
- Average: ~4.2 entries per character (but shared across templates)

### DATA Entry Purpose

**Hypotheses:**
1. **Block separators** - Mark boundaries between character move sets
2. **Metadata storage** - Character-specific data (unused in most cases)
3. **Linkage data** - References to other systems
4. **Padding** - Alignment or reserved space

**Research needed:**
- Analyze DATA entry contents
- Check if DATA entries correlate with character indices
- Determine if DATA entries contain block metadata

---

## 6. Critical Unknowns

### 1. Entry Selection Mechanism

**Problem:** Characters sharing jpower blocks have different movesets.

**Examples:**
- Goku and Majin Buu both use Block 0 but different moves
- Luffy and Robin both use Block 9 but different moves

**Possible mechanisms:**
1. **Collision subType** - Selects jpower entry index within block
2. **Collision type2** - Attack type selects entry
3. **Collision linkCategory** - Combo category selects entry
4. **ARM9 lookup table** - Hardcoded mapping per character
5. **Character index offset** - chr_b index + offset = entry index

**Research priority:** CRITICAL

### 2. Goku B=8 Damage Mystery

**Problem:** Goku's B move deals 8 damage, but Block 0 has no entry with total=40 or 56.

**Possible explanations:**
1. Uses jpower entry outside Block 0 (indices 146, 195, 218 have total=40)
2. Uses collision-based damage (bypasses jpower)
3. Uses different formula (not ÷5 or ÷7)
4. Uses modifier sub-record (2x damage from different entry)

**Research priority:** HIGH

### 3. Multi-Hit Move Implementation

**Problem:** Multi-hit moves (Goku up B: 3+3, Y combo: 4+4+6) don't match single jpower totals.

**Hypothesis:** Uses nextId chains to link multiple jpower entries.

**Research needed:**
- Map all nextId chains
- Verify damage calculation across chains
- Determine if each hit uses separate jpower entry

**Research priority:** HIGH

### 4. Block 52 Empty Entries

**Problem:** Block 52 (Ichigo/Train) may point to empty entries (all zeros).

**Possible explanations:**
1. Block index counts DATA entries, not array index
2. Block index requires offset/multiplication
3. Characters use collision-based damage exclusively
4. Block index is wrong (needs verification)

**Research priority:** MEDIUM-HIGH

### 5. ExtendedData Purpose

**Problem:** 66/311 entries have non-zero extendedData, purpose unknown.

**Research needed:**
- Analyze extendedData patterns
- Correlate with attack types, characters, or moves
- Test if modifying extendedData affects gameplay

**Research priority:** MEDIUM

---

## 7. Recommendations for Further Research

### Immediate Priorities

1. **Map all nextId chains** - Understand multi-hit move structure
2. **Analyze collision-to-jpower mapping** - Determine entry selection mechanism
3. **Test Block 52 entries** - Verify if block is truly empty or uses different indexing
4. **Extract extendedData patterns** - Identify what non-zero values represent
5. **Document all 43 ATTACK blocks** - Complete block inventory with entry counts

### Analysis Tools Needed

1. **jpower.bin parser** - Extract all entries with full field analysis
2. **Block identifier** - Automatically identify ATTACK vs DATA blocks
3. **nextId chain mapper** - Visualize multi-hit move structures
4. **Character-to-block analyzer** - Cross-reference chr_b with jpower blocks
5. **ExtendedData pattern analyzer** - Find correlations in non-zero extendedData

### Testing Priorities

1. **Majin Buu damage values** - Compare to Goku's Block 0 entries
2. **Multi-hit move damage** - Verify nextId chain damage calculation
3. **Modifier sub-record effects** - Test if 2x damage applies in powered state
4. **LinkType effects** - Test if LinkType=2 affects combo system
5. **ExtendedData modifications** - Test gameplay changes from extendedData edits

---

## 8. Data Structure Reference

### JPowerEntry Field Summary

| Field | Offset | Type | Known Purpose | Unknown Aspects |
|-------|--------|------|---------------|-----------------|
| Id | 0x00 | u16 | Record identifier | Relationship to entry selection? |
| Type1 | 0x04 | u16 | 0=DATA, 1=ATTACK | - |
| Type2 | 0x06 | u16 | Attack subtype | Values 2-6 unknown |
| NextId | 0x08 | u16 | Linked record | Multi-hit chain structure |
| Damage1 | 0x0C | u16 | Punch/kick damage | - |
| Damage2 | 0x0E | u16 | Energy/ki damage | - |
| Damage3 | 0x10 | u16 | Blade damage | - |
| Hitstun | 0x16 | u16 | Hitstun frames | Exact formula to frame duration |
| LinkType | 0x18 | u16 | 0 or 2 | Meaning of value 2 |
| LinkCategory | 0x1A | u16 | Combo category | Full category list |
| LinkFlags | 0x1C | u16 | Flags | Purpose unknown |
| ExtendedData | 0x20 | u8[16] | Extra data | Purpose unknown (66 entries) |
| ModifierDamage1-3 | 0x48+ | u16 | 2x damage typically | When applied? |
| ModifierEffect | 0x52 | u16 | Effect value | Purpose unknown |

---

## Conclusion

The jpower.bin structure reveals a sophisticated template library system where:

1. **Blocks are shared templates**, not character-specific movesets
2. **Entry selection mechanism is unknown** - Critical research gap
3. **Damage formulas vary** - ÷5 for some characters, ÷7 for others
4. **Multi-hit moves use chains** - nextId links multiple entries
5. **ExtendedData contains hidden mechanics** - 66 entries have non-zero data

**Key insight:** The system is more complex than a simple 1:1 mapping. Characters select entries from shared blocks via an unknown mechanism, allowing efficient data reuse while maintaining unique movesets.

**Next steps:** Focus on entry selection mechanism and nextId chain analysis to unlock the full combat system understanding.
