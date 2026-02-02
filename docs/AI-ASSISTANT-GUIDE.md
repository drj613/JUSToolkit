# AI Assistant Guide - Jump Ultimate Stars Research

**Read this FIRST at the start of every session.**

This document provides context for AI assistants working on the JUSToolkit project - a reverse engineering effort for Jump Ultimate Stars (Nintendo DS, 2006).

---

## Project Goals (Priority Order)

### 1. Build a Reusable Fighting Game Engine (Primary)

**Epic:** JUS-55i

Extract JUS's game mechanics and implement them in a clean, moddable 2D fighting game engine. This is NOT about modding the original ROM - it's about creating a new engine inspired by JUS.

Key systems to implement:
- Damage calculation (jpower system, tier modifiers, nature advantage)
- Hitstun/knockback physics
- Koma deck building system
- Character passives
- Data-driven character definitions (JSON/YAML)

### 2. Create LLM-Assisted RE Framework (Secondary)

**Epic:** JUS-acr (in progress)

Document the methodology and tooling as a reusable template for LLM-assisted game reverse engineering.

### 3. Game Decompilation (Tertiary, Lowest Priority)

Create an exact decompilation of the original game code. This is a long-term goal that supports the primary goal.

---

## Issue Tracking

This project uses **beads** (`bd`) for issue tracking:

```bash
bd ready              # Find available work
bd show <id>          # View issue details  
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

**Always check `bd ready` at session start** to see current priorities.

---

## Key Files & How They Work Together

### Game Data Files

Located in `jus_files/ripped_jus_files/`:

| File | Purpose | Key Fields |
|------|---------|------------|
| `bin/chr_b.bin` | 74 battle character stats | formType, tier, classId, statC |
| `bin/jpower.bin` | Damage/hitstun values | damage1, damage2, damage3, hitstun |
| `bin/koma.bin` | 890 deck panel definitions | komaType, passiveIndex |
| `bin/chr_s.bin` | 140+ support characters | Similar to chr_b |

### How They Connect

```
chr_b.bin                     jpower.bin
┌─────────────┐              ┌─────────────┐
│ Character   │              │ Attack Data │
│ - classId ──┼──────────────▶ Block Index │
│ - tier      │              │ - damage1   │
│ - statC     │              │ - hitstun   │
└──────┬──────┘              └─────────────┘
       │
       │ (index)
       ▼
