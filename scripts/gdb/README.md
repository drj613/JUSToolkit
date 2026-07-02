# JUS GDB Watcher

Memory analysis tools for reverse engineering Jump Ultimate Stars using
melonDS + GDB.

**Platform:** Mac, Linux (Windows users can use this too, or use DeSmuME Lua
instead)

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

| Command            | Description                                     |
| ------------------ | ----------------------------------------------- |
| `jus-status`       | Show current battle state (HP, timer, special)  |
| `jus-check-hp`     | Show HP for you and opponent (active + deck)    |
| `jus-find-hp <n>`  | Search memory for HP value (to find addresses)  |
| `jus-addresses`    | List all known memory addresses                 |
| `jus-read-char N`  | Read player N's character state struct          |

### Watchpoints & Breakpoints

| Command                | Description                                        |
| ---------------------- | -------------------------------------------------- |
| `jus-watch-hp`         | Set watchpoints on all player HP addresses         |
| `jus-watch-code`       | Set breakpoint at health calculation function      |
| `jus-trace <addr> on`  | Log function calls at address with register values |
| `jus-trace <addr> off` | Stop tracing                                       |

### Memory Analysis

| Command                          | Description                                              |
| -------------------------------- | -------------------------------------------------------- |
| `jus-dump <start> <end> <file>`  | Dump memory region to file                               |
| `jus-scan <start> <end> <value>` | Search for byte value in range                           |
| `jus-snapshot <name> [region]`   | Save memory snapshot (regions: `battle`, `char`, `full`) |
| `jus-diff <snap1> <snap2\|now>`  | Compare two snapshots or snapshot vs current             |
| `jus-bt`                         | Backtrace with ARM9 offset translation                   |

### Hitstun/Velocity Research

| Command                                    | Description                                           |
| ------------------------------------------ | ----------------------------------------------------- |
| `jus-char-dump [player] [offset] [length]` | Dump character struct bytes with annotations          |
| `jus-char-snapshot <name> [player]`        | Save character struct snapshot                        |
| `jus-char-diff <snap1> <snap2\|now>`       | Compare char struct snapshots (find velocity/hitstun) |
| `jus-char-values <snap> [start] [end]`     | Show actual values in snapshot (not just diffs)       |
| `jus-compare-field <off> <snaps...>`       | Compare one field across multiple snapshots           |
| `jus-velocity-watch [player]`              | Show physics region values                            |

### Automated Triggers

The main working command for automatic capture:

| Command                                                | Description                                |
| ------------------------------------------------------ | ------------------------------------------ |
| `jus-auto-snapshot-on-damage <target> [prefix]`        | Capture when HP decreases (WORKS!)         |
| `jus-auto-snapshot-off`                                | Disable all auto-triggers + show summary   |

**Target options:**

| Target              | Description                        |
| ------------------- | ---------------------------------- |
| `me` / `player` / `1` | Your active character            |
| `2-4`               | Your deck members (supports)       |
| `opp` / `enemy` / `o1` | Opponent's active character     |
| `o2-o4`             | Opponent's deck members            |

**Examples:**

```gdb
jus-auto-snapshot-on-damage me goku       # Track damage to your character
jus-auto-snapshot-on-damage opp enemy     # Track damage to opponent
```

**Important notes:**

- HP is stored at **1/4 scale** (160 displayed HP = 40 stored)
- The damage code fires constantly during idle, but the command filters to only
  capture when HP actually decreases.
- Use `jus-check-hp` to see current HP values for both sides.

