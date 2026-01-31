# Reverse Engineering Session Playbook

Strategies and approaches for human+LLM collaborative reverse engineering sessions.

---

## Session Start Checklist

1. **Read entrypoint**: `docs/research/README.md`
2. **Check issue tracker**: `bd ready` for available work
3. **Review blocking unknowns**: What's stuck and why?
4. **Pick a focus**: One specific question per session works best

---

## Research Strategies

### Strategy 1: Address Mining from Cheat Codes

**When to use:** Starting research on a new system (health, SP, position, etc.)

**Approach:**
1. Search web for Action Replay / cheat codes for the game
2. Parse hex addresses from codes (format: `XXXXXXXX YYYYYYYY`)
3. Cluster addresses by region to find related systems
4. Cross-reference with known addresses in `Cheat-Code-Analysis.md`

**Tools:** `scripts/cheat_code_parser.py`, web search

**LLM prompt template:**
```
Search for Action Replay cheat codes for [GAME] related to [SYSTEM].
Parse the addresses and identify what memory regions they manipulate.
Cross-reference with existing documented addresses at [FILE].
```

---

### Strategy 2: Memory Diffing via GDB

**When to use:** Finding where specific game state is stored

**Approach:**
1. Run `jus-baseline-noise` to identify timer fields (filter noise)
2. Set up automated snapshot trigger for the event you're studying
3. Play the game to trigger the event multiple times
4. Use `jus-char-diff` to find fields that change with the event
5. Narrow down by testing with different parameters (characters, moves, etc.)

**Tools:** `scripts/gdb/jus_gdb_watcher.py`, melonDS with GDB stub

**Human tasks:** Run emulator, provide controller input, observe game behavior

---

### Strategy 3: Guide/FAQ Cross-Reference

**When to use:** Understanding game mechanics from player perspective

**Approach:**
1. Find comprehensive game guide (GameFAQs, etc.)
2. Extract specific mechanical sections (damage, combos, status effects)
3. Convert player-facing descriptions to technical hypotheses
4. Test hypotheses against extracted game data

**Key insight:** Guides describe *what* happens, not *how*. Use them for:
- Confirming mechanics exist
- Getting terminology right
- Finding edge cases to test

**LLM prompt template:**
```
Fetch [GUIDE URL]. Extract ONLY the sections about [MECHANIC].
Convert player-facing descriptions into testable technical hypotheses.
```

---

### Strategy 4: File Format Analysis

**When to use:** Mapping game data files to runtime behavior

