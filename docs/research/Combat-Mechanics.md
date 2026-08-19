# Combat Mechanics Research

> ## ⚠️ THE BANNER THAT USED TO BE HERE WAS WRONG — corrected 2026-08-19
>
> This document asserts a **1.5× nature multiplier on advantage** under the words
> "CONFIRMED 2026-01-30". From 2026-08-19 until later the same day, a banner here called
> that **wrong**. The banner was the error, not the claim.
>
> The two nature factor tables the damage routine reads, at `0x0209FEF4` and `0x0209FF14`,
> contain `0x0180` — exactly 1.5 in 8.8 — and the instructions turn a base of 8 into 12.000
> [`jus-nature-is-read-in-damage-path-hbt`]. What the August measurement actually showed is
> narrower: poking the byte *it* poked, mid-battle, changed nothing. The path reads a 2-bit
> field on a per-scratch copy, and has a bypass that skips the tables entirely, so a null
> there had three innocent explanations. [`jus-nature-does-not-affect-damage-0c6`] is
> `state:tainted`.
>
> One correction to the number as written below, though: nature and the resistance gates
> land in the **same accumulator** and are **additive**. Advantage plus one resist gate is
> 1.25×, not 1.5 × 0.75.
>
> The damage reduction described elsewhere in this file is also **×0.75 per gate, not a
> flat term** — claim [`jus-reduction-is-quarter-multiplier-xk1`].
>
> The rest of this document has not been re-audited against the current record. Treat
> any bare "CONFIRMED" in it as unverified until it carries a bead id.


Documented gameplay mechanics for Jump Ultimate Stars, derived from in-game testing and data analysis.

---

## Damage System

### Damage Formula (CONFIRMED 2026-01-30)

`damage = floor(jpower.damage1 / 5) + (tier - 2)`, times 1.5x nature
multiplier on advantage only (bonus-only system; floor after multiplying).
Uses `damage1` (first component) only — NOT the d1+d2+d3 total.

**Canonical reference (full derivation + verified character table):**
[Research-Status.md](Research-Status.md). Per-move Goku verification:
`docs/characters/Goku-Character-Map.md`.

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

- Weight is NOT in chr_b.bin battleParams (proven via Nami/Franky identical
  params) - storage location unknown (JUS-cb0.1)
- Knockback formula hypothesis: `applied_knockback = base_knockback * weight_factor * hp_factor`
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
  — **REFUTED as a per-character shot index (2026-08-14).** Tested across all 2837 collision records
  and 184 shot files: only 5/211 (2.4%) negative values fall inside the owning character's shot
  record count, 31 characters carry negative values while owning no shot file, and 95 of 184
  characters with a shot file have no negative value anywhere. The negatives form a contiguous
  −18..−34 band with nothing between −1 and −17. See
  `findings/shot-data-and-projectileid-refuted.md`.
  **What it is instead (2026-08-14, iteration 39):** a per-character *selector*, not an index of any
  kind. 92 of the 120 characters that use a negative value use exactly **one** distinct value across
  their whole file, and 194 of 211 negatives (92%) sit on `CollisionType` 4 (projectile) or 5
  (summon) — so the field is genuinely projectile machinery, just not a pointer. The "global 17-entry
  table" successor hypothesis is itself **REFUTED**: no file in any of the four `chr/`
  subdirectories has 17 records at any of six strides. Current PLAUSIBLE reading is a hardcoded
  spawn-behavior selector dispatched by a code switch. See
  `findings/projectileid-is-a-selector-not-an-index.md`.
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