**Broken with melonDS** (these use hardware watchpoints which melonDS doesn't support):

| Command                         | Status                          |
| ------------------------------- | ------------------------------- |
| `jus-auto-snapshot-on-hit`      | ❌ Uses watchpoints, fails      |
| `jus-auto-snapshot-on-state`    | ❌ Uses watchpoints, fails      |
| `jus-auto-snapshot-on-status`   | ❌ Uses watchpoints, fails      |

### Manual Capture Commands

These require manual continue/Ctrl+C between captures (stepi doesn't work with melonDS):

| Command                                         | Description                    |
| ----------------------------------------------- | ------------------------------ |
| `jus-burst-snapshot <count> <prefix> [player]`  | Capture one, then c/Ctrl+C     |
| `jus-baseline-noise <player> [count] [prefix]`  | Capture one, then c/Ctrl+C     |

### Velocity Logging (Lightweight Alternative)

Instead of capturing full 288-byte snapshots, you can log just the physics
region values:

| Command                          | Description                              |
| -------------------------------- | ---------------------------------------- |
| `jus-velocity-log <player> [file]` | Log physics offsets when HP decreases  |
| `jus-velocity-show [last_n]`     | Show velocity log entries                |
| `jus-velocity-clear`             | Clear velocity log                       |

This logs offsets 0x006A-0x007E (likely velocity), 0x0078 (ground/air state),
and 0x0098-0x009A (timer region) each time damage is taken.

### Snapshot Management

| Command                      | Description                              |
| ---------------------------- | ---------------------------------------- |
| `jus-snapshot-list [prefix]` | List all snapshots with metadata         |

### Noise Filtering

Before analyzing combat data, capture baseline "noise" to identify timer fields:

| Command                                              | Description                                |
| ---------------------------------------------------- | ------------------------------------------ |
| `jus-baseline-noise <player> [count] [prefix] [steps]` | Capture idle state (stepi-based)         |
| `jus-baseline-timed <player> [count] [prefix]`       | Capture idle state (continue-based)        |
| `jus-find-timers <prefix>`                           | Identify always-changing fields (timers)   |

Fields that change during idle time are timers/counters - **not** physics data.
After running `jus-find-timers`, these offsets are marked `[TIMER - ignore]` in
diff output.

**Note:** `jus-baseline-noise` uses `stepi` (default 500,000 steps) between
snapshots. If timers don't change, increase steps or use `jus-baseline-timed`
which uses `continue` for more realistic timing (requires manual Ctrl+C).

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

### FIRST: Capture Baseline Noise (Recommended!)

Before analyzing combat data, identify timer fields that always change:

```gdb
# Start battle, have both characters STAND STILL
(gdb) jus-baseline-noise 1 5 idle
# Takes 5 snapshots: idle_0, idle_1, ..., idle_4

# Analyze which fields change during idle time
(gdb) jus-find-timers idle
# Output shows always-changing fields (these are timers, not physics)
# Example:
#   +0012: 1234 -> 1235 -> 1236 ...  (frame counter)
#   +0054: 100 -> 99 -> 98 ...       (animation timer)

# Now these fields will be marked [TIMER - ignore] in future diffs!
```

**Known limitation:** The baseline-noise command uses `stepi 5000` between
snapshots, which may not advance enough game time to see timer changes. If you
get "none found", the snapshots were taken too quickly. Alternative: use
jus-auto-snapshot-on-damage and capture during idle time (the damage code fires
periodically even without combat).

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
# Timer fields from baseline are marked [TIMER - ignore]
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

### Using Automated Triggers (Recommended!)

The manual Ctrl+C approach has a focus problem - you can't control the game AND
the terminal simultaneously. Use the damage-based trigger instead:

```gdb
# Connect and get into a battle first
(gdb) target remote localhost:3333
(gdb) continue
# ... start a 1v1 battle, then Ctrl+C to set up triggers ...

# Track when YOU take damage
(gdb) jus-auto-snapshot-on-damage me mychar
(gdb) continue

# ... play the game, get hit multiple times ...
# Snapshots are captured automatically in background!
# You'll see: [AUTO] Snapshot 'mychar_dmg1' captured (player_active HP: 160 -> 148, dmg: 12)

# When done, Ctrl+C to analyze
(gdb) jus-auto-snapshot-off
(gdb) jus-char-diff mychar_dmg1 mychar_dmg2
```

### Tracking Opponent Damage

```gdb
# Track when OPPONENT takes damage
(gdb) jus-auto-snapshot-on-damage opp enemy
(gdb) continue

# ... attack the opponent ...
# You'll see: [AUTO] Snapshot 'enemy_dmg1' captured (opponent_active HP: 160 -> 140, dmg: 20)

(gdb) jus-auto-snapshot-off
```

### Burst Snapshots for Movement Analysis

```gdb
# Capture sequence during movement (manual continue/Ctrl+C between each)
(gdb) jus-burst-snapshot 5 walking 1
# Captured: walking_0 (1/5)
(gdb) c
# (wait, Ctrl+C)
(gdb) jus-burst-snapshot 5 walking 1
# Captured: walking_1 (2/5)
# ... repeat ...

(gdb) jus-char-diff walking_0 walking_4
# See position/velocity change over time
```

## Known Addresses

### Deck Builder State

| Address      | Size | Description                                       |
| ------------ | ---- | ------------------------------------------------- |
| `0x020A0C98` | 1    | Deck state flag (0x05=has leader, 0x07=no leader) |
| `0x020A2289` | 1    | Leader boolean (1=leader set, 0=no leader)        |
| `0x020A4368` | 4    | Pointer to leader koma data (0 if no leader)      |
| `0x020AFEB4` | 4    | Active deck slot index (0-7)                      |
| `0x020B9480` | -    | Koma master table (sequential 4-byte IDs)         |

### Battle State (RAM)

| Address      | Size | Description     |
| ------------ | ---- | --------------- |
| `0x021DEA71` | 1    | Battle timer    |
| `0x021DF731` | 1    | Special meter 1 |

### HP Addresses

HP is stored at **1/4 scale** (160 displayed = 40 stored).

**Your side:**

| Address      | Description                    |
| ------------ | ------------------------------ |
| `0x021DF1D5` | Your active character HP       |
| `0x021DF225` | Your deck slot 1 (support/tagged out) |
| `0x021DF275` | Your deck slot 2               |
| `0x021DF2C5` | Your deck slot 3               |

**Opponent side** (0x61C offset from your side):

| Address      | Description                    |
| ------------ | ------------------------------ |
| `0x021DF7F1` | Opponent active character HP   |
| `0x021DF841` | Opponent deck slot 1           |
| `0x021DF891` | Opponent deck slot 2           |
| `0x021DF8E1` | Opponent deck slot 3           |

Deck slots are spaced 0x50 apart. Use `jus-check-hp` to see all values at once.

### Character State Struct (offsets from pointer)

**Confirmed offsets (from Action Replay codes + GDB testing 2026-02-03):**

| Offset    | Description                                        |
| --------- | -------------------------------------------------- |
| `+0x0078` | Ground/Air state (0=air, 0x22=ground, **0xC0=LAUNCHED/HITSTUN**) |
| `+0x0088` | Positive status ID                                 |
| `+0x00A0` | Negative status flags                              |
| `+0x00D9` | Jump counter                                       |
| `+0x00DA` | Air action counter                                 |
| `+0x0102` | Defense timer                                      |

**Timer region (discovered 2026-02-03):**

These fields decrement in a -5/-3 alternating pattern during hitstun/recovery.
They appear to be 32-bit countdown timers read as 16-bit pairs:

| Offset Pair     | Description          |
| --------------- | -------------------- |
| `+0x0098/0x009A` | Timer pair 1        |
| `+0x00A0/0x00A2` | Timer pair 2 (overlaps negative_status) |
| `+0x00A8/0x00AA` | Timer pair 3        |
| `+0x00B0/0x00B2` | Timer pair 4        |
| `+0x00B8/0x00BA` | Timer pair 5        |

**Physics/combat data region:**

| Region        | Description                                       |
| ------------- | ------------------------------------------------- |
| `+0x006A-0x007C` | Shows large deltas during knockback - possible velocity |
| `+0x0070-0x0092` | Near ground_air - state/physics data             |
| `+0x0098-0x00BA` | Timer region - countdown timers during hitstun   |

Total struct size: at least 0x120 bytes (~288 bytes)

### Code Hooks

| Address      | Description                 |
| ------------ | --------------------------- |
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

## Known Limitations

### Wifi Pointers Don't Work in Offline/Training Mode

The character state pointers (`player1_state_ptr` at `0x021E2A7C` etc.) were
extracted from **wifi mode** cheat codes and contain **invalid data** in
training or offline battle modes:

```
(gdb) x/1xw 0x021E2A7C
0x21e2a7c:  0xe8100842   # NOT a valid 0x02xxxxxx pointer
```

This means `jus-read-char`, `jus-char-snapshot`, and other commands that use
these pointers will fail to capture meaningful data in offline modes.

**Investigation Status (JUS-98z):**

**SOLUTION FOUND (2026-02-03):**

The working pointer chain for offline/training mode is:
```
0x023D2A74 (alt_state_base) -> read dword -> +0x10 -> character struct
```

**Recommended commands:**

| Command                          | Description                              |
| -------------------------------- | ---------------------------------------- |
| `jus-read-char-offline`          | Read char state using working pointer chain |
| `jus-snapshot-offline <name>`    | Take snapshot using working pointer chain |
| `jus-snapshot-at <name> <addr>`  | Take snapshot from direct address        |

**Example workflow for offline mode:**
```gdb
(gdb) jus-read-char-offline           # View current state
(gdb) jus-snapshot-offline standing   # Take snapshot while standing
(gdb) c
# (jump, Ctrl+C while in air)
(gdb) jus-snapshot-offline jumping    # Take snapshot while jumping
(gdb) jus-char-diff standing jumping  # Compare the two
```

### Opponent State Pointer (JUS-nqp)

**SOLUTION FOUND (2026-02-03):**

The opponent uses a **different pointer chain** than the player:

```
PLAYER:   0x023D2A74 -> intermediate -> +0x10 -> player struct
OPPONENT: 0x023D2A74 -> intermediate -> +0x00 -> ptr -> +0x10 -> opponent struct
```

The intermediate structure at `alt_state_base` contains:
- `+0x00`: Pointer to another struct (follow +0x10 for opponent)
- `+0x10`: Direct pointer to player struct

**Opponent commands:**

| Command                        | Description                              |
| ------------------------------ | ---------------------------------------- |
| `jus-read-opponent`            | Read opponent state using pointer chain  |
| `jus-snapshot-opponent <name>` | Take opponent snapshot                   |

**Example workflow for analyzing opponent:**
```gdb
(gdb) jus-read-opponent                # View opponent's current state
(gdb) jus-snapshot-opponent opp_idle   # Snapshot while opponent idle
(gdb) c
# (opponent jumps, Ctrl+C while in air)
(gdb) jus-snapshot-opponent opp_jump   # Snapshot while opponent jumping
(gdb) jus-char-diff opp_idle opp_jump  # Compare states
```

**Ground/Air state values (updated):**

| Value  | State              |
| ------ | ------------------ |
| `0x00` | Air (jumping/rising) |
| `0x02` | Fast fall (down+jump in air) |
| `0x22` | Ground             |
| `0xC0` | Launched/Hitstun   |

### Hardware Watchpoints Not Supported

The melonDS GDB stub does not properly support hardware watchpoints. Commands
that use watchpoints (`jus-auto-snapshot-on-hit`, `jus-auto-snapshot-on-state`,
`jus-auto-snapshot-on-status`) will fail with errors like:

```
Hardware watchpoint 1: *0x21dea71
Python Exception <class 'RuntimeError'>: Breakpoint 0 is invalid.
```

**Workaround:** Use `jus-auto-snapshot-on-damage` instead, which uses a regular
breakpoint at the damage calculation function.

### stepi Doesn't Work Reliably

The melonDS GDB stub crashes or hangs when executing large `stepi` counts. The
`jus-baseline-noise` and `jus-burst-snapshot` commands now require manual
continue/Ctrl+C between captures instead of automatic stepping.

### HP Memory Layout

The battle has separate addresses for **active characters** (currently fighting)
and **deck slots** (supports, tagged out characters):

- **Your active** + **Your deck 1-3**: Starting at `0x021DF1D5`, spaced 0x50 apart
- **Opponent active** + **Opponent deck 1-3**: Starting at `0x021DF7F1`, spaced 0x50 apart
- **Offset between sides**: 0x61C (1564 bytes)

HP values are stored at **1/4 of displayed value**:
- 160 HP displayed = 40 stored
- 128 HP displayed = 32 stored

Use `jus-check-hp` to see all HP values, or `jus-find-hp <value>` to search for
specific HP values in memory.

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
- `scripts/archive/jus_watcher.lua` - Archived alternative for Windows/DeSmuME users (superseded by this GDB watcher)
