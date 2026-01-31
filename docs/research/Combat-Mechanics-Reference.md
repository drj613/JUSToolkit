# JUS Combat Mechanics Reference

Documentation of Jump Ultimate Stars combat mechanics as implemented in the original game.
Research-driven, with clear markers for unknowns and assumptions.

**Status:** Draft - actively being refined through research

---

## 1. Character States

### Grounded States

| State | Description | Can Act? | Transitions To |
|-------|-------------|----------|----------------|
| Idle | Standing neutral | Yes | Walk, Dash, Jump, Attack, Block |
| Walking | Moving left/right | Yes | Idle, Dash, Jump, Attack, Block |
| Crouching | Holding down | Yes | Idle, Attack, Block |
| Blocking | Holding down (guard) | Limited | Idle (release), Guardstun, Guardbreak |
| Attacking | In attack animation | No | Recovery, Hitstun (if hit) |
| Recovery | Post-attack cooldown | No | Idle |

### Airborne States

| State | Description | Can Act? | Transitions To |
|-------|-------------|----------|----------------|
| Jumping | Rising/falling | Yes | Attack, Air Dash, Ledge Grab |
| Air Attack | Attacking in air | No | Air Recovery, Hitstun |
| Air Dash | Dashing in air | No | Jumping |

### Hit States

| State | Vulnerable? | Duration | Triggered By | Visual |
|-------|-------------|----------|--------------|--------|
| Light Hitstun | Yes | Very short (~10-15f?) | Jabs, light attacks | Flinch animation |
| Medium Hitstun | Yes | Moderate (~20-30f?) | Launchers, heavy attacks | Airborne tumble |
| Surprise Hitstun | Yes | Short? | "Gag" attacks | Shocked expression |
| Heavy Hitstun (Spin) | **No** | Until lands or times out | Specific moves, damage cap? | Spinning in air |
| Knockdown | **No** | Variable | Ground spike, damage cap, landing in medium hitstun | Laying on ground |
| Wakeup | Varies | Fixed | End of knockdown | Getting up animation |

### Guardstun States

| State | Description | Duration |
|-------|-------------|----------|
| Guardstun | Blocking an attack | Based on attack |
| Guardbreak | Guard health depleted | Very long (punishable) |

---

## 2. Movement System

### Ground Movement

| Action | Input | Notes |
|--------|-------|-------|
| Walk | Hold direction | Speed varies by character (statC threshold system) |
| Dash | Double-tap direction | Type varies: Standard dash vs Flash dash |
| Crouch | Hold down | Used for blocking, some attacks |

#### Walk Speed Tiers

Based on chr_b.bin `statC` field:
- **Slow:** statC < ~100
- **Normal/Fast:** statC >= ~100

> **UNKNOWN:** Exact threshold values. May be 2+ tiers.

#### Dash Types

- **Standard Dash:** Visible forward movement, can be reacted to
- **Flash Dash:** Near-instant teleport, harder to react to

> **UNKNOWN:** What determines dash type per character.

### Air Movement

| Action | Input | Notes |
|--------|-------|-------|
| Jump | Press up/jump button | Height varies by character? |
| Double Jump | Jump again in air | Standard for all? |
| Triple Jump | Jump third time | Requires helper passive |
| Wall Jump | Jump while touching wall | Requires helper passive |
| Air Dash | Double-tap direction in air | Requires helper passive OR innate |
| Fast Fall | Hold down while falling | TBD if exists |

### Ledge Mechanics

| Action | Input | Result |
|--------|-------|--------|
| Ledge Grab | Automatic when falling near ledge | Hang from ledge |
| Ledge Stand | Press up | Stand at edge |
| Ledge Roll | Press forward | Roll onto stage |

---

## 3. Attack System

### Input Layout

| Input | Grounded | Airborne |
|-------|----------|----------|
| Y | Light attack | Air light |
| B | Heavy attack | Air heavy |
| X | Special A | Air special |
| Up + X | Special B | - |
| Down + Y | **Guard Break** (universal) | - |
| Down + B | **Force Switch** (universal) | Spike attack |

### Attack Properties

Each attack has:
- **Startup frames:** Before hitbox is active
- **Active frames:** Hitbox is out
- **Recovery frames:** After hitbox, before can act
- **Damage:** Base value (modified by tier, nature)
- **Hitstun type:** Light, Medium, Heavy, Knockdown
- **Knockback:** Direction and magnitude

### Move Priority System

Attacks and projectiles have implicit priority tiers:
- Higher priority moves beat/cancel lower priority
- Same priority = both lose (clash)

> **UNKNOWN:** Exact priority values, how many tiers.

---

## 4. Damage Calculation (JSoul)

> **Note:** Health in JUS is called "JSoul"

### Core Formula (TENTATIVE - needs more testing)

```
jsoul_damage = (jpower_total / 5) + (tier_modifier)
```

Where:
- `jpower_total` = Sum of damage + hitstun values from jpower.bin
- `tier_modifier` = tier - 2 (so tier 1 = -1, tier 2 = 0, tier 3 = +1)

**Testing Status:**
| Character | Tested Moves | Notes |
|-----------|--------------|-------|
| Ichigo | Full kit (minus specials) | Most thoroughly tested |
| Goku | Extensive | Second most tested |
| Caramelman | Full kit (minus specials) | In-battle damage numbers |
| Buu | Full kit (minus specials) | In-battle damage numbers |
| Various | B move only | Handful of spot checks |

