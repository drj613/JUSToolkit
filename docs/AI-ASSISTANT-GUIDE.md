# AI Assistant Guide - Jump Ultimate Stars Research

This document serves as an entrypoint for AI assistants working on JUS reverse
engineering. Read this FIRST to avoid re-investigating solved problems.

---

## Quick Reference

### Key Files

| File | Location | Purpose |
|------|----------|---------|
| chr_b.bin | bin/ | 74 battle character entries (stats, tier, classId) |
| jpower.bin | bin/ | Damage/hitstun values indexed by classId |
| koma.bin | bin/ | 890 deck panel entries (type, passive index) |
| ARM9.bin | ftc/ | Game code + pointer tables |
| Collision files | ChrBin.aar/chr/col/ | Hitbox data per character |

### Key Documentation

- `docs/research/ARM9-Research-Guide.md` - Comprehensive reverse engineering guide
- `docs/research/Character-Mapping.md` - All 74 battle characters mapped to files
- `docs/characters/*.md` - Per-character deep dives (Goku, Ichigo most complete)

---

## SOLVED MYSTERIES - Do Not Re-Investigate

### 1. tr_b_01 Identity (SOLVED 2026-01-30)

**tr_b_01 = Tsuna Sawada & Reborn** from "Katekyo Hitman Reborn"

- The "tr" prefix = ka**T**ekyo hitman **R**eborn
- This is a LEGITIMATE battle character with 35 collision entries
- NOT Taizo, NOT Tar-chan, NOT cut content

**Taizo** (the actual unused character) is **dt_b_04** under Meta/Debug category
with only 1 collision entry ("can only move, no attacks").

### 2. Character File Prefixes (SOLVED)

All prefixes are documented in `docs/research/Character-Mapping.md`. Key ones:

| Prefix | Series | Notes |
|--------|--------|-------|
| db | Dragon Ball | 12 characters |
| bl | Bleach | 5 characters |
| op | One Piece | 8 characters |
| na | Naruto | 5 characters |
| tr | Katekyo Hitman Reborn | 1 character (Tsuna) |
| hs | Houshin Engi | 1 character (Taikoubou) |
| hk | Hokuto no Ken | 2 characters (Kenshiro, Raoh) |
| dt | Meta/Debug | 4 characters (Komaman x3, Taizo) |

### 3. Walk Speed Storage (PARTIALLY SOLVED)

**Location:** chr_b.bin `statC` field (offset 12, 2 bytes)

**System:** Threshold-based, NOT linear scaling

| statC Range | Walk Speed |
|-------------|------------|
| < ~100 | SLOW |
| >= ~100 | Normal/Fast |

**Key proof:** Lenalee (statC=153) and Killua (statC=300) have IDENTICAL walk speed.

### 4. Damage Formula (CONFIRMED for most characters)

```
damage = (jpower_total / 5) + (tier - 2)
```

- tier 1 = -1 damage modifier
- tier 2 = no modifier
- tier 3 = +1 damage modifier

**Verified for:** Ichigo, Bankai Ichigo

**Exception:** Goku's B move (8 damage) doesn't fit - likely different jpower
entry selection mechanism, NOT a different formula.

### 5. Passive Storage (DISCOVERED 2026-01-30)

**Location:** koma.bin `PassiveIndex` field (byte 7)

**Key fact:** Passives are **per-form**, not per-koma. All koma sizes of the same
form share the same passive ability.

- Battle komas: 47 unique passive indices (values 0-55)
- Support komas: Different range (values 92-192)

### 6. Koma Types (SOLVED)

koma.bin byte 6 (`KomaType`):
- 0 = Help koma (stat booster)
- 1 = Support koma (activatable assist)
- 2 = Battle koma (playable fighter)

### 7. chr_b Flags Field (PARTIALLY SOLVED)

- `flags = 0` means support character (no battle form)
- `flags > 0` means battle character
- Specific flag bits not fully mapped

---

## COMMON PITFALLS - Avoid These Assumptions

### 1. "chr_b index = collision table index"
**CORRECT.** These are 1:1 mapped. chr_b[39] uses collision file at table[39].

### 2. "jpower block index = chr_b index"
**WRONG.** jpower block = `classId & 0xFF`. Multiple characters share blocks.

### 3. "DamageFlags in collision = actual damage"
**WRONG.** DamageFlags is an index into jpower, not a damage value.

### 4. "statA/statB are gameplay stats"
**WRONG.** These are series-grouped values (likely sprite/text offsets).

### 5. "battleParams encodes weight/speed"
**WRONG.** Characters with identical battleParams have different weights/speeds.

### 6. "Characters sharing jpower block have same moveset"
**WRONG.** Majin Buu uses Block 0 (Goku's block) but has different moves.

### 7. "Toriko or Hikaru no Go are in this game"
**WRONG.** Neither series appears. Don't waste time searching for them.

---

## REMAINING UNKNOWNS

### High Priority

1. **jpower entry selection mechanism** - How does damageFlags=0 select an entry?
   Goku's collision has damageFlags=0 but damage=8 requires jpower total=40.

2. **Exact walk speed thresholds** - We know <100 is slow, but exact cutoffs
   between tiers are unknown. May be 2 or 3+ tiers.

3. **Passive ability table location** - We know PassiveIndex exists but haven't
   found the ARM9 table that defines what each index means.

4. **Dash type determination** - What makes Ichigo a "flash dasher" vs Goku's
   standard dash?

### Medium Priority

5. **Knockback formula** - Affected by HP, passives, possibly statC, but exact
   formula unknown.

6. **komaSize meaning** - chr_b values 2-6 don't match deck komas (4-8).

7. **Special damage scaling** - Koma 4→8 scaling is non-linear (+8/+7/+5/+5).

---

## USEFUL COMMANDS

### Export chr_b.bin to JSON
```bash
dotnet run --project src/JUS.CLI -- jus combat export-chr \
    --bin jus_files/ripped_jus_files/bin/chr_b.bin \
    --output /tmp/chr_b.json
```

### Export jpower.bin to JSON
```bash
dotnet run --project src/JUS.CLI -- jus combat export-jpower \
    --bin jus_files/ripped_jus_files/bin/jpower.bin \
    --output /tmp/jpower.json
```

### Check beads issues
```bash
bd ready      # Show ready-to-work tasks
bd list       # Show all issues
bd show <id>  # Show issue details
```

---

## ARM9 Key Offsets

| Offset | Contents |
|--------|----------|
| 0x0924B0 | Collision file pointer table (74 entries × 8 bytes) |
| 0x08D4A0 | chr_b → collision identity mapping |
| 0x09E780 | Koma name table |

---

## Session History

| Date | Key Discoveries |
|------|-----------------|
| 2026-01-29 | Damage formula confirmed (jpower/5 + tier-2), damageFlags = jpower index |
| 2026-01-30 | Walk speed = statC threshold, tr_b_01 = Tsuna, passives in koma.bin |

---

## Contact / Resources

- Project repo: This JUSToolkit repository
- Issue tracking: `.beads/` directory (use `bd` commands)
- Character list: `docs/full_character_list.md`
