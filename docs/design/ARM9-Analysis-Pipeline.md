# ARM9 Analysis Pipeline

A combined static + dynamic approach to reverse engineering Jump Ultimate Stars.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARM9 ANALYSIS PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│   │   STATIC    │     │   DYNAMIC   │     │     AI      │                   │
│   │  ANALYSIS   │────►│  ANALYSIS   │────►│  ASSISTED   │                   │
│   └─────────────┘     └─────────────┘     └─────────────┘                   │
│         │                   │                   │                            │
│         ▼                   ▼                   ▼                            │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│   │ ARM9 Tables │     │ RAM Values  │     │ Pattern     │                   │
│   │ Block Map   │     │ Watchpoints │     │ Recognition │                   │
│   │ Pointers    │     │ Cheat Codes │     │ Decompile   │                   │
│   └─────────────┘     └─────────────┘     └─────────────┘                   │
│                                                                              │
│   Tools: Python        Tools: DeSmuME     Tools: Claude                     │
│          Ghidra               Lua Script         LLM4Decompile              │
│                               Bizhawk            Ghidra                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Static ARM9 Analysis

### 1.1 Block Detection

ARM9.bin contains distinct regions:

| Region Type | Detection Pattern | Example |
|-------------|-------------------|---------|
| **Code** | ARM instruction prefixes (0xE3, 0xE5, 0xE1, 0xEB) | Functions |
| **Pointer Tables** | Sequences of 0x020xxxxx values | Collision table at 0x0924B0 |
| **Index Tables** | Bounded byte arrays (0-73 for chr_b) | Identity map at 0x08D4A0 |
| **String Tables** | ASCII sequences with null terminators | "bl_b_01", "db_b_01" |
| **Data Arrays** | Repeating struct-like patterns | Unknown tables |

### 1.2 Known ARM9 Structure

```
0x00000000 - 0x00080000  Code section (ARM instructions)
0x00080000 - 0x000A0000  Data section (tables, strings, constants)
0x000A0000 - End         Mixed/overlay data
```

**Discovered Tables:**

| Offset | Size | Contents | Confidence |
|--------|------|----------|------------|
| 0x0924B0 | ~640B | Collision file pointer table (74 entries × 8B) | Confirmed |
| 0x08D4A0 | 74B | chr_b → collision identity map | Confirmed |
| 0x09E780 | ~200B | Koma name table | Confirmed |
| 0x078000? | Unknown | Damage calculation code | Suspected |

### 1.3 Automated Table Scanner

Run `scripts/arm9_table_scanner.py` to find:
- Pointer tables (arrays of ROM addresses)
- Index tables (bounded byte arrays)
- Potential struct arrays (repeating patterns)

---

## Phase 2: Dynamic Analysis with melonDS + GDB

### 2.1 Emulator Options

| Emulator | Scripting | GDB | Platform | Best For |
|----------|-----------|-----|----------|----------|
| **melonDS** | None | Yes | Mac/Linux/Win | Ghidra integration, breakpoints |
| **DeSmuME** | Lua | Partial | Windows only | RAM watch (if on Windows) |
| **Bizhawk + melonDS** | Lua (full) | No | Windows/.NET | TAS, comprehensive scripting |

### 2.2 melonDS + GDB Setup (Mac/Linux)

**Prerequisites:**
- melonDS with GDB enabled (build from source with `-DENABLE_GDB_STUB=ON` or get GitHub Actions build)
- `gdb-multiarch` or `arm-none-eabi-gdb`
- Ghidra 11.0.3+

**Step 1: Enable GDB in melonDS**
```
Config → Emu Settings → Devtools tab
☑ Enable GDB stub
ARM9 Port: 3333
ARM7 Port: 3334
```

Or edit `melonDS.ini`:
```ini
[Gdb]
Enabled=true

[Gdb.ARM9]
Port=3333
BreakOnStartup=false

[Gdb.ARM7]
Port=3334
BreakOnStartup=false
```

**Step 2: Connect with GDB**
```bash
# Mac (via Homebrew)
brew install arm-none-eabi-gdb

# Linux
sudo apt install gdb-multiarch

# Connect
arm-none-eabi-gdb -ex "set arch armv5t" -ex "target remote localhost:3333"
```

**Step 3: Ghidra Integration**

1. Open Ghidra, enable Debugger: `File → Configure → check "Debugger"`
2. Open `Window → Debugger → Debugger Targets`
3. Click connect button, select:
   - **Linux**: "gdb" with command: `arm-none-eabi-gdb -ex "set arch armv5t"`
   - **macOS**: "gdb via SSH" with localhost, same command
4. In GDB interpreter: `target remote localhost:3333`

### 2.3 GDB Commands for JUS Analysis