**UNKNOWN:** Whether divisor varies by character/series, rounding behavior

### Nature Advantage

When attacker's nature beats defender's nature: **1.5x damage**

| Attacker | Beats |
|----------|-------|
| Power (Red) | Knowledge (Green) |
| Knowledge (Green) | Laughter (Yellow) |
| Laughter (Yellow) | Power (Red) |

### Damage Cap / Combo Breaker

Hidden "damage since last knockdown" gauge:
- Accumulates damage taken while not in knockdown/heavy hitstun
- When threshold reached → forced knockdown state
- Prevents infinite combos
- No visual indicator

> **UNKNOWN:** Exact threshold value.

---

## 5. Guard System

### Basic Guard

- **Input:** Hold down on D-pad
- **Effect:** Block incoming attacks, no chip damage
- **Guard Health:** Separate pool that depletes when blocking

### Guard Health

- Depletes when blocking attacks
- Visual indicator flashes red when low
- Regenerates when not blocking (rate TBD)

> **UNKNOWN:** Exact guard health values, regen rate.

### Guard Break

Two ways to break guard:
1. **Deplete guard health:** Any attack that reduces it to 0
2. **Guard break attack:** Down + Y (universal), some specials

**Result:** Extended vulnerable animation (very punishable)

### Tap-Block Behavior

Rapidly tapping guard reportedly refreshes guard health, creating an exploitable defensive technique.

> **UNKNOWN:** Exact mechanics of tap-block refresh.

### Auto-Guard (Helper Passive)

Some helper komas provide auto-guard ability:
- Automatically blocks incoming attacks
- Costs SP per block
- See `docs/research/Passives-Reference.md` for which helpers provide this

---

## 6. Support System

### Support Calls

- Tap support character on touch screen
- Support appears, does their action, leaves
- Has cooldown between uses

### Support Properties

- **Invulnerability:** On entry? For how long?
- **Cooldown:** Time before can call again
- **SP Cost:** Some may cost SP?

> **UNKNOWN:** Most support mechanics need research.

---

## 7. SP Gauge System

### SP Basics

- Shared across deck (not per-character)
- Maximum bars: 3 base + helper bonuses (up to ~5?)
- Used for: Special moves (1 bar), Dream Combos, auto-guard

### SP Gain

Multiple ways to gain SP:
- Landing attacks
- Taking damage
- Breaking item boxes
- Blocking at last moment (parry?)
- Character-specific passives

### Dream Combo

1. Tap current character
2. Tap 2nd character → they do a quick attack
3. Tap 3rd character → they do a quick attack
4. Tap back to 1st → they do powered-up special

- Each hit in sequence is free
- Final special costs 1 SP but deals bonus damage
- Bonus scales with number of characters (2 < 3 < 4)

---

## 8. Win Conditions

### Game Modes

JUS has three game modes:
- **Survival:** Last player with living characters wins
- **Point:** Score-based (TBD)
- **Star:** Objective-based (TBD)

### Survival Mode

- Each player has a deck of battle characters
- KO = that character is eliminated from deck
- Last player with living characters wins

### KO Mechanics

- HP reaches 0 → KO
- Character removed from deck
- If more characters remain: switch to next
- If no characters remain: lose

---

## 9. Passives System

### Battle Character Passives (Innate)

- Every battle character form has innate passive abilities
- Stored in koma.bin PassiveIndex field
- Same passive for all koma sizes of that form

**Categories:**
- SP gain conditions (attacking, blocking, low health, KOs, etc.)
- Damage reduction (vs punches, specials, blades)
- Status immunities
- Movement abilities (air dash, wall jump, triple jump)
- Health regen
- Unique abilities (see invisible, solid stance)

### Helper Koma Passives

- Helper komas grant abilities to adjacent characters
- Directional: must point at recipient
- Exception: "Increase Max SP" is deck-wide

**Categories:** Similar to battle passives plus:
- Increase max HP
- Increase guard strength
- Auto-guard (uses SP)
- Solid stance on platforms

See `docs/research/Passives-Reference.md` for complete list.

---

## 10. Open Questions

### High Priority

1. **jpower entry selection:** How does damageFlags=0 select a jpower entry?
2. **Walk speed thresholds:** Exact statC cutoffs
3. **Dash type determination:** What makes flash dash vs standard?
4. **Support mechanics:** Cooldowns, invuln frames, SP costs

### Medium Priority

5. **Weight/knockback formula:** How is knockback calculated?
6. **Damage cap threshold:** Exact value for combo breaker
7. **Priority system:** How many tiers? Values per move?
8. **Surprise hitstun:** Which moves trigger it?
9. **Guard health values:** Base values, regen rate, tap-block mechanics

### Low Priority (Nice to Have)

10. **Exact passive ARM9 table:** Binary mapping of PassiveIndex
11. **Frame data:** Startup/active/recovery for all moves
12. **Hitbox data:** Exact collision boxes per move
13. **Point/Star mode rules:** Complete documentation

---

## Changelog

| Date | Changes |
|------|---------|
| 2026-01-30 | Initial draft with all known mechanics |
| 2026-01-30 | Refocused as JUS reference doc (removed design decisions) |
