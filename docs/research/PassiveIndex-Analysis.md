# Koma.bin PassiveIndex Analysis

## Overview

- **Total komas:** 890
- **Battle komas:** 312
- **Unique PassiveIndex values (battle):** 47 (range 0-55)

## Series Distribution

Battle komas are organized by `nameIdx` (series) and `nameNum` (character/form within series).

| nameIdx | Battle Komas | Unique PassiveIndices |
|---------|--------------|----------------------|
| 1 | 17 | 16 |
| 2 | 4 | 4 |
| 3 | 7 | 7 |
| 4 | 10 | 10 |
| 5 | 5 | 4 |
| 6 | 13 | 11 |
| 7 | 10 | 10 |
| 8 | 15 | 14 |
| 9 | 3 | 3 |
| 10 | 10 | 10 |
| 11 | 4 | 4 |
| 12 | 8 | 8 |
| 13 | 4 | 4 |
| 14 | 10 | 10 |
| 15 | 7 | 7 |
| 16 | 7 | 7 |
| 17 | 3 | 3 |
| 18 | 9 | 9 |
| 19 | 9 | 9 |
| 20 | 5 | 4 |
| 21 | 7 | 6 |
| 22 | 3 | 3 |
| 23 | 13 | 11 |
| 24 | 9 | 7 |
| 25 | 3 | 3 |
| 26 | 7 | 7 |
| 27 | 7 | 5 |
| 28 | 4 | 4 |
| 29 | 5 | 5 |
| 30 | 17 | 12 |
| 31 | 4 | 4 |
| 32 | 7 | 7 |
| 33 | 12 | 10 |
| 34 | 4 | 4 |
| 35 | 3 | 2 |
| 36 | 7 | 7 |
| 37 | 5 | 5 |
| 38 | 6 | 6 |
| 39 | 7 | 7 |
| 40 | 5 | 4 |
| 41 | 10 | 9 |
| 42 | 7 | 5 |


## PassiveIndex → Effect Mapping (Partial)

Based on cross-referencing with GameFAQs guide data, here's what we know:

### Confirmed Mappings
(Need to match specific characters to their koma entries to confirm)

### Passive Categories Found in Battle Characters

**SP Gain:**
- Gain SP when attacking/blocking
- Gain SP when KOing
- Gain SP when health is low
- Gain SP from items/chests
- Gain SP when guarding
- SP regen when idle/not switching
- Gain SP from opposing nature attacks

**Damage/Defense:**
- Less damage from punches/kicks
- Less damage from specials
- Less damage from swords
- More damage from specific elements (fire, lightning)
- Attack power increases when health is low

**Status Immunities:**
- Immune to: Shock, Burn, Freeze, Poison, Confusion, Paralysis, Blindness, Judgment

**Health:**
- Gradual health regen
- More/less health from food
- Max health increase on KO return

**Movement:**
- Can air-dash
- Can wall-jump
- Can triple-jump
- Solid stance (hard to move when attacked)
- Cannot be moved when guarding

**Unique:**
- Can see invisible characters
- Auto-guard (at SP cost)
- SP gauge decreases passively

## Next Steps

1. Match koma nameIdx to series names (likely matches deck order)
2. Match specific character passives to PassiveIndex values
3. Find the ARM9 table that defines PassiveIndex → effect
