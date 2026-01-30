#!/usr/bin/env python3
"""
Action Replay Code Parser for Jump Ultimate Stars.

Parses Action Replay DS cheat codes and extracts:
- Memory addresses being written/read
- Values being written
- Code structure and meaning

Useful for reverse engineering - cheat codes reveal real memory addresses.

Usage:
    python cheat_code_parser.py --input cheats.txt --output addresses.json
    python cheat_code_parser.py --code "020784FC EAFE1EBF"
"""

import argparse
import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple


@dataclass
class ARCodeLine:
    """A single Action Replay code line."""
    raw: str
    code_type: int
    address: Optional[int]
    value: int
    meaning: str


@dataclass
class ARCode:
    """A complete Action Replay code."""
    name: str
    lines: List[ARCodeLine]
    addresses: List[dict]  # Unique addresses affected
    description: str


# Action Replay DS code types
CODE_TYPES = {
    0x0: ("32-bit write", "Write 32-bit value to address"),
    0x1: ("16-bit write", "Write 16-bit value to address"),
    0x2: ("8-bit write", "Write 8-bit value to address"),
    0x3: ("32-bit if >", "If [address] > value, execute next"),
    0x4: ("32-bit if <", "If [address] < value, execute next"),
    0x5: ("32-bit if ==", "If [address] == value, execute next"),
    0x6: ("32-bit if !=", "If [address] != value, execute next"),
    0x7: ("16-bit if >", "If [address] > value, execute next"),
    0x8: ("16-bit if <", "If [address] < value, execute next"),
    0x9: ("Button activator", "Execute if buttons pressed"),
    0xA: ("16-bit if ==", "If [address] == value, execute next"),
    0xB: ("16-bit if !=", "If [address] != value, execute next"),
    0xC: ("Loop", "Loop code block"),
    0xD: ("Conditional", "Various conditional operations"),
    0xE: ("Patch code", "Write block of data to address"),
    0xF: ("Memory copy", "Copy memory block"),
}

# Button masks for type 9 codes
BUTTON_MASKS = {
    0x0001: "A",
    0x0002: "B",
    0x0004: "Select",
    0x0008: "Start",
    0x0010: "Right",
    0x0020: "Left",
    0x0040: "Up",
    0x0080: "Down",
    0x0100: "R",
    0x0200: "L",
    0x0400: "X",
    0x0800: "Y",
}


def parse_code_line(line: str) -> Optional[ARCodeLine]:
    """Parse a single AR code line (XXXXXXXX YYYYYYYY)."""
    # Clean line
    line = line.strip()
    if not line or line.startswith('#') or line.startswith('//'):
        return None

    # Match hex pattern
    match = re.match(r'^([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})$', line)
    if not match:
        return None

    left = int(match.group(1), 16)
    right = int(match.group(2), 16)

    # Extract code type (first nibble)
    code_type = (left >> 28) & 0xF

    # Parse based on type
    if code_type in [0x0, 0x1, 0x2]:
        # Write codes: address in left (masked), value in right
        address = left & 0x0FFFFFFF
        # Add DS RAM base if needed
        if address < 0x02000000:
            address += 0x02000000
        value = right

        type_name, desc = CODE_TYPES.get(code_type, ("Unknown", "Unknown"))
        if code_type == 0x0:
            meaning = f"Write 0x{value:08X} to [0x{address:08X}]"
        elif code_type == 0x1:
            meaning = f"Write 0x{value & 0xFFFF:04X} to [0x{address:08X}]"
        else:
            meaning = f"Write 0x{value & 0xFF:02X} to [0x{address:08X}]"

    elif code_type == 0x9:
        # Button activator
        address = None
        value = right
        buttons = []
        # Invert and mask
        mask = (~right) & 0xFFFF
        for bit, name in BUTTON_MASKS.items():
            if mask & bit:
                buttons.append(name)
        meaning = f"If pressed: {'+'.join(buttons) if buttons else 'None'}"

    elif code_type == 0x5:
        # 32-bit conditional
        address = left & 0x0FFFFFFF
        if address < 0x02000000:
            address += 0x02000000
        value = right
        meaning = f"If [0x{address:08X}] == 0x{value:08X}"

    elif code_type == 0xD:
        # D-type conditionals
        subtype = (left >> 24) & 0xF
        if subtype == 0x2:
            meaning = "End code block"
            address = None
            value = right
        elif subtype == 0x5:
            address = None
            value = right
            meaning = f"Set offset register to 0x{right:08X}"
        else:
            address = left & 0x00FFFFFF
            value = right
            meaning = f"D-type conditional (subtype {subtype})"

    elif code_type == 0xE:
        # Patch code - writes block of data
        address = left & 0x0FFFFFFF
        if address < 0x02000000:
            address += 0x02000000
        value = right  # Size of patch
        meaning = f"Patch {right} bytes at [0x{address:08X}]"

    elif code_type == 0xC:
        # Loop
        address = None
        value = left & 0x0FFFFFFF
        meaning = f"Loop {value} times"

    else:
        address = left & 0x0FFFFFFF
        if address < 0x02000000 and address > 0:
            address += 0x02000000
        value = right
        type_name, desc = CODE_TYPES.get(code_type, ("Unknown", "Unknown"))
        meaning = f"{type_name}: {desc}"

    return ARCodeLine(
        raw=line,
        code_type=code_type,
        address=address,
        value=value,
        meaning=meaning,
    )


