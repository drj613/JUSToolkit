# Multi-Hitbox Mechanics

How Jump Ultimate Stars implements variable damage and complex attack patterns.

**Status:** CONFIRMED via in-game testing (2026-02-02)

---

## Core Concept: Multiple Collision Entries Per Move

A single move can have **multiple collision entries** in the character's
collision file. Each entry defines a separate hitbox with its own:

- Position (`offsetX`, `offsetY`)
- Size (`width`, `height`)
- Damage reference (`damageFlags` → jpower entry)
- Timing (`frameStart`, `durationMult`)
- Properties (`knockback`, `hitTier`)

This allows the game to create complex attack patterns without special-case
code.

---

## Pattern Types

### 1. Zone Damage (Different damage by distance)

**Example:** Caramelman fwd Y (mouth beam)

- Close range: 3 damage per tick
- Far range: 2 damage per tick

**Implementation:**

```
Entry A: offsetX=small, width=small, damageFlags→d1=10 → 3 damage
Entry B: offsetX=large, width=large, damageFlags→d1=5  → 2 damage
```

Two separate hitbox entries with different positions. The close hitbox has
higher damage. Both are active simultaneously during the beam attack.

---

### 2. Repeating + Finisher (Variable hit count)

**Example:** Caramelman Y (drill tank)

- Press Y 1x: 4 hits × 2 damage + 1 hit × 9 damage = 17 total
- Press Y 4x: 8 hits × 2 damage + 1 hit × 9 damage = 25 total
- Press Y 8x: 12 hits × 2 damage + 1 hit × 9 damage = 33 total

**Implementation:**

```
Entry A: type=repeating tick, damageFlags→d1=5  → 2 damage (applies multiple times)
Entry B: type=finisher,       damageFlags→d1=40 → 9 damage (applies once at end)
```

The animation duration (controlled by input) determines how many times the tick
hitbox registers. The finisher always applies once at the end.

---

### 3. Multi-Part Hitbox (Different hitboxes on same frame)

**Example:** Caramelman air B (spiked ball wrap)

- Spiked ball: 15 damage
- Body contact: 5 damage per touch

**Implementation:**

```
Entry A: offsetX=forward, damageFlags→d1=70 → 15 damage (spiked ball)
Entry B: offsetX=body,    damageFlags→d1=20 → 5 damage  (body contact)
```

Two hitboxes active simultaneously on different parts of the character model.
Opponents can be hit by either or both depending on positioning.

---

### 4. Multi-Hit Combos (Sequential hits)

**Example:** Buu Y (punch, punch, kick)

- Hit 1: 3 damage
- Hit 2: 3 damage
- Hit 3: 12 damage

**Implementation:**

```
Entry 1: frameStart=X,  damageFlags→d1=15 → 3 damage
Entry 2: frameStart=Y,  damageFlags→d1=15 → 3 damage
Entry 3: frameStart=Z,  damageFlags→d1=60 → 12 damage
```

Each hit is a separate collision entry with different `frameStart` values,
triggering at different points in the animation.

---

### 5. Projectile Multi-Hit (Continuous damage)

**Example:** Buu up Y (detached fist throw)

- Initial: 3 damage
- Travel: 1 damage × 7 hits
- Final: 8 damage

**Implementation:** Likely uses `nextId` chaining in jpower entries:

```
jpower[A]: damage1=15, nextId=B  → 3 damage, links to B
jpower[B]: damage1=5,  nextId=C  → 1 damage, links to C (repeated)
jpower[C]: damage1=40, nextId=0  → 8 damage, end of chain
```

The `nextId` field in jpower.bin creates damage chains for complex projectiles.

---

## Collision Entry Structure Reference

