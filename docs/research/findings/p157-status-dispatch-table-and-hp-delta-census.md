# P157 — The ov6 status-effect dispatch table, and why the chain multiplier is not on the HP path

**Iteration 157. Static only.** Two results from one census.

The queue's top item was the dream-attack chain-length multiplier. The state file named the next step: *"the delta arrives ALREADY COMPUTED … Search space is now the producers of `r1` at those 8 sites."* That census answered the multiplier question at the HP boundary (**no**) and unexpectedly turned up the dispatch table for every status effect.

---

## 1. The 42-entry dispatch table at ov6 `0x02171168`

The small HP-touching handlers in ov6 have **zero** recorded xrefs — they're reached only through function pointers that the xref index doesn't model. Searching `ov06.bin` for their raw little-endian words found them. Attribution is by **file**, sidestepping the `0x0214CD20` overlay-aliasing hazard entirely: these bytes are in ov6 because they're in `ov06.bin`, not because of where they land in RAM.

`CONFIRMED_STATIC`: ov6 `0x02171168`–`0x021712B7` is a table of **42 eight-byte entries** — a function pointer followed by four packed bytes. In memory order: `[cat, key, b2, status]`.

- **`key`** (byte 1) is the real key: 42 entries carry **exactly 32 non-`0xFF` values, all unique, covering `0x00`–`0x1F` with no gaps or duplicates.** The other 10 entries are `0xFF` padding (4 leading, 1 mid, 5 trailing). A perfect permutation of a 32-member enum doesn't happen by accident with a wrong stride — this pins the layout.
- **`cat`** (byte 0): `0x07`, `0x09`, `0x0C`, `0x0D`, `0xFF`.
- **`b2`**: `0x00`–`0x0E` and `0xFF`. `SPECULATIVE`: animation or sub-effect index.
- **`status`** (byte 3): `0x19`–`0x22` and `0xFF` — see below.
- `0x02159258` is the shared no-op handler, appearing 7 times.

| entry | handler (ov6) | cat | key | b2 | status id |
|---|---|---|---|---|---|
| `0x02171168` | `0x02159258` | 0xFF | 0xFF | 0xFF | 0xFF |
| `0x02171170` | `0x021592A0` | 0x07 | 0xFF | 0x00 | 0xFF |
| `0x02171178` | `0x021592A0` | 0x07 | 0xFF | 0x00 | 0xFF |
| `0x02171180` | `0x021592A0` | 0x07 | 0xFF | 0x00 | 0xFF |
| `0x02171188` | `0x021592C0` | 0x0D | 0x00 | 0x01 | 0xFF |
| `0x02171190` | `0x021592DC` | 0x0D | 0x01 | 0x03 | 0xFF |
| `0x02171198` | `0x021592F8` | 0x0D | 0xFF | 0x05 | 0xFF |
| `0x021711A0` | `0x0215930C` | 0x0D | 0x02 | 0x09 | 0xFF |
| `0x021711A8` | `0x02159258` | 0x0D | 0x03 | 0x07 | 0xFF |
| `0x021711B0` | `0x0215931C` | 0x0D | 0x05 | 0x05 | 0xFF |
| `0x021711B8` | `0x0215932C` | 0x0D | 0x04 | 0x05 | 0xFF |
| `0x021711C0` | `0x02159258` | 0x0D | 0x06 | 0x05 | 0xFF |
| `0x021711C8` | `0x02159344` | 0x0D | 0x13 | 0x05 | 0xFF |
| `0x021711D0` | `0x02159364` | 0x0D | 0x0B | 0x05 | 0xFF |
| `0x021711D8` | `0x02159378` | 0x0D | 0x08 | 0x05 | 0xFF |
| `0x021711E0` | `0x021593A4` | 0x0D | 0x09 | 0x05 | 0xFF |
| `0x021711E8` | `0x021593D0` | 0x0D | 0x0A | 0x05 | 0xFF |
| `0x021711F0` | `0x02159434` | 0x0D | 0x07 | 0x05 | 0xFF |
| `0x021711F8` | `0x021594E4` | 0x0C | 0x0C | 0x0A | 0x1F |
| `0x02171200` | `0x02159500` | 0x0C | 0x0D | 0x0B | 0x1D |
| `0x02171208` | `0x02159538` | 0x0C | 0x0F | 0x0C | 0x1C |
| `0x02171210` | `0x02159258` | 0x0C | 0x10 | 0x0D | 0xFF |
| `0x02171218` | `0x02159578` | 0x0C | 0x11 | 0x08 | 0x21 |
| `0x02171220` | `0x02159594` | 0x0C | 0x12 | 0x0E | 0x1E |
| `0x02171228` | `0x02159608` | 0x0C | 0x14 | 0x0E | 0x22 |
| `0x02171230` | `0x02159608` | 0x0C | 0x15 | 0x0E | 0x22 |
| `0x02171238` | `0x02159258` | 0x0C | 0x16 | 0x0E | 0xFF |
| `0x02171240` | `0x02159258` | 0x0C | 0x17 | 0x0E | 0xFF |
| `0x02171248` | `0x021596E0` | 0x0C | 0x19 | 0x0E | 0x20 |
| `0x02171250` | `0x021597F8` | 0x0C | 0x1A | 0x0E | 0x20 |
| `0x02171258` | `0x02159624` | 0xFF | 0x1B | 0xFF | 0x1B |
| `0x02171260` | `0x02159694` | 0xFF | 0x1C | 0xFF | 0x19 |
| `0x02171268` | `0x02159678` | 0xFF | 0x1D | 0xFF | 0x1A |
| `0x02171270` | `0x021592DC` | 0x0C | 0x0E | 0x04 | 0xFF |
| `0x02171278` | `0x02159258` | 0x0C | 0x18 | 0x0E | 0xFF |
| `0x02171280` | `0x0215941C` | 0x0D | 0x1E | 0xFF | 0xFF |
| `0x02171288` | `0x021593E8` | 0x0D | 0x1F | 0xFF | 0xFF |
| `0x02171290` | `0x02159260` | 0x07 | 0xFF | 0x00 | 0xFF |
| `0x02171298` | `0x02159260` | 0x07 | 0xFF | 0x00 | 0xFF |
| `0x021712A0` | `0x02159280` | 0x09 | 0xFF | 0x02 | 0xFF |
| `0x021712A8` | `0x02159280` | 0x09 | 0xFF | 0x02 | 0xFF |
| `0x021712B0` | `0x02159280` | 0x09 | 0xFF | 0x02 | 0xFF |

