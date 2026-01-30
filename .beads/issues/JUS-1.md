---
id: JUS-1
title: Validate combat data against gameplay
type: task
status: closed
priority: 2
created: 2026-01-29
closed: 2026-01-29
---

# Validate combat data against gameplay

Compare extracted damage/frame values from jpower.bin and collision files to actual in-game behavior to understand the damage formula.

## Resolution

**Damage formula confirmed:**
```
actual_damage = floor(jpower_totalDamage / 7 * nature_multiplier)
```

**Nature Multipliers:**
- Neutral: 1.0x
- Advantage: 1.5x
- No disadvantage penalty (bonus-only system)

**Key findings:**
- jpower damage values (30-200) are divided by 7 to get actual HP damage
- Collision `damageFlags` field is NOT raw damage - likely a hit effect type
- Multi-hit moves split totalDamage across hits, each floored individually

## Research Steps

1. ✅ **Test in-game with known attacks** - Tested Goku neutral and advantage damage
2. ⏭️ **Look for damage formula in ARM9 binary** - Not needed, formula derived empirically
3. ⏭️ **Cross-reference collision hitbox counts** - Partially done

## Answered Questions

- ✅ Are jpower "damage" values (30-200) scaled? **Yes, divide by 7**
- ✅ Is the collision `damageFlags` field (0-63) the actual per-hit damage? **No, it's a modifier/effect type**
- ❓ What does the "knockback" field really represent? **Still unknown**
- ❓ How do defense stats factor into the formula? **Not tested yet**

## Files to Analyze

- `bin/jpower.bin` - 311 move definitions with damage1/damage2/damage3 fields
- `ChrBin.aar/chr/col/*.bin` - Per-character hitbox data with damageFlags/knockback
- `bin/chr_b.bin` - Character stats that may include defense values

## Notes

Exported JSON files are in `/tmp/jus_combat_export/` for reference.
Documentation updated in `docs/Combat-Specification.md`.