```c
struct CollisionEntry {  // 20 bytes
    u8  collisionType;   // 2=attack, 3=extended, 4=projectile, 5=summon
    u8  subType;         // 1=jab, 2=combo, 5=launcher, 6=aerial, 7=heavy
    u8  extFlags;        // Extended flags
    s8  projectileId;    // Negative=spawn entity, 0=melee
    u8  frameStart;      // Frame when hitbox activates
    u8  durationMult;    // Duration multiplier
    u8  reserved0;
    u8  hitModifier;     // Hit property modifier
    s8  offsetX;         // Hitbox X position (signed)
    u8  offsetY;         // Hitbox Y position
    u8  positionFlags;   // 0x00=standard, 0x02=alternate, 0x20=aerial
    u8  reserved1;
    s8  width;           // Hitbox width (signed)
    s8  height;          // Hitbox height (signed)
    u8  damageFlags;     // Links to jpower entry (0xFF=terminator)
    u8  knockback;       // Knockback force (0xFF=terminator)
    u8  hitTier;         // 0=passive, 1=light, 2=medium, 3=heavy
    u8  hitProperties;   // 0=default, 1=force blunt damage
    u8  reserved2[2];
};
```

---

## Key Fields for Variable Damage

| Field          | Purpose           | How it creates variation           |
| -------------- | ----------------- | ---------------------------------- |
| `offsetX/Y`    | Hitbox position   | Different zones (close vs far)     |
| `width/height` | Hitbox size       | Overlapping vs separate regions    |
| `frameStart`   | Activation timing | Sequential hits in combos          |
| `durationMult` | How long active   | Repeating tick damage              |
| `damageFlags`  | jpower reference  | Different damage values per hitbox |

---

## Verified Examples

### Caramelman (ds_b_03) - Verified 2026-02-02

Detailed collision export notes, `damageFlags` mapping attempts, and per-move
analysis are maintained in: `docs/characters/Caramelman-Character-Map.md` (see
**damageFlags Mapping (WIP)**).

### Majin Buu (db_b_12) - Verified 2026-02-02

| Move  | Pattern          | Damage  | Mechanism                             |
| ----- | ---------------- | ------- | ------------------------------------- |
| Y     | Multi-hit combo  | 3+3+12  | Three entries, different frameStart   |
| fwd Y | Repeating        | 6×4 max | Single repeating hitbox               |
| up Y  | Projectile chain | 3+1×7+8 | nextId chain in jpower                |
| air Y | Continuous       | 4/tick  | Single hitbox, multiple registrations |

---

## Research Implications

1. **Damage formula still applies:** Each hitbox independently uses
   `damage = d1/5 + (tier-2)`
2. **damageFlags is key:** Different damageFlags values point to different
   jpower entries
3. **Animation controls timing:** frameStart and durationMult determine when/how
   often hits register
4. **No special code needed:** Complex attacks emerge from simple collision
   entry combinations

---

## Tools

### Full Extraction Workflow

**Step 1:** Extract ChrBin.aar from ROM (contains collision files)

```bash
# Extract the container
./JUS.CLI jus containers export --alar /path/to/ChrBin.aar --output ./extracted/ChrBin

# Collision files will be in: ./extracted/ChrBin/chr/col/
```

**Step 2:** Export collision file to JSON

```bash
# Export single character (e.g., Caramelman = ds_b_03)
./JUS.CLI jus combat export-collision --bin ./extracted/ChrBin/chr/col/ds_b_03.bin --output ./output

# Export all collision files at once
./JUS.CLI jus combat export-all-collisions --directory ./extracted/ChrBin/chr/col/ --output ./output/collision
```

**Step 3:** Analyze JSON output The JSON will show all collision entries with
their exact values for:

- `offsetX`, `offsetY` - hitbox position
- `width`, `height` - hitbox size
- `damageFlags` - jpower entry reference
- `frameStart` - activation timing
- `knockback`, `hitTier` - hit properties

### File Locations in ROM

| Data            | Container  | Path             |
| --------------- | ---------- | ---------------- |
| Collision files | ChrBin.aar | `chr/col/*.bin`  |
| Character stats | bin/       | `chr_b.bin`      |
| Move parameters | bin/       | `jpower.bin`     |
| Projectile data | ChrBin.aar | `chr/shot/*.bin` |

---

## Related Documentation

- [Combat-Formats.md](../formats/Combat-Formats.md) - Binary format specs
- [jpower-Block-Pattern-Analysis.md](./jpower-Block-Pattern-Analysis.md) -
  jpower entry analysis
- [Research-Status.md](./Research-Status.md) - Overall research status
