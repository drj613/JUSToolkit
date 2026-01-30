# JUS DeSmuME Lua Watcher

RAM monitoring script for DeSmuME emulator.

**Platform:** Windows only (DeSmuME Lua scripting is not available on Mac/Linux builds)

> **Mac/Linux users:** Use `scripts/gdb/jus_gdb_watcher.py` with melonDS instead.

## Setup

1. Download DeSmuME for Windows (ensure it has Lua support)
2. Open DeSmuME and load the JUS ROM
3. Go to **Tools → Lua Scripting → New Lua Script Window**
4. Click **Browse** and select `jus_watcher.lua`
5. Click **Run**

## Features

### On-Screen Display

When in battle, the script displays:
- Battle timer
- Player HP values
- Special meter

### Console Commands

Open the Lua console and call these functions:

| Function | Description |
|----------|-------------|
| `jus_status()` | Print current battle values |
| `jus_watch(addr, name, size)` | Watch an address for changes |
| `jus_scan(start, end, value)` | Search memory range for a byte value |
| `jus_read(addr, size)` | Hex dump memory at address |
| `jus_dump_history()` | Show log of recent changes |

### Automatic Watchpoints

The script automatically watches:
- Leader HP (`0x021DF1D5`)
- Partner HP (`0x021DF225`)

Changes are logged to the console.

## Known Addresses

Same addresses as the GDB script - see `scripts/gdb/README.md` for the full list.

Key addresses:
- `0x021DF1D5` - Player 1 HP
- `0x021DF225` - Player 2 HP
- `0x021DEA71` - Battle timer
- `0x021DF731` - Special meter

## Example Session

```lua
-- In Lua console after loading script:

-- Check current state
jus_status()

-- Watch a custom address
jus_watch(0x021DF275, "Player3 HP", 1)

-- Search for a value (e.g., find where "100" appears)
jus_scan(0x021D0000, 0x02200000, 100)

-- Hex dump 32 bytes
jus_read(0x021DF1D0, 32)
```

## Troubleshooting

**"Lua Scripting" menu not available**
- Your DeSmuME build doesn't have Lua support
- Download a build with Lua enabled, or use the official Windows release

**Script errors on load**
- Make sure you're using a recent DeSmuME version
- Check that the ROM is loaded before running the script

**Values show as 0 or incorrect**
- Addresses may differ between ROM versions
- Verify you're in battle (some addresses only valid during battle)
