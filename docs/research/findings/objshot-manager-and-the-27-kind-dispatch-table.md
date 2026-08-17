# BattleObjShot: the manager, the 0x6C element, and a 27-entry kind dispatch table

Iteration 147. Static only. Region `ov6`.

## What this settles

`Battle_ObjShotManCreate` is the projectile subsystem's constructor. This pass pins
down the manager's layout, the shot element's `0x6C`-byte stride with its first eleven
fields, and the key finding: **a one-byte kind index selects every shot behaviour
through a 27-entry function-pointer table at `0x02172864`.** The table's extent is
bounded by data on both sides — no guesswork.

## Identity — CONFIRMED_STATIC

The function starts at **`0x0216A7BC`**, not `0x0216A7D4`. The latter is the `bl` to
the allocator veneer — the same off-by-one citation hazard seen with
`Battle_MoveManCreate`. Always cite the push.

The allocator arguments name the function directly:

| Reg | Value | Meaning |
|-----|-------|---------|
| r0 | `0x00003FD4` | size |
| r1 | `0x021728D0` → `"BattleObjShot.cpp"` | `__FILE__` |
| r2 | `0x02172774` → `"Battle_ObjShotManCreate"` | `__FUNCTION__` |
| r3 | `0x118` (280) | `__LINE__` |

The manager is **`0x3FD4` bytes**, and the attribution comes from its own string
arguments — not proximity. The `0x3FD4` literal at `0x0216A8B8` is loaded twice: once
as the allocation size, once as the `memset` length at `0x0216A814`.

The neighbouring strings `0x02172748` `"Battle_ObjCtrlManCreate"` and `0x02172760`
`"BattleObjCtrl.cpp"` sit immediately before — a separate lead for the still-open
obj-ctrl attribution question.

## Manager layout — CONFIRMED_STATIC

Read off the constructor at `0x0216A7BC`–`0x0216A8B0`:

| Offset | Contents |
|--------|----------|
| `+0x00` | active-list head (elements link in here on spawn) |
| `+0x10` | free-list head (all 72 elements link here at construction) |
| `+0x18` | a resource/track object; created by `0x02026F94` |
| `+0x1C` | element array base — 72 × `0x6C` |
| `+0x1E7C` | **unaccounted**; see open questions |

The singleton pointer lives at **`0x021729EC`**; the constructor stores the manager
there at `0x0216A8A8`, and three other sites load it.

Construction sequence:

1. Allocate `0x3FD4`, zero the six words `+0x00`…`+0x14` if allocation succeeded, then
   `memset` the whole `0x3FD4`. Like `MoveMan`, the six explicit clears are dead — the
   `memset` at `0x0216A814` covers them.
2. `0x02026F94` → stored at `+0x18`. Three virtual calls follow on `[[+0x18]+4]`:
   slot `0xA0` with id **`0x88000`**, slot `0x24` with the manager itself, slot `0x94`
   with `0x10000`. The `0x88000` id belongs to the same family as `MoveMan`'s NoteTrack
   ids `0xA1000` / `0xA6000`.
3. `0x02028384` with `0x0216AF04` — a callback registration. **`0x0216AF04` is the
   per-frame entry point** for obj-shot, matching the pattern that gave `MoveMan` its
   frame pass at `0x02082E10`.
4. Free-list build: `r5 = manager+0x1C`, 72 iterations (`cmp r6, #0x48`), stride
   `0x6C`, each linked via `0x02037B98` into the head at `manager+0x10`.

The **shot element is `0x6C` bytes, and there are 72 of them**. The link node sits at
element offset `0` — the loop passes `r5` itself as the node.

## The kind dispatch table — CONFIRMED_STATIC

The element initializer `0x0216ACC8` stores a byte into element `+0x1A` from the
parameter block, then at `0x0216ADD8`:

```
0x0216ADD0: ldrb r2, [r8, #0x1a]      ; kind
0x0216ADD8: ldr  r3, [r1, r2, lsl #2] ; r1 = 0x02172864
0x0216ADE4: blx  r3                   ; r0=element, r1=owner, r2=params
```

`r1` comes from the literal at `0x0216AF00` → **`0x02172864`**.