def parse_cheat_block(text: str) -> List[ARCode]:
    """Parse a block of cheat codes with names."""
    codes = []
    current_name = "Unknown"
    current_lines = []

    for line in text.strip().split('\n'):
        line = line.strip()

        if not line:
            continue

        # Check if this is a code name (starts with :: or doesn't look like hex)
        if line.startswith('::'):
            # Save previous code if any
            if current_lines:
                codes.append(build_ar_code(current_name, current_lines))
                current_lines = []
            current_name = line[2:].strip()

        elif re.match(r'^[A-Za-z]', line) and not re.match(r'^[0-9A-Fa-f]{8}', line):
            # Looks like a code name
            if current_lines:
                codes.append(build_ar_code(current_name, current_lines))
                current_lines = []
            current_name = line

        else:
            # Try to parse as code line
            parsed = parse_code_line(line)
            if parsed:
                current_lines.append(parsed)

    # Don't forget last code
    if current_lines:
        codes.append(build_ar_code(current_name, current_lines))

    return codes


def build_ar_code(name: str, lines: List[ARCodeLine]) -> ARCode:
    """Build an ARCode from parsed lines."""
    # Extract unique addresses
    addresses = []
    seen = set()

    for line in lines:
        if line.address and line.address not in seen:
            seen.add(line.address)
            addresses.append({
                "address": f"0x{line.address:08X}",
                "decimal": line.address,
                "code_type": line.code_type,
                "arm9_offset": f"0x{line.address - 0x02000000:06X}" if line.address >= 0x02000000 else None,
            })

    # Generate description
    desc_parts = []
    for line in lines:
        if line.meaning and line.meaning != "End code block":
            desc_parts.append(line.meaning)

    return ARCode(
        name=name,
        lines=lines,
        addresses=addresses,
        description="; ".join(desc_parts[:3]),  # First 3 operations
    )


