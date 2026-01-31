"""
JUS GDB Watcher - Memory analysis script for GDB + melonDS

This script runs inside GDB's Python environment to monitor
Jump Ultimate Stars memory during gameplay.

Usage:
    1. Start melonDS with GDB stub enabled (port 3333)
    2. Load JUS ROM
    3. Connect GDB: arm-none-eabi-gdb -x jus_gdb_watcher.py

Or from GDB prompt:
    (gdb) source jus_gdb_watcher.py
    (gdb) jus-status
    (gdb) jus-watch-hp
"""

import gdb
import struct

# ============================================================================
# KNOWN ADDRESSES (from Action Replay codes)
# ============================================================================

ADDRESSES = {
    # Battle state
    'battle_timer': 0x021DEA71,
    'battle_timer_wifi': 0x021E29B0,

    # Player HP (spaced 0x50 apart)
    'player1_hp': 0x021DF1D5,
    'player2_hp': 0x021DF225,
    'player3_hp': 0x021DF275,
    'player4_hp': 0x021DF2C5,

    # Special meter
    'special_1': 0x021DF731,
    'special_2': 0x021DF8B1,

    # Player state pointers (wifi)
    'player1_state_ptr': 0x021E2A7C,
    'player2_state_ptr': 0x021E2A80,
    'player3_state_ptr': 0x021E2A84,
    'player4_state_ptr': 0x021E2A88,

    # ARM9 code hooks
    'health_code': 0x020784FC,

    # Save/progress
    'koma_points': 0x020B76C8,
    'gems': 0x020B7718,
    'active_deck': 0x020AFEB4,
}

# Character state struct offsets (from pointer)
# These are CONFIRMED from Action Replay code analysis
CHAR_OFFSETS = {
    'ground_air': 0x0078,      # 0x00=air, 0x22=ground
    'positive_status': 0x0088,
    'negative_status': 0x00A0,
    'jump_count': 0x00D9,
    'air_actions': 0x00DA,
    'defense_timer': 0x0102,
}

