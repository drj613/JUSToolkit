# Which ARM9 overlay is resident during a battle

**Status:** measured 2026-08-14 by comparing extracted overlay binaries against
a 4MB live RAM dump taken during a J Arena training battle.

## Why this matters

The ROM declares 14 ARM9 overlays, and they **share load addresses**:

| RAM address | overlays sharing it |
|---|---|
| `0x0214CD20` | 0–9 |
| `0x02172A60` | 10, 11 |
| `0x021AC1C0` | 12, 13 |

Ten overlays occupy the same window, one at a time. So a runtime address in that
range is meaningless on its own — it depends entirely on which overlay is
currently loaded. Any watchpoint, breakpoint, or "address X holds Y" claim in
that window has to name the resident overlay or it isn't reproducible.

## Result: ov06 is the battle overlay

Method: extract every overlay (`python3 scripts/extract_arm9.py <rom> <outdir>`,
which also writes `overlays/` and records the shared addresses), then compare
each against live RAM at its declared load address. Overlays are uncompressed,
so a resident one should match byte-for-byte.

| overlay | load address | size | match vs live RAM |
|---|---|---|---|
| ov00–ov05, ov07, ov08 | `0x0214CD20` | 65K–153K | 3–4% (not resident) |
| **ov06** | `0x0214CD20` | 154,688 | **100.0%** ← resident |
| ov09 | `0x0214CD20` | 32 | 0% |
| ov10 | `0x02172A60` | 215,264 | 7.4% (not resident) |
| **ov11** | `0x02172A60` | 61,440 | **100.0%** ← resident |
| ov12 | `0x021AC1C0` | 167,776 | 59.6% (ambiguous) |
| ov13 | `0x021AC1C0` | 32 | 100% (see caveat) |

The ov06 and ov11 results are conclusive — 100% across 154KB and 60KB
respectively is not something a wrong guess produces.

**Caveats, stated plainly:**

- **ov13's 100% means nothing.** It is 32 bytes. A tiny blob of mostly-zero
  bytes matches almost anything.
- **The `0x021AC1C0` window is unresolved.** ov12 at 59.6% over 167KB is
  consistent with "ov12 is resident but roughly 40% of it is writable data that
  the running game has since modified" — but it's also consistent with something
  else being loaded there. Don't rely on either reading.

## Practical consequence

**Battle code lives in `arm9.bin` and `ov06`.** Anyone searching for combat
logic — damage application, hitstun, knockback — should include ov06's 154KB and
can ignore ov00–ov05, ov07, ov08 for battle-time behavior.

`fn_health_calc` at `0x020784FC` is unaffected: it sits in `arm9.bin` proper,
which is always resident, and the extracted `arm9.bin` was verified
byte-identical to live RAM at that address.

To identify the resident overlay for a *different* game mode (deck editor, story
map), repeat the comparison from a RAM dump taken in that mode:

```bash
cd scripts/emu && python3 jusemu.py dump 0x02000000 0x02400000 /tmp/ram.bin
```

then diff each overlay against `/tmp/ram.bin` at its `ram_address` from
`jus_files/arm9/binaries.json`. This is the cheapest way to attribute an
overlay to a mode, and it needs no disassembly.