**Approach:**
1. Export game files using CLI tools
2. Look at existing format documentation (C# deserializers)
3. Compare file data to observed in-game values
4. Test hypotheses by modifying files and observing changes

**Key files for JUS:**
- `jpower.bin` - Damage/hitstun values
- `chr_b.bin` - Character parameters
- `koma.bin` - Deck/koma data
- `collision/` - Hitbox data

---

### Strategy 5: ARM9 Code Analysis

**When to use:** Finding formula implementations, understanding control flow

**Approach:**
1. Start from known address (from cheat codes or watchpoint)
2. Disassemble surrounding code
3. Trace data flow to understand what inputs affect output
4. Look for magic constants (divisors, multipliers)

**Tools:** Ghidra, IDA, radare2

**Key addresses for JUS:**
- `0x020784FC` - Health calculation function
- `0x021548E2` - Health calculation instruction
- `0x020543C0` - Code enable flag

---

### Strategy 6: Comparative Testing

**When to use:** Validating formulas, finding edge cases

**Approach:**
1. Create controlled test cases (specific characters, moves, conditions)
2. Predict expected values using hypothesized formula
3. Test in-game and record actual values
4. Iterate on formula when predictions don't match

**JUS damage formula test matrix:**
| Variable | Test Cases |
|----------|------------|
| Character | Different series (DB, OP, Naruto, etc.) |
| Move type | B, Y, Side-B, Air-B, K-moves |
| Nature | Same, advantage, disadvantage |
| Status | Normal, buffed, debuffed |

---

### Strategy 7: Hex-Theorize / Human-Validate Loop (CORE PATTERN)

**When to use:** This is the primary workflow for discovering game mechanics

**Why it works:**
- LLMs excel at pattern recognition across large hex/data dumps
- Humans excel at precise in-game observation and input
- Rapid iteration between theory and validation

**The Loop:**

```
┌─────────────────────────────────────────────────────────┐
│  1. LLM analyzes hex data, proposes hypothesis          │
│     "damage1 field at offset 0x04 divided by 5 = damage"│
├─────────────────────────────────────────────────────────┤
│  2. LLM generates specific, falsifiable predictions     │
│     "Nami B should deal 6 damage (d1=30, 30/5=6)"       │
├─────────────────────────────────────────────────────────┤
│  3. Human tests prediction in-game                      │
│     → Records actual value: Nami B = 6 ✓                │
├─────────────────────────────────────────────────────────┤
│  4. Results fed back to LLM                             │
│     → If match: hypothesis gains confidence             │
│     → If mismatch: refine hypothesis, repeat            │
└─────────────────────────────────────────────────────────┘
```

**Success example (JUS damage formula):**
1. LLM analyzed jpower.bin, hypothesized `total/5` formula
2. Goku B=8 didn't match (total=50 → should be 10)
3. Human confirmed Buu B=9 (same block as Goku)
4. LLM refined: formula uses `damage1` only, not total
5. Human validated across 12 characters → CONFIRMED

**Keys to success:**
- Make predictions **specific and falsifiable**
- Test **diverse cases** (different series, tiers, move types)
- Document **both matches AND mismatches**
- Update docs immediately when validated

**LLM responsibilities:**
- Analyze data patterns
- Generate testable predictions
- Refine hypotheses based on results
- Update documentation

**Human responsibilities:**
- Run the game
- Execute precise test cases
- Report exact values observed
- Identify edge cases to test

---

## Topic-Specific Research Guides

### Researching Damage/JSoul

**Known:**
- JSoul = health terminology
- Formula: `floor(jpower.damage1 / 5) + (tier - 2)` (CONFIRMED)
- Nature advantage: 1.5x multiplier
- jpower.bin contains raw damage values

**Unknown:**
- How collision files select which jpower entry to use (damageFlags mechanism)
- Special move (K) formula differences
- Multi-hit move calculation (nextId chains)

**Recommended approach:** Strategy 7 (Hex-Theorize/Human-Validate) + Strategy 4 (jpower analysis)

---

### Researching Velocity/Knockback

**Known:**
- Knockback depends on: attack power, weight, HP ratio, passives
- Weight is NOT in chr_b.bin (confirmed via Franky/Nami comparison)
- Position system at `0x0218xxxx` region

**Unknown:**
- Weight storage location
- Knockback formula
- Hitstun duration storage

**Recommended approach:** Strategy 2 (Memory Diffing) with heavy vs light characters

---

### Researching Status Effects

**Known:**
- Positive status at struct offset `+0x88`
- Negative status flags at offset `+0xA0`
- ~30 documented status effects from guides

**Documented status IDs:**
- `0x00` = None
- `0x09` = Invincibility
- Guard Seal, Toughen, Critical, Regain, etc. (need mapping)

**Recommended approach:** Strategy 1 (Address Mining) + Strategy 2 (Memory Diffing)

---

### Researching Combo/Hitstun

**Known:**
- Hitstun field in jpower.bin (values: 5=light, 10=heavy, 50+=special)
- Combo breaker/forced knockdown exists (threshold unknown)
- Dream Combo system requires 2+ Battle characters

**Unknown:**
- Where hitstun countdown is stored in RAM
- How hitstun value maps to frame duration
- Combo damage scaling (if any)

**Recommended approach:** Strategy 2 with `jus-auto-snapshot-on-hit`

---

## Common Pitfalls

### 1. Timer Noise
**Problem:** Memory diffs show hundreds of changes from timers/counters
**Solution:** Run `jus-baseline-noise` + `jus-find-timers` FIRST

### 2. Pointer Indirection
**Problem:** Address from cheat code is a pointer, not the actual data
**Solution:** Follow the pointer dereference in cheat code format

### 3. Shared Data Blocks
**Problem:** Multiple characters share same jpower block but have different moves
**Solution:** There's a secondary selection mechanism - focus on HOW characters select from blocks

### 4. Confirmation Bias
**Problem:** Formula "works" for tested cases but fails edge cases
**Solution:** Test across character roster, not just DB characters

### 5. Stale Documentation
**Problem:** Docs say "confirmed" but testing shows otherwise
**Solution:** Always mark confidence level, document test coverage

---

## Session End Checklist

1. **Update issue notes** with progress
2. **Document new findings** (even negative results)
3. **Create issues** for follow-up work
4. **Commit changes**: `git add -A && git commit`
5. **Sync and push**: `bd sync && git push`
6. **Verify push**: `git status` shows up to date

---

## Quick Reference: LLM Collaboration Tips

### Good prompts:
- "Search for [specific thing] in [specific files]"
- "Compare [X] to [Y] and identify differences"
- "Parse this cheat code and explain what it does"
- "Create a test matrix for validating [formula]"

### Bad prompts:
- "Figure out how [broad system] works" (too vague)
- "Read all the documentation" (too much context)
- "Is this correct?" (need specific testable question)

### LLM strengths:
- Pattern matching across large datasets
- Cross-referencing multiple information sources
- Generating test cases systematically
- Documenting findings in structured format

### Human required:
- Running the game/emulator
- Providing controller input
- Observing visual behavior
- Making judgment calls on ambiguous data

---

*Last updated: 2026-01-31*
