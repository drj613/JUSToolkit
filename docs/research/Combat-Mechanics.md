# Combat Mechanics Research

Documented gameplay mechanics for Jump Ultimate Stars, derived from in-game testing and data analysis.

---

## Damage System

### Damage Formula (Confirmed)

```
actual_damage = floor(jpower_totalDamage / 7 * nature_multiplier)
```

Where `jpower_totalDamage = damage1 + damage2 + damage3` from the jpower.bin entry.

### Nature Multipliers

| Matchup | Multiplier |
|---------|------------|
| Neutral | 1.0x |
| Advantage | 1.5x |
| Disadvantage | 1.0x (no penalty) |

The nature system is **bonus-only** - you gain advantage but never take extra damage from disadvantage.

### Verified Damage Values (Goku)

| Move | jpower Total | Neutral | Advantage (1.5x) |
|------|--------------|---------|------------------|
| B (jab) | ~56 | 8 | 12 |
| fwd B | ~50 | 7 | 10 |
| up B (2 hits) | ~42 | 3+3 | 4+5 |
| down B | ~50 | 7 | 10 |
| Y combo (3 hits) | ~100 | 4+4+6 | 6+6+9 |
| fwd Y (projectile x3) | ~105 | 5+5+5 | 7+8+7 |
| up Y | ~100 | 14 | 21 |
| down Y | ~100 | 14 | 21 |

### Damage Types

The game has three damage types that interact with character resistances:

| Type | jpower Field | Examples |
|------|--------------|----------|
| Punch/Kick (Blunt) | damage1 | Physical strikes, Goku's attacks |
| Energy/Ki | damage2 | Energy blasts, special beams |
| Blade | damage3 | Sword slashes, cutting attacks |

### hitProperties Override

The `hitProperties` field in collision data can override visual damage type:
- `hitProperties = 1` forces **blunt damage** regardless of weapon

**Example:** Kenshin uses a sword visually but deals punch/kick damage because his attacks have `hitProperties = 1`. This matches his lore (reverse-blade sword).

**Verification:**
- Kenshin B vs Naruto (no resistances): 7 damage
- Kenshin B vs Luffy (resists punch/kick, weak to blade): 5 damage
- If Kenshin dealt blade damage, Luffy would take MORE damage, not less

### Known Defensive Passives

| Passive Effect | Affects |
|----------------|---------|
| Decreased punch/kick damage | damage1 |
| Decreased blade damage | damage3 |
| Decreased lightning damage | Subtype of damage2? |
| Increased/decreased special damage | Heavy attacks |

**Note:** No observed passives for fire or ice damage types.

---

## Character Weight System

Characters have different weights affecting knockback physics.

### Reference Characters

| Character | Series | Weight Class |
|-----------|--------|--------------|
| Lenalee | D.Gray-man | Light |
| Raoh | Hokuto no Ken | Heavy |

### Technical Details

- `battleParams` bytes 8-10 in chr_b.bin likely contain weight values
- Lighter characters tend to have higher values in byte 8
- Knockback formula: `applied_knockback = base_knockback * weight_factor * hp_factor`
- HP factor likely based on remaining HP percentage

---

## Projectile System

Projectiles are defined in `shot/*.bin` files and referenced via `projectileId` in collision data.

### Projectile Categories

#### 1. True Projectiles
Travel across the screen independently.

| Character | Move | Description |
|-----------|------|-------------|
| Goku | fwd Y | Energy blasts (can fire up to 3) |
| Zoro | fwd Y | Ranged slash wave |
| Yusuke | fwd Y | Spirit Gun |
| Ichigo | fwd Y, up Y, air Y | Getsuga Tensho variants |
| Dio | fwd B | Knife throw |

#### 2. Extended Hitboxes
Large area attacks with minimal travel.

| Character | Move | Description |
|-----------|------|-------------|
| Goku | down B | Pushes air forward |
| Goku | down Y | Air push on both sides |
| Raoh | Y, up Y | Extended damage area around character |

#### 3. Summons
Separate entities that perform attacks.

| Character | Move | Description |
|-----------|------|-------------|
| Yugi | All except fwd B | Summons monsters to attack |
| Taikoubou | down B, Y, fwd Y, up Y | Y summon has its own hurtbox (can be attacked!) |
| Dio | down B, fwd Y, air B | Stand attacks for him |

**Note:** Taikoubou's Y summon is unique - it can receive attacks, unlike other summons.

#### 4. Persistent/Traps
Remain active after character switches out or is KO'd.