```gdb
# Read memory at address
x/10xb 0x021DF1D5          # 10 bytes at HP address

# Set watchpoint (break when memory changes)
watch *0x021DF1D5          # Break when leader HP changes
rwatch *0x020784FC         # Break when code at HP hook is read

# Set breakpoint at ARM9 code
break *0x020784FC          # Break at health check function

# Continue execution
continue

# Step one instruction
stepi

# Print registers
info registers

# Dump memory range to file
dump binary memory hp_region.bin 0x021DF000 0x021E0000
```

### 2.3 Key RAM Addresses (from Cheat Codes)

Action Replay codes reveal real memory addresses:

```lua
-- Game ID: AJUJ-65E1D889

-- Known RAM addresses (derived from AR codes)
ADDRESSES = {
    -- Health system
    health_code_hook = 0x020784FC,    -- Infinite health code patches here
    leader_health = 0x021DF1D5,       -- From "Refill Health" code
    nonleader_health = 0x021DF225,    -- From "Refill Health" code

    -- Special meter
    special_meter_1 = 0x021DF731,     -- From "Unlimited Special" code
    special_meter_2 = 0x021DF8B1,

    -- Timer
    battle_timer = 0x021DEA71,        -- From "Unlimited Time" code

    -- Gems/Points (multiple addresses)
    gems_base = 0x020B7718,           -- From "Infinite Gems" code
    koma_points_base = 0x020B76C8,    -- From "Infinite Koma Points" code
}
```

### 2.4 RAM Search Workflow

```
1. Start battle with known character
2. Note current HP value (e.g., 100)
3. RAM Search → Search for value 100
4. Take damage → HP becomes 85
5. RAM Search → Search for value 85
6. Result: Narrow to exact HP address
7. Set watchpoint on that address
8. Attack again → DeSmuME pauses at damage calculation
9. View disassembly → Find damage formula location
```

---

## Phase 3: Cheat Code Mining

### 3.1 Action Replay Code Format

```
Type 0: 32-bit write     0xxxxxxx yyyyyyyy  → [xxxxxxx] = yyyyyyyy
Type 1: 16-bit write     1xxxxxxx 0000yyyy  → [xxxxxxx] = yyyy
Type 2: 8-bit write      2xxxxxxx 000000yy  → [xxxxxxx] = yy
Type 3: > comparison     3xxxxxxx yyyyyyyy  → If [xxxxxxx] > yyyyyyyy
Type 5: 32-bit load      5xxxxxxx 00000000  → offset = [xxxxxxx]
Type 9: Button activator 94000130 xxxxxxxx  → If buttons pressed
Type D: Conditional      Dxxxxxxx yyyyyyyy  → Various conditions
Type E: Patch code       Eaaaaaaa ssssssss  → Patch at aaaaaaa
```

### 3.2 Known JUS Cheat Codes → Address Map

| Code Name | Type | Address | Meaning |
|-----------|------|---------|---------|
| Infinite Health | E/5/0 | 0x020784FC | Health check function hook |
| Leader Refill | 2 | 0x021DF1D5 | Player 1 HP storage |
| Non-leader Refill | 2 | 0x021DF225 | Player 2 HP storage |
| Unlimited Special | 2 | 0x021DF731 | SP meter 1 |
| Unlimited Time | 2 | 0x021DEA71 | Battle timer |
| Infinite Gems | 0 | 0x020B7718+ | Gem counters (6 addresses) |

### 3.3 Reverse Engineering from Codes

The **Infinite Health** code:
```
E2000000 00000010     ; Start patch, 16 bytes
E1D411F6 E1C411B8     ; ARM: LDRSH R1,[R4,#0x16] → STRH R1,[R4,#0x18]
E1A00000 EA01E13B     ; ARM: NOP, Branch
520784FC E1D411F8     ; If [0x20784FC] == E1D411F8 (original instruction)
020784FC EAFE1EBF     ; Write EAFE1EBF (branch to patch)
D2000000 00000000     ; End
```

This tells us:
- **0x020784FC** is in the damage/health calculation code path
- Original instruction: `LDRSH R1,[R4,#0x18]` (load signed halfword)
- The patch prevents HP from decreasing

---

## Phase 4: AI-Assisted Analysis

### 4.1 Pattern Recognition Workflow

```python
# Feed ARM9 regions to Claude for analysis

prompt = """
Here's a hex dump of ARM9.bin from offset 0x08D4A0 to 0x08D4EA (74 bytes).
This region is located right after the collision file pointer table.
I know there are 74 battle characters in this game.

Hex dump:
00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F
...

What pattern do you see? What might this table be used for?
"""
```

### 4.2 Function Decompilation

For specific functions found via watchpoints:

