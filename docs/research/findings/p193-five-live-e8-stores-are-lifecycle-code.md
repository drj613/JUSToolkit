## P193 — the five live `+0xE8` stores are object lifecycle code in a different struct

Byte-checked all 21 stores against RAM (ov6 control matched). **16 cleared, 5 live** — all in ov12's partially-resident region. My `0x021CC29A` prediction was correct; it's one of the five. Moved this ahead of the shifted-register scan because their breakpoints were about to fire and knowing the five changes how any hit gets read.

`functions.json` doesn't cover these addresses, so I walked back from each store to its Thumb prologue and read the function directly.

| Store | Prologue | What the function is |
|---|---|---|
| `0x021C6032` | `0x021C6008` | **Constructor.** Installs a vtable at `+0x0`, zeroes `+0x4C`/`+0x50`/`+0x54`, sub-constructs `+0x40` and `+0x58`, then `movs r1,#0` / `str r1,[r0]` — writes a **literal zero** to `+0xE8` |
| `0x021C628E` | `0x021C6264` | **Copy constructor.** `ldr r1,[src+0xE8]` then `str r1,[dest+0xE8]` |
| `0x021C6666` | `0x021C662C` | Assignment/attach — `blx` through vtable slots `+0x8`/`+0xC`/`+0x18`, stores to `+0x54` |
| `0x021C6B60` | `0x021C6B04` | Text formatting — **reads** `+0xE8`, then `movs r0,#0x41` (`'A'`), `strb`, `ldrsh` |
| `0x021CC29A` | `0x021CC260` | Initialiser — `ldr r0,[r5,#4]` / `ldr r4,[r0,#0x10]`, then `strb` runs to `+0x8`/`+0xA`/`+0xB`/`+0xC` and `str` to `+0x1C` |

### The structural point outranks the labels

These objects have a **vtable pointer at `+0x0`** and fields at `+0x40`, `+0x4C`, `+0x50`, `+0x54`, `+0x58`. That doesn't match the scratch's layout. `PLAUSIBLE`: this is a **different `+0xE8` in a different struct** that happens to share the offset — the P171 trap again, but established by reading code instead of assumed from the overlay. Plausible, not confirmed: I've shown the layouts differ, not that no ov12 object is ever the scratch.

This also **converges with runtime from the other direction.** The bracket read `+0xE8 = 0` at both `0x02156DE8` and `0x0215AC08`. A constructor writing literal zero to `+0xE8` is exactly consistent. Even taken at face value, these five explain why `+0xE8` reads zero — they don't supply a damage value.

### Pre-registered prediction

**None of the five fires during a landed hit.** All are object-lifecycle or text code — runs at construction and screen setup, not on a damage frame. One hedge: `0x021C6B60` could fire if it's a per-frame HUD formatter rather than one-shot text, but it **reads** `+0xE8` rather than computing one, so a fire there still wouldn't make it the writer.

- None fires → `+0xE8`'s remaining candidates are irrelevant to B11; the field is done as a static lead.
- One fires with `+0x134` already `384` → the speculative one-writer-stages-both link dies, and we learn where the copy happens.
- One fires with `+0x134` still `0` → I'm wrong about the struct and it's live.

### Two characterisations hid the same four addresses

Four of the five live stores sit at `+0x19E72`–`+0x1A9A0`. Runtime had sampled `+0x10000` (16/128) and `+0x20000` (128/128) and inferred the resident region was "around `+0x20000`" — a residency map built from three samples. Mine was the word "mainly" in a distribution. **Both characterisations concealed the identical four addresses.** That's worth more as a lesson than either alone: count, don't characterise — and that applies to a partner's sampling grid as much as to your own prose.

### Scope, in the words it needs to travel in

These are five live **`+0xE8` store** candidates whose struct probably isn't the scratch. Not "five live B11 candidates" — `+0xE8` isn't the carrier; `+0x134` is, and it already holds the reduced value before the per-character update begins.
