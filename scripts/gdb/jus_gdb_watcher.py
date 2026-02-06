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

    # HP ADDRESSES
    # HP is stored at 1/4 scale (160 displayed = 40 stored)
    # Structure: active character, then deck slots spaced 0x50 apart
    #
    # YOUR SIDE:
    #   active = currently fighting character
    #   deck1-3 = other deck members (supports, tagged out, etc.)
    'player_active_hp': 0x021DF1D5,
    'player_deck1_hp': 0x021DF225,
    'player_deck2_hp': 0x021DF275,
    'player_deck3_hp': 0x021DF2C5,

    # OPPONENT SIDE (0x61C offset from your active):
    #   active = opponent's currently fighting character
    #   deck1-3 = opponent's other deck members
    'opponent_active_hp': 0x021DF7F1,
    'opponent_deck1_hp': 0x021DF841,
    'opponent_deck2_hp': 0x021DF891,
    'opponent_deck3_hp': 0x021DF8E1,

    # Legacy aliases (for backward compatibility)
    'player1_hp': 0x021DF1D5,  # = player_active_hp
    'player2_hp': 0x021DF225,  # = player_deck1_hp
    'player3_hp': 0x021DF275,  # = player_deck2_hp
    'player4_hp': 0x021DF2C5,  # = player_deck3_hp
    'opponent1_hp': 0x021DF7F1,  # = opponent_active_hp
    'opponent2_hp': 0x021DF841,  # = opponent_deck1_hp
    'opponent3_hp': 0x021DF891,  # = opponent_deck2_hp
    'opponent4_hp': 0x021DF8E1,  # = opponent_deck3_hp

    # Special meter
    'special_1': 0x021DF731,
    'special_2': 0x021DF8B1,

    # Player state pointers (wifi mode only!)
    # WARNING: These contain invalid data in training/offline modes
    'player1_state_ptr': 0x021E2A7C,
    'player2_state_ptr': 0x021E2A80,
    'player3_state_ptr': 0x021E2A84,
    'player4_state_ptr': 0x021E2A88,

    # ALTERNATIVE POINTERS for offline/training modes (JUS-98z)
    # These may work when wifi pointers don't
    'alt_state_base': 0x023D2A74,      # +0x10 to reach char struct
    'alt_position_ptr': 0x020A3A6C,    # Player state for position tracking
    'char_ptr_leader': 0x021DF1F0,     # Character pointer (leader) - near HP
    'player1_coords_ptr': 0x02181AF8,  # Player 1 base coordinates
    'player2_coords_base': 0x02181BDC, # Player 2 base reference
    # Position offsets from coords_ptr:
    #   P1: X=+0x40, Y=+0x44, facing=+0x48
    #   P3: X=+0x80, Y=+0x84
    #   P4: X=+0xC0, Y=+0xC4

    # SP gauge (from cheat codes)
    'sp_check': 0x020ADAD8,           # Battle state check for SP
    'sp_base_ptr': 0x020A282C,        # SP gauge base pointer
    'char_state_alt': 0x02172960,     # Alt character state pointer

    # ARM9 code hooks
    'health_code': 0x020784FC,

    # Save/progress
    'koma_points': 0x020B76C8,
    'gems': 0x020B7718,
    'active_deck': 0x020AFEB4,
}

# Character state struct offsets (from pointer)
# These are CONFIRMED from Action Replay code analysis and GDB testing
CHAR_OFFSETS = {
    'ground_air': 0x0078,      # 0x00=air, 0x22=ground, 0xC0=LAUNCHED/HITSTUN
    'positive_status': 0x0088,
    'negative_status': 0x00A0,
    'jump_count': 0x00D9,
    'air_actions': 0x00DA,
    'defense_timer': 0x0102,
}

# Timer region offsets (discovered 2026-02-03)
# These fields decrement in -5/-3 pattern during hitstun/recovery
# Appear to be 32-bit values read as 16-bit pairs
TIMER_REGION_OFFSETS = [
    0x0098, 0x009A,  # Timer pair 1
    0x00A0, 0x00A2,  # Timer pair 2 (overlaps negative_status)
    0x00A8, 0x00AA,  # Timer pair 3
    0x00B0, 0x00B2,  # Timer pair 4
    0x00B8, 0x00BA,  # Timer pair 5
]

# Ground/air state values
GROUND_AIR_STATES = {
    0x00: 'air (jumping/rising)',
    0x02: 'fast fall',           # Discovered 2026-02-03 (down+jump in air)
    0x22: 'ground',
    0xC0: 'LAUNCHED/HITSTUN',
}

# WORKING OFFLINE MODE POINTER CHAIN (discovered 2026-02-03, JUS-98z)
# This works in training/offline modes where wifi pointers are invalid:
#   1. Read dword from 0x023D2A74 (alt_state_base)
#   2. Add 0x10 to get character struct pointer
#   3. Read character struct from that address
# Example: 0x023D2A74 -> 0x02206838 -> +0x10 -> 0x0220f30c (char struct)

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


def test_watchpoint_support(test_addr=None):
    """Test if the GDB stub supports hardware watchpoints.

    Returns True if watchpoints work, False otherwise.
    Note: ARM has limited hardware debug registers (~2 watchpoints).
    """
    if test_addr is None:
        test_addr = ADDRESSES.get('battle_timer', 0x021DEA71)

    try:
        # Try to create a test watchpoint
        test_bp = gdb.Breakpoint(f"*{test_addr:#x}", type=gdb.BP_WATCHPOINT, wp_class=gdb.WP_WRITE)
        # If we got here, it was created - delete it
        test_bp.delete()
        return True
    except gdb.error as e:
        error_str = str(e).lower()
        if 'watchpoint' in error_str or 'hardware' in error_str or 'not supported' in error_str:
            return False
        # Unknown error - assume not supported
        return False
    except Exception:
        return False


# Global flag for watchpoint support (tested once at first use)
_watchpoint_support_tested = False
_watchpoint_support_available = None


def check_watchpoint_support():
    """Check and cache watchpoint support status."""
    global _watchpoint_support_tested, _watchpoint_support_available

    if not _watchpoint_support_tested:
        _watchpoint_support_available = test_watchpoint_support()
        _watchpoint_support_tested = True

        if not _watchpoint_support_available:
            print()
            print("=" * 60)
            print("WARNING: Hardware watchpoints may not be supported!")
            print("=" * 60)
            print()
            print("melonDS GDB stub has limited watchpoint support.")
            print("If watchpoint-based triggers fail, use these alternatives:")
            print("  - jus-auto-snapshot-on-damage (uses breakpoint, more reliable)")
            print("  - jus-burst-snapshot (manual timing)")
            print()

    return _watchpoint_support_available


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


