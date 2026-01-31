# Combat Engine Design Document

**Purpose:** Define the combat mechanics of Jump Ultimate Stars accurately
enough to recreate them in a new fighting game engine.

**Status:** Draft - Actively refining through research

---

## Design Philosophy

JUS is a platform fighter with:

- 2D movement with platforming elements
- Tag-team system with deck building
- Rock-paper-scissors type advantage (Nature system)
- Accessible inputs with depth in positioning and meter management

---

## Screen Layout (NDS)

The original game runs on Nintendo DS with two screens:

| Screen           | Purpose                | Engine Equivalent    |
| ---------------- | ---------------------- | -------------------- |
| Top (256×192)    | Battle viewport        | Main game view       |
| Bottom (256×192) | Player deck / touch UI | HUD / touch controls |

**Key points for engine recreation:**

- **No split-screen**: Each player has their own device with full viewport
- **Local multiplayer**: Two separate NDS devices, independent cameras
- **Camera per player**: Each player's camera follows their character
- **Off-screen indicators**: Arrows point to opponents outside viewport

The bottom screen deck UI is specific to NDS touch input but the concept
(quick-access to supports and tag-outs) could translate to button UI. The game
also includes the ability to register L and R as hotkeys

---

## 1. Movement System

### Ground Movement

| Action | Behavior                       | Parameters Needed                             |
| ------ | ------------------------------ | --------------------------------------------- |
| Walk   | Constant velocity in direction | `walk_speed` per character                    |
| Dash   | Quick forward movement         | `dash_type`, `dash_distance`, `dash_duration` |
| Crouch | Enter crouch state             | `crouch_transition_frames`                    |

#### Walk Speed Implementation

**KNOWN:** Walk speed uses a threshold system based on `statC` value:

```
if statC < SLOW_THRESHOLD:
    walk_speed = SLOW_SPEED
else:
    walk_speed = NORMAL_SPEED
```

**UNKNOWN:**

- Exact `SLOW_THRESHOLD` value (estimated ~95-100)
- Exact `SLOW_SPEED` and `NORMAL_SPEED` values (pixels/frame)
- Whether there are more than 2 tiers

**Reference characters:**

- Nami: Fast (statC high)
- Goku: Normal (statC=161)
- Franky: Slow (statC low)

#### Dash Types

Two dash behaviors exist:

| Type          | Visual                           | Characters                              |
| ------------- | -------------------------------- | --------------------------------------- |
| Standard Dash | Forward movement, visible travel | Most characters                         |
| Flash Dash    | Near-instant teleport            | Some characters (determination unknown) |

**UNKNOWN:** What determines dash type per character.

### Air Movement

| Action      | Behavior                      | Parameters                            |
| ----------- | ----------------------------- | ------------------------------------- |
| Jump        | Upward velocity with gravity  | `jump_velocity`, `gravity`            |
| Double Jump | Second jump in air            | Same params, resets vertical velocity |
| Triple Jump | Third jump (passive required) | Helper passive grants this            |
| Air Dash    | Horizontal dash in air        | Passive required OR innate            |
| Fast Fall   | Increased fall speed          | Hold down (if exists)                 |

**KNOWN from observation:**

- All characters share same jump height and gravity
- Fall speed appears universal
- Air control (horizontal velocity while airborne) exists

**UNKNOWN:**

- Exact `jump_velocity` value
- Exact `gravity` value
- Air control strength

### Ledge Mechanics

| Action      | Behavior                               |
| ----------- | -------------------------------------- |
| Ledge Grab  | Automatic when falling near ledge edge |
| Ledge Stand | Press up to stand at edge              |
| Ledge Roll  | Press forward to roll onto stage       |

---

## 2. Hit States & Hitstun

### State Categories

| State                | Vulnerable? | Can Act? | Visual           | Transitions To        |
| -------------------- | ----------- | -------- | ---------------- | --------------------- |
| Light Hitstun        | Yes         | No       | Flinch animation | Idle (after duration) |
| Medium Hitstun       | Yes         | No       | Airborne tumble  | Knockdown on land     |
| Heavy Hitstun (Spin) | **No**      | No       | Spinning in air  | Knockdown on land     |
| Knockdown            | **No**      | No       | On ground        | Wakeup                |
| Wakeup               | Invuln?     | No       | Getting up       | Idle                  |

### Hitstun Duration Formula

**KNOWN from jpower.bin:**

- Light attacks have `hitstun = 5`
- Heavy attacks have `hitstun = 10`
- Some specials have `hitstun = 50+`

**HYPOTHESIS:** Hitstun duration in frames = `jpower.hitstun` value directly

**OBSERVED (approximate):**

- Light hitstun: ~10-15 frames
- Medium hitstun: ~20-30 frames

**UNKNOWN:**

- Exact formula connecting jpower.hitstun to actual frame duration
- Whether hitstun scales with damage or is fixed per move
- Hitstun decay (if combos reduce hitstun over time)

### Damage Cap / Combo Breaker

**KNOWN:** A hidden "rage" or "damage cap" system exists:

- Tracks cumulative damage since last knockdown
- When threshold reached → forced knockdown state
- Prevents infinite combos

**UNKNOWN:**

- Exact damage threshold value
- Whether it's damage-based or hit-count-based
- Reset conditions

---

## 3. Knockback & Velocity