Data on both ends pins the table's size. It begins at `0x02172864`, and the string
`"BattleObjShot.cpp"` begins at `0x021728D0`. That leaves `0x6C` bytes — exactly
**27 entries, kinds `0x00`–`0x1A`**. No index arithmetic is involved, no bound check
exists in the caller, so 27 is the true arity.

| Kind | Handler | | Kind | Handler |
|------|---------|-|------|---------|
| `0x00` | `0x0216EEF4` | | `0x0E` | `0x0216B768` |
| `0x01` | `0x0216B4F4` | | `0x0F` | `0x0216EEF4` |
| `0x02` | `0x0216B514` | | `0x10` | `0x0216D9DC` |
| `0x03` | `0x0216B4F4` | | `0x11` | `0x02170500` |
| `0x04` | `0x0216B4F4` | | `0x12` | `0x0216D9F8` |
| `0x05` | `0x0216B910` | | `0x13` | `0x0217061C` |
| `0x06` | `0x0216D88C` | | `0x14` | `0x0216D0C8` |
| `0x07` | `0x0216DF50` | | `0x15` | `0x0216EEF4` |
| `0x08` | `0x02170044` | | `0x16` | `0x0216EEF4` |
| `0x09` | `0x0216B2C8` | | `0x17` | `0x0216B9B0` |
| `0x0A` | `0x0216D99C` | | `0x18` | `0x02170900` |
| `0x0B` | `0x0216EF7C` | | `0x19` | `0x0216B9D8` |
| `0x0C` | `0x0216D05C` | | `0x1A` | `0x0216B2A0` |
| `0x0D` | `0x0216FB10` | | | |

`0x0216EEF4` is shared by kinds `0x00`, `0x0F`, `0x15`, `0x16` — four slots, making it
either a no-op stub or a genuine default. `0x0216B4F4` is shared by `0x01`, `0x03`,
`0x04`. Neither has been read yet.

**New `functions.json` gap.** Kind `0x1A`'s handler `0x0216B2A0` is missing from
`functions.json`. The record before it, `0x0216B220`, spans 124 bytes and ends at
`0x0216B29C`; the next record starts at `0x0216B2C8`. That puts `0x0216B2A0`–`0x0216B2C8`
as a `0x28`-byte function the database doesn't know about — the same hazard seen with
`0x0207DD40` and friends, now affecting a fifth module.

## Shot element fields — CONFIRMED_STATIC

From `0x0216ACC8`, with `r8` = the element popped off the free list and `r6` = the
caller's parameter block:

| Offset | Width | Written from | Reading |
|--------|-------|--------------|---------|
| `+0x08` | word | `r6` | the parameter block, retained |
| `+0x10` | word | (elsewhere) | read at `0x0216ADF8`; a byte counter target |
| `+0x18` | half | `[r6+6]`, or **`0x1E` when zero** | lifetime in frames; 30 is the default |
| `+0x1A` | byte | `[r6+0]` | **kind** — the dispatch index |
| `+0x1C` | word | `[r6+0x14]` if `[r6+8] & 1`, else `0` | conditional payload |
| `+0x20` | half | `[r6+4]` | |
| `+0x22` | half | (params) | read back as a sound id at `0x0216AEE8` |
| `+0x24` | half | (params) | read back as a sound id at `0x0216AED8` |
| `+0x26` | half | `0` at init | flags; `0x0216AC10` sets bit 0, bit 3 is tested at `0x0216ADF0` |
| `+0x28` | word | argument, else `[r7+0x10]` | |
| `+0x2C` | word | written by the kind handler | the spawned entity, or absent |

`+0x2C` is the interesting one. `0x0216A910` reads it:

```
kind in {0x01, 0x05, 0x0E} or (kind + 0xE9) & 0xFF <= 2  ->  return 0
otherwise                                                ->  return [element+0x2C]
```

`(kind + 0xE9) & 0xFF <= 2` selects kinds `0x17`, `0x18`, `0x19`. So **six kinds —
`0x01`, `0x05`, `0x0E`, `0x17`, `0x18`, `0x19` — carry no entity**, and the other 21
store one at `+0x2C`. The handler writes it; the initializer never does.

