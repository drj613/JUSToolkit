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
CHAR_OFFSETS = {
    'ground_air': 0x0078,      # 0x00=air, 0x22=ground
    'positive_status': 0x0088,
    'negative_status': 0x00A0,
    'jump_count': 0x00D9,
    'air_actions': 0x00DA,
    'defense_timer': 0x0102,
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
    print("Tracing:")
    print("  jus-trace <addr> [on|off]  - Log function calls")
    print("  jus-bt                     - Backtrace with ARM9 offsets")
    print()
    print("Connect to melonDS: target remote localhost:3333")
    print()


# Auto-initialize when sourced
init()