```python
prompt = """
Here's ARM assembly from a DS game at address 0x020784F0.
This function is called when a character takes damage.

020784F0:  E92D4010  PUSH {R4, LR}
020784F4:  E1A04000  MOV R4, R0
020784F8:  E1D411F8  LDRSH R1, [R4, #0x18]
020784FC:  E1D400F6  LDRSH R0, [R4, #0x6]
02078500:  E0410000  SUB R0, R1, R0
...

Decompile this to C code. What does this function do?
"""
```

### 4.3 Automated Function Analysis

Use LLM4Decompile or Claude to batch-process functions:

1. Export function list from Ghidra
2. For each function with known data references (chr_b, jpower, collision):
   - Extract disassembly
   - Send to LLM with context
   - Store results in `docs/decompiled/`

---

## Phase 5: Integration

### 5.1 Cross-Reference Database

Build a database linking:
- ARM9 offset → Discovered purpose
- RAM address → Runtime value type
- Cheat code → Function location
- Decompiled function → Game mechanic

### 5.2 Verification Loop

```
Static Analysis ──► Hypothesis
        │
        ▼
Dynamic Testing ──► Verify/Refine
        │
        ▼
AI Analysis ──────► Document
        │
        ▼
Update Database ──► New Hypotheses
```

---

## Tools & Scripts

### Available

| Script | Purpose |
|--------|---------|
| `scripts/extract_character_data.py` | Parse chr_b.bin, collision, jpower |
| `scripts/game_formats_analyzer.py` | Scan file headers |
| `scripts/arm9_table_scanner.py` | Find pointer/index tables in ARM9 |
| `scripts/cheat_code_parser.py` | Extract addresses from AR codes |
| `scripts/gdb/jus_gdb_watcher.py` | GDB Python script for memory watching (Mac/Linux) |
| `scripts/desmume/jus_watcher.lua` | DeSmuME Lua script (Windows only) |

### To Create

| Script | Purpose |
|--------|---------|
| `scripts/arm9_block_mapper.py` | Map code vs data regions (more detailed) |
| `scripts/ai_decompile.py` | Send functions to Claude for analysis |

---

## Quick Start

### 1. Static: Find New Tables

```bash
# Scan ARM9 for potential tables
python scripts/arm9_table_scanner.py \
    --arm9 jus_files/ripped_jus_files/ftc/arm9.bin \
    --output jus_files/analysis/ \
    --map-regions

# Parse cheat codes to extract known addresses
python scripts/cheat_code_parser.py --builtin --output jus_files/analysis/cheat_addresses.json
```

### 2. Dynamic: Watch Memory with melonDS + GDB (Mac/Linux)

```bash
# Terminal 1: Start melonDS with GDB enabled, load JUS ROM

# Terminal 2: Connect GDB with JUS watcher
arm-none-eabi-gdb -x scripts/gdb/jus_gdb_watcher.py

# In GDB:
(gdb) target remote localhost:3333
(gdb) jus-status           # Show battle values
(gdb) jus-watch-hp         # Set watchpoints on HP
(gdb) jus-watch-code       # Break at damage calculation
(gdb) continue             # Resume emulation
# Play - GDB will break when HP changes
(gdb) bt                   # Show call stack
(gdb) info registers       # Show CPU state
```

### 3. Ghidra: Analyze ARM9 Code

```bash
# Import ARM9.bin into Ghidra
# Set Language: ARM:LE:32:v5t
# Base Address: 0x02000000

# After GDB breaks at interesting code, find it in Ghidra:
# Go to address shown in GDB (e.g., 0x020784FC)
# Analyze surrounding functions
```

### 4. AI: Analyze Unknown Function

```
# Copy disassembly from Ghidra, paste to Claude:
"Here's ARM assembly from JUS at 0x020784F0.
This function is called when HP changes (from GDB watchpoint).
Decompile to C and explain what it does."
```

---

## Resources

### Documentation
- [Starcube Labs - RE DS Games](https://www.starcubelabs.com/reverse-engineering-ds/)
- [TASVideos Lua Scripting](https://tasvideos.org/LuaScripting)
- [LLM4Decompile](https://github.com/albertan017/LLM4Decompile)
- [decomp.me](https://decomp.me) - Collaborative matching decompilation

### Communities
- [GBAtemp](https://gbatemp.net/) - DS hacking community
- [Retro Reversing](https://www.retroreversing.com/ds) - NDS RE resources
- [decomp.me Discord](https://discord.gg/decomp) - Decomp community

---

## Next Steps

1. **Immediate**: Create `arm9_table_scanner.py` to find more tables
2. **Short-term**: Set up DeSmuME Lua environment and test RAM watching
3. **Medium-term**: Map damage calculation path from 0x020784FC
4. **Long-term**: Build cross-reference database of all discovered addresses