class JUSFindHP(gdb.Command):
    """Search for HP value in memory to find correct address.

    Usage: jus-find-hp <expected_hp> [region]

    Searches for a byte matching the expected HP value in the battle
    memory region. Useful for verifying HP addresses or finding the
    correct one for different game modes.

    Example:
        jus-find-hp 160       # Find where HP=160 is stored
        jus-find-hp 100 char  # Search in character region only
    """

    REGIONS = {
        'battle': (0x021DF000, 0x021E0000),  # Character data region
        'char': (0x021DF100, 0x021DF400),    # Narrower char region
        'wide': (0x021D0000, 0x02200000),    # Full battle RAM
    }

    def __init__(self):
        super().__init__("jus-find-hp", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-find-hp <expected_hp> [region]")
            print()
            print("Searches for HP value in memory.")
            print("Regions: battle (default), char, wide")
            print()
            print("Example: If Kenshin shows 160 HP on screen:")
            print("  jus-find-hp 160")
            print("  jus-find-hp 40    # Maybe stored as HP/4?")
            return

        try:
            target_hp = int(args[0])
        except ValueError:
            print("HP must be a number")
            return

        region = args[1] if len(args) > 1 else 'battle'
        if region not in self.REGIONS:
            print(f"Unknown region: {region}")
            print(f"Available: {list(self.REGIONS.keys())}")
            return

        start, end = self.REGIONS[region]
        print(f"Searching for HP={target_hp} in {region} ({start:#x}-{end:#x})...")

        data = read_bytes(start, end - start)
        if not data:
            print("Failed to read memory")
            return

        # Find all matches
        matches = []
        for i, b in enumerate(data):
            if b == target_hp:
                addr = start + i
                matches.append(addr)

        if not matches:
            print(f"No matches found for value {target_hp}")
            print()
            print("Try searching for related values:")
            print(f"  jus-find-hp {target_hp // 4}  # HP/4")
            print(f"  jus-find-hp {target_hp // 2}  # HP/2")
            return

        print(f"Found {len(matches)} matches:")
        print()

        # Show matches with context
        known_hp_addrs = [
            ADDRESSES['player1_hp'],
            ADDRESSES['player2_hp'],
            ADDRESSES['player3_hp'],
            ADDRESSES['player4_hp'],
        ]

        for addr in matches[:20]:
            # Check if this is a known HP address
            known = ""
            for i, known_addr in enumerate(known_hp_addrs, 1):
                if addr == known_addr:
                    known = f" <- KNOWN player{i}_hp"
                    break
                elif abs(addr - known_addr) < 0x10:
                    known = f" (near player{i}_hp)"
                    break

            # Show nearby bytes for context
            offset = addr - start
            context_start = max(0, offset - 2)
            context_end = min(len(data), offset + 3)
            context = data[context_start:context_end]
            context_hex = ' '.join(f'{b:02X}' for b in context)

            print(f"  {addr:#010x}: {target_hp} (0x{target_hp:02X})  context: [{context_hex}]{known}")

        if len(matches) > 20:
            print(f"  ... and {len(matches) - 20} more")


class JUSCheckHP(gdb.Command):
    """Quick check of current HP values at known addresses.

    Usage: jus-check-hp

    Shows HP values for active characters and deck members.
    Run before and after damage to verify addresses are correct.
    """

    def __init__(self):
        super().__init__("jus-check-hp", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        print("=== HP Check (raw values at known addresses) ===")
        print("Note: Values are stored at 1/4 scale (40 = 160 displayed)")
        print()

        # Your side
        print("YOUR SIDE:")
        addr = ADDRESSES['player_active_hp']
        hp = read_byte(addr)
        displayed = hp * 4 if hp else 0
        print(f"  Active:  {hp:3d} (displayed: ~{displayed:3d}) @ {addr:#010x}")

        for i in range(1, 4):
            addr = ADDRESSES[f'player_deck{i}_hp']
            hp = read_byte(addr)
            displayed = hp * 4 if hp else 0
            note = " [KO'd or empty]" if hp == 0 else ""
            print(f"  Deck {i}:  {hp:3d} (displayed: ~{displayed:3d}) @ {addr:#010x}{note}")

        print()

        # Opponent side
        print("OPPONENT SIDE:")
        addr = ADDRESSES['opponent_active_hp']
        hp = read_byte(addr)
        displayed = hp * 4 if hp else 0
        print(f"  Active:  {hp:3d} (displayed: ~{displayed:3d}) @ {addr:#010x}")

        for i in range(1, 4):
            addr = ADDRESSES[f'opponent_deck{i}_hp']
            hp = read_byte(addr)
            displayed = hp * 4 if hp else 0
            note = " [KO'd or empty]" if hp == 0 else ""
            print(f"  Deck {i}:  {hp:3d} (displayed: ~{displayed:3d}) @ {addr:#010x}{note}")


class JUSProbeOffline(gdb.Command):
    """Probe alternative pointer addresses for offline/training mode.

    Usage: jus-probe-offline

    The wifi state pointers (0x021E2A7C etc) don't work in training or
    offline modes. This command probes alternative addresses that may
    contain character state data in these modes.

    Run this while in a training/offline battle to find working pointers.
    """

    def __init__(self):
        super().__init__("jus-probe-offline", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        print("=== Probing Alternative State Pointers ===")
        print("Use this in TRAINING or OFFLINE mode to find working pointers.")
        print()

        # Check wifi pointers first (expect invalid)
        print("--- Wifi Pointers (should be INVALID in offline mode) ---")
        for i in range(1, 5):
            ptr_addr = ADDRESSES[f'player{i}_state_ptr']
            ptr = read_dword(ptr_addr)
            valid = ptr and 0x02000000 <= ptr < 0x02400000
            status = "VALID" if valid else "INVALID"
            ptr_str = f"{ptr:#010x}" if ptr else "NULL"
            print(f"  player{i}_state_ptr @ {ptr_addr:#010x} = {ptr_str} [{status}]")

        print()
        print("--- Alternative Pointers ---")

        # Probe alt_state_base + 0x10
        alt_base = read_dword(ADDRESSES['alt_state_base'])
        if alt_base:
            print(f"  alt_state_base @ {ADDRESSES['alt_state_base']:#010x} = {alt_base:#010x}")
            # Try +0x10 offset as per cheat codes
            alt_char = read_dword(alt_base + 0x10) if alt_base >= 0x02000000 else None
            if alt_char and 0x02000000 <= alt_char < 0x02400000:
                print(f"    +0x10 -> {alt_char:#010x} [POTENTIALLY VALID]")
                # Try to read ground_air state to verify
                ground_air = read_byte(alt_char + CHAR_OFFSETS['ground_air'])
                if ground_air is not None:
                    state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
                    print(f"      ground_air (+0x78) = {ground_air} ({state})")
        else:
            print(f"  alt_state_base @ {ADDRESSES['alt_state_base']:#010x} = NULL/invalid")

        # Probe char_ptr_leader (near HP address)
        char_ptr = read_dword(ADDRESSES['char_ptr_leader'])
        if char_ptr:
            valid = 0x02000000 <= char_ptr < 0x02400000
            print(f"  char_ptr_leader @ {ADDRESSES['char_ptr_leader']:#010x} = {char_ptr:#010x} [{'VALID' if valid else 'INVALID'}]")
            if valid:
                # Try to read character struct
                ground_air = read_byte(char_ptr + CHAR_OFFSETS['ground_air'])
                if ground_air is not None:
                    state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
                    print(f"    ground_air (+0x78) = {ground_air} ({state})")
        else:
            print(f"  char_ptr_leader @ {ADDRESSES['char_ptr_leader']:#010x} = NULL")

        # Probe char_state_alt
        char_alt = read_dword(ADDRESSES['char_state_alt'])
        if char_alt:
            valid = 0x02000000 <= char_alt < 0x02400000
            print(f"  char_state_alt @ {ADDRESSES['char_state_alt']:#010x} = {char_alt:#010x} [{'VALID' if valid else 'INVALID'}]")
            if valid:
                # Read a few bytes to see what's there
                data = read_bytes(char_alt, 16)
                if data:
                    hex_str = ' '.join(f'{b:02X}' for b in data)
                    print(f"    First 16 bytes: {hex_str}")
        else:
            print(f"  char_state_alt @ {ADDRESSES['char_state_alt']:#010x} = NULL")

        # Probe coordinates pointer
        coords_ptr = read_dword(ADDRESSES['player1_coords_ptr'])
        if coords_ptr:
            valid = 0x02000000 <= coords_ptr < 0x02400000
            print(f"  player1_coords_ptr @ {ADDRESSES['player1_coords_ptr']:#010x} = {coords_ptr:#010x} [{'VALID' if valid else 'INVALID'}]")
            if valid:
                # Read position data
                x = read_dword(coords_ptr + 0x40)
                y = read_dword(coords_ptr + 0x44)
                facing = read_byte(coords_ptr + 0x48)
                if x is not None:
                    facing_str = f"0x{facing:02X}" if facing is not None else "N/A"
                    print(f"    Position: X={x}, Y={y}, facing={facing_str}")
        else:
            print(f"  player1_coords_ptr @ {ADDRESSES['player1_coords_ptr']:#010x} = NULL")

        # Probe alt_position_ptr
        pos_ptr = read_dword(ADDRESSES['alt_position_ptr'])
        if pos_ptr:
            valid = 0x02000000 <= pos_ptr < 0x02400000
            print(f"  alt_position_ptr @ {ADDRESSES['alt_position_ptr']:#010x} = {pos_ptr:#010x} [{'VALID' if valid else 'INVALID'}]")
        else:
            print(f"  alt_position_ptr @ {ADDRESSES['alt_position_ptr']:#010x} = NULL")

        print()
        print("--- Calculated Character Pointers (HP stride = 0x50) ---")
        # If char_ptr_leader at +0x1B from HP, calculate for all slots
        hp_base = ADDRESSES['player_active_hp']
        char_ptr_offset = ADDRESSES['char_ptr_leader'] - hp_base  # Should be 0x1B
        print(f"  (char_ptr is at HP + {char_ptr_offset:#x})")

        for slot in range(4):
            hp_addr = hp_base + slot * 0x50
            ptr_addr = hp_addr + char_ptr_offset
            ptr = read_dword(ptr_addr)
            if ptr:
                valid = 0x02000000 <= ptr < 0x02400000
                ground_air = read_byte(ptr + CHAR_OFFSETS['ground_air']) if valid else None
                state_str = ""
                if ground_air is not None:
                    state_str = f" ground_air={GROUND_AIR_STATES.get(ground_air, f'0x{ground_air:02X}')}"
                status = "VALID" + state_str if valid else "INVALID"
                print(f"  Slot {slot} ptr @ {ptr_addr:#010x} = {ptr:#010x} [{status}]")
            else:
                print(f"  Slot {slot} ptr @ {ptr_addr:#010x} = NULL")

        print()
        print("--- Memory Near HP (scanning for pointers to char structs) ---")
        hp_addr = ADDRESSES['player_active_hp']
        print(f"Player HP at {hp_addr:#010x}")

        # Scan nearby memory for pointers
        found_valid = []
        scan_start = hp_addr - 0x30
        for offset in range(0, 0x60, 4):
            addr = scan_start + offset
            val = read_dword(addr)
            if val and 0x02000000 <= val < 0x02400000:
                # Might be a pointer - check if it points to valid char struct
                ground_air = read_byte(val + CHAR_OFFSETS['ground_air'])
                note = ""
                if ground_air is not None and ground_air in GROUND_AIR_STATES:
                    note = f" <- ground_air={GROUND_AIR_STATES[ground_air]} *** LIKELY CHAR STRUCT ***"
                    found_valid.append((addr, val, ground_air))
                print(f"  {addr:#010x} (+{offset-0x30:+d} from HP): {val:#010x}{note}")

        print()
        print("--- Searching for Character Struct Pattern ---")
        # The character struct should have ground_air at +0x78 with value 0x00, 0x22, or 0xC0
        # Search the 0x021DF000 region for this pattern
        search_start = 0x021DF000
        search_end = 0x021E0000
        print(f"Scanning {search_start:#010x} - {search_end:#010x} for structs with valid ground_air at +0x78...")

        candidates = []
        for base in range(search_start, search_end - 0x120, 0x10):  # Align to 16 bytes
            ground_air = read_byte(base + 0x78)
            if ground_air is not None and ground_air in GROUND_AIR_STATES:
                # Check if this looks like a char struct (defense_timer at +0x102 should be small)
                defense = read_byte(base + 0x102)
                if defense is not None and defense < 60:  # Reasonable timer value
                    candidates.append((base, ground_air, defense))

        if candidates:
            print(f"Found {len(candidates)} potential character struct bases:")
            for base, ground_air, defense in candidates[:10]:
                state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
                print(f"  {base:#010x}: ground_air={state}, defense_timer={defense}")
            if len(candidates) > 10:
                print(f"  ... and {len(candidates) - 10} more")
        else:
            print("  No candidates found with valid ground_air pattern")

        print()
        if found_valid:
            print("=== RECOMMENDATION ===")
            print("Found pointer(s) with valid ground_air state:")
            for addr, ptr, state in found_valid:
                print(f"  {addr:#010x} -> {ptr:#010x}")
            print()
            print("Try using this pointer for character state snapshots!")
            print("Update player1_state_ptr or use jus-read-char-at <address>")
        else:
            print("TIP: If wifi pointers are invalid but HP works, the game must")
            print("     access character state differently in offline mode.")
            print("     Check the 'Calculated Character Pointers' section above.")


class JUSReadCharAt(gdb.Command):
    """Read character state from a specific address.

    Usage: jus-read-char-at <address>

    Reads a character struct from the given address (not a pointer to a pointer).
    Use this to test candidate addresses found by jus-probe-offline.

    Example:
        jus-read-char-at 0x021E5000
    """

    def __init__(self):
        super().__init__("jus-read-char-at", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        if not arg:
            print("Usage: jus-read-char-at <address>")
            print("Example: jus-read-char-at 0x021E5000")
            return

        try:
            addr = int(arg.strip(), 0)
        except ValueError:
            print(f"Invalid address: {arg}")
            return

        if addr < 0x02000000 or addr >= 0x02400000:
            print(f"Warning: Address {addr:#010x} is outside main RAM (0x02000000-0x02400000)")

        print(f"=== Character State at {addr:#010x} ===")
        print()

        # Read known offsets
        print("Known fields:")
        for name, offset in sorted(CHAR_OFFSETS.items(), key=lambda x: x[1]):
            value = read_byte(addr + offset)
            if value is not None:
                extra = ""
                if name == 'ground_air':
                    state = GROUND_AIR_STATES.get(value, f"unknown")
                    extra = f" ({state})"
                print(f"  +0x{offset:04X} {name:20s} = {value:3d} (0x{value:02X}){extra}")
            else:
                print(f"  +0x{offset:04X} {name:20s} = READ FAILED")

        # Read timer region
        print()
        print("Timer region:")
        for offset in TIMER_REGION_OFFSETS:
            value = read_word(addr + offset)
            if value is not None:
                signed = struct.unpack('<h', struct.pack('<H', value))[0]
                print(f"  +0x{offset:04X}: {value:5d} (signed: {signed:+6d})")

        # Read physics region
        print()
        print("Physics region (0x6A-0x7E):")
        for offset in range(0x6A, 0x80, 2):
            value = read_word(addr + offset)
            if value is not None:
                signed = struct.unpack('<h', struct.pack('<H', value))[0]
                marker = " <-- ground_air" if offset == 0x78 else ""
                print(f"  +0x{offset:04X}: {signed:+6d} (0x{value:04X}){marker}")

        # Show first 32 bytes as hex dump
        print()
        print("First 32 bytes:")
        data = read_bytes(addr, 32)
        if data:
            for row in range(0, 32, 16):
                hex_str = ' '.join(f'{b:02X}' for b in data[row:row+16])
                print(f"  +0x{row:04X}: {hex_str}")


def get_offline_char_ptr(slot=0):
    """Get character struct pointer for offline/training mode.
    
    Uses the working pointer chain: alt_state_base -> +offset -> char struct
    
    Args:
        slot: 0 for player, 1-3 for other slots (opponent search)
    
    Returns the character struct address, or None if invalid.
    """
    alt_base = read_dword(ADDRESSES['alt_state_base'])
    if not alt_base or alt_base < 0x02000000:
        return None
    
    # Player is at +0x10, try +0x14, +0x18, etc. for other slots
    offset = 0x10 + (slot * 4)
    char_ptr = read_dword(alt_base + offset)
    if not char_ptr or char_ptr < 0x02000000 or char_ptr >= 0x02400000:
        return None
    
    return char_ptr


def get_offline_opponent_ptr():
    """Get opponent character struct pointer for offline/training mode.
    
    Uses the discovered pointer chain:
      alt_state_base -> intermediate -> +0x00 -> ptr -> +0x10 -> opponent struct
    
    Returns the opponent struct address, or None if invalid.
    """
    alt_base = read_dword(ADDRESSES['alt_state_base'])
    if not alt_base or alt_base < 0x02000000:
        return None
    
    # Opponent chain: intermediate+0x00 -> ptr -> +0x10 -> struct
    ptr1 = read_dword(alt_base + 0x00)
    if not ptr1 or ptr1 < 0x02000000 or ptr1 >= 0x02400000:
        return None
    
    opponent_ptr = read_dword(ptr1 + 0x10)
    if not opponent_ptr or opponent_ptr < 0x02000000 or opponent_ptr >= 0x02400000:
        return None
    
    return opponent_ptr


def _probe_opponent_candidates():
    """Internal: Search for opponent pointer candidates (used by probe command).
    
    Returns list of (address, method_description, ground_air) tuples.
    """
    player_ptr = get_offline_char_ptr(0)
    if not player_ptr:
        return []
    
    alt_base = read_dword(ADDRESSES['alt_state_base'])
    candidates = []
    
    # Method 1: Try adjacent slots in alt_state_base structure
    for slot in range(1, 8):  # Try slots 1-7
        offset = 0x10 + (slot * 4)
        ptr = read_dword(alt_base + offset) if alt_base else None
        if ptr and 0x02000000 <= ptr < 0x02400000 and ptr != player_ptr:
            # Verify it looks like a character struct
            ground_air = read_byte(ptr + CHAR_OFFSETS['ground_air'])
            if ground_air is not None and ground_air in [0x00, 0x02, 0x22, 0xC0]:
                candidates.append((ptr, f"alt_base+0x{offset:02X}", ground_air))
    
    # Method 2: Search around player struct (character structs might be contiguous)
    # Typical struct size seems to be ~0x120 bytes
    for stride in [0x120, 0x140, 0x100, 0x200]:
        for direction in [1, -1]:
            test_ptr = player_ptr + (stride * direction)
            if 0x02000000 <= test_ptr < 0x02400000:
                ground_air = read_byte(test_ptr + CHAR_OFFSETS['ground_air'])
                if ground_air is not None and ground_air in [0x00, 0x02, 0x22, 0xC0]:
                    dir_str = "+" if direction > 0 else "-"
                    candidates.append((test_ptr, f"player{dir_str}0x{stride:X}", ground_air))
    
    # Method 3: Check player2_coords_base area
    coords2 = ADDRESSES.get('player2_coords_base')
    if coords2:
        ptr = read_dword(coords2)
        if ptr and 0x02000000 <= ptr < 0x02400000 and ptr != player_ptr:
            ground_air = read_byte(ptr + CHAR_OFFSETS['ground_air'])
            if ground_air is not None:
                candidates.append((ptr, "player2_coords_base", ground_air))
    
    return candidates


class JUSReadCharOffline(gdb.Command):
    """Read character state using offline mode pointer chain.

    Usage: jus-read-char-offline

    Automatically follows the working pointer chain for offline/training mode:
      alt_state_base (0x023D2A74) -> +0x10 -> character struct

    This is the recommended command for offline/training mode.
    """

    def __init__(self):
        super().__init__("jus-read-char-offline", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        char_ptr = get_offline_char_ptr()
        if not char_ptr:
            print("Failed to get offline character pointer.")
            print("Make sure you're in a battle (training or offline mode).")
            return

        print(f"=== Character State (Offline Mode) ===")
        print(f"Pointer chain: 0x023D2A74 -> +0x10 -> {char_ptr:#010x}")
        print()

        # Read known offsets
        print("State fields:")
        for name, offset in sorted(CHAR_OFFSETS.items(), key=lambda x: x[1]):
            value = read_byte(char_ptr + offset)
            if value is not None:
                extra = ""
                if name == 'ground_air':
                    state = GROUND_AIR_STATES.get(value, f"unknown(0x{value:02X})")
                    extra = f" ({state})"
                print(f"  {name:20s} = {value:3d} (0x{value:02X}){extra}")

        # Show physics region
        print()
        print("Physics region (0x6A-0x7E):")
        for offset in range(0x6A, 0x80, 2):
            value = read_word(char_ptr + offset)
            if value is not None:
                signed = struct.unpack('<h', struct.pack('<H', value))[0]
                marker = " <-- ground_air" if offset == 0x78 else ""
                print(f"  +0x{offset:04X}: {signed:+6d}{marker}")


class JUSSnapshotOffline(gdb.Command):
    """Take character snapshot using offline mode pointer chain.

    Usage: jus-snapshot-offline <name>

    Automatically follows the working pointer chain for offline/training mode.
    Use with jus-char-diff to compare snapshots.

    Example:
        jus-snapshot-offline before
        (do action)
        jus-snapshot-offline after
        jus-char-diff before after
    """

    def __init__(self):
        super().__init__("jus-snapshot-offline", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        if not arg:
            print("Usage: jus-snapshot-offline <name>")
            return

        name = arg.strip()
        char_ptr = get_offline_char_ptr()
        
        if not char_ptr:
            print("Failed to get offline character pointer.")
            print("Make sure you're in a battle (training or offline mode).")
            return

        data = read_bytes(char_ptr, 0x120)
        if data:
            _char_snapshots[name] = {
                'data': data,
                'ptr': char_ptr,
                'player': 'offline',
                'source': 'jus-snapshot-offline',
            }
            ground_air = data[CHAR_OFFSETS['ground_air']]
            state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
            print(f"Snapshot '{name}' saved from {char_ptr:#010x}")
            print(f"  ground_air = {ground_air} ({state})")
        else:
            print(f"Failed to read character struct at {char_ptr:#010x}")


class JUSProbeOpponent(gdb.Command):
    """Probe for opponent character state pointer in offline/training mode.

    Usage: jus-probe-opponent

    Searches multiple memory locations to find the opponent's character
    state struct. This extends jus-probe-offline specifically for opponent.

    The command tries:
    1. Explore intermediate structure from alt_state_base
    2. Follow pointer chains from intermediate structure
    3. Search near opponent HP address
    4. Adjacent slots and stride search from player

    Run this while in training/offline mode with an opponent present.
    """

    def __init__(self):
        super().__init__("jus-probe-opponent", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        print("=== Probing for Opponent State Pointer ===")
        print("Run this in TRAINING or OFFLINE mode with opponent present.")
        print()

        # First show player state for reference
        player_ptr = get_offline_char_ptr(0)
        if not player_ptr:
            print("ERROR: Cannot find player state pointer.")
            print("Make sure you're in a battle first.")
            return

        player_ground_air = read_byte(player_ptr + CHAR_OFFSETS['ground_air'])
        player_state = GROUND_AIR_STATES.get(player_ground_air, f"0x{player_ground_air:02X}")
        print(f"Player state @ {player_ptr:#010x}")
        print(f"  ground_air = {player_ground_air} ({player_state})")
        print()

        # Explore intermediate structure thoroughly
        alt_state_base_addr = ADDRESSES['alt_state_base']
        alt_base = read_dword(alt_state_base_addr)
        
        print(f"--- Exploring Intermediate Structure ---")
        print(f"alt_state_base @ {alt_state_base_addr:#010x} = {alt_base:#010x}")
        print()
        
        if alt_base and 0x02000000 <= alt_base < 0x02400000:
            # Dump the intermediate structure (first 0x40 bytes)
            print(f"Intermediate struct at {alt_base:#010x}:")
            int_data = read_bytes(alt_base, 0x40)
            if int_data:
                for row in range(0, 0x40, 16):
                    hex_str = ' '.join(f'{b:02X}' for b in int_data[row:row+16])
                    print(f"  +0x{row:02X}: {hex_str}")
            print()
            
            # Try each dword as a potential character pointer
            print("Checking each pointer in intermediate struct:")
            found_candidates = []
            for offset in range(0, 0x40, 4):
                ptr = read_dword(alt_base + offset)
                if ptr and 0x02000000 <= ptr < 0x02400000 and ptr != player_ptr:
                    ground_air = read_byte(ptr + CHAR_OFFSETS['ground_air'])
                    if ground_air is not None:
                        state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
                        marker = " <-- PLAYER" if ptr == player_ptr else ""
                        if ground_air in [0x00, 0x02, 0x22, 0xC0]:
                            marker += " [VALID STATE]"
                            found_candidates.append((ptr, f"intermediate+0x{offset:02X}", ground_air))
                        print(f"  +0x{offset:02X}: {ptr:#010x} -> ground_air={ground_air} ({state}){marker}")
            print()
            
            # Also try dereferencing those pointers (double indirection)
            print("Checking double-indirection (ptr -> ptr -> struct):")
            for offset in range(0, 0x20, 4):
                ptr1 = read_dword(alt_base + offset)
                if ptr1 and 0x02000000 <= ptr1 < 0x02400000:
                    # Try +0x10 offset like player chain
                    ptr2 = read_dword(ptr1 + 0x10)
                    if ptr2 and 0x02000000 <= ptr2 < 0x02400000 and ptr2 != player_ptr:
                        ground_air = read_byte(ptr2 + CHAR_OFFSETS['ground_air'])
                        if ground_air is not None and ground_air in [0x00, 0x02, 0x22, 0xC0]:
                            state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
                            print(f"  +0x{offset:02X} -> {ptr1:#010x} -> +0x10 -> {ptr2:#010x}")
                            print(f"       ground_air = {ground_air} ({state})")
                            found_candidates.append((ptr2, f"double_ind+0x{offset:02X}", ground_air))
            print()
        
        # Search near opponent HP (0x61C offset from player HP)
        print("--- Searching Near Opponent HP ---")
        opponent_hp_addr = ADDRESSES['opponent_active_hp']
        print(f"Opponent HP @ {opponent_hp_addr:#010x}")
        
        # Look for pointers in region around opponent HP
        search_start = opponent_hp_addr - 0x20
        search_end = opponent_hp_addr + 0x40
        for addr in range(search_start, search_end, 4):
            ptr = read_dword(addr)
            if ptr and 0x02000000 <= ptr < 0x02400000:
                ground_air = read_byte(ptr + CHAR_OFFSETS['ground_air'])
                if ground_air is not None and ground_air in [0x00, 0x02, 0x22, 0xC0]:
                    state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
                    offset = addr - opponent_hp_addr
                    print(f"  HP{offset:+d} @ {addr:#010x} -> {ptr:#010x}")
                    print(f"       ground_air = {ground_air} ({state})")
                    found_candidates.append((ptr, f"near_opp_hp+{offset:+d}", ground_air))
        print()

        # Summary of candidates
        if found_candidates:
            print(f"=== {len(found_candidates)} Candidates Found ===")
            for i, (ptr, method, ground_air) in enumerate(found_candidates):
                state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
                print(f"  [{i+1}] {ptr:#010x} via {method} - ground_air={ground_air} ({state})")
            print()
            print("TIP: Test candidates by making opponent jump/land and re-running.")
        else:
            print("No valid candidates found.")
        
        print()
        print("Use 'jus-read-char-at <address>' to examine a candidate.")


class JUSReadOpponent(gdb.Command):
    """Read opponent character state using offline mode pointer chain.

    Usage: jus-read-opponent

    Follows the discovered pointer chain for opponent in offline/training mode:
      alt_state_base -> +0x00 -> ptr -> +0x10 -> opponent struct

    This is the recommended command for reading opponent state.
    """

    def __init__(self):
        super().__init__("jus-read-opponent", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        opponent_ptr = get_offline_opponent_ptr()
        if not opponent_ptr:
            print("Failed to get opponent pointer.")
            print("Make sure you're in a battle with an opponent present.")
            return

        # Also show player for comparison
        player_ptr = get_offline_char_ptr()
        if player_ptr:
            player_ga = read_byte(player_ptr + CHAR_OFFSETS['ground_air'])
            player_state = GROUND_AIR_STATES.get(player_ga, f"0x{player_ga:02X}") if player_ga else "?"
            print(f"Player   @ {player_ptr:#010x} - ground_air={player_ga} ({player_state})")

        opp_ga = read_byte(opponent_ptr + CHAR_OFFSETS['ground_air'])
        opp_state = GROUND_AIR_STATES.get(opp_ga, f"0x{opp_ga:02X}") if opp_ga else "?"
        print(f"Opponent @ {opponent_ptr:#010x} - ground_air={opp_ga} ({opp_state})")
        print()

        print(f"=== Opponent State @ {opponent_ptr:#010x} ===")
        print()

        # Read known offsets
        print("State fields:")
        for name, offset in sorted(CHAR_OFFSETS.items(), key=lambda x: x[1]):
            value = read_byte(opponent_ptr + offset)
            if value is not None:
                extra = ""
                if name == 'ground_air':
                    state = GROUND_AIR_STATES.get(value, f"unknown(0x{value:02X})")
                    extra = f" ({state})"
                print(f"  {name:20s} = {value:3d} (0x{value:02X}){extra}")

        # Show physics region
        print()
        print("Physics region (0x6A-0x7E):")
        for offset in range(0x6A, 0x80, 2):
            value = read_word(opponent_ptr + offset)
            if value is not None:
                signed = struct.unpack('<h', struct.pack('<H', value))[0]
                marker = " <-- ground_air" if offset == 0x78 else ""
                print(f"  +0x{offset:04X}: {signed:+6d}{marker}")


class JUSSnapshotOpponent(gdb.Command):
    """Take opponent character snapshot using offline mode pointer chain.

    Usage: jus-snapshot-opponent <name>

    Takes a snapshot of opponent state for comparison.
    Use with jus-char-diff to compare snapshots.

    Example:
        jus-snapshot-opponent opp_idle
        (opponent does action)
        jus-snapshot-opponent opp_attack
        jus-char-diff opp_idle opp_attack
    """

    def __init__(self):
        super().__init__("jus-snapshot-opponent", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        if not arg:
            print("Usage: jus-snapshot-opponent <name>")
            return

        name = arg.strip()
        opponent_ptr = get_offline_opponent_ptr()
        
        if not opponent_ptr:
            print("Failed to get opponent pointer.")
            print("Make sure you're in a battle with an opponent present.")
            return

        data = read_bytes(opponent_ptr, 0x120)
        if data:
            _char_snapshots[name] = {
                'data': data,
                'ptr': opponent_ptr,
                'player': 'opponent',
                'source': 'jus-snapshot-opponent',
            }
            ground_air = data[CHAR_OFFSETS['ground_air']]
            state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
            print(f"Opponent snapshot '{name}' saved from {opponent_ptr:#010x}")
            print(f"  ground_air = {ground_air} ({state})")
        else:
            print(f"Failed to read opponent struct at {opponent_ptr:#010x}")


class JUSSnapshotAt(gdb.Command):
    """Take a character struct snapshot from a specific address.

    Usage: jus-snapshot-at <name> <address>

    Like jus-char-snapshot but uses a direct address instead of the wifi pointer.
    Use for offline/training mode when wifi pointers are invalid.

    Example:
        jus-snapshot-at idle 0x021E5000
    """

    def __init__(self):
        super().__init__("jus-snapshot-at", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if len(args) < 2:
            print("Usage: jus-snapshot-at <name> <address>")
            print("Example: jus-snapshot-at before_hit 0x021E5000")
            return

        name = args[0]
        try:
            addr = int(args[1], 0)
        except ValueError:
            print(f"Invalid address: {args[1]}")
            return

        # Read full character struct
        data = read_bytes(addr, 0x120)
        if data:
            _char_snapshots[name] = {
                'data': data,
                'ptr': addr,
                'player': 'direct',
                'source': 'jus-snapshot-at',
            }
            print(f"Snapshot '{name}' saved from {addr:#010x} ({len(data)} bytes)")
            # Show current ground_air state
            ground_air = data[CHAR_OFFSETS['ground_air']]
            state = GROUND_AIR_STATES.get(ground_air, f"0x{ground_air:02X}")
            print(f"  ground_air = {ground_air} ({state})")
        else:
            print(f"Failed to read memory at {addr:#010x}")


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
            ptr_str = f"{ptr:#010x}" if ptr else "NULL"
            print(f"Player {player} state pointer invalid: {ptr_str}")
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
            ptr_str = f"{ptr:#010x}" if ptr else "NULL"
            print(f"Player {player} state pointer invalid: {ptr_str}")
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
        timer_count = 0
        physics_count = 0

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

                # Check if known timer (from baseline analysis)
                is_timer = i in _known_timer_offsets

                # Highlight likely velocity/position fields
                hint = ""
                if is_timer:
                    hint = " [TIMER - ignore]"
                    timer_count += 1
                elif abs(delta) > 100 and abs(delta) < 10000:
                    hint = " <-- possible velocity/position?"
                    physics_count += 1
                elif i < 0x40:
                    hint = " <-- physics region"
                    physics_count += 1

                print(f"  +{i:04X}: {sword1:6d} -> {sword2:6d} (delta: {delta:+6d}){known}{hint}")

        if timer_count > 0:
            print()
            print(f"Note: {timer_count} field(s) marked as timers (run jus-baseline-noise first)")

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
    """Internal breakpoint that triggers on HP change.

    Uses a hardware watchpoint on the HP address to automatically
    capture character state when damage is taken.
    """

    def __init__(self, player, snapshot_name_prefix):
        self.player = player
        self.prefix = snapshot_name_prefix
        self.hit_count = 0

        # Watch HP address for writes
        hp_addr = ADDRESSES[f'player{player}_hp']
        super().__init__(f"*{hp_addr:#x}", type=gdb.BP_WATCHPOINT, wp_class=gdb.WP_WRITE)
        self.silent = True

        # Initialize last_hp from current value
        self.last_hp = read_byte(hp_addr)

    def stop(self):
        """Called when HP changes. Take snapshot and continue.

        TIMING NOTE: This fires when HP is written. The knockback velocity
        may have been applied in a previous instruction. We capture the
        state at the moment of HP write, which should be close to (but
        possibly not exactly at) the moment of impact.
        """
        hp = read_byte(ADDRESSES[f'player{self.player}_hp'])

        # Handle read failure
        if hp is None:
            return False

        # Only trigger on HP decrease (taking damage)
        if self.last_hp is not None and hp < self.last_hp:
            self.hit_count += 1

            # Get character struct pointer
            ptr_addr = ADDRESSES[f'player{self.player}_state_ptr']
            ptr = read_dword(ptr_addr)

            if ptr and ptr >= 0x02000000:
                data = read_bytes(ptr, 0x120)
                if data:
                    name = f"{self.prefix}_hit{self.hit_count}"
                    _char_snapshots[name] = {
                        'data': data,
                        'ptr': ptr,
                        'player': self.player,
                        'hp_before': self.last_hp,
                        'hp_after': hp,
                        'timing': 'at_hp_write',
                    }
                    print(f"\n[AUTO] Snapshot '{name}' captured (HP: {self.last_hp} -> {hp})")

        self.last_hp = hp
        return False  # Don't stop, continue running


class JUSAutoSnapshotOnHit(gdb.Command):
    """Automatically take snapshots when a player takes damage.

    WARNING: This uses hardware watchpoints which do NOT work with melonDS!
    Use 'jus-auto-snapshot-on-damage' instead.

    Usage: jus-auto-snapshot-on-hit <player> [prefix]
    """

    _active_breakpoints = []

    def __init__(self):
        super().__init__("jus-auto-snapshot-on-hit", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        print("=" * 60)
        print("WARNING: This command uses hardware watchpoints which")
        print("do NOT work with the melonDS GDB stub!")
        print("=" * 60)
        print()
        print("Use this instead (works reliably):")
        print("  jus-auto-snapshot-on-damage <player> [prefix]")
        print()
        print("Example:")
        print("  jus-auto-snapshot-on-damage 1 goku")
        print()

        # Still allow attempting it in case user has different emulator
        args = arg.split()
        if not args:
            return

        player = int(args[0])
        prefix = args[1] if len(args) > 1 else "auto"

        if player < 1 or player > 4:
            print("Player must be 1-4")
            return

        print("Attempting anyway (may fail with melonDS)...")
        try:
            bp = HitTriggerBreakpoint(player, prefix)
            self._active_breakpoints.append(bp)
            print(f"Watchpoint created for player {player}")
        except (gdb.error, RuntimeError) as e:
            print(f"Failed (as expected with melonDS): {e}")


class JUSAutoSnapshotOff(gdb.Command):
    """Disable all automatic snapshot triggers and show capture summary."""

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

        # Show summary of captured snapshots
        if not _char_snapshots:
            print("\nNo snapshots captured.")
            return

        print(f"\n=== Capture Summary ({len(_char_snapshots)} snapshots) ===")

        # Group by type
        hit_snaps = []
        dmg_snaps = []
        state_snaps = []
        other_snaps = []

        for name, snap in _char_snapshots.items():
            if 'hp_before' in snap and 'hp_after' in snap:
                hp_b, hp_a = snap['hp_before'], snap['hp_after']
                entry = f"{name}: HP {hp_b} -> {hp_a}"
                if snap.get('timing') == 'at_damage_code':
                    dmg_snaps.append(entry)
                else:
                    hit_snaps.append(entry)
            elif 'state_from' in snap:
                state_snaps.append(f"{name}: {snap['state_from']} -> {snap['state_to']}")
            else:
                other_snaps.append(name)

        if hit_snaps:
            print(f"\nHP Change (on-hit): {len(hit_snaps)}")
            for s in hit_snaps[-5:]:  # Show last 5
                print(f"  {s}")
            if len(hit_snaps) > 5:
                print(f"  ... and {len(hit_snaps) - 5} more")

        if dmg_snaps:
            print(f"\nDamage Code: {len(dmg_snaps)}")
            for s in dmg_snaps[-5:]:
                print(f"  {s}")
            if len(dmg_snaps) > 5:
                print(f"  ... and {len(dmg_snaps) - 5} more")

        if state_snaps:
            print(f"\nState Changes: {len(state_snaps)}")
            for s in state_snaps[-5:]:
                print(f"  {s}")
            if len(state_snaps) > 5:
                print(f"  ... and {len(state_snaps) - 5} more")

        if other_snaps:
            print(f"\nOther: {len(other_snaps)}")
            for s in other_snaps[-5:]:
                print(f"  {s}")
            if len(other_snaps) > 5:
                print(f"  ... and {len(other_snaps) - 5} more")

        print()
        print("Next steps:")
        print("  jus-snapshot-list              - Full list with metadata")
        print("  jus-char-diff <s1> <s2>        - Compare two snapshots")
        print("  jus-compare-field 0x0078 <s1> <s2>  - Compare specific field")


class StateTriggerBreakpoint(gdb.Breakpoint):
    """Internal breakpoint that triggers on ground/air state change.

    Watches the ground_air field in the character struct.
    Note: The watchpoint address is captured at init time. If the
    character struct moves, this may become stale.
    """

    def __init__(self, player, snapshot_name_prefix):
        self.player = player
        self.prefix = snapshot_name_prefix
        self.state_count = 0
        self.ptr_addr = ADDRESSES[f'player{player}_state_ptr']

        # Get character struct pointer to find state address
        ptr = read_dword(self.ptr_addr)

        if not ptr or ptr < 0x02000000:
            raise ValueError(f"Player {player} state pointer invalid")

        # Watch the ground_air field
        state_addr = ptr + CHAR_OFFSETS['ground_air']
        super().__init__(f"*{state_addr:#x}", type=gdb.BP_WATCHPOINT, wp_class=gdb.WP_WRITE)
        self.silent = True
        self.state_addr = state_addr

        # Initialize from current value
        self.last_state = read_byte(state_addr)

    def stop(self):
        """Called when ground/air state changes."""
        state = read_byte(self.state_addr)

        # Handle read failure
        if state is None:
            return False

        if self.last_state is not None and state != self.last_state:
            self.state_count += 1

            # Decode state
            state_name = "air" if state == 0x00 else "ground" if state == 0x22 else f"0x{state:02X}"
            last_name = "air" if self.last_state == 0x00 else "ground" if self.last_state == 0x22 else f"0x{self.last_state:02X}"

            name = f"{self.prefix}_state{self.state_count}"

            # Re-read pointer in case it changed
            ptr = read_dword(self.ptr_addr)

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

    WARNING: This uses hardware watchpoints which do NOT work with melonDS!

    Usage: jus-auto-snapshot-on-state <player> [prefix]
    """

    _active_breakpoints = []

    def __init__(self):
        super().__init__("jus-auto-snapshot-on-state", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        print("=" * 60)
        print("WARNING: This command uses hardware watchpoints which")
        print("do NOT work with the melonDS GDB stub!")
        print("=" * 60)
        print()
        print("For damage-based capture, use:")
        print("  jus-auto-snapshot-on-damage <player> [prefix]")
        print()

        args = arg.split()
        if not args:
            return

        try:
            player = int(args[0])
        except ValueError:
            print("Player must be a number 1-4")
            return

        prefix = args[1] if len(args) > 1 else "state"

        if player < 1 or player > 4:
            print("Player must be 1-4")
            return

        print("Attempting anyway (may fail with melonDS)...")
        try:
            bp = StateTriggerBreakpoint(player, prefix)
            self._active_breakpoints.append(bp)
            JUSAutoSnapshotOnHit._active_breakpoints.append(bp)
            print(f"Watchpoint created for player {player}")
        except (ValueError, gdb.error, RuntimeError) as e:
            print(f"Failed: {e}")


class StatusTriggerBreakpoint(gdb.Breakpoint):
    """Internal breakpoint that triggers on positive/negative status changes.

    This may catch hitstun state transitions since hitstun might be
    encoded in the status fields.
    """

    def __init__(self, player, snapshot_name_prefix, status_type='positive'):
        self.player = player
        self.prefix = snapshot_name_prefix
        self.status_type = status_type
        self.change_count = 0
        self.ptr_addr = ADDRESSES[f'player{player}_state_ptr']

        # Get character struct pointer
        ptr = read_dword(self.ptr_addr)

        if not ptr or ptr < 0x02000000:
            raise ValueError(f"Player {player} state pointer invalid")

        # Watch the status field
        offset = CHAR_OFFSETS['positive_status'] if status_type == 'positive' else CHAR_OFFSETS['negative_status']
        status_addr = ptr + offset
        super().__init__(f"*{status_addr:#x}", type=gdb.BP_WATCHPOINT, wp_class=gdb.WP_WRITE)
        self.silent = True
        self.status_addr = status_addr
        self.offset = offset

        # Initialize from current value
        self.last_status = read_byte(status_addr)

    def stop(self):
        """Called when status changes."""
        status = read_byte(self.status_addr)

        if status is None:
            return False

        if self.last_status is not None and status != self.last_status:
            self.change_count += 1
            name = f"{self.prefix}_{self.status_type}{self.change_count}"

            ptr = read_dword(self.ptr_addr)

            if ptr and ptr >= 0x02000000:
                data = read_bytes(ptr, 0x120)
                if data:
                    _char_snapshots[name] = {
                        'data': data,
                        'ptr': ptr,
                        'player': self.player,
                        'status_type': self.status_type,
                        'status_from': self.last_status,
                        'status_to': status,
                    }
                    print(f"\n[AUTO] Snapshot '{name}' captured ({self.status_type}: 0x{self.last_status:02X} -> 0x{status:02X})")

        self.last_status = status
        return False


class JUSAutoSnapshotOnStatus(gdb.Command):
    """Automatically take snapshots when status fields change.

    WARNING: This uses hardware watchpoints which do NOT work with melonDS!

    Usage: jus-auto-snapshot-on-status <player> [prefix] [type]
    """

    def __init__(self):
        super().__init__("jus-auto-snapshot-on-status", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        print("=" * 60)
        print("WARNING: This command uses hardware watchpoints which")
        print("do NOT work with the melonDS GDB stub!")
        print("=" * 60)
        print()
        print("For damage-based capture, use:")
        print("  jus-auto-snapshot-on-damage <player> [prefix]")
        print()

        args = arg.split()
        if not args:
            return

        try:
            player = int(args[0])
        except ValueError:
            print("Player must be a number 1-4")
            return

        prefix = args[1] if len(args) > 1 else "status"
        status_type = args[2] if len(args) > 2 else "both"

        if player < 1 or player > 4:
            print("Player must be 1-4")
            return

        print("Attempting anyway (may fail with melonDS)...")
        try:
            types_to_watch = ["positive", "negative"] if status_type == "both" else [status_type]
            for st in types_to_watch:
                bp = StatusTriggerBreakpoint(player, prefix, st)
                JUSAutoSnapshotOnHit._active_breakpoints.append(bp)
            print(f"Watchpoints created for player {player}")
        except (ValueError, gdb.error, RuntimeError) as e:
            print(f"Failed: {e}")


class DamageCodeBreakpoint(gdb.Breakpoint):
    """Breakpoint at damage calculation function.

    This triggers BEFORE HP is decremented, which may be closer to
    the actual moment knockback velocity is applied.

    NOTE: The damage code fires VERY frequently (~every few ms) even during
    idle time, not just when damage is dealt. We filter by tracking HP and
    only capturing when HP actually decreases.
    """

    def __init__(self, slot, snapshot_name_prefix, debug=False, is_opponent=False, is_active=False):
        self.slot = slot
        self.is_opponent = is_opponent
        self.is_active = is_active
        self.prefix = snapshot_name_prefix
        self.trigger_count = 0
        self.debug = debug

        # Get HP address based on target
        if is_opponent:
            if is_active:
                hp_addr = ADDRESSES['opponent_active_hp']
            else:
                hp_addr = ADDRESSES[f'opponent_deck{slot-1}_hp']
            # For opponents, we don't have state pointers yet
            # TODO: Find opponent state pointer addresses
            self.ptr_addr = None  # Don't capture invalid data
        else:
            if is_active:
                hp_addr = ADDRESSES['player_active_hp']
                self.ptr_addr = ADDRESSES['player1_state_ptr']
            else:
                hp_addr = ADDRESSES[f'player_deck{slot-1}_hp']
                self.ptr_addr = ADDRESSES.get(f'player{slot}_state_ptr')

        self.hp_addr = hp_addr
        self.last_hp = read_byte(hp_addr)
        self.call_count = 0  # Track total calls for debugging

        # Break at health calculation code
        addr = ADDRESSES['health_code']
        super().__init__(f"*{addr:#x}", type=gdb.BP_BREAKPOINT)
        self.silent = True

    def stop(self):
        """Called when damage code is reached.

        Only captures snapshot when HP has DECREASED since last check.
        This filters out the constant noise from damage code firing during idle.
        """
        self.call_count += 1

        # Read current HP
        current_hp = read_byte(self.hp_addr)
        if current_hp is None:
            if self.debug:
                print(f"[DEBUG] Call #{self.call_count}: HP read failed")
            return False

        # Debug: show HP values periodically
        if self.debug and self.call_count <= 5:
            target = f"opponent{self.slot}" if self.is_opponent else f"player{self.slot}"
            print(f"[DEBUG] Call #{self.call_count}: {target} HP addr={self.hp_addr:#x}, current={current_hp}, last={self.last_hp}")

        # Only trigger on HP decrease (actual damage taken)
        if self.last_hp is None or current_hp >= self.last_hp:
            # HP didn't decrease - this is noise, skip it
            # But if HP INCREASED, that's a heal or reset - update tracking
            if current_hp != self.last_hp:
                if self.debug:
                    print(f"[DEBUG] HP changed but not decrease: {self.last_hp} -> {current_hp}")
                self.last_hp = current_hp
            return False

        # HP decreased! This is a real damage event
        self.trigger_count += 1
        name = f"{self.prefix}_dmg{self.trigger_count}"

        # For opponents, we may not have valid state pointer - just log HP change
        ptr = read_dword(self.ptr_addr) if self.ptr_addr else None

        if self.is_active:
            target_name = "opponent_active" if self.is_opponent else "player_active"
        else:
            target_name = f"opponent_deck{self.slot-1}" if self.is_opponent else f"player_deck{self.slot-1}"
        displayed_before = self.last_hp * 4
        displayed_after = current_hp * 4
        damage = displayed_before - displayed_after

        if ptr and ptr >= 0x02000000:
            data = read_bytes(ptr, 0x120)
            if data:
                # Capture with HP change info
                _char_snapshots[name] = {
                    'data': data,
                    'ptr': ptr,
                    'slot': self.slot,
                    'is_opponent': self.is_opponent,
                    'timing': 'at_damage_code',
                    'hp_before': self.last_hp,
                    'hp_after': current_hp,
                }
                print(f"\n[AUTO] Snapshot '{name}' captured ({target_name} HP: {displayed_before} -> {displayed_after}, dmg: {damage})")
        else:
            # No state pointer (e.g., opponent) - just log the HP change
            print(f"\n[AUTO] {target_name} took {damage} damage (HP: {displayed_before} -> {displayed_after})")

        self.last_hp = current_hp
        return False  # Continue running


class JUSAutoSnapshotOnDamageCode(gdb.Command):
    """Capture state when damage calculation code is reached AND HP decreases.

    Usage: jus-auto-snapshot-on-damage <target> [prefix] [debug]

    Target can be:
      me / player / 1    Your active character
      2-4                Your deck members (supports, tagged out)
      opp / enemy / o1   Opponent's active character
      o2-o4              Opponent's deck members

    This breakpoints on the damage calculation function (0x020784FC),
    which fires BEFORE HP is decremented. Snapshots are only captured
    when HP actually DECREASES - filtering out the constant noise from
    the damage code firing during idle time (~every few ms).

    Examples:
      jus-auto-snapshot-on-damage me goku       # You take damage
      jus-auto-snapshot-on-damage opp enemy     # Opponent takes damage
      jus-auto-snapshot-on-damage 2 support     # Your deck slot 2
    """

    def __init__(self):
        super().__init__("jus-auto-snapshot-on-damage", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-auto-snapshot-on-damage <target> [prefix] [debug]")
            print()
            print("Target can be:")
            print("  me / player / 1    Your active character")
            print("  2-4                Your deck members")
            print("  opp / enemy / o1   Opponent's active character")
            print("  o2-o4              Opponent's deck members")
            print()
            print("Examples:")
            print("  jus-auto-snapshot-on-damage me goku     # You take damage")
            print("  jus-auto-snapshot-on-damage opp enemy   # Opponent takes damage")
            print()
            print("Add 'debug' as last arg to see HP values being read.")
            return

        target = args[0].lower()
        prefix = args[1] if len(args) > 1 else "dmg"
        debug = len(args) > 2 and args[-1].lower() == 'debug'

        # Parse target
        is_opponent = False
        is_active = False
        slot = None

        if target in ('me', 'player', '1'):
            is_active = True
            slot = 1
        elif target in ('opp', 'opponent', 'enemy', 'o1'):
            is_opponent = True
            is_active = True
            slot = 1
        elif target.isdigit():
            slot = int(target)
            if slot < 1 or slot > 4:
                print("Slot must be 1-4")
                return
            is_active = (slot == 1)
        elif target.startswith('o') and len(target) == 2 and target[1].isdigit():
            slot = int(target[1])
            is_opponent = True
            is_active = (slot == 1)
        else:
            print(f"Invalid target: {target}")
            print("Use: me, opp, 1-4, o1-o4")
            return

        if slot < 1 or slot > 4:
            print("Slot must be 1-4")
            return

        bp = DamageCodeBreakpoint(slot, prefix, debug=debug, is_opponent=is_opponent, is_active=is_active)
        JUSAutoSnapshotOnHit._active_breakpoints.append(bp)

        if is_active:
            target_name = "Opponent active" if is_opponent else "Your active"
        else:
            target_name = f"Opponent deck {slot-1}" if is_opponent else f"Your deck {slot-1}"

        print(f"=== Auto-Snapshot on Damage Code ENABLED ===")
        print(f"Target: {target_name}")
        print(f"Prefix: {prefix}")
        print(f"Breakpoint at: {ADDRESSES['health_code']:#010x}")
        print(f"HP address: {bp.hp_addr:#010x}")
        print(f"Current HP value: {bp.last_hp} (displayed: ~{bp.last_hp * 4 if bp.last_hp else 0})")
        if is_opponent:
            print()
            print("NOTE: Opponent state pointer not yet known - will log HP changes")
            print("      but won't capture character struct snapshots.")
        if debug:
            print(f"DEBUG MODE: Will show HP values for first 5 calls")
        print()
        print("This fires BEFORE HP is decremented.")
        print("NOTE: Only captures when HP actually DECREASES (filters idle noise).")
        print("Use 'continue' to resume. Stop with: jus-auto-snapshot-off")


# ============================================================================
# VELOCITY LOGGING (lightweight alternative to full snapshots)
# ============================================================================

# Global log storage for velocity logger
_velocity_log = []


class VelocityLoggerBreakpoint(gdb.Breakpoint):
    """Breakpoint that logs specific offsets when HP changes.

    This is a lightweight alternative to full snapshots - it only logs
    the specific offsets that are likely to contain velocity/physics data,
    making it easier to analyze without storing full 288-byte snapshots.
    """

    # Default offsets to log (physics/velocity region)
    DEFAULT_OFFSETS = [
        0x006A, 0x006C, 0x006E,  # Possible velocity region
        0x0070, 0x0072, 0x0074, 0x0076,  # Near ground_air
        0x0078,  # ground_air state
        0x007A, 0x007C, 0x007E,  # After ground_air
        0x0098, 0x009A,  # Timer region start
    ]

    def __init__(self, player, offsets=None, log_file=None):
        self.player = player
        self.offsets = offsets or self.DEFAULT_OFFSETS
        self.log_file = log_file
        self.ptr_addr = ADDRESSES[f'player{player}_state_ptr']
        self.trigger_count = 0

        # Track HP to filter noise
        hp_addr = ADDRESSES[f'player{player}_hp']
        self.hp_addr = hp_addr
        self.last_hp = read_byte(hp_addr)

        # Break at health calculation code
        addr = ADDRESSES['health_code']
        super().__init__(f"*{addr:#x}", type=gdb.BP_BREAKPOINT)
        self.silent = True

    def stop(self):
        """Called when damage code is reached."""
        # Read current HP
        current_hp = read_byte(self.hp_addr)
        if current_hp is None:
            return False

        # Only trigger on HP decrease
        if self.last_hp is None or current_hp >= self.last_hp:
            self.last_hp = current_hp
            return False

        # HP decreased! Log the physics values
        self.trigger_count += 1

        ptr = read_dword(self.ptr_addr)
        if not ptr or ptr < 0x02000000:
            self.last_hp = current_hp
            return False

        # Read values at each offset
        entry = {
            'hit': self.trigger_count,
            'player': self.player,
            'hp_before': self.last_hp,
            'hp_after': current_hp,
            'damage': self.last_hp - current_hp,
            'values': {},
        }

        for offset in self.offsets:
            val = read_word(ptr + offset)
            if val is not None:
                # Store both unsigned and signed interpretations
                sval = struct.unpack('<h', struct.pack('<H', val))[0]
                entry['values'][offset] = {'unsigned': val, 'signed': sval}

        _velocity_log.append(entry)

        # Print summary
        print(f"\n[VELOCITY] Hit #{self.trigger_count} (HP: {self.last_hp} -> {current_hp}, dmg: {entry['damage']})")

        # Print key values
        ground_air = entry['values'].get(0x0078, {}).get('unsigned', 0)
        state_name = GROUND_AIR_STATES.get(ground_air & 0xFF, f"0x{ground_air:04X}")
        print(f"  State: {state_name}")

        # Print velocity candidates (signed values)
        vel_offsets = [0x006A, 0x006C, 0x006E, 0x0070, 0x0072, 0x0074]
        vel_str = " ".join(f"{entry['values'].get(o, {}).get('signed', 0):+5d}" for o in vel_offsets)
        print(f"  Velocity region: {vel_str}")

        # Write to file if specified
        if self.log_file:
            import json
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')

        self.last_hp = current_hp
        return False


class JUSVelocityLog(gdb.Command):
    """Log velocity/physics values when damage is taken.

    Usage: jus-velocity-log <player> [file]

    This is a lightweight alternative to full snapshots. It logs only
    the specific offsets likely to contain velocity/physics data each
    time HP decreases.

    The logged offsets include:
    - 0x006A-0x007E: Likely velocity/position region
    - 0x0078: Ground/air state
    - 0x0098-0x009A: Timer region start

    Example:
        jus-velocity-log 1                    # Log to console only
        jus-velocity-log 1 /tmp/velocity.log  # Also save to file

    To view logged data: jus-velocity-show
    To clear log: jus-velocity-clear
    """

    def __init__(self):
        super().__init__("jus-velocity-log", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-velocity-log <player 1-4> [log_file]")
            print()
            print("Logs velocity/physics values when HP decreases.")
            print("Lighter weight than full snapshots.")
            print()
            print("View data: jus-velocity-show")
            print("Clear log: jus-velocity-clear")
            return

        try:
            player = int(args[0])
        except ValueError:
            print("Player must be a number 1-4")
            return

        if player < 1 or player > 4:
            print("Player must be 1-4")
            return

        log_file = args[1] if len(args) > 1 else None

        bp = VelocityLoggerBreakpoint(player, log_file=log_file)
        JUSAutoSnapshotOnHit._active_breakpoints.append(bp)

        print(f"=== Velocity Logger ENABLED ===")
        print(f"Player: {player}")
        print(f"Current HP: {bp.last_hp}")
        if log_file:
            print(f"Log file: {log_file}")
        print()
        print("Logs physics values when HP decreases.")
        print("Use 'continue' to resume. Stop with: jus-auto-snapshot-off")


class JUSVelocityShow(gdb.Command):
    """Show the velocity log entries.

    Usage: jus-velocity-show [last_n]

    Shows logged velocity data from jus-velocity-log.
    Optionally show only the last N entries.
    """

    def __init__(self):
        super().__init__("jus-velocity-show", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        if not _velocity_log:
            print("No velocity data logged yet.")
            print("Use 'jus-velocity-log <player>' to start logging.")
            return

        args = arg.split()
        last_n = int(args[0]) if args else len(_velocity_log)

        entries = _velocity_log[-last_n:]

        print(f"=== Velocity Log ({len(entries)} entries) ===")
        print()

        for entry in entries:
            print(f"Hit #{entry['hit']}: HP {entry['hp_before']} -> {entry['hp_after']} (dmg: {entry['damage']})")

            # Ground/air state
            ground_air = entry['values'].get(0x0078, {}).get('unsigned', 0)
            state_name = GROUND_AIR_STATES.get(ground_air & 0xFF, f"0x{ground_air:04X}")
            print(f"  State: {state_name}")

            # All values
            print("  Offsets:")
            for offset in sorted(entry['values'].keys()):
                val = entry['values'][offset]
                known = ""
                for name, off in CHAR_OFFSETS.items():
                    if offset == off:
                        known = f" [{name}]"
                        break
                print(f"    +{offset:04X}: {val['signed']:+6d} (0x{val['unsigned']:04X}){known}")
            print()


class JUSVelocityClear(gdb.Command):
    """Clear the velocity log."""

    def __init__(self):
        super().__init__("jus-velocity-clear", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        global _velocity_log
        count = len(_velocity_log)
        _velocity_log = []
        print(f"Cleared {count} velocity log entries.")


class JUSBaselineNoise(gdb.Command):
    """Capture timer/noise fields by snapshotting during idle time.

    Usage: jus-baseline-noise <player> [count] [prefix]

    Takes multiple snapshots. You manually continue/pause between each.
    Fields that change between these snapshots are timers/counters
    that should be IGNORED when analyzing physics/combat data.

    NOTE: melonDS GDB stub doesn't support stepi well, so this command
    now requires manual continue/Ctrl+C between snapshots.

    Example workflow:
    1. Get into battle, have both characters stand still
    2. jus-baseline-noise 1 5 idle
    3. Type 'c', wait 1 second, Ctrl+C
    4. Repeat step 3 until all snapshots captured
    5. jus-find-timers idle
    """

    def __init__(self):
        super().__init__("jus-baseline-noise", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-baseline-noise <player 1-4> [count] [prefix]")
            print()
            print("Takes snapshots during idle time to identify timer fields.")
            print("Run this command repeatedly - it captures one snapshot each time.")
            print()
            print("Workflow:")
            print("  1. jus-baseline-noise 1 5 idle   # Start capture")
            print("  2. c                              # Continue game")
            print("  3. (wait ~1 second)")
            print("  4. Ctrl+C                         # Pause")
            print("  5. jus-baseline-noise 1 5 idle   # Capture next")
            print("  6. Repeat until done")
            print("  7. jus-find-timers idle")
            return

        try:
            player = int(args[0])
        except ValueError:
            print("Player must be a number 1-4")
            return

        count = int(args[1]) if len(args) > 1 else 5
        prefix = args[2] if len(args) > 2 else "baseline"

        if player < 1 or player > 4:
            print("Player must be 1-4")
            return

        ptr_addr = ADDRESSES[f'player{player}_state_ptr']

        # Check how many we already have
        existing = [k for k in _char_snapshots.keys()
                   if k.startswith(prefix + "_") and _char_snapshots[k].get('baseline')]
        current_idx = len(existing)

        if current_idx >= count:
            print(f"Already have {current_idx} snapshots with prefix '{prefix}'.")
            print(f"Use 'jus-find-timers {prefix}' to analyze them.")
            print(f"Or use a different prefix to start fresh.")
            return

        # Capture one snapshot
        ptr = read_dword(ptr_addr)
        if not ptr or ptr < 0x02000000:
            print(f"Player {player} state pointer invalid: {ptr:#x if ptr else 'NULL'}")
            return

        data = read_bytes(ptr, 0x120)
        if data:
            name = f"{prefix}_{current_idx}"
            _char_snapshots[name] = {
                'data': data,
                'ptr': ptr,
                'player': player,
                'baseline': True,
                'index': current_idx,
            }
            print(f"Captured: {name} ({current_idx + 1}/{count})")

            remaining = count - current_idx - 1
            if remaining > 0:
                print(f"\n{remaining} more needed. Now:")
                print("  1. Type 'c' to continue")
                print("  2. Wait ~1 second")
                print("  3. Press Ctrl+C")
                print(f"  4. Run: jus-baseline-noise {player} {count} {prefix}")
            else:
                print(f"\nAll {count} snapshots captured!")
                print(f"Run: jus-find-timers {prefix}")
        else:
            print("Failed to read character data")


class JUSBaselineTimed(gdb.Command):
    """Capture timer/noise fields using timed continues (more realistic timing).

    Usage: jus-baseline-timed <player> [count] [prefix]

    Like jus-baseline-noise but uses brief 'continue' periods instead of
    'stepi'. This lets the game run at full speed for a short time,
    which is more likely to trigger timer changes.

    The downside is less control over exact timing - the game runs
    freely until you Ctrl+C again.

    Workflow:
    1. Run: jus-baseline-timed 1 5 idle
    2. After each snapshot, press Enter to continue briefly
    3. Press Ctrl+C after a moment to capture next snapshot
    4. Repeat until all snapshots taken
    5. Run: jus-find-timers idle
    """

    def __init__(self):
        super().__init__("jus-baseline-timed", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-baseline-timed <player 1-4> [count] [prefix]")
            print()
            print("Takes snapshots with 'continue' between them.")
            print("More realistic timing than stepi, but requires manual Ctrl+C.")
            return

        try:
            player = int(args[0])
        except ValueError:
            print("Player must be a number 1-4")
            return

        count = int(args[1]) if len(args) > 1 else 5
        prefix = args[2] if len(args) > 2 else "baseline"

        if player < 1 or player > 4:
            print("Player must be 1-4")
            return

        ptr_addr = ADDRESSES[f'player{player}_state_ptr']

        print(f"=== Baseline Timed Capture ===")
        print(f"Taking {count} snapshots")
        print(f"Player: {player}, Prefix: {prefix}")
        print()
        print("Make sure both characters are STANDING STILL.")
        print()
        print("After each snapshot:")
        print("  1. Type 'continue' (or 'c') and press Enter")
        print("  2. Wait ~0.5 seconds")
        print("  3. Press Ctrl+C to pause")
        print("  4. Run this command again with same args to continue")
        print()

        # Check how many we already have with this prefix
        existing = [k for k in _char_snapshots.keys()
                   if k.startswith(prefix + "_") and _char_snapshots[k].get('baseline')]
        start_idx = len(existing)

        if start_idx >= count:
            print(f"Already have {start_idx} snapshots with prefix '{prefix}'.")
            print(f"Use 'jus-find-timers {prefix}' to analyze them.")
            return

        # Take one snapshot
        ptr = read_dword(ptr_addr)
        if ptr and ptr >= 0x02000000:
            data = read_bytes(ptr, 0x120)
            if data:
                name = f"{prefix}_{start_idx}"
                _char_snapshots[name] = {
                    'data': data,
                    'ptr': ptr,
                    'player': player,
                    'baseline': True,
                    'index': start_idx,
                }
                print(f"Captured: {name} ({start_idx + 1}/{count})")

        remaining = count - start_idx - 1
        if remaining > 0:
            print(f"\n{remaining} more snapshot(s) needed.")
            print("Type 'c' to continue, wait briefly, then Ctrl+C and run this again.")
        else:
            print(f"\nAll {count} snapshots captured!")
            print(f"Run: jus-find-timers {prefix}")


class JUSFindTimers(gdb.Command):
    """Analyze baseline snapshots to find timer/counter fields.

    Usage: jus-find-timers <prefix>

    Compares snapshots with the given prefix to find fields that
    change over time even with no input. These are timers/counters
    that should be IGNORED in physics analysis.
    """

    def __init__(self):
        super().__init__("jus-find-timers", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        if not arg:
            print("Usage: jus-find-timers <prefix>")
            print("Example: jus-find-timers baseline")
            return

        prefix = arg.strip()

        # Find all snapshots with this prefix
        matching = [(k, v) for k, v in _char_snapshots.items()
                    if k.startswith(prefix + "_") and v.get('baseline')]

        if len(matching) < 2:
            print(f"Need at least 2 baseline snapshots with prefix '{prefix}'")
            print(f"Found: {[k for k, v in matching]}")
            return

        # Sort by index
        matching.sort(key=lambda x: x[1].get('index', 0))

        print(f"=== Timer/Noise Analysis: {prefix} ===")
        print(f"Comparing {len(matching)} baseline snapshots")
        print()

        # Track which offsets change between ANY pair of snapshots
        always_changing = set()
        sometimes_changing = set()

        for i in range(len(matching) - 1):
            name1, snap1 = matching[i]
            name2, snap2 = matching[i + 1]
            data1, data2 = snap1['data'], snap2['data']

            for offset in range(0, min(len(data1), len(data2)) - 1, 2):
                word1 = struct.unpack('<H', data1[offset:offset+2])[0]
                word2 = struct.unpack('<H', data2[offset:offset+2])[0]

                if word1 != word2:
                    if i == 0:
                        always_changing.add(offset)
                    elif offset in always_changing:
                        pass  # Still in always_changing
                    else:
                        sometimes_changing.add(offset)
                else:
                    if offset in always_changing:
                        always_changing.remove(offset)
                        sometimes_changing.add(offset)

        print("=== ALWAYS CHANGING (definite timers - ignore these) ===")
        if always_changing:
            for offset in sorted(always_changing):
                # Show sample values
                vals = []
                for name, snap in matching[:3]:
                    word = struct.unpack('<H', snap['data'][offset:offset+2])[0]
                    vals.append(str(word))
                print(f"  +{offset:04X}: {' -> '.join(vals)} ...")
        else:
            print("  (none found - good, less noise!)")

        print()
        print("=== SOMETIMES CHANGING (may be timers or state) ===")
        if sometimes_changing:
            for offset in sorted(sometimes_changing):
                vals = []
                for name, snap in matching[:3]:
                    word = struct.unpack('<H', snap['data'][offset:offset+2])[0]
                    vals.append(str(word))
                print(f"  +{offset:04X}: {' -> '.join(vals)} ...")
        else:
            print("  (none found)")

        # Store the timer offsets for filtering
        global _known_timer_offsets
        _known_timer_offsets = always_changing | sometimes_changing

        print()
        print(f"Total timer/noise offsets identified: {len(_known_timer_offsets)}")
        print("These will be highlighted in future jus-char-diff output.")


# Global set to track known timer offsets
_known_timer_offsets = set()


class JUSCharValues(gdb.Command):
    """Show actual values from a stored character snapshot.

    Usage: jus-char-values <snapshot_name> [start_offset] [end_offset]

    Unlike jus-char-diff which shows deltas, this shows the actual
    stored values at specific offsets. Useful for comparing absolute
    values between different characters.

    Example:
        jus-char-values nami_hit1 0x0070 0x00C0
        jus-char-values raoh_hit1 0x0070 0x00C0
    """

    def __init__(self):
        super().__init__("jus-char-values", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if not args:
            print("Usage: jus-char-values <snapshot_name> [start_offset] [end_offset]")
            print("Stored snapshots:", list(_char_snapshots.keys()))
            return

        name = args[0]
        start_off = int(args[1], 0) if len(args) > 1 else 0x0070
        end_off = int(args[2], 0) if len(args) > 2 else 0x00C0

        if name not in _char_snapshots:
            print(f"Snapshot '{name}' not found")
            print("Available:", list(_char_snapshots.keys()))
            return

        snap = _char_snapshots[name]
        data = snap['data']

        print(f"=== Snapshot '{name}' Values ===")
        print(f"Player: {snap.get('player', '?')}")
        if 'hp_before' in snap:
            print(f"HP: {snap['hp_before']} -> {snap['hp_after']}")
        print(f"Offsets: {start_off:#04x} to {end_off:#04x}")
        print()

        # Print as 16-bit signed values with annotations
        print("Offset    Unsigned   Signed    Hex       Notes")
        print("-" * 60)

        for offset in range(start_off, min(end_off, len(data) - 1), 2):
            if offset + 2 > len(data):
                break

            uval = struct.unpack('<H', data[offset:offset+2])[0]
            sval = struct.unpack('<h', data[offset:offset+2])[0]

            # Check for known offsets
            notes = []
            for field_name, field_off in CHAR_OFFSETS.items():
                if offset == field_off:
                    notes.append(f"[{field_name}]")
                    break

            # Check ground_air state
            if offset == 0x0078:
                low_byte = data[offset]
                state_name = GROUND_AIR_STATES.get(low_byte, f"unknown(0x{low_byte:02X})")
                notes.append(f"state={state_name}")

            # Check if in timer region
            if offset in TIMER_REGION_OFFSETS:
                notes.append("[timer]")

            note_str = " ".join(notes)
            print(f"+{offset:04X}:   {uval:6d}    {sval:6d}    0x{uval:04X}    {note_str}")


class JUSCompareSnapshots(gdb.Command):
    """Compare specific field values across multiple snapshots.

    Usage: jus-compare-field <offset> <snapshot1> <snapshot2> [snapshot3] ...

    Shows the actual value at a specific offset across multiple snapshots.
    Useful for tracking how a single field changes over time or between
    characters.

    Example:
        jus-compare-field 0x0078 nami_hit1 nami_hit2 nami_hit3
        jus-compare-field 0x0098 nami_hit1 raoh_hit1
    """

    def __init__(self):
        super().__init__("jus-compare-field", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if len(args) < 3:
            print("Usage: jus-compare-field <offset> <snapshot1> <snapshot2> ...")
            print("Example: jus-compare-field 0x0078 nami_hit1 raoh_hit1")
            return

        try:
            offset = int(args[0], 0)
        except ValueError:
            print(f"Invalid offset: {args[0]}")
            return

        snapshots = args[1:]

        print(f"=== Field +{offset:04X} Comparison ===")
        print()

        # Check for known field name
        for field_name, field_off in CHAR_OFFSETS.items():
            if offset == field_off:
                print(f"Known field: {field_name}")
                break

        if offset in TIMER_REGION_OFFSETS:
            print("Note: This is in the timer region")

        print()
        print(f"{'Snapshot':<30} {'Unsigned':>8} {'Signed':>8} {'Hex':>8}")
        print("-" * 60)

        for name in snapshots:
            if name not in _char_snapshots:
                print(f"{name:<30} (not found)")
                continue

            data = _char_snapshots[name]['data']
            if offset + 2 > len(data):
                print(f"{name:<30} (offset out of range)")
                continue

            uval = struct.unpack('<H', data[offset:offset+2])[0]
            sval = struct.unpack('<h', data[offset:offset+2])[0]

            # Special handling for ground_air
            extra = ""
            if offset == 0x0078:
                low_byte = data[offset]
                state = GROUND_AIR_STATES.get(low_byte, "")
                if state:
                    extra = f"  <- {state}"

            print(f"{name:<30} {uval:>8} {sval:>8}   0x{uval:04X}{extra}")


class JUSSnapshotList(gdb.Command):
    """List all stored character snapshots with metadata.

    Usage: jus-snapshot-list [prefix]

    Shows all stored snapshots with their metadata including:
    - Player number
    - HP change (if captured during damage)
    - State change (if captured during state transition)
    - Snapshot type (baseline, hit, damage, state, etc.)

    Optionally filter by prefix to show only matching snapshots.

    Example:
        jus-snapshot-list           # Show all
        jus-snapshot-list goku      # Show only goku_* snapshots
    """

    def __init__(self):
        super().__init__("jus-snapshot-list", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        prefix = arg.strip() if arg else None

        if not _char_snapshots:
            print("No character snapshots stored.")
            print()
            print("Capture snapshots with:")
            print("  jus-char-snapshot <name> [player]")
            print("  jus-auto-snapshot-on-hit <player> [prefix]")
            print("  jus-auto-snapshot-on-damage <player> [prefix]")
            return

        # Filter by prefix if provided
        if prefix:
            snapshots = {k: v for k, v in _char_snapshots.items()
                        if k.startswith(prefix)}
            if not snapshots:
                print(f"No snapshots with prefix '{prefix}'")
                print(f"Available: {list(_char_snapshots.keys())}")
                return
        else:
            snapshots = _char_snapshots

        print(f"=== Character Snapshots ({len(snapshots)} stored) ===")
        print()
        print(f"{'Name':<25} {'Player':>6} {'Type':<12} {'Details'}")
        print("-" * 70)

        for name in sorted(snapshots.keys()):
            snap = snapshots[name]
            player = snap.get('player', '?')

            # Determine type and details
            if snap.get('baseline'):
                snap_type = "baseline"
                details = f"index {snap.get('index', '?')}"
            elif 'hp_before' in snap and 'hp_after' in snap:
                hp_b, hp_a = snap['hp_before'], snap['hp_after']
                if snap.get('timing') == 'at_damage_code':
                    snap_type = "damage"
                else:
                    snap_type = "hit"
                details = f"HP: {hp_b} -> {hp_a} (dmg: {hp_b - hp_a})"
            elif 'state_from' in snap and 'state_to' in snap:
                snap_type = "state"
                details = f"{snap['state_from']} -> {snap['state_to']}"
            elif 'status_type' in snap:
                snap_type = "status"
                s_from = snap.get('status_from', '?')
                s_to = snap.get('status_to', '?')
                details = f"{snap['status_type']}: 0x{s_from:02X} -> 0x{s_to:02X}"
            elif snap.get('burst_index') is not None:
                snap_type = "burst"
                details = f"index {snap['burst_index']}"
            else:
                snap_type = "manual"
                details = ""

            print(f"{name:<25} {player:>6} {snap_type:<12} {details}")

        print()
        print("Commands:")
        print("  jus-char-diff <snap1> <snap2>    - Compare two snapshots")
        print("  jus-char-values <snap>           - Show values in snapshot")
        print("  jus-compare-field <off> <snaps>  - Compare field across snapshots")


class JUSPeriodicSnapshot(gdb.Command):
    """Take a burst of snapshots with manual continues between.

    Usage: jus-burst-snapshot <count> <prefix> [player]

    Takes snapshots one at a time. You manually continue/pause between each.
    Useful for capturing movement/animation over time.

    NOTE: melonDS GDB stub doesn't support stepi well, so this command
    requires manual continue/Ctrl+C between snapshots.

    Example workflow:
        jus-burst-snapshot 5 walking 1   # Capture first
        c                                 # Continue game
        (Ctrl+C after brief moment)
        jus-burst-snapshot 5 walking 1   # Capture next
        ... repeat ...
    """

    def __init__(self):
        super().__init__("jus-burst-snapshot", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        args = arg.split()
        if len(args) < 2:
            print("Usage: jus-burst-snapshot <count> <prefix> [player]")
            print()
            print("Takes snapshots one at a time with manual continue between.")
            print("Run repeatedly until all snapshots captured.")
            print()
            print("Example:")
            print("  jus-burst-snapshot 5 walking 1")
            print("  c              # continue")
            print("  (Ctrl+C)")
            print("  jus-burst-snapshot 5 walking 1")
            print("  ... repeat ...")
            return

        try:
            count = int(args[0])
            if count <= 0:
                print("Count must be positive")
                return
        except ValueError:
            print("Count must be a number")
            return

        prefix = args[1]

        try:
            player = int(args[2]) if len(args) > 2 else 1
            if player < 1 or player > 4:
                print("Player must be 1-4")
                return
        except ValueError:
            print("Player must be a number 1-4")
            return

        ptr_addr = ADDRESSES[f'player{player}_state_ptr']

        # Check how many we already have
        existing = [k for k in _char_snapshots.keys()
                   if k.startswith(prefix + "_") and
                   _char_snapshots[k].get('burst_index') is not None]
        current_idx = len(existing)

        if current_idx >= count:
            print(f"Already have {current_idx} snapshots with prefix '{prefix}'.")
            print(f"Compare with: jus-char-diff {prefix}_0 {prefix}_{count-1}")
            print(f"Or use a different prefix to start fresh.")
            return

        # Capture one snapshot
        ptr = read_dword(ptr_addr)
        if not ptr or ptr < 0x02000000:
            print(f"Player {player} state pointer invalid")
            return

        data = read_bytes(ptr, 0x120)
        if data:
            name = f"{prefix}_{current_idx}"
            _char_snapshots[name] = {
                'data': data,
                'ptr': ptr,
                'player': player,
                'burst_index': current_idx,
            }
            print(f"Captured: {name} ({current_idx + 1}/{count})")

            remaining = count - current_idx - 1
            if remaining > 0:
                print(f"\n{remaining} more needed. Now:")
                print("  1. Type 'c' to continue")
                print("  2. Wait briefly (or perform action)")
                print("  3. Press Ctrl+C")
                print(f"  4. Run: jus-burst-snapshot {count} {prefix} {player}")
            else:
                print(f"\nAll {count} snapshots captured!")
                print(f"Compare with: jus-char-diff {prefix}_0 {prefix}_{count-1}")
        else:
            print("Failed to read character data")


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
    JUSFindHP()
    JUSCheckHP()
    JUSProbeOffline()      # Probe for offline/training mode (JUS-98z)
    JUSReadCharOffline()   # Read char using offline pointer chain (JUS-98z)
    JUSSnapshotOffline()   # Snapshot using offline pointer chain (JUS-98z)
    JUSReadCharAt()        # Read char struct from direct address (JUS-98z)
    JUSSnapshotAt()        # Snapshot from direct address (JUS-98z)
    JUSProbeOpponent()     # Probe for opponent state pointer (JUS-nqp)
    JUSReadOpponent()      # Read opponent state (JUS-nqp)
    JUSSnapshotOpponent()  # Snapshot opponent state (JUS-nqp)
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
    JUSAutoSnapshotOnStatus()
    JUSAutoSnapshotOnDamageCode()

    # Velocity logging (lightweight alternative to full snapshots)
    JUSVelocityLog()
    JUSVelocityShow()
    JUSVelocityClear()

    # Noise filtering
    JUSBaselineNoise()
    JUSBaselineTimed()
    JUSFindTimers()

    JUSPeriodicSnapshot()

    # Snapshot inspection (added 2026-02-03)
    JUSCharValues()
    JUSCompareSnapshots()
    JUSSnapshotList()

    print("=" * 50)
    print("  JUS GDB Watcher loaded!")
    print("=" * 50)
    print()
    print("Commands:")
    print("  jus-status       - Show battle state")
    print("  jus-check-hp     - Show HP for both sides")
    print("  jus-watch-hp     - Set HP watchpoints")
    print("  jus-watch-code   - Break at health code")
    print("  jus-read-char N  - Read player N char state (wifi mode only)")
    print("  jus-dump         - Dump memory to file")
    print("  jus-scan         - Scan for byte value")
    print("  jus-addresses    - List known addresses")
    print()
    print("OFFLINE/TRAINING MODE (when wifi pointers are invalid):")
    print("  jus-probe-offline              - Probe alternative pointers, find char struct")
    print("  jus-probe-opponent             - Search for opponent state pointer")
    print("  jus-read-char-offline          - Read PLAYER using working pointer chain")
    print("  jus-read-opponent              - Read OPPONENT using working pointer chain")
    print("  jus-snapshot-offline <name>    - Snapshot PLAYER state")
    print("  jus-snapshot-opponent <name>   - Snapshot OPPONENT state")
    print("  jus-read-char-at <addr>        - Read char struct from direct address")
    print("  jus-snapshot-at <name> <addr>  - Take snapshot from direct address")
    print()
    print("Snapshot/Diff commands (for finding changes):")
    print("  jus-snapshot <name> [region]  - Save memory snapshot")
    print("  jus-diff <snap1> <snap2|now>  - Compare snapshots")
    print()
    print("Character Struct Research (hitstun/velocity):")
    print("  jus-char-dump [player]            - Dump char struct bytes")
    print("  jus-char-snapshot <name> [player] - Save char struct snapshot")
    print("  jus-char-diff <snap1> <snap2|now> - Find changing fields")
    print("  jus-char-values <snap> [start] [end]  - Show actual values in snapshot")
    print("  jus-compare-field <off> <snaps...>    - Compare field across snapshots")
    print("  jus-snapshot-list [prefix]            - List all snapshots with metadata")
    print("  jus-velocity-watch [player]           - Show physics region")
    print()
    print("AUTOMATED TRIGGERS:")
    print("  jus-auto-snapshot-on-damage <player> [prefix]   - Capture on HP decrease (WORKS!)")
    print("  jus-auto-snapshot-off                           - Disable + show summary")
    print()
    print("  NOTE: 'player' = deck slot (1=lead, 2-3=supports), not opponent!")
    print("        Use jus-find-hp to locate opponent HP addresses.")
    print()
    print("  BROKEN with melonDS (use on-damage instead):")
    print("    jus-auto-snapshot-on-hit     - Uses hardware watchpoints")
    print("    jus-auto-snapshot-on-state   - Uses hardware watchpoints")
    print("    jus-auto-snapshot-on-status  - Uses hardware watchpoints")
    print()
    print("MANUAL CAPTURE (for burst/baseline):")
    print("  jus-burst-snapshot <count> <prefix> [player]    - One at a time, manual c/Ctrl+C")
    print("  jus-baseline-noise <player> [count] [prefix]    - One at a time, manual c/Ctrl+C")
    print()
    print("VELOCITY LOGGING (lightweight alternative):")
    print("  jus-velocity-log <player> [file]                - Log physics on HP decrease")
    print("  jus-velocity-show [last_n]                      - Show velocity log")
    print("  jus-velocity-clear                              - Clear velocity log")
    print()
    print("NOISE FILTERING (run first to identify timer fields):")
    print("  jus-baseline-noise <player> [count] [prefix] [steps] - Capture idle (stepi)")
    print("  jus-baseline-timed <player> [count] [prefix]         - Capture idle (continue)")
    print("  jus-find-timers <prefix>                             - Find always-changing fields")
    print()
    print("Tracing:")
    print("  jus-trace <addr> [on|off]  - Log function calls")
    print("  jus-bt                     - Backtrace with ARM9 offsets")
    print()
    print("Connect to melonDS: target remote localhost:3333")
    print()


# Auto-initialize when sourced
init()
