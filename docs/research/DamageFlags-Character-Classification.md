# DamageFlags Character Classification

Tracking which characters use Direct vs Indirect jpower entry selection.

**Issue:** JUS-9lp.1.1

---

## Classification System

| System | Pattern | Example |
|--------|---------|---------|
| **Direct Reference** | damageFlags > 0 for most entries | Ichigo (19/20 entries) |
| **Indirect Lookup** | damageFlags = 0 for most entries | Goku (2/25 entries) |

---

## Classified Characters

### Direct Reference System (damageFlags = jpower index)

| Character | File | Entries with flags>0 | Total Entries | Ratio | Source |
|-----------|------|---------------------|---------------|-------|--------|
| Ichigo | bl_b_01 | 19 | 20 | 95% | Goku-Character-Map.md |
| Bankai Ichigo | bl_b_02 | ? | ? | ? | (needs verification) |

### Indirect Lookup System (damageFlags = 0, alternative lookup)

| Character | File | Entries with flags>0 | Total Entries | Ratio | Source |
|-----------|------|---------------------|---------------|-------|--------|
| Goku | db_b_01 | 2 | 25 | 8% | Goku-Character-Map.md |
| Goku SSJ | db_b_02 | ? | ? | ? | (likely same as base) |
| Majin Buu | db_b_12 | ? | ? | ? | (same block as Goku) |
| Luffy | op_b_01 | ? | 38 | ? | Luffy-Character-Map.md |
| Robin | op_b_07 | ? | 32 | ? | Robin-Character-Map.md |
| Franky | op_b_08 | ? | 21 | ? | Franky-Character-Map.md |
| Nami | op_b_04 | ? | 22 | ? | Nami-Character-Map.md |
| Naruto | na_b_01 | ? | 46 | ? | Naruto-Character-Map.md |
| Kyuubi Naruto | na_b_02 | ? | 30 | ? | Kyuubi-Naruto-Character-Map.md |

### Unclassified (need data)

All other 60+ characters need collision data extraction.

---

## Observed Patterns

### By Series (Hypothesis)

| Series | Likely System | Evidence |
|--------|---------------|----------|
| Dragon Ball | Indirect | Goku confirmed indirect |
| One Piece | Indirect | Luffy/Robin/Franky/Nami all B=8 (similar to Goku) |
| Naruto | Indirect | Naruto B=8 (similar to Goku) |
| Bleach | **Direct** | Ichigo confirmed direct |
| Others | Unknown | Need data |

**Key Question:** Is Bleach the only series using Direct, or are there others?

---

## Data Collection Needed

### Priority 1: Verify pattern by series
1. Extract collision data for one character from each series
2. Count damageFlags=0 vs damageFlags>0
3. Confirm/refute series-based hypothesis

### Priority 2: Full roster classification
1. Extract all 74 character collision files
2. Generate classification table
3. Look for correlation with jpower block, tier, or other factors

---

## Extraction Script

To extract collision data, use:

```bash
# Export collision files from ROM
dotnet run --project src/JUS.CLI -- jus combat export-collision <rom_path> <output_dir>

# Then analyze with Python script
python scripts/classify_damage_flags.py <collision_dir>
```

Script needed at: `scripts/classify_damage_flags.py`

---

## Notes

- Direct system: `damageFlags` IS the jpower array index
- Indirect system: Unknown lookup based on subType, hitTier, or ARM9 table
- Ichigo pattern allows easy damage prediction
- Goku pattern requires discovering the lookup mechanism

---

*Last updated: 2026-01-31*
