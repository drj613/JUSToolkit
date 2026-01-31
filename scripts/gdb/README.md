# JUS GDB Watcher

Memory analysis tools for reverse engineering Jump Ultimate Stars using melonDS + GDB.

**Platform:** Mac, Linux (Windows users can use this too, or use DeSmuME Lua instead)

## Prerequisites

### macOS
```bash
brew install melonds arm-none-eabi-gdb
# Or build melonDS from source with GDB enabled (see below)
```

### Linux
```bash
sudo apt install melonds gdb-multiarch
# Use gdb-multiarch instead of arm-none-eabi-gdb
```

### Building melonDS with GDB Support

If your melonDS build doesn't have GDB support:

```bash
git clone https://github.com/melonDS-emu/melonDS
cd melonDS
mkdir build && cd build
cmake .. -DENABLE_GDB_STUB=ON
make -j$(nproc)
```

## Setup

### 1. Configure melonDS

Open melonDS, go to **Config → Emu Settings → Devtools**:
- ☑ Enable GDB stub
- ARM9 Port: `3333`
- ARM7 Port: `3334`

Or edit `~/.config/melonDS/melonDS.ini`:
```ini
[Gdb]
Enabled=true

[Gdb.ARM9]
Port=3333
BreakOnStartup=false
```

### 2. Load ROM

Start melonDS and load the JUS ROM. The game will run normally.

### 3. Connect GDB

```bash
# From the JUSToolkit directory
arm-none-eabi-gdb -x scripts/gdb/jus_gdb_watcher.py

# Or on Linux with gdb-multiarch
gdb-multiarch -x scripts/gdb/jus_gdb_watcher.py
```

Then in GDB:
```gdb
(gdb) target remote localhost:3333
```

The emulator will pause. Use `continue` to resume.

## Commands

### Basic Status

| Command | Description |
|---------|-------------|
| `jus-status` | Show current battle state (HP, timer, special) |
| `jus-addresses` | List all known memory addresses |
| `jus-read-char N` | Read player N's character state struct |

### Watchpoints & Breakpoints

| Command | Description |
|---------|-------------|
| `jus-watch-hp` | Set watchpoints on all player HP addresses |
| `jus-watch-code` | Set breakpoint at health calculation function |
| `jus-trace <addr> on` | Log function calls at address with register values |
| `jus-trace <addr> off` | Stop tracing |

### Memory Analysis

| Command | Description |
|---------|-------------|
| `jus-dump <start> <end> <file>` | Dump memory region to file |
| `jus-scan <start> <end> <value>` | Search for byte value in range |
| `jus-snapshot <name> [region]` | Save memory snapshot (regions: `battle`, `char`, `full`) |
| `jus-diff <snap1> <snap2\|now>` | Compare two snapshots or snapshot vs current |
| `jus-bt` | Backtrace with ARM9 offset translation |

### Hitstun/Velocity Research

| Command | Description |
|---------|-------------|
| `jus-char-dump [player] [offset] [length]` | Dump character struct bytes with annotations |
| `jus-char-snapshot <name> [player]` | Save character struct snapshot |
| `jus-char-diff <snap1> <snap2\|now>` | Compare char struct snapshots (find velocity/hitstun) |
| `jus-velocity-watch [player]` | Show physics region values |

### Binary Dump Scripts

For detailed analysis, use the standalone GDB scripts:

```gdb
# Dump deck builder memory to /tmp/jus_dumps/
source scripts/gdb/dump_deck_binary.gdb

# Dump to named subdirectories for comparison
source scripts/gdb/dump_deck_named.gdb
dump-state1    # saves to /tmp/jus_dumps/state1/
dump-state2    # saves to /tmp/jus_dumps/state2/
```

Then analyze with Python:
```bash
python scripts/analyze_deck_dump.py --dir /tmp/jus_dumps/state1
python scripts/analyze_deck_dump.py --diff /tmp/jus_dumps/state1/deck_0a1000.bin /tmp/jus_dumps/state2/deck_0a1000.bin
```

## Workflows

### Finding What Changes During an Attack

```gdb
(gdb) target remote localhost:3333
(gdb) continue
# Start a battle in-game, then Ctrl+C to pause

(gdb) jus-snapshot before
# Resume, do ONE attack, Ctrl+C again
(gdb) continue
# ... do attack ...
# Ctrl+C

(gdb) jus-diff before now
# Shows all bytes that changed
```

### Tracing Damage Calculation

```gdb
(gdb) jus-watch-hp
(gdb) continue
# Attack an enemy, GDB breaks when HP changes

(gdb) jus-bt          # See call stack
(gdb) info registers  # See CPU state
(gdb) x/20i $pc-20    # Disassemble nearby code
```

### Logging Function Calls

```gdb
# Log every call to health code with arguments
(gdb) jus-trace 0x020784FC on
(gdb) continue

# Output shows R0-R3 (function arguments) and LR (return address)
# TRACE 0x020784fc: R0=021df1a0 R1=0000000a R2=00000002 R3=00000000 LR=0207a234
```