### Knockback Formula (CRITICAL UNKNOWN)

When a character is hit, knockback velocity is applied based on:

```
knockback_velocity = f(
    attack_knockback,    // From collision/jpower data
    defender_weight,     // Character weight class
    defender_hp_ratio,   // Lower HP = more knockback
    defender_passives    // e.g., "hard to knock back"
)
```

**KNOWN:**

- HP affects knockback (lower HP = more displacement)
- Weight classes exist (Light, Normal, Heavy)
- Some passives reduce knockback (Edajima's "Principal")

**UNKNOWN:**

- Exact formula
- Weight values per character
- Where weight is stored (NOT in chr_b.bin)
- HP scaling factor

### Weight Classes

| Class  | Example Characters    | Behavior                |
| ------ | --------------------- | ----------------------- |
| Light  | Lenalee, Nami         | High knockback received |
| Normal | Goku, most characters | Standard knockback      |
| Heavy  | Raoh, Franky, Edajima | Low knockback received  |

**CRITICAL:** Franky and Nami have **identical** chr_b.bin data but **opposite**
weights. This proves weight is stored elsewhere (ARM9 hardcoded? Overlay
files?).

### Velocity Components

Characters need tracking for:

- `position_x`, `position_y` - Screen position
- `velocity_x`, `velocity_y` - Current velocity
- `hitstun_velocity_x`, `hitstun_velocity_y` - Applied knockback (decays?)

**UNKNOWN:** Whether knockback velocity decays over time or is constant until
landing.

---

## 4. Damage System

### Damage Formula (CONFIRMED)

```
base_damage = floor(jpower.damage1 / 5)
tier_modifier = character_tier - 2
final_damage = floor((base_damage + tier_modifier) * nature_multiplier)
```

Where:

- `damage1` = First damage component from jpower entry (NOT total!)
- `divisor` = 5 (confirmed across 12+ characters)
- `tier_modifier` = character_tier - 2 (-1, 0, or +1)
- `nature_multiplier` = 1.0 (neutral) or 1.5 (advantage)

### Nature Advantage

```
if attacker_nature beats defender_nature:
    damage *= 1.5
```

| Attacker          | Beats             |
| ----------------- | ----------------- |
| Power (Red)       | Knowledge (Green) |
| Knowledge (Green) | Laughter (Yellow) |
| Laughter (Yellow) | Power (Red)       |

**NOTE:** No penalty for disadvantage - neutral damage only.

### Damage Types

Three damage types interact with defensive passives:

| Type   | jpower Field | Resisted By                   |
| ------ | ------------ | ----------------------------- |
| Blunt  | damage1      | "Decreased punch/kick damage" |
| Energy | damage2      | (No known passive)            |
| Blade  | damage3      | "Decreased blade damage"      |

---

## 5. Guard System

### Guard Mechanics

| Mechanic     | Behavior                                     |
| ------------ | -------------------------------------------- |
| Block        | Hold down to block, negates damage           |
| Guard Health | Depletes when blocking, regenerates when not |
| Guard Break  | Guard health depleted OR guard break attack  |
| Guardstun    | Brief stun while blocking an attack          |

**UNKNOWN:**

- Guard health pool value
- Guard health regeneration rate
- Guardstun duration formula
- Tap-block exploit mechanics

---

## 6. SP (Special) System

### SP Basics

- Shared across entire deck (not per-character)
- Base max: 3 bars (helpers can increase to ~5)
- Used for: Special moves, Dream Combos, auto-guard

### SP Gain Sources

- Landing attacks
- Taking damage
- Breaking item boxes
- Character passives (e.g., "SP gain on KO")

**UNKNOWN:** Exact SP gain values per source.

---

## 7. Implementation Priorities

### Phase 1: Core Movement (Required for Prototype)

1. Walk speed tiers - Test exact threshold
2. Jump/gravity values - Measure from gameplay
3. Dash mechanics - Standard vs Flash determination

### Phase 2: Combat Core

4. **Hitstun formula** - Map jpower.hitstun to actual duration
5. **Knockback formula** - Derive weight and HP factors
6. Damage formula - Already confirmed, implement

### Phase 3: Advanced Systems

7. Guard system - Pool, regen, guardstun
8. SP system - Gain rates, costs
9. Dream Combo - Multi-character special

---

## 8. Research Methods

### For Hitstun/Knockback (Current Focus)

**Approach 1: Frame Analysis**

- Record gameplay at known FPS
- Count hitstun frames for different attacks
- Correlate with jpower.hitstun values

**Approach 2: Memory Analysis (GDB)**

- Snapshot character state before/after hit
- Find velocity and hitstun timer fields
- Derive formula from observed values

**Approach 3: Comparative Testing**

- Same attack on different weight characters
- Same attack at different HP levels
- Document velocity/displacement differences

### Reference Tests Needed

| Test                        | Purpose                 |
| --------------------------- | ----------------------- |
| Goku B vs Lenalee (full HP) | Baseline knockback      |
| Goku B vs Raoh (full HP)    | Heavy weight comparison |
| Goku B vs Lenalee (low HP)  | HP modifier             |
| Goku Y vs Lenalee (full HP) | Heavy attack comparison |

---

## Changelog

| Date       | Changes                                              |
| ---------- | ---------------------------------------------------- |
| 2026-01-31 | Initial design document focused on engine recreation |