# Known JUS cheat codes
JUS_CHEATS = """
::Game ID
AJUJ 65E1D889

::Unlimited Time
221DEA71 00000099

::Unlimited Health
E2000000 00000010
E1D411F6 E1C411B8
E1A00000 EA01E13B
520784FC E1D411F8
020784FC EAFE1EBF
D2000000 00000000

::Unlimited Special (Press X)
94000136 FFFE0000
221DF731 00000009
221DF8B1 00000009
D2000000 00000000

::Leader Refill Health (Select+Down)
94000130 FF7B0000
221DF1D5 00000050
D2000000 00000000

::Non-leader Refill Health (Select+Up)
94000130 FFBB0000
221df225 00000050
D2000000 00000000

::Infinite Gems
020b7718 0001869F
020b771c 0001869F
020b7720 0001869F
020b7724 0001869F
020b7728 0001869F
020b772c 0001869F

::Infinite Koma Points (Press Select)
94000130 FFFB0000
920AFE3C 0000001E
020B76C8 0001869F
020B76F0 0001869F
020B7718 0001869F
020B7768 0001869F
020B7790 0001869F
020B77B8 0001869F
020B77E0 0001869F
D2000000 00000000

::Hold L to Unlock All Komas (on menu)
94000130 FDFF0000
D5000000 FFFFFFFF
C0000000 0000001C
D6000000 020B0BAC
D2000000 00000000
"""


def categorize_address(addr: int) -> str:
    """Categorize an address by likely purpose."""
    if addr < 0x02000000:
        return "Invalid/Offset"
    elif 0x02070000 <= addr < 0x02080000:
        return "Game Code (ARM9)"
    elif 0x020A0000 <= addr < 0x020C0000:
        return "Save Data / Progress"
    elif 0x021D0000 <= addr < 0x02200000:
        return "Battle State / RAM"
    elif 0x020B0000 <= addr < 0x020C0000:
        return "Inventory / Currency"
    else:
        return "Unknown"


def main():
    parser = argparse.ArgumentParser(description="Parse Action Replay codes")
    parser.add_argument("--input", help="Input file with cheat codes")
    parser.add_argument("--code", help="Single code line to parse")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--builtin", action="store_true",
                        help="Parse built-in JUS codes")

    args = parser.parse_args()

    if args.code:
        # Parse single line
        result = parse_code_line(args.code)
        if result:
            print(f"Code Type: {result.code_type} ({CODE_TYPES.get(result.code_type, ('?', '?'))[0]})")
            if result.address:
                print(f"Address: 0x{result.address:08X}")
                print(f"ARM9 Offset: 0x{result.address - 0x02000000:06X}")
            print(f"Value: 0x{result.value:08X}")
            print(f"Meaning: {result.meaning}")
        return

    # Parse code block
    if args.input:
        with open(args.input, 'r') as f:
            text = f.read()
    elif args.builtin:
        text = JUS_CHEATS
    else:
        print("Provide --input, --code, or --builtin")
        return

    codes = parse_cheat_block(text)

    print(f"Parsed {len(codes)} cheat codes\n")

    # Collect all addresses
    all_addresses = {}

    for code in codes:
        print(f"=== {code.name} ===")
        print(f"  Lines: {len(code.lines)}")
        print(f"  Description: {code.description}")

        for addr_info in code.addresses:
            addr = addr_info['decimal']
            category = categorize_address(addr)
            print(f"  Address: {addr_info['address']} [{category}]")

            if addr not in all_addresses:
                all_addresses[addr] = {
                    "address": addr_info['address'],
                    "arm9_offset": addr_info['arm9_offset'],
                    "category": category,
                    "used_by": [],
                }
            all_addresses[addr]["used_by"].append(code.name)

        print()

    # Summary
    print("=== ADDRESS SUMMARY ===")
    for addr in sorted(all_addresses.keys()):
        info = all_addresses[addr]
        print(f"{info['address']}: {info['category']}")
        print(f"  Used by: {', '.join(info['used_by'])}")

    # Save output
    if args.output:
        output = {
            "codes": [
                {
                    "name": c.name,
                    "description": c.description,
                    "lines": [asdict(l) for l in c.lines],
                    "addresses": c.addresses,
                }
                for c in codes
            ],
            "address_summary": list(all_addresses.values()),
            "categories": {
                "game_code": [a for a in all_addresses.values() if "Game Code" in a["category"]],
                "battle_state": [a for a in all_addresses.values() if "Battle State" in a["category"]],
                "inventory": [a for a in all_addresses.values() if "Inventory" in a["category"]],
            }
        }

        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nSaved to: {args.output}")


if __name__ == "__main__":
    main()