### Finding Velocity/Position Fields

```gdb
(gdb) target remote localhost:3333
(gdb) continue
# Start a battle, have character stand still, Ctrl+C

(gdb) jus-char-snapshot idle 1
# Resume, have character walk right, Ctrl+C
(gdb) continue
# Ctrl+C when walking

(gdb) jus-char-snapshot walking 1
(gdb) jus-char-diff idle walking
# Fields that changed are likely velocity X or position X
```

### Finding Hitstun/Knockback Fields

```gdb
# Start battle, position characters, Ctrl+C before getting hit
(gdb) jus-char-snapshot before_hit 1
(gdb) continue
# Get hit with a known attack (light vs heavy)
# Ctrl+C while in hitstun

(gdb) jus-char-snapshot in_hitstun 1
(gdb) jus-char-diff before_hit in_hitstun
# Look for:
#   - Velocity fields (large signed values ~100-500)
#   - Hitstun timer (countdown values 5-15 for light, 10-30 for heavy)
```

### Comparing Weight Classes

```gdb
# Test same attack on different weight characters
# Raoh (heavy) vs Lenalee (light)

# 1. Set up: Raoh gets hit by Goku's B
(gdb) jus-char-snapshot raoh_before 1
(gdb) continue
# ... get hit ...
(gdb) jus-char-snapshot raoh_hit 1
(gdb) jus-char-diff raoh_before raoh_hit

# 2. Set up: Lenalee gets hit by same attack
(gdb) jus-char-snapshot lenalee_before 1
(gdb) continue
# ... get hit ...
(gdb) jus-char-snapshot lenalee_hit 1
(gdb) jus-char-diff lenalee_before lenalee_hit

# Compare velocity values - Lenalee should have higher knockback velocity
```

## Known Addresses

### Deck Builder State
| Address | Size | Description |
|---------|------|-------------|
| `0x020A0C98` | 1 | Deck state flag (0x05=has leader, 0x07=no leader) |
| `0x020A2289` | 1 | Leader boolean (1=leader set, 0=no leader) |
| `0x020A4368` | 4 | Pointer to leader koma data (0 if no leader) |
| `0x020AFEB4` | 4 | Active deck slot index (0-7) |
| `0x020B9480` | - | Koma master table (sequential 4-byte IDs) |

### Battle State (RAM)
| Address | Size | Description |
|---------|------|-------------|
| `0x021DEA71` | 1 | Battle timer |
| `0x021DF1D5` | 1 | Player 1 HP |
| `0x021DF225` | 1 | Player 2 HP |
| `0x021DF731` | 1 | Special meter 1 |

### Character State Struct (offsets from pointer)

**Confirmed offsets (from Action Replay codes):**

| Offset | Description |
|--------|-------------|
| `+0x0078` | Ground/Air state (0=air, 0x22=ground) |
| `+0x0088` | Positive status ID |
| `+0x00A0` | Negative status flags |
| `+0x00D9` | Jump counter |
| `+0x00DA` | Air action counter |
| `+0x0102` | Defense timer |

**Candidate regions for velocity/hitstun (to be verified):**

| Region | Description |
|--------|-------------|
| `+0x00-0x40` | Physics region - likely X/Y position and velocity |
| `+0x70-0x88` | Near ground_air - possibly fall velocity |
| `+0xA0-0xD9` | Large gap - combat state, hitstun timer? |
| `+0xF0-0x110` | Near defense_timer - stun timer? |

Total struct size: at least 0x120 bytes (~288 bytes)

### Code Hooks
| Address | Description |
|---------|-------------|
| `0x020784FC` | Health calculation function |

## Tips

- **Ctrl+C** in GDB pauses the emulator
- **continue** (or just `c`) resumes
- **stepi** steps one ARM instruction
- **x/10i $pc** disassembles 10 instructions at current position
- Snapshots use regions to avoid dumping all 4MB of RAM:
  - `battle` = `0x021D0000-0x02200000` (battle state, default)
  - `deck` = `0x020A0000-0x020C0000` (deck builder, menu state)
  - `save` = `0x020B0000-0x020C0000` (currency, unlocks)
  - `koma` = `0x02280000-0x022A0000` (koma holder during deck building)
  - `char` = `0x021DF000-0x021E0000` (character data in-battle)
  - `full` = `0x02000000-0x02400000` (all main RAM, slow)

## Troubleshooting

**"Connection refused"**
- Make sure melonDS GDB stub is enabled
- Check the port number (default 3333)
- Try restarting melonDS

**"Remote connection closed"**
- melonDS may have crashed or closed
- Try a different ARM9 port in melonDS settings

**GDB hangs on connect**
- The ROM might not be loaded yet in melonDS
- Load the ROM first, then connect GDB

## See Also

- `docs/design/ARM9-Analysis-Pipeline.md` - Full analysis pipeline documentation
- `docs/research/Cheat-Code-Analysis.md` - Memory addresses from cheat codes
- `scripts/desmume/jus_watcher.lua` - Alternative for Windows/DeSmuME users