## Spawn path — CONFIRMED_STATIC

`0x0216A944` is the spawn entry with two arms, selected by a byte at
`[[r1+0x10] + slot*32]`:

**Arm A (`== 0xF`, the multi-target arm).** Calls `0x0208369C(9)` to get a list head,
then walks it. Per node: payload `= [node+8]`, skip if `[payload+0x2C] & 1` or `& 8`,
then `record = [payload+0x10]` and test the ColPrm record fields —

- `[record+0x38] & 0x800` → skip (the category mask, consistent with `0x800` being
  category routing)
- `[record+0x3C] & 0xF` against `r5` → skip on overlap
- `[record+0x17C]` zero, or `[record+0x34] & 0xF != r5` → skip

Survivors get a shot spawned at `[[record+0x5C]+0x10] + r8` and
`[[record+0x5C]+0x0C] + sb`, via `0x0216AB58`.

**Arm B (`!= 0xF`, the single arm).** Pops `r5 = [singleton]+0x10` — the free-list
head — writes `+0x0C`, `+0x10`, `+0x22`, `+0x24`, and calls the initializer
`0x0216ACC8`.

`record+0x17C` is a field not previously in the ColPrm map.

### The chain, independently confirmed

Two byte-identical leaves, `0x0216B3D8` and `0x0216B740`, do exactly this:

```
ldr r0, [r0, #0x10]   ; entity -> ColPrm record
ldr r0, [r0, #0x5c]   ; record -> MoveMan element
add r0, r0, #0xc      ; -> element position pair
bx  lr
```

That is `entity +0x10 → record`, `record +0x5C → element`, `element +0x0C → position`,
recovered from a module we hadn't touched before — and it matches the existing map on
all three hops. Independent confirmation of `ColPrm+0x5C` and `element+0x0C`.

## Two more observations

`0x0216AE70`–`0x0216AE84`: after the handler returns an entity, the initializer stores
the shot element back into `entity+0x30`, then clears **`0x200`** in
`[[entity+0x10]+0x5C] + 0x34` — the MoveMan element's flags word. `0x100` there is the
known snapshot suppressor; `0x200` is new and gets cleared on projectile attach.

`0x0216AEAC`–`0x0216AEF0`: if `[r6+8] & 0x10000`, play a sound through `0x0207342C`,
picking by `[r6+0x1D]`: below `0xC8` → id `0x7A`; `0xC8`–`0xDB` → `[element+0x24]` with
index `[r6+0x1D] - 0xC8`; `0xDC` and up → `[element+0x22]` with index `- 0xDC`. So
`+0x22` and `+0x24` are sound-id banks, and `0xC8`/`0xDC` partition the parameter
block's byte `0x1D` into three sound modes.

## Open questions

1. **`0x2158` bytes of the manager are unaccounted.** Elements end at `+0x1E7C`; the
   manager is `0x3FD4`. `0x2158` doesn't divide evenly by 72 (`118.55`), so it isn't an
   obvious parallel array. A `search-imm 0x1E7C` returns zero hits anywhere in the ROM,
   so nothing addresses the boundary with a literal. The region is either reached by a
   computed offset, or is a fixed sub-object, or is slack — and `MoveMan` had zero
   slack, so slack would be out of character.
2. `0x0216AF04`, the frame pass — 760 bytes, registered as the callback. Not yet read.
3. `0x0216EEF4` and `0x0216B4F4`, the two shared handlers. Reading `0x0216EEF4` first
   tells us whether kinds `0x00`/`0x0F`/`0x15`/`0x16` are stubs or real.
4. `record+0x17C` — new field, gates the arm-A target filter.
5. `element+0x10` — read as a pointer to a signed byte that gets decremented when
   `element+0x26 & 8`. A reference count or a slot counter.

## Not claimed

The `0x88000` value at `+0x18` is called an id only by analogy with `MoveMan`'s
`0xA1000`/`0xA6000`; the vtable slots `0xA0`/`0x24`/`0x94` were not read, so the object
at `+0x18` is unidentified. `0x0208369C(9)`'s argument is called a category on the
strength of the surrounding filter alone. The kind names are unknown — nothing in the
string pool labels the 27 entries.
