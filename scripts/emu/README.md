# melonDS agent control layer

This directory holds the tooling that lets an agent play Jump Ultimate Stars
without touching the emulator by hand. A patched melonDS fork runs a Lua
bridge script (`agent_bridge.lua`) inside the emulator; the `jusemu.py` CLI
talks to it over files, sends button plans, reads memory watches, and drives
savestates. The GDB stub stays available for breakpoint work, so Lua and GDB
can be used together on the same running game.

## Build

```bash
bash scripts/emu/build_melonds_lua.sh
```

The build needs Lua 5.4 from Homebrew. Note that `lua5.4` and `luac5.4` live in
`/opt/homebrew/opt/lua@5.4/bin` and are **not** on `PATH` by default — call them
with the full path, or add that directory to `PATH` yourself.

### Pinned commit

TBD — filled in after the first successful build (see `build_info.json`).

### ROM/BIOS hashes

Filled in at the human checkpoint; see `hashes.json`.

| File | SHA-256 |
| --- | --- |
| ROM | TBD |
| BIOS9 | TBD |
| BIOS7 | TBD |
| Firmware | TBD |
| Save | TBD |

## Verified behavior (spike findings)

## Combined Lua+GDB workflow
