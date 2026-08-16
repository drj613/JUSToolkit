# Findings: the ColPrm record's field map, and the `add` blind spot that hid half of it

Loop-Atlas iteration 78. Static.

Mapping the `0x188`-byte ColPrm record exposed a gap in `struct_fields.py`: it only
knew load/store encodings, so it missed any field whose **address** is taken.
That covers every list head and embedded sub-region —
`add r0,r4,#8` then link, `add r0,r4,#0xa4` then memset. The first run found 13
offsets and **none of the record's structural fields**.

Two new guards fix this: **24 fields** across both binaries, with `+0x40` appearing
in arm9 and ov6 independently — the first cross-binary proof that the damage
pipeline and the collision installer share one object.

---

## 1. Two guards added

**Guard 8, address-taken.** `add Rd, base, #imm` is a field reference, reported as kind
`addr`. Unconditional, S clear, `imm != 0` (`add Rd,base,#0` is a move), `Rd != pc`.

**Guard 9, split bases.** `+0x100` is *not* a field. The code does
`add r0,r4,#0x100` then `strh r2,[r0,#0x86]` to reach `+0x186` — ARM's 12-bit immediate
covers `0x186` directly, so this is a compiler choice. Guard 8 alone would false-positive
`+0x100`. Guard 9 looks ahead up to six instructions for an access off the new register
and reports `N+M` instead, as kind `…/split`.

Selftest asserts both guards: the NoteTrack map reproduces with no phantoms, and
ColPrm's `+0x08` and `+0xA4` are found. Before guard 9 the run reported
`+0x100` and `+0x98`; after, it reports `+0x184`/`+0x186` and `+0x098`/`+0x09A`.

## 2. The map

Anchors, each a register provably holding the record: arm9 `0x0207CCDC:r4` (teardown
arg1), `0x0207CA20:r4` (installer), `0x0207D498:r4` and `0x0207D870:r4` (the pool
methods); ov6 `0x02158B9C:r1` and `0x0215A308:r0`, both loaded from `entity+0x10`.

| offset | kind | what | first site |
|---|---|---|---|
| `+0x008` | addr | list head, `0x2C`-byte pool nodes | `0x0207D490` |
| `+0x030` | str | — | `0x0207C9C8` |
| `+0x034` | ldr,str | seeds node`+0x14` | `0x0207CA64` |
| `+0x038` | ldr,str | seeds node`+0x18` | `0x0207CA6C` |
| `+0x03C` | ldr,str | — | `0x0207CA7C` |
| `+0x040` | ldr,str | **flags**: bit `0x200` cleared by the installer; bit `0x800` gates delta application | `0x0207CB24` |
| `+0x050` | str | — | `0x0207CB38` |
| `+0x05C` | str | — | `0x0207CA0C` |
| `+0x060` | ldr,str | the **ColObj**; zeroed by the teardown | `0x0207CA20` |
| `+0x068` | ldr | object whose `+0x20` list holds this record's bucket nodes | `0x0207CCDC` |
| `+0x06C` | ldr | — | `0x0207D4C4` |
| `+0x090` | addr | sub-region | `0x0207CAA8` |
| `+0x094` | addr | sub-region | `0x0207CAFC` |
| `+0x098` | strh/split | — | `0x0207CB00` |
| `+0x09A` | ldrsh/split | — | `0x0207CB00` |
| `+0x0A4` | addr | start of the `0xD0`-byte scratch region, `+0xA4`–`+0x173` | `0x0207CA70` |
| `+0x0E8` | ldr | per-hit damage magnitude, negated before use | `0x02158BA8` |
| `+0x130` | ldr | second signed field, negated alongside `+0xE8` | `0x02158BAC` |
| `+0x140` | ldr | fed to the damage trampoline, no negation | `0x0215A308` |
| `+0x144` | ldr | the SP counterpart of `+0x140` | *(map claim 6)* |
| `+0x174` | strb | — | `0x0207CA90` |
| `+0x175` | ldrb,strb | bitfield; bits `0x30`, `0xC`, `0x3` manipulated | `0x0207CAA0` |
| `+0x182` | strb | — | `0x0207CA88` |
| `+0x184` | strh/split | — | `0x0207CA94` |
| `+0x186` | strh/split | — | `0x0207CA94` |

## 3. What the map shows

**`+0xE8`, `+0x130`, `+0x140` and `+0x144` all sit inside the `+0xA4`–`+0x173` scratch
region.** All four damage fields live in the block the installer memsets — a per-hit
scratch area wiped at setup, consistent with iteration 76's finding that nothing
ever *sets* `+0xE8`.

**`+0x40` is reached from both binaries.** arm9's installer clears bit `0x200` at
`0x0207CB2C`; ov6's damage path tests bit `0x800` at `0x02158BA0` before reading
`+0xE8`. Before this, the shared-object claim rested on an address expression
(iteration 75). Two binaries hitting the same flags word is independent support.

**The record ends at `+0x186`.** Highest field: a halfword at `+0x186`,
exactly `0x188 - 2` — flush with the teardown memset size. Independent size
confirmation from a different direction.

## 4. Coverage

24 fields on a `0x188`-byte struct. Unmapped: `+0x00`–`+0x2C`, `+0x44`–`+0x4C`,
`+0x54`–`+0x58`, `+0x64`, `+0x70`–`+0x8C`, `+0x9C`–`+0xA0`, and most of
`+0xA4`–`+0x173` beyond the four damage fields. **Partial map, not the full struct** —
six anchor functions; any field touched only elsewhere is invisible.

The `+0xA4` region is the biggest gap: `0xD0` bytes, four known fields. The rest is
likely reached through `+0x90`/`+0x94` sub-pointers or from code outside these anchors.

## Predictions status

| Claim | Verdict |
|---|---|
| `add Rd,base,#imm` is a field reference the old scan could not see | **CONFIRMED_STATIC** — added `+0x08`, `+0x90`, `+0x94`, `+0xA4`, none visible before |
| `+0x100` is a split base, not a field | **CONFIRMED_STATIC** — `add r0,r4,#0x100` then `strh r2,[r0,#0x86]` at `0x0207CA94` → `+0x186` |
| The record's four damage fields lie inside the `+0xA4` memset region | **CONFIRMED_STATIC** — `0xA4 ≤ 0xE8, 0x130, 0x140, 0x144 < 0x174` |
| `+0x40` is reached from both arm9 and ov6 on the same struct | **CONFIRMED_STATIC** — `0x0207CB24` and `0x02158B9C` |
| The record is `0x188` bytes | **CONFIRMED_STATIC** *(independent second route)* — highest field is a halfword at `+0x186` = `0x188 - 2` |
| `+0x08` is the record's own node list, distinct from ColPrm manager `+0x08` | **CONFIRMED_STATIC** — `add r0,r4,#8` at `0x0207D490` with `r4` the record |
| This is a complete field map | **REFUTED** — 24 of the struct's fields, from six anchor functions; large spans unmapped |
| `+0x090` and `+0x094` are sub-structures | **PLAUSIBLE** — addresses taken and passed on; contents not traced |

## Next angles, ranked

1. **Follow `+0x090` and `+0x094`.** Both have their address taken and handed to a
   call; whatever those callees do names two sub-structures and probably fills in the
   `+0xA4` region.
2. **Resolve `record+0x68`** (carried) — the object whose `+0x20` list holds this
   record's bucket nodes.
3. **Re-run the map with anchors from the eight per-frame collision stages** — they are
   the code most likely to touch the unmapped spans.
4. **Re-audit the map's `char+0xNN` offsets** across the three objects (carried).