| Character | Move | Description |
|-----------|------|-------------|
| Yugi | fwd B | Trap persists after switch/KO |
| Dr. Mashirito | Y, fwd Y | Traps persist after switch/KO |
| Ryotsu | fwd B, Y | Traps persist after switch/KO |
| Franky | down B | Table persists if interrupted |

### Technical Details

- `projectileId` in collision: negative values reference shot definitions
- Shot file structure: 32 bytes per record
- Collision types: type4 = projectile, type5 = summon
- High `durationMult` values indicate trap/persistent behavior

---

## Buff/Powered State System

Some characters have invisible buff states that enhance certain moves. These buffs can transfer between characters on tag-out.

### Buff Triggers by Character

#### Ichigo (bl_b_01)
- **Trigger 1:** Continue tapping Y during blade spin until all spins complete
- **Trigger 2:** Complete taunt animation without interruption
- **Enhanced Moves:** up Y, fwd Y, air Y
- **Effects:** Larger hitbox, more damage, more hitstun, greater knockback

#### Yusuke (yh_b_01)
- **Trigger:** Hold taunt until animation changes (tapping briefly does NOT work)
- **Enhanced Moves:** fwd Y, air Y
- **Effects:** More damage, stronger knockback
- **Note:** fwd Y travels horizontal, air Y travels diagonal-down (same projectile, different trajectory)

#### Fuusuke (nk_b_01)
- **Trigger:** Taunt
- **Enhanced Moves:** Neutral Y (and possibly others)

#### Raoh (hk_b_02)
- **Trigger:** Use neutral Y
- **Enhanced Moves:** up Y, fwd Y
- **Effects:** More damage and range

#### Franky (op_b_08)
- **Trigger:** Taunt
- **Enhanced Moves:** fwd Y (different sizes/strengths)

### Buff Transfer Compatibility

Buffs can transfer between characters when switching, but NOT all buff types are compatible:

| From | To | Compatible? |
|------|-----|-------------|
| Yusuke | Ichigo | Yes |
| Ichigo | Yusuke | Yes |
| Fuusuke | Raoh | Yes |
| Raoh | Fuusuke | Yes |
| Yusuke/Ichigo | Fuusuke | No |
| Fuusuke/Raoh | Yusuke/Ichigo | No |

### Buff Groups

- **Group A:** Yusuke, Ichigo (energy/spirit type)
- **Group B:** Fuusuke, Raoh (physical enhancement type)
- Groups A and B are **NOT compatible**

### Buff Consumption Rules

- Using an enhanced move with an **incompatible** buff **consumes** the buff with no effect
- Using a **non-enhanced** move does NOT consume the buff

**Example:**
1. Buff as Fuusuke
2. Switch to Ichigo
3. Use neutral B (non-enhanced) - buff NOT consumed
4. Switch back to Fuusuke
5. Neutral Y is still buffed

**Example:**
1. Buff as Fuusuke
2. Switch to Ichigo
3. Use up Y (enhanced but incompatible) - buff IS consumed with no effect

### Technical Details

- `damageFlags = 64` (0x40) in collision data triggers buff state
- Modifier sub-records in jpower.bin (offset 0x40+) contain 2x damage values for buffed state
- Buff state likely stored as team-wide flag with type identifier

---

## Frame Data

### Universal Timings

| Action | Frames |
|--------|--------|
| Landing Lag | 16 |
| Dash | 15 |
| Jump | 19 |

### Frame Data Notes

- `frameStart` in collision data = when **hitbox activates**, not move startup
- In-game startup frames include animation wind-up before hitbox
- No consistent offset between frameStart and startup (varies per move)

---

## Collision Entry Patterns

### Highest Entry Counts

Characters with most complex collision data:

| Character | File | Entries | Notes |
|-----------|------|---------|-------|
| Kinnikuman | kn_b_01 | 60 | Wrestler with many grapple moves |
| Zoro | op_b_03 | 51 | Multi-hit sword combos |
| Naruto | na_b_01 | 46 | Shadow clone complexity |
| Fuusuke | nk_b_01 | 45 | |
| Seiya | ss_b_01 | 45 | |

### Form Variant Patterns

| Pattern | Example | Entry Counts |
|---------|---------|--------------|
| Same kit, same entries | Don Patch / Super Patch | 18 / 18 |
| Same animations, enhanced hitboxes | Bo-bobo / Shinsetsu | 24 / 33 |
| Completely different moveset | Ichigo / Bankai Ichigo | 20 / 26 |
