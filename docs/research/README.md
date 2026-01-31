# JUS Research Documentation

**Start here for new sessions.** This is the entrypoint for understanding the
reverse engineering research.

---

## Quick Status

Run `bd ready` to see available work, or `bd show JUS-p5i` for current focus.

### Current Focus: Hitstun/Velocity Research (JUS-p5i)

- GDB tooling ready at `scripts/gdb/jus_gdb_watcher.py`
- Need to capture in-game data to find velocity/hitstun fields
- See workflow in `scripts/gdb/README.md`

### Blocking Unknowns

1. **Weight storage location** (JUS-cb0.1) - Critical for knockback formula
2. **Hitstun timer field** - Where in RAM is hitstun countdown stored?
3. **Velocity fields** - Where are X/Y velocity stored in character struct?

---

## Document Map

| Document                        | Purpose                           | Read When                  |
| ------------------------------- | --------------------------------- | -------------------------- |
| **This README**                 | Entrypoint, navigation            | Start of every session     |
| **`RE-Session-Playbook.md`**    | **Human+LLM strategies**          | **Planning research approach** |
| `Combat-Mechanics-Reference.md` | Canonical game behavior reference | Understanding mechanics    |
| `Combat-Mechanics.md`           | Raw research findings             | Deep diving into specifics |
| `Character-State-Struct.md`     | In-battle character RAM structure | GDB debugging, hitstun research |
| `chr_b-Complete-Mapping.md`     | Character file format             | Working with chr_b.bin     |
| `jpower-Mapping.md`             | Damage/move data format           | Working with jpower.bin    |
| `jpower-Block-Pattern-Analysis.md` | Block patterns and unknowns    | jpower deep dive           |
| `Cheat-Code-Analysis.md`        | Known memory addresses            | GDB debugging              |
| `ARM9-Research-Guide.md`        | ARM9 binary analysis              | Low-level research         |
| `Research-Status.md`            | Historical status tracking        | Understanding progress     |
| `Passives-Reference.md`         | Character passive abilities       | Passive system work        |

### Design Documents (in `../design/`)

| Document                  | Purpose                     |
| ------------------------- | --------------------------- |
| `Combat-Engine-Design.md` | Specs for engine recreation |
| `LLM-RE-Framework.md`     | Reusable RE methodology     |

---

## Glossary

| Term             | Definition                                                  |
| ---------------- | ----------------------------------------------------------- |
| **jpower.bin**   | Move data file - damage values, hitstun, attack types       |
| **chr_b.bin**    | Character parameters - 74 entries, one per battle character |
| **classId**      | Field linking character to jpower block (`classId & 0xFF`)  |
| **statC**        | Walk speed threshold field in chr_b.bin                     |
| **koma**         | Panel/card in deck system (Help, Support, or Battle)        |
| **PassiveIndex** | Index into passive ability table (in koma.bin)              |
| **tier**         | Character power level (1-3), affects damage                 |
| **nature**       | Rock-paper-scissors type (Power/Knowledge/Laughter)         |
| **JSoul**        | Health/HP in this game (not "health" or "HP")               |

---

## Key Formulas

### Damage Formula (CONFIRMED 2026-01-30)

```
jsoul_damage = floor(jpower.damage1 / 5) + (tier - 2)
actual_damage = floor(jsoul_damage × nature_multiplier)
```

- `damage1` = **first damage component only** (NOT total!)
- `tier` = koma size (2=standard, 1=weak form, 3=8-koma)
- Nature advantage: 1.5x multiplier

**Verified across 12+ characters:**
| Character | tier | B Damage | damage1 |
|-----------|------|----------|---------|
| Nami | 2 | 6 | 30 |
| Train | 2 | 7 | 35 |
| Goku, Luffy, Robin, Franky, Naruto | 2 | 8 | 40 |
| Buu | 2 | 9 | 45 |
| Bankai Ichigo | 1 | 9 | 50 |
| Ichigo | 2 | 10 | 50 |
| Caramelman | 3 | 13 | 60 |

**REMAINING UNKNOWN:** How collision files SELECT which jpower entry to use

### Walk Speed

```
if statC < ~100: walk_speed = SLOW
else: walk_speed = NORMAL
```

Exact threshold TBD (JUS-n3p)

### Knockback (UNKNOWN)

```
knockback_velocity = f(attack_power, weight, hp_ratio, passives)
```

Weight storage location unknown (JUS-cb0.1)

---

## Research Tools

### GDB Watcher (`scripts/gdb/`)

Memory analysis for melonDS. Key commands:

- `jus-baseline-noise` - Identify timer fields (run first!)
- `jus-auto-snapshot-on-hit` - Capture state on damage
- `jus-char-diff` - Compare snapshots to find changes

### CLI Tool (`src/JUS.CLI/`)

Extract and analyze game files:

```bash
dotnet run --project src/JUS.CLI -- jus combat export-all <rom_path> <output>
```

### Analysis Scripts (`scripts/`)

- `cheat_code_parser.py` - Extract addresses from AR codes
- `analyze_deck_dump.py` - Analyze memory dumps

---

## Getting Started (New Contributor)

1. **Read this document** - Understand the project state
2. **Check `bd ready`** - See what work is available
3. **Read the relevant doc** - From the document map above
4. **Pick an issue** - Claim with `bd update <id> --status in_progress`

### For GDB Research

1. Set up melonDS with GDB stub (see `scripts/gdb/README.md`)
2. Load the watcher: `arm-none-eabi-gdb -x scripts/gdb/jus_gdb_watcher.py`
3. Run baseline noise capture first
4. Use automated triggers for data collection

---

## Issue Tracking

We use [beads](https://github.com/steveyegge/beads) for persistent issue
tracking.

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Start work
bd close <id>         # Complete work
bd sync               # Sync with git
```

### Key Epics

- **JUS-55i**: Create reusable fighting game engine (PRIMARY GOAL)
- **JUS-cb0**: Combat System
- **JUS-acr**: LLM-assisted RE framework

---

## Session End Checklist

Before ending a session:

1. Update issue notes with progress
2. Commit documentation changes
3. Run `bd sync && git push`
4. Verify `git status` shows up to date

---

_Last updated: 2026-01-31_