## 2. The table independently confirms all nine C6b status mappings — and finds the missing one

`findings/c6b-poison-burn-opcodes.md` mapped status opcodes `0x19`–`0x22` to handlers by matching a **prologue shape** (`mov r2,#ID; bl 0x0215986C`) in disassembly. It found nine of ten, leaving the tenth open: *"`0x20` NOT FOUND (blindness — different prologue shape)."*

The `status` byte in this table reproduces **all nine** from a completely different representation — a data table read from the overlay file, sharing no reasoning or tooling with the prologue scan:

| status | C6b name | C6b handler | table handler | agrees |
|---|---|---|---|---|
| `0x19` | shock | `0x02159694` | `0x02159694` | yes |
| `0x1A` | freeze | `0x02159678` | `0x02159678` | yes |
| `0x1B` | burn | `0x02159624` | `0x02159624` | yes |
| `0x1C` | confusion | `0x02159538` | `0x02159538` | yes |
| `0x1D` | poison | `0x02159500` | `0x02159500` | yes |
| `0x1E` | judgment | `0x02159594` | `0x02159594` | yes |
| `0x1F` | paralysis | `0x021594E4` | `0x021594E4` | yes |
| `0x20` | blindness | **not found** | **`0x021596E0` and `0x021597F8`** | new |
| `0x21` | speed-down | `0x02159578` | `0x02159578` | yes |
| `0x22` | seal | `0x02159608` | `0x02159608` (two entries) | yes |

`CONFIRMED_STATIC`: **status `0x20` is handled by ov6 `0x021596E0` (276 B) and `0x021597F8` (116 B).** Both open with `bl 0x02087724; cmp r0, #2; moveq r0,#1` — a genuinely different prologue from the other nine, which is exactly why C6b's shape scan missed them and corroborates C6b's own explanation for the gap. Both have zero callers, consistent with table-only dispatch.

Two statuses have two handlers each (`0x20`, `0x22`), so `status` isn't a unique key; `key` is. `PLAUSIBLE`: the pairs are per-side or apply/tick splits.

Nine of nine prior mappings reproduced plus the one that was open — the strongest confirmation the static-only rule allows.

