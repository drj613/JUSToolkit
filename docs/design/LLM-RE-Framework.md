# LLM-Assisted Game Reverse Engineering Framework

**Status:** Draft - Capturing patterns from JUSToolkit development

This document extracts reusable patterns for working with LLMs (Claude, GPT, etc.) to reverse engineer video games.

---

## Why LLMs for Reverse Engineering?

LLMs excel at RE tasks because they can:
- Maintain context across complex codebases and data structures
- Generate tooling quickly (GDB scripts, analysis tools)
- Document findings in structured formats
- Suggest hypotheses based on partial data
- Handle tedious tasks (mapping tables, cross-referencing)

LLMs struggle with:
- Tasks requiring real-time interaction (gameplay testing)
- Hardware debugging without automated triggers
- Truly novel patterns not seen in training data

---

## 1. Project Organization

### Dual-Goal Structure

Most RE projects have two goals that require different approaches:

| Goal | Focus | Precision |
|------|-------|-----------|
| **Decompilation/Hacking** | Exact binary compatibility | Must match original exactly |
| **Engine Recreation** | Behavioral accuracy | Can differ if behavior matches |

Organize documentation to serve both:
```
docs/
├── research/     # Raw findings, exact values, file formats
├── design/       # Engine specs, behavioral requirements
├── formats/      # Binary format specifications (decompilation)
└── characters/   # Entity-specific data (both goals)
```

### Issue Tracking for Multi-Session Work

**Problem:** LLM conversations compact/reset, losing context.

**Solution:** Use persistent issue tracking (we use [beads](https://github.com/steveyegge/beads)):
- Create epics for major research areas
- Track blocking unknowns explicitly
- Rich comments preserve context
- Dependencies show what's blocked

**Pattern:**
```
Epic: Combat System
├── Task: Damage formula (CONFIRMED)
├── Task: Knockback formula (BLOCKED - needs weight location)
├── Task: Hitstun mechanics (IN_PROGRESS)
└── Task: Guard system (OPEN)
```

### AGENTS.md

Every project needs an `AGENTS.md` file that tells LLM agents:
- How to find current work (`bd ready`)
- How to claim and complete work
- Project-specific conventions
- What to commit vs what needs review

---

## 2. Research Methodology

### Finding "Blocking Unknowns"

Not all unknowns are equal. Identify which ones block progress:

```markdown
## Blocking Unknowns
1. Weight storage location
   - Blocks: Knockback formula, walk speed implementation
   - Checked: chr_b.bin, collision files, ARM9 near names
   - Next: Memory diff during gameplay

2. Hitstun timer field
   - Blocks: Combo system implementation
   - Checked: jpower.bin has values, but RAM location unknown
   - Next: GDB snapshot on damage
```

### Formula Derivation Process

1. **Observe** - Document raw behavior (Goku B does 8 damage)
2. **Hypothesize** - Propose formula (`damage = jpower_total / 5`)
3. **Test** - Check against other cases (does Ichigo match?)
4. **Refine** - Adjust formula for exceptions
5. **Confirm** - Mark as confirmed with test evidence

**Always document confidence level:**
- **CONFIRMED:** Tested across multiple characters/scenarios
- **HYPOTHESIS:** Fits observed data, needs more testing
- **UNKNOWN:** No working theory yet

### Comparative Testing

When you can't read the code, compare behavior:

| Test | Purpose |
|------|---------|
| Same attack, different defenders | Find weight/defense effects |
| Same defender, different attacks | Find attack-specific values |
| Same attack, different HP levels | Find HP-based scaling |
| Different characters, same stats | Find character-specific factors |

---

## 3. Tooling Patterns

### Emulator Debugging (GDB Pattern)

Most emulators support GDB stubs. Create a watcher script with:

```python
# 1. Known addresses (from cheat codes, prior research)
ADDRESSES = {
    'player1_hp': 0x021DF1D5,
    'battle_timer': 0x021DEA71,
}

# 2. Helper functions
def read_byte(addr): ...
def read_dword(addr): ...

# 3. Snapshot/diff capability
def take_snapshot(name, region): ...
def diff_snapshots(snap1, snap2): ...

# 4. Automated triggers (solve focus problem)
class OnDamageBreakpoint(gdb.Breakpoint):
    def stop(self):
        # Capture state automatically
        return False  # Continue running
```

**Key insight:** Automated triggers solve the "window focus problem" - you can't control both the game and GDB simultaneously.

### Cheat Code Mining

Action Replay/GameShark codes reveal memory addresses:
- HP addresses show character struct locations
- Infinite ammo shows weapon data structures  
- Unlock codes show save data format

Create a parser to extract addresses from cheat databases.

### Memory Diffing

To find unknown fields:
1. Take snapshot in state A (idle)
2. Take snapshot in state B (moving)
3. Diff to find what changed
4. Interpret changed bytes (position? velocity? timer?)

---

## 4. Documentation Templates

### Mechanics Reference

```markdown
# [Game] Combat Mechanics Reference

## 1. Character States
| State | Description | Can Act? | Transitions To |
|-------|-------------|----------|----------------|
| Idle | Standing | Yes | Walk, Attack, ... |

## 2. Damage System
### Formula (CONFIRMED/HYPOTHESIS/UNKNOWN)
```
damage = ...
```
### Test Evidence
- Character A attack vs Character B: X damage
- ...

## 3. Open Questions
1. **High Priority:** [question]
2. **Medium Priority:** [question]
```

### Character/Entity Map

```markdown
# [Character Name] Map

## Overview
| Property | Value | Source |
|----------|-------|--------|
| File | chr_b_01 | Extracted |
| Weight | Heavy | Observed |

## Moves
| Input | Damage | Properties |
|-------|--------|------------|
| B | 8 | Knockback |

## Unknowns
- [ ] Exact frame data
- [ ] Hitbox sizes
```

### Design Document (Engine Recreation)

```markdown
# [System] Engine Design

## Purpose
Recreate [behavior] accurately enough to [goal].

## Known Behavior
- [Confirmed fact]
- [Confirmed fact]

## Formula
```
value = f(input1, input2, ...)
```

## Implementation Notes
- [Consideration for engine]

## Test Cases
| Input | Expected Output |
|-------|-----------------|
| ... | ... |
```

---

## 5. LLM Collaboration Patterns

### Effective Prompting

**Good:** "Find all addresses in cheat codes related to HP or health"
**Bad:** "Reverse engineer the game"

**Good:** "Compare these two memory dumps and identify fields that changed"
**Bad:** "Figure out how damage works"

### Task Decomposition

Break complex RE into LLM-sized chunks:
1. Parse this file format (bounded, clear output)
2. Create a diff tool (concrete deliverable)
3. Document these findings (synthesis task)
4. Hypothesize formula from these observations (reasoning task)

### Preserving Context

- Use issue tracking comments liberally
- Commit documentation frequently
- Create glossaries for project-specific terms
- Cross-reference documents explicitly

---

## 6. Platform-Specific Notes

### Nintendo DS
- Two ARM CPUs (ARM9 main, ARM7 audio/wifi)
- Main RAM at 0x02000000-0x02400000
- GDB stubs: melonDS (port 3333), DeSmuME (Lua alternative)
- Common tools: ndstool, tinke, CrystalTile2

### [Other Platforms]
*(To be added as framework expands)*

---

## Changelog

| Date | Changes |
|------|---------|
| 2026-01-31 | Initial draft from JUSToolkit patterns |