# Candidate offsets for velocity/hitstun (TO BE VERIFIED)
# Gaps in known offsets suggest physics data may be nearby:
#   - 0x00-0x77: Unknown (likely position, velocity)
#   - 0x79-0x87: Unknown (near ground_air)
#   - 0x89-0x9F: Unknown (between status fields)
#   - 0xA1-0xD8: Unknown (large gap - likely combat state)
#   - 0xDB-0x101: Unknown (between air_actions and defense)
# Total struct size: at least 0x102+ bytes (~260+ bytes)
VELOCITY_CANDIDATES = {
    # Likely position/velocity region (start of struct)
    'region_physics': (0x00, 0x40),      # First 64 bytes - likely X/Y pos/vel
    # Near ground/air state - might have fall velocity
    'region_air_physics': (0x70, 0x88),  # Around ground_air offset
    # Between status and jump - might have hitstun timer
    'region_combat_state': (0xA0, 0xD9), # Large unknown region
    # Near defense timer - might have stun timer
    'region_timers': (0xF0, 0x110),      # Around defense_timer
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def read_byte(addr):
    """Read a single byte from memory."""
    try:
        inferior = gdb.selected_inferior()
        mem = inferior.read_memory(addr, 1)
        return struct.unpack('B', mem)[0]
    except gdb.MemoryError:
        return None

def read_word(addr):
    """Read a 16-bit word from memory (little-endian)."""
    try:
        inferior = gdb.selected_inferior()
        mem = inferior.read_memory(addr, 2)
        return struct.unpack('<H', mem)[0]
    except gdb.MemoryError:
        return None

def read_dword(addr):
    """Read a 32-bit dword from memory (little-endian)."""
    try:
        inferior = gdb.selected_inferior()
        mem = inferior.read_memory(addr, 4)
        return struct.unpack('<I', mem)[0]
    except gdb.MemoryError:
        return None

def read_bytes(addr, count):
    """Read multiple bytes from memory."""
    try:
        inferior = gdb.selected_inferior()
        mem = inferior.read_memory(addr, count)
        return bytes(mem)
    except gdb.MemoryError:
        return None


# ============================================================================
# GDB COMMANDS
# ============================================================================

class JUSStatus(gdb.Command):
    """Show current JUS battle state."""

    def __init__(self):
        super().__init__("jus-status", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        print("=== JUS Battle Status ===")

        timer = read_byte(ADDRESSES['battle_timer'])
        print(f"Timer: {timer if timer else 'N/A'}")

        for i in range(1, 5):
            hp = read_byte(ADDRESSES[f'player{i}_hp'])
            if hp is not None and hp > 0:
                print(f"Player {i} HP: {hp}")

        sp1 = read_byte(ADDRESSES['special_1'])
        sp2 = read_byte(ADDRESSES['special_2'])
        if sp1 is not None:
            print(f"Special: {sp1} / {sp2}")

        print()


class JUSWatchHP(gdb.Command):
    """Set watchpoints on all HP addresses."""

    def __init__(self):
        super().__init__("jus-watch-hp", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        for i in range(1, 5):
            addr = ADDRESSES[f'player{i}_hp']
            gdb.execute(f"watch *{addr:#x}")
            print(f"Watching Player {i} HP at {addr:#010x}")


class JUSWatchCode(gdb.Command):
    """Set breakpoint at health calculation code."""

    def __init__(self):
        super().__init__("jus-watch-code", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        addr = ADDRESSES['health_code']
        gdb.execute(f"break *{addr:#x}")
        print(f"Breakpoint set at health code: {addr:#010x}")


class JUSReadChar(gdb.Command):
    """Read character state from pointer (wifi mode)."""

    def __init__(self):
        super().__init__("jus-read-char", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        player = int(arg) if arg else 1
        if player < 1 or player > 4:
            print("Usage: jus-read-char [1-4]")
            return

        ptr_addr = ADDRESSES[f'player{player}_state_ptr']
        ptr = read_dword(ptr_addr)

        if not ptr or ptr < 0x02000000:
            print(f"Player {player} state pointer invalid: {ptr:#010x if ptr else 'NULL'}")
            return

        print(f"=== Player {player} Character State ===")
        print(f"Pointer: {ptr:#010x}")

        for name, offset in CHAR_OFFSETS.items():
            value = read_byte(ptr + offset)
            if value is not None:
                print(f"  {name} (0x{offset:04X}): {value} (0x{value:02X})")


class JUSDump(gdb.Command):
    """Dump memory region to file."""

    def __init__(self):
        super().__init__("jus-dump", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if len(args) < 3:
            print("Usage: jus-dump <start_addr> <end_addr> <filename>")
            print("Example: jus-dump 0x021DF000 0x021E0000 battle_state.bin")
            return

        start = int(args[0], 0)
        end = int(args[1], 0)
        filename = args[2]

        data = read_bytes(start, end - start)
        if data:
            with open(filename, 'wb') as f:
                f.write(data)
            print(f"Dumped {len(data)} bytes to {filename}")
        else:
            print("Failed to read memory")


class JUSScan(gdb.Command):
    """Scan memory range for a byte value."""

    def __init__(self):
        super().__init__("jus-scan", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if len(args) < 3:
            print("Usage: jus-scan <start_addr> <end_addr> <value>")
            print("Example: jus-scan 0x021D0000 0x02200000 100")
            return

        start = int(args[0], 0)
        end = int(args[1], 0)
        target = int(args[2], 0)

        print(f"Scanning {start:#010x} - {end:#010x} for value {target}...")

        results = []
        chunk_size = 0x1000

        for chunk_start in range(start, end, chunk_size):
            chunk_end = min(chunk_start + chunk_size, end)
            data = read_bytes(chunk_start, chunk_end - chunk_start)

            if data:
                for i, b in enumerate(data):
                    if b == target:
                        results.append(chunk_start + i)

        print(f"Found {len(results)} matches:")
        for addr in results[:20]:
            print(f"  {addr:#010x}")
        if len(results) > 20:
            print(f"  ... and {len(results) - 20} more")


class JUSAddresses(gdb.Command):
    """List all known JUS addresses."""

    def __init__(self):
        super().__init__("jus-addresses", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        print("=== Known JUS Addresses ===")
        for name, addr in sorted(ADDRESSES.items(), key=lambda x: x[1]):
            print(f"  {addr:#010x}  {name}")

        print("\n=== Character State Offsets (from pointer) ===")
        for name, offset in sorted(CHAR_OFFSETS.items(), key=lambda x: x[1]):
            print(f"  +0x{offset:04X}  {name}")


# Storage for memory snapshots
_snapshots = {}


class JUSSnapshot(gdb.Command):
    """Take a named memory snapshot for later diffing.

    Usage: jus-snapshot <name> [region]
    Regions: battle (default), deck, save, char, full
    """

    REGIONS = {
        'battle': (0x021D0000, 0x02200000),   # Battle state RAM
        'deck':   (0x020A0000, 0x020C0000),   # Deck builder, unlocks, menu state
        'save':   (0x020B0000, 0x020C0000),   # Save data, currency, unlocks
        'koma':   (0x02280000, 0x022A0000),   # Koma holder, deck construction
        'char':   (0x021DF000, 0x021E0000),   # Character data (in-battle)
        'full':   (0x02000000, 0x02400000),   # All main RAM (slow!)
    }

    def __init__(self):
        super().__init__("jus-snapshot", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-snapshot <name> [region]")
            print("       jus-snapshot <name> <start_addr> <end_addr>")
            print(f"Regions: {list(self.REGIONS.keys())}")
            print("Stored snapshots:", list(_snapshots.keys()))
            return

        name = args[0]

        # Check if custom range provided (two hex addresses)
        if len(args) >= 3:
            try:
                start = int(args[1], 0)
                end = int(args[2], 0)
                region = 'custom'
            except ValueError:
                print("Invalid address format. Use hex like 0x020A0000")
                return
        else:
            region = args[1] if len(args) > 1 else 'battle'
            if region not in self.REGIONS:
                print(f"Unknown region: {region}")
                print(f"Available: {list(self.REGIONS.keys())}")
                print("Or specify custom range: jus-snapshot <name> <start> <end>")
                return
            start, end = self.REGIONS[region]

        size = end - start
        print(f"Taking snapshot '{name}' of {region} ({start:#x}-{end:#x}, {size:,} bytes)...")

        data = read_bytes(start, end - start)
        if data:
            _snapshots[name] = {
                'data': data,
                'start': start,
                'end': end,
                'region': region,
            }
            print(f"Snapshot '{name}' saved ({len(data)} bytes)")
        else:
            print("Failed to read memory!")
            print("Possible causes:")
            print("  - Connection to melonDS lost (try: info target)")
            print("  - Memory region not mapped (try smaller range)")
            print("  - Emulator paused in wrong state")
            print(f"Try: x/4xb {start:#x}  (to test if address is readable)")


class JUSDiff(gdb.Command):
    """Compare two snapshots and show differences.

    Usage: jus-diff <snapshot1> <snapshot2>
    """

    def __init__(self):
        super().__init__("jus-diff", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if len(args) < 2:
            print("Usage: jus-diff <snapshot1> <snapshot2>")
            print("Or: jus-diff <snapshot1> now")
            print("Stored snapshots:", list(_snapshots.keys()))
            return

        name1, name2 = args[0], args[1]

        if name1 not in _snapshots:
            print(f"Snapshot '{name1}' not found")
            return

        snap1 = _snapshots[name1]

        if name2 == 'now':
            # Compare to current memory
            data2 = read_bytes(snap1['start'], snap1['end'] - snap1['start'])
            if not data2:
                print("Failed to read current memory")
                return
        elif name2 in _snapshots:
            snap2 = _snapshots[name2]
            if snap1['start'] != snap2['start']:
                print("Snapshots cover different regions")
                return
            data2 = snap2['data']
        else:
            print(f"Snapshot '{name2}' not found (use 'now' for current memory)")
            return

        data1 = snap1['data']
        start = snap1['start']

        # Find differences
        diffs = []
        for i in range(min(len(data1), len(data2))):
            if data1[i] != data2[i]:
                diffs.append((start + i, data1[i], data2[i]))

        print(f"=== Diff: {name1} vs {name2} ===")
        print(f"Total differences: {len(diffs)} bytes")

        if not diffs:
            print("No differences found")
            return

        # Group consecutive diffs
        groups = []
        current_group = [diffs[0]]

        for d in diffs[1:]:
            if d[0] == current_group[-1][0] + 1:
                current_group.append(d)
            else:
                groups.append(current_group)
                current_group = [d]
        groups.append(current_group)

        print(f"Changed regions: {len(groups)}")
        print()

        # Show first 20 groups
        for i, group in enumerate(groups[:20]):
            addr = group[0][0]
            size = len(group)

            # Check if this is a known address
            known = None
            for name, known_addr in ADDRESSES.items():
                if addr <= known_addr < addr + size:
                    known = f" <- {name}"
                    break

            old_bytes = ' '.join(f'{d[1]:02X}' for d in group[:8])
            new_bytes = ' '.join(f'{d[2]:02X}' for d in group[:8])

            if size > 8:
                old_bytes += ' ...'
                new_bytes += ' ...'

            print(f"{addr:#010x} ({size:3d} bytes){known or ''}")
            print(f"  Old: {old_bytes}")
            print(f"  New: {new_bytes}")

        if len(groups) > 20:
            print(f"\n... and {len(groups) - 20} more regions")


class JUSTrace(gdb.Command):
    """Start/stop logging function calls at an address.

    Usage: jus-trace <address> [on|off]
    """

    def __init__(self):
        super().__init__("jus-trace", gdb.COMMAND_USER)
        self._traces = {}

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-trace <address> [on|off]")
            print("Example: jus-trace 0x020784FC on")
            return

        addr = int(args[0], 0)
        action = args[1] if len(args) > 1 else 'on'

        if action == 'off':
            # Remove breakpoint
            if addr in self._traces:
                self._traces[addr].delete()
                del self._traces[addr]
                print(f"Trace disabled at {addr:#010x}")
            return

        # Create logging breakpoint
        bp = gdb.Breakpoint(f"*{addr:#x}")
        bp.silent = True
        bp.commands = f'''
printf "TRACE {addr:#010x}: R0=%08x R1=%08x R2=%08x R3=%08x LR=%08x\\n", $r0, $r1, $r2, $r3, $lr
continue
'''
        self._traces[addr] = bp
        print(f"Trace enabled at {addr:#010x} (logs R0-R3, LR)")


class JUSBacktrace(gdb.Command):
    """Show backtrace with ARM9 offset translation."""

    def __init__(self):
        super().__init__("jus-bt", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        print("=== Backtrace (ARM9 offsets) ===")
        frame = gdb.newest_frame()
        depth = 0

        while frame and depth < 20:
            pc = frame.pc()
            arm9_offset = pc - 0x02000000 if pc >= 0x02000000 else pc

            # Check if near known address
            nearest = None
            for name, addr in ADDRESSES.items():
                if abs(pc - addr) < 0x100:
                    nearest = f" (near {name})"
                    break

            print(f"  #{depth}: {pc:#010x} (ARM9: {arm9_offset:#08x}){nearest or ''}")

            try:
                frame = frame.older()
            except:
                break
            depth += 1


# ============================================================================
# HITSTUN/VELOCITY RESEARCH COMMANDS
# ============================================================================

# Storage for character struct snapshots
_char_snapshots = {}


class JUSCharDump(gdb.Command):
    """Dump character struct bytes for analysis.

    Usage: jus-char-dump [player] [start_offset] [length]
    Default: player 1, offset 0, length 0x120 (288 bytes)

    This dumps raw bytes from the character state struct to help
    identify unknown fields like velocity and hitstun timers.
    """

    def __init__(self):
        super().__init__("jus-char-dump", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        player = int(args[0]) if args else 1
        start_off = int(args[1], 0) if len(args) > 1 else 0
        length = int(args[2], 0) if len(args) > 2 else 0x120

        if player < 1 or player > 4:
            print("Usage: jus-char-dump [player 1-4] [start_offset] [length]")
            return

        ptr_addr = ADDRESSES[f'player{player}_state_ptr']
        ptr = read_dword(ptr_addr)

        if not ptr or ptr < 0x02000000:
            print(f"Player {player} state pointer invalid: {ptr:#010x if ptr else 'NULL'}")
            return

        print(f"=== Player {player} Character Struct Dump ===")
        print(f"Base pointer: {ptr:#010x}")
        print(f"Reading {length} bytes from offset {start_off:#04x}")
        print()

        data = read_bytes(ptr + start_off, length)
        if not data:
            print("Failed to read memory")
            return

        # Print hex dump with annotations
        for row_start in range(0, length, 16):
            addr = start_off + row_start
            row_data = data[row_start:row_start + 16]

            # Format hex bytes
            hex_str = ' '.join(f'{b:02X}' for b in row_data)
            if len(row_data) < 16:
                hex_str += '   ' * (16 - len(row_data))

            # Check for known offsets in this row
            annotation = ""
            for name, offset in CHAR_OFFSETS.items():
                if addr <= offset < addr + 16:
                    rel = offset - addr
                    annotation = f"  <- {name} at +{offset:#04x}"
                    break

            print(f"  +{addr:04X}: {hex_str}{annotation}")

        # Print any non-zero words that might be position/velocity
        print()
        print("=== Non-zero 16-bit values (potential position/velocity) ===")
        interesting = []
        for i in range(0, length - 1, 2):
            word = struct.unpack('<H', data[i:i+2])[0]
            if word != 0 and word != 0xFFFF:
                sword = struct.unpack('<h', data[i:i+2])[0]  # Signed
                interesting.append((start_off + i, word, sword))

        for offset, uval, sval in interesting[:30]:
            known = ""
            for name, off in CHAR_OFFSETS.items():
                if offset == off:
                    known = f" [{name}]"
                    break
            print(f"  +{offset:04X}: {uval:5d} (0x{uval:04X}) signed: {sval:6d}{known}")

        if len(interesting) > 30:
            print(f"  ... and {len(interesting) - 30} more")


class JUSCharSnapshot(gdb.Command):
    """Take a snapshot of character struct for diffing.

    Usage: jus-char-snapshot <name> [player]
    Default: player 1

    Use with jus-char-diff to find fields that change during combat.
    """

    def __init__(self):
        super().__init__("jus-char-snapshot", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-char-snapshot <name> [player 1-4]")
            print("Stored snapshots:", list(_char_snapshots.keys()))
            return

        name = args[0]
        player = int(args[1]) if len(args) > 1 else 1

        ptr_addr = ADDRESSES[f'player{player}_state_ptr']
        ptr = read_dword(ptr_addr)

        if not ptr or ptr < 0x02000000:
            print(f"Player {player} state pointer invalid")
            return

        # Read full character struct (280 bytes should cover it)
        data = read_bytes(ptr, 0x120)
        if data:
            _char_snapshots[name] = {
                'data': data,
                'ptr': ptr,
                'player': player,
            }
            print(f"Snapshot '{name}' saved (player {player}, {len(data)} bytes)")
        else:
            print("Failed to read character struct")


class JUSCharDiff(gdb.Command):
    """Compare character struct snapshots to find changing fields.

    Usage: jus-char-diff <snapshot1> <snapshot2|now>

    This helps identify velocity/hitstun fields by comparing
    snapshots taken at different game states:
    - Idle vs moving (find velocity fields)
    - Not hit vs in hitstun (find hitstun timer)
    - Different knockback amounts (find knockback velocity)
    """

    def __init__(self):
        super().__init__("jus-char-diff", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if len(args) < 2:
            print("Usage: jus-char-diff <snapshot1> <snapshot2|now>")
            print("Stored snapshots:", list(_char_snapshots.keys()))
            return

        name1, name2 = args[0], args[1]

        if name1 not in _char_snapshots:
            print(f"Snapshot '{name1}' not found")
            return

        snap1 = _char_snapshots[name1]

        if name2 == 'now':
            ptr_addr = ADDRESSES[f'player{snap1["player"]}_state_ptr']
            ptr = read_dword(ptr_addr)
            if ptr != snap1['ptr']:
                print(f"Warning: pointer changed {snap1['ptr']:#x} -> {ptr:#x}")
            data2 = read_bytes(ptr, len(snap1['data']))
            if not data2:
                print("Failed to read current state")
                return
        elif name2 in _char_snapshots:
            snap2 = _char_snapshots[name2]
            data2 = snap2['data']
        else:
            print(f"Snapshot '{name2}' not found")
            return

        data1 = snap1['data']

        print(f"=== Character Struct Diff: {name1} vs {name2} ===")
        print()

        # Find differences
        diffs = []
        for i in range(min(len(data1), len(data2))):
            if data1[i] != data2[i]:
                diffs.append((i, data1[i], data2[i]))

        if not diffs:
            print("No differences found!")
            return

        print(f"Changed bytes: {len(diffs)}")
        print()

        # Group by 2-byte words for velocity/position analysis
        print("=== Changes (grouped by word) ===")

        # Track which offsets changed
        changed_offsets = set(d[0] for d in diffs)

        # Analyze as 16-bit words
        for i in range(0, min(len(data1), len(data2)) - 1, 2):
            word1 = struct.unpack('<H', data1[i:i+2])[0]
            word2 = struct.unpack('<H', data2[i:i+2])[0]

            if word1 != word2:
                sword1 = struct.unpack('<h', data1[i:i+2])[0]
                sword2 = struct.unpack('<h', data2[i:i+2])[0]
                delta = sword2 - sword1

                # Check if known offset
                known = ""
                for name, offset in CHAR_OFFSETS.items():
                    if i <= offset < i + 2:
                        known = f" [{name}]"
                        break

                # Highlight likely velocity/position fields
                hint = ""
                if abs(delta) > 100 and abs(delta) < 10000:
                    hint = " <-- possible velocity/position?"
                elif i < 0x40:
                    hint = " <-- physics region"

                print(f"  +{i:04X}: {sword1:6d} -> {sword2:6d} (delta: {delta:+6d}){known}{hint}")

        # Summary of regions that changed
        print()
        print("=== Summary ===")
        regions_changed = set()
        for off in changed_offsets:
            for region_name, (start, end) in VELOCITY_CANDIDATES.items():
                if start <= off < end:
                    regions_changed.add(region_name)

        if regions_changed:
            print(f"Candidate regions with changes: {', '.join(regions_changed)}")
        else:
            print("Changes outside candidate velocity regions")


class JUSVelocityWatch(gdb.Command):
    """Monitor specific offsets over time to identify velocity fields.

    Usage: jus-velocity-watch [player] [interval_ms]
    Default: player 1, 100ms interval

    Takes repeated readings and shows fields that are changing,
    which helps identify velocity (constantly changing during movement)
    vs position (gradual change) vs timers (decrementing).

    Press Ctrl+C to stop.
    """

    def __init__(self):
        super().__init__("jus-velocity-watch", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        player = int(args[0]) if args else 1
        interval_ms = int(args[1]) if len(args) > 1 else 100

        ptr_addr = ADDRESSES[f'player{player}_state_ptr']
        ptr = read_dword(ptr_addr)

        if not ptr or ptr < 0x02000000:
            print(f"Player {player} state pointer invalid")
            return

        print(f"=== Velocity Watch (Player {player}) ===")
        print(f"Monitoring first 64 bytes (physics region)")
        print(f"Interval: {interval_ms}ms")
        print("Press Ctrl+C to stop")
        print()

        # Just read once and show what looks interesting
        # (GDB python doesn't have async sleep, so we do single read)

        data = read_bytes(ptr, 0x40)  # First 64 bytes
        if not data:
            print("Failed to read")
            return

        print("Current physics region values (as signed 16-bit):")
        for i in range(0, 64, 2):
            word = struct.unpack('<h', data[i:i+2])[0]
            if word != 0:
                print(f"  +{i:04X}: {word:6d} (0x{struct.unpack('<H', data[i:i+2])[0]:04X})")

        print()
        print("TIP: Use automated triggers instead of manual Ctrl+C:")
        print("  jus-auto-snapshot-on-hit 1   - Auto-capture when P1 takes damage")
        print("  jus-auto-snapshot-on-state 1 - Auto-capture when P1 state changes")


# ============================================================================
# AUTOMATED SNAPSHOT TRIGGERS (solve focus problem)
# ============================================================================

class HitTriggerBreakpoint(gdb.Breakpoint):
    """Internal breakpoint that triggers on HP change."""

    def __init__(self, player, snapshot_name_prefix):
        self.player = player
        self.prefix = snapshot_name_prefix
        self.hit_count = 0
        self.last_hp = None

        # Watch HP address for writes
        hp_addr = ADDRESSES[f'player{player}_hp']
        super().__init__(f"*{hp_addr:#x}", gdb.BP_WATCHPOINT, gdb.WP_WRITE)
        self.silent = True

    def stop(self):
        """Called when HP changes. Take snapshot and continue."""
        hp = read_byte(ADDRESSES[f'player{self.player}_hp'])

        # Only trigger on HP decrease (taking damage)
        if self.last_hp is not None and hp < self.last_hp:
            self.hit_count += 1
            name = f"{self.prefix}_hit{self.hit_count}"

            # Get character struct pointer
            ptr_addr = ADDRESSES[f'player{self.player}_state_ptr']
            ptr = read_dword(ptr_addr)

            if ptr and ptr >= 0x02000000:
                data = read_bytes(ptr, 0x120)
                if data:
                    _char_snapshots[name] = {
                        'data': data,
                        'ptr': ptr,
                        'player': self.player,
                        'hp_before': self.last_hp,
                        'hp_after': hp,
                    }
                    print(f"\n[AUTO] Snapshot '{name}' captured (HP: {self.last_hp} -> {hp})")

        self.last_hp = hp
        return False  # Don't stop, continue running


class JUSAutoSnapshotOnHit(gdb.Command):
    """Automatically take snapshots when a player takes damage.

    Usage: jus-auto-snapshot-on-hit <player> [prefix]

    This sets up a watchpoint on HP that automatically captures
    character state whenever damage is taken. No need to Ctrl+C!

    The snapshots are named: <prefix>_hit1, <prefix>_hit2, etc.
    Default prefix: "auto"

    To stop: jus-auto-snapshot-off
    """

    _active_breakpoints = []

    def __init__(self):
        super().__init__("jus-auto-snapshot-on-hit", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-auto-snapshot-on-hit <player 1-4> [prefix]")
            print("Example: jus-auto-snapshot-on-hit 1 goku")
            print("  -> Creates snapshots: goku_hit1, goku_hit2, ...")
            return

        player = int(args[0])
        prefix = args[1] if len(args) > 1 else "auto"

        if player < 1 or player > 4:
            print("Player must be 1-4")
            return

        # Create the watchpoint
        bp = HitTriggerBreakpoint(player, prefix)
        self._active_breakpoints.append(bp)

        print(f"=== Auto-Snapshot on Hit ENABLED ===")
        print(f"Player: {player}")
        print(f"Prefix: {prefix}")
        print()
        print("Now use 'continue' to resume the game.")
        print("Snapshots will be captured automatically when damage is taken.")
        print()
        print("To view snapshots: jus-char-snapshot (no args)")
        print("To compare: jus-char-diff auto_hit1 auto_hit2")
        print("To stop: jus-auto-snapshot-off")


class JUSAutoSnapshotOff(gdb.Command):
    """Disable all automatic snapshot triggers."""

    def __init__(self):
        super().__init__("jus-auto-snapshot-off", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        count = 0
        for bp in JUSAutoSnapshotOnHit._active_breakpoints:
            bp.delete()
            count += 1
        JUSAutoSnapshotOnHit._active_breakpoints.clear()

        if count:
            print(f"Disabled {count} auto-snapshot trigger(s)")
        else:
            print("No active auto-snapshot triggers")

        print(f"Captured snapshots: {list(_char_snapshots.keys())}")


class StateTriggerBreakpoint(gdb.Breakpoint):
    """Internal breakpoint that triggers on ground/air state change."""

    def __init__(self, player, snapshot_name_prefix):
        self.player = player
        self.prefix = snapshot_name_prefix
        self.state_count = 0
        self.last_state = None

        # Get character struct pointer to find state address
        ptr_addr = ADDRESSES[f'player{player}_state_ptr']
        ptr = read_dword(ptr_addr)

        if not ptr or ptr < 0x02000000:
            raise ValueError(f"Player {player} state pointer invalid")

        # Watch the ground_air field
        state_addr = ptr + CHAR_OFFSETS['ground_air']
        super().__init__(f"*{state_addr:#x}", gdb.BP_WATCHPOINT, gdb.WP_WRITE)
        self.silent = True
        self.state_addr = state_addr

    def stop(self):
        """Called when ground/air state changes."""
        state = read_byte(self.state_addr)

        if self.last_state is not None and state != self.last_state:
            self.state_count += 1

            # Decode state
            state_name = "air" if state == 0x00 else "ground" if state == 0x22 else f"0x{state:02X}"
            last_name = "air" if self.last_state == 0x00 else "ground" if self.last_state == 0x22 else f"0x{self.last_state:02X}"

            name = f"{self.prefix}_state{self.state_count}"

            # Get full character struct
            ptr_addr = ADDRESSES[f'player{self.player}_state_ptr']
            ptr = read_dword(ptr_addr)

            if ptr and ptr >= 0x02000000:
                data = read_bytes(ptr, 0x120)
                if data:
                    _char_snapshots[name] = {
                        'data': data,
                        'ptr': ptr,
                        'player': self.player,
                        'state_from': last_name,
                        'state_to': state_name,
                    }
                    print(f"\n[AUTO] Snapshot '{name}' captured ({last_name} -> {state_name})")

        self.last_state = state
        return False


class JUSAutoSnapshotOnState(gdb.Command):
    """Automatically take snapshots when ground/air state changes.

    Usage: jus-auto-snapshot-on-state <player> [prefix]

    Captures state when character:
    - Jumps (ground -> air)
    - Lands (air -> ground)
    - Gets launched (ground -> air from hit)
    - Enters hitstun states

    Default prefix: "state"
    """

    _active_breakpoints = []

    def __init__(self):
        super().__init__("jus-auto-snapshot-on-state", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-auto-snapshot-on-state <player 1-4> [prefix]")
            return

        player = int(args[0])
        prefix = args[1] if len(args) > 1 else "state"

        if player < 1 or player > 4:
            print("Player must be 1-4")
            return

        try:
            bp = StateTriggerBreakpoint(player, prefix)
            self._active_breakpoints.append(bp)
            JUSAutoSnapshotOnHit._active_breakpoints.append(bp)  # Share cleanup

            print(f"=== Auto-Snapshot on State Change ENABLED ===")
            print(f"Player: {player}")
            print(f"Prefix: {prefix}")
            print()
            print("Triggers on: jump, land, launched, knockdown")
            print("Use 'continue' to resume. Stop with: jus-auto-snapshot-off")

        except ValueError as e:
            print(f"Error: {e}")
            print("Make sure you're in a battle and the character is loaded.")


class JUSPeriodicSnapshot(gdb.Command):
    """Take a burst of snapshots with brief continues between.

    Usage: jus-burst-snapshot <count> <name_prefix> [player]

    Takes <count> snapshots, briefly continuing between each.
    Useful for capturing movement/animation over time.

    Example: jus-burst-snapshot 10 walking 1
    Creates: walking_0, walking_1, ... walking_9
    """

    def __init__(self):
        super().__init__("jus-burst-snapshot", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if len(args) < 2:
            print("Usage: jus-burst-snapshot <count> <prefix> [player]")
            print("Example: jus-burst-snapshot 5 walking 1")
            return

        count = int(args[0])
        prefix = args[1]
        player = int(args[2]) if len(args) > 2 else 1

        ptr_addr = ADDRESSES[f'player{player}_state_ptr']
        ptr = read_dword(ptr_addr)

        if not ptr or ptr >= 0x02000000:
            pass  # Will check per snapshot
        else:
            print(f"Player {player} state pointer invalid")
            return

        print(f"Taking {count} snapshots with prefix '{prefix}'...")
        print("(Game will briefly continue between each)")
        print()

        for i in range(count):
            # Read current state
            ptr = read_dword(ptr_addr)
            if ptr and ptr >= 0x02000000:
                data = read_bytes(ptr, 0x120)
                if data:
                    name = f"{prefix}_{i}"
                    _char_snapshots[name] = {
                        'data': data,
                        'ptr': ptr,
                        'player': player,
                        'burst_index': i,
                    }
                    print(f"  {name}: captured")

            if i < count - 1:
                # Brief continue (stepi advances one instruction)
                gdb.execute("stepi 1000", to_string=True)

        print()
        print(f"Done! Snapshots: {prefix}_0 through {prefix}_{count-1}")
        print(f"Compare with: jus-char-diff {prefix}_0 {prefix}_{count-1}")


# ============================================================================
# BREAKPOINT HANDLERS
# ============================================================================

class HPChangeBreakpoint(gdb.Breakpoint):
    """Custom breakpoint that logs HP changes."""

    def __init__(self, player):
        self.player = player
        addr = ADDRESSES[f'player{player}_hp']
        super().__init__(f"*{addr:#x}", gdb.BP_WATCHPOINT, gdb.WP_WRITE)

    def stop(self):
        hp = read_byte(ADDRESSES[f'player{self.player}_hp'])
        frame = gdb.selected_frame()
        pc = frame.pc()
        print(f"[HP CHANGE] Player {self.player} HP = {hp} (from {pc:#010x})")
        return False  # Don't stop, just log


# ============================================================================
# INITIALIZATION
# ============================================================================

def init():
    """Initialize JUS GDB commands."""
    JUSStatus()
    JUSWatchHP()
    JUSWatchCode()
    JUSReadChar()
    JUSDump()
    JUSScan()
    JUSAddresses()
    JUSSnapshot()
    JUSDiff()
    JUSTrace()
    JUSBacktrace()

    # Hitstun/velocity research commands
    JUSCharDump()
    JUSCharSnapshot()
    JUSCharDiff()
    JUSVelocityWatch()

    # Automated snapshot triggers (solve window focus problem)
    JUSAutoSnapshotOnHit()
    JUSAutoSnapshotOff()
    JUSAutoSnapshotOnState()
    JUSPeriodicSnapshot()

    print("=" * 50)
    print("  JUS GDB Watcher loaded!")
    print("=" * 50)
    print()
    print("Commands:")
    print("  jus-status       - Show battle state")
    print("  jus-watch-hp     - Set HP watchpoints")
    print("  jus-watch-code   - Break at health code")
    print("  jus-read-char N  - Read player N char state")
    print("  jus-dump         - Dump memory to file")
    print("  jus-scan         - Scan for byte value")
    print("  jus-addresses    - List known addresses")
    print()
    print("Snapshot/Diff commands (for finding changes):")
    print("  jus-snapshot <name> [region]  - Save memory snapshot")
    print("  jus-diff <snap1> <snap2|now>  - Compare snapshots")
    print()
    print("Character Struct Research (hitstun/velocity):")
    print("  jus-char-dump [player]            - Dump char struct bytes")
    print("  jus-char-snapshot <name> [player] - Save char struct snapshot")
    print("  jus-char-diff <snap1> <snap2|now> - Find changing fields")
    print("  jus-velocity-watch [player]       - Show physics region")
    print()
    print("AUTOMATED TRIGGERS (no manual Ctrl+C needed!):")
    print("  jus-auto-snapshot-on-hit <player> [prefix]   - Capture on damage")
    print("  jus-auto-snapshot-on-state <player> [prefix] - Capture on jump/land")
    print("  jus-burst-snapshot <count> <prefix> [player] - Rapid-fire snapshots")
    print("  jus-auto-snapshot-off                        - Disable triggers")
    print()
    print("Tracing:")
    print("  jus-trace <addr> [on|off]  - Log function calls")
    print("  jus-bt                     - Backtrace with ARM9 offsets")
    print()
    print("Connect to melonDS: target remote localhost:3333")
    print()


# Auto-initialize when sourced
init()