collision/*.bin
┌─────────────┐
│ Hitbox Data │
│ - damageFlags ───▶ (Direct: jpower index)
│ - subType        (Indirect: ARM9 lookup)
│ - hitTier   │
└─────────────┘
```

### Collision Files

Located in `jus_files/extracted_chrbin/ChrBin.aar/chr/col/`:
- One `.bin` file per character (e.g., `db_b_01.bin` = Goku)
- Contains hitbox definitions with damage references
- **Two systems**: Direct (damageFlags=jpower index) or Indirect (damageFlags≤1)

### Exported JSON (Pre-processed)

Located in `jus_files/exported_combat/`:
- `chr_b.json` - All battle characters as JSON
- `jpower.json` - All jpower entries as JSON
- `*_collision.json` - Individual character collision exports

---

## Critical Research Documents

### Must-Read Before Working

| Document | Purpose |
|----------|---------|
| `docs/research/Research-Status.md` | What's CONFIRMED vs UNKNOWN |
| `docs/research/DamageFlags-Character-Classification.md` | How damage lookup works |
| `docs/research/Combat-Mechanics-Reference.md` | Observed game mechanics |
| `docs/research/Character-Mapping.md` | All 74 characters mapped to files |

### Design Documents

| Document | Purpose |
|----------|---------|
| `docs/design/Combat-Engine-Design.md` | Engine implementation spec |
| `docs/research/Passives-Reference.md` | All passive abilities documented |

### Per-Character Data

`docs/characters/*.md` - Individual character maps with stats, moves, collision data.
Most complete: `Goku-Character-Map.md`, `Ichigo-Character-Map.md`

---

## Current Research State

### CONFIRMED (High Confidence)

**Damage Formula:**
```
damage = floor(jpower.damage1 / 5) + (tier - 2)
```
- tier 1: -1 damage, tier 2: +0, tier 3: +1
- Verified across 15+ characters

**DamageFlags Classification (completed 2026-02-02):**
- 64 characters use **Indirect** lookup (damageFlags ≤ 1)
- 10 characters use **Direct** lookup (damageFlags ≥ 2 = jpower index)
- `damageFlags=1` is a FLAG, not an index

**Character Mapping:** All 74 battle characters mapped to collision files.

### UNKNOWN (Blocking Engine Development)

| Unknown | Why It Matters | Ticket |
|---------|----------------|--------|
| Weight storage location | Knockback formula | JUS-cb0.1 |
| Indirect lookup mechanism | 64 characters use this | JUS-9lp.1 |
| Walk speed exact thresholds | Movement system | JUS-n3p |
| Hitstun timer location | Combo system | JUS-9lp.2.2 |

**These require GDB debugging** - see `scripts/gdb/README.md` for setup.

---

## SOLVED MYSTERIES - Do Not Re-Investigate

### tr_b_01 Identity
**tr_b_01 = Tsuna** from "Katekyo Hitman Reborn" (NOT Taizo, NOT cut content).
Taizo (unused) is dt_b_04.

### Walk Speed
Stored in chr_b.bin `statC` field. Threshold-based (not linear).

### Passive Storage
koma.bin byte 7 = PassiveIndex. Passives are per-form, not per-koma.

### Series NOT in Game
Toriko, Hikaru no Go - don't search for them.

---

## Common Pitfalls

| Wrong Assumption | Reality |
|------------------|---------|
| "jpower block = chr_b index" | jpower block = `classId & 0xFF` |
| "damageFlags = damage value" | It's a jpower index (Direct) or flag (Indirect) |
| "Characters sharing jpower block have same moveset" | They share damage VALUES, not movesets |
| "statA/statB are gameplay stats" | They're sprite/text offsets |
| "battleParams = weight/speed" | Nami/Franky have identical params, opposite weight |

---

## Useful Scripts

### Python Analysis Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `classify_damage_flags.py` | Classify characters by damage system |
| `extract_character_data.py` | Export character data to JSON |
| `cheat_code_parser.py` | Parse cheat codes for RAM addresses |

### GDB Debugging (`scripts/gdb/`)

| Script | Purpose |
|--------|---------|
| `jus_gdb_watcher.py` | Memory watching and snapshotting |
| `README.md` | GDB experiment setup guide |

### CLI Commands

```bash
# Export collision to JSON
dotnet run --project src/JUS.CLI -- jus combat export-collision --bin <file> --output <dir>

# Export chr_b to JSON  
dotnet run --project src/JUS.CLI -- jus combat export-chr --bin <file> --output <dir>

# Classify all characters
python scripts/classify_damage_flags.py ./jus_files/extracted_chrbin/ChrBin.aar/chr/col/
```

---

## ARM9 Key Offsets

| Offset | Contents |
|--------|----------|
| 0x0924B0 | Collision file pointer table (74 entries) |
| 0x08D4A0 | chr_b → collision identity mapping |
| 0x09E780 | Koma name table |

See `docs/research/ARM9-Research-Guide.md` for comprehensive guide.

---

## Session Workflow

### Starting a Session

1. Read this document
2. Run `bd ready` to see current priorities
3. Check `docs/research/Research-Status.md` for context
4. Review any in-progress tickets with `bd list --status in_progress`

### Ending a Session

Per `AGENTS.md`, you MUST:
1. Update/close relevant tickets
2. Commit and **push** changes
3. Provide handoff context

---

## File Prefix Reference

| Prefix | Series | Battle Chars |
|--------|--------|--------------|
| db | Dragon Ball | 12 |
| op | One Piece | 8 |
| na | Naruto | 5 |
| bl | Bleach | 5 |
| bb | Bobobo | 4 |
| yh | Yu Yu Hakusho | 3 |
| hk | Hokuto no Ken | 2 |
| ss | Saint Seiya | 2 |
| sk | Shaman King | 3 |
| jj | JoJo | 2 |
| hh | Hunter x Hunter | 2 |
| gt | Gintama | 2 |
| dg | D.Gray-man | 2 |
| ds | Dr. Slump | 3 |
| dt | Debug/Meta | 4 |

Full mapping: `docs/research/Character-Mapping.md`

---

*Last updated: 2026-02-02*