---

## 3. Census: how the HP delta is produced at all ten call sites

Ten `bl` sites in ov6 call the arm9 HP-adjust family. Nothing in arm9 calls it.

| site (ov6) | target | enclosing fn | how `r1` (the delta) is produced |
|---|---|---|---|
| `0x02157DC0` | `0x020783CC` | `0x02157A44` (1368 B) | `mov r1, r4` — from a dispatch handler |
| `0x021582C4` | `0x020783CC` | `0x0215807C` (996 B) | `mov r1, r4` — same shape |
| `0x02158BC0` | `0x020783CC` | `0x02158B20` (876 B) | `rsb r4, r0, #0` where `r0 = [e+0xE8]` — **negated field** |
| `0x02158BCC` | `0x020781E4` | `0x02158B20` | `rsb r5, r2, #0` where `r2 = [e+0x130]` — **negated field** |
| `0x02159274` | `0x020783CC` | `0x02159260` (32 B) | `ldrsh r1,[p,#4]` then **`lsl r1, r1, #6`** |
| `0x021592B4` | `0x020783DC` | `0x021592A0` (32 B) | `ldrsh r1,[p,#4]` then **`lsl r1, r1, #6`** |
| `0x021592D0` | `0x020783CC` | `0x021592C0` (28 B) | `ldrsh r1,[p,#4]`, **no shift** |
| `0x0215952C` | `0x020783CC` | `0x02159500` (56 B) | `ldrsh r1,[p,#4]`, **no shift** |
| `0x02159668` | `0x020783CC` | `0x02159624` (80 B) | `ldrsh r1,[p,#4]`, **no shift** |
| `0x0215A318` | `0x020783CC` | `0x02159EF8` (1860 B) | gated on `[[e+0x1A8]+0x10]+0x140 != 0` |

The shared idiom, verbatim at `0x02159260`:

```
0x02159260: 08402de9  push {r3, lr}
0x02159264: 041091e5  ldr r1, [r1, #4]        ; param block
0x02159268: b40190e5  ldr r0, [r0, #0x1b4]    ; HP manager
0x0215926C: f410d1e1  ldrsh r1, [r1, #4]      ; signed 16-bit amount
0x02159270: 0113a0e1  lsl r1, r1, #6          ; x64
0x02159274: 547cfceb  bl #0x20783cc
```

`CONFIRMED_STATIC`: the amount is a **signed halfword at `+0x4` of a parameter block reached through `+0x4` of the handler's second argument**; the battle object reaches its HP manager through `+0x1B4`. This matches C6b's poison-handler read and closes its two "not established" sites (`0x02159274`, `0x021592D0`) as the same shape.

## 4. The multiplier answer: not here

`CONFIRMED_STATIC`: **no non-constant scaling happens at the HP-adjust boundary.** Across all ten sites the delta is copied from a register, negated from a struct field, or loaded as a signed halfword — with a shift-left-6 in two of five cases. `lsl #6` is a **constant**: the already-confirmed display-to-raw HP unit conversion (HP is a u16 in 1/64 units; `0x02077C50` does the same `lsl #6` at init). Unit conversion, not a damage multiplier.

`PLAUSIBLE`: the two shifted handlers take their amount in **displayed** HP; the three unshifted ones in **raw 1/64** units. The writer of `[param+0x4]` is unread, so this isn't proven.

A sweep of ov6 `0x02157C00`–`0x0215A400` (2561 listing lines) finds **13** multiply instructions. Three — `0x02159E04`, `0x02159F48`, `0x02159FDC` — are `mul rX, r4, #0xC` feeding `ldr rY, [table, rX]`: **12-byte record indexing**, bounded by `cmp r4, #0xD` at `0x02159F3C` (index `0`–`12`). Not scaling. The other ten aren't on any traced path; `not claimed`.

**Where the chain multiplier must be, if it exists:** not on the HP-adjust path. It has to be applied when `[param+0x4]` is written, or inside whatever computes `[e+0xE8]`. That's the next task.

`0x02159280`, the map's third sibling, scales the same field by **×256** into the `char+0x5C8`
counter — another constant. So every scale on the whole family is a fixed power of two, and the
verdict holds across all of it.

## 5. Fields — mostly already on the record

Honest accounting: most of section 3 was **already documented**. `Battle-Engine-Map.md`'s
guard-sp-gauges block (claims 1–14) already enumerates all 8 trampoline sites, already records
`0x02159260`/`0x021592C0` feeding a signed halfword from `[[r1+4]+4]` with one `lsl #6` and one
unscaled, already names a **third** sibling `0x02159280` scaling the same field **×256** into a
`char+0x5C8` counter, and already has `+0xE8` as a confirmed one-shot-hit drain. This wake's
census reproduces all of that from a clean start, which is worth something as a check, but it is
not new.

What section 3 adds:

- `0x02158BCC` sends `-[e+0x130]` to `0x020781E4`, the entry the map ties to the `char+0x5C8`
  counter. So `PLAUSIBLE`: **`entity+0x130` is the pending amount for the `+0x5C8` counter**, the
  sibling of `+0xE8`'s role for HP. Both are read under the same `[e+0x40] & 0x800` gate at
  `0x02158BA0`, and each gates its own effect and sound call (`0x0207342C`, `r0 = 0x7A`).
- `+0x130` is the same offset the P156 handoff flagged as starting a sub-object separate from
  `char+0x120`..`+0x128`. Consistent.
- Caution: `+0xE8`/`+0x130` are **not** the runtime `+0x134`/`+0x138` pending-damage pair the peer
  harness confirmed. Different offsets; whether they belong to the same object is `not claimed`.
- The ARMv4T encoding-ceiling argument in the P156 handoff said no Thumb immediate store can write
  `owner+0xE8`. Untouched by this — `+0xE8` is *read* here, in ARM.

The census also closes C6b's two "not established" sites (`0x02159274`, `0x021592D0`) as the same
`ldrsh [p,#4]` shape, and it promotes map claim 5 (`PLAUSIBLE`) — the `0x02159500`/`0x02159624`
effect codes — to `CONFIRMED_STATIC` via the table in section 2.

## 6. Convergent verification

Codex was handed the raw instruction words of `0x02078488` and `0x02078428` with **no addresses and no hypothesis** before any conclusion was written. It independently reproduced the clamp (`current + delta`, floor 0, ceiling `[+0x16]`, returns alive/dead) and the percent-of-max setter (`max * arg2 / 100` via `0x0200D12C` with `r1 = 100`). Two additions:

1. **`movmi r1, #0` tests the N flag of the ADD result, not signed overflow.** The floor-at-zero reading is only correct because both operands are in 16-bit range. A reimplementation note, not a refutation.
2. **`0x02078428` has a special case this session read past: if `r1` is 0, it stores HP = 1** on every living character (`strheq r4,[r6,#0x18]`, `r4 = 1`) and skips the multiply entirely. A "reduce everyone to 1 HP" mode.

One disagreement, resolved in favour of the absolute listing: Codex placed two loop branches one instruction earlier than they are (`+0x4C` vs `+0x50`); `0700001a` at `0x02078454` targets `0x02078478`. Relative-offset arithmetic from a context-free hex dump is the weaker representation for placement. It cost nothing — both sides agreed on the arithmetic, which is what matters.

## 7. Corrections to the record

`0x02078488` should stop being called the "damage core." It's a **generic signed HP-delta apply-and-clamp** and a **mid-function entry point** inside `0x02078428`. Damage is a negative delta; every damage decision happens upstream, in ov6.

## 8. Queued

1. Find the writer of `[param+0x4]` — the signed halfword every status tick and heal reads. That's where chain-length scaling would land if it exists.
2. Read the `cat` byte's meaning (`0x07`/`0x09`/`0x0C`/`0x0D`) and the `key` `0x00`–`0x1F` enum: 32 named effects would be a large block of reimplementation-grade documentation.
3. Find the code that *indexes* `0x02171168` — the `key` lookup site — which names the enum's producer.
4. Read `0x02087724` (arm9), the `cmp r0,#2` gate shared by both status-`0x20` handlers.

> **Pending.** A second Codex run was dispatched on the three new `r1`-producer fragments
> (`0x02158B98`, `0x02159260`, `0x021592C0`) as raw hex with no addresses; it had not returned by
> the end of this wake. Prompt kept at `scratchpad/codex-p157b.txt`. Fold its verdict in next
> wake. It is a redundancy check, not the load-bearing one — the table's agreement with
> `c6b-poison-burn-opcodes.md` is what carries section 2.
