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

### The 4-bit nibble in `record+0x34` is compared attacker-against-target

Arm A pulls a 4-bit value out of the **attacker's** ColPrm record and checks it against
three fields in each **target's** record. The full sequence, both sides:

```
; attacker: sl = arg0, [sl+0x10] = attacker's ColPrm record
0x0216A990: ldr  r0, [r1, #0x38]
0x0216A994: ldr  r1, [r1, #0x34]
0x0216A998: tst  r0, #0x800
0x0216A99C: andne r0, r1, #0xf0
0x0216A9A0: orrne r1, r1, r0, lsr #4
0x0216A9A8: and  r5, r1, #0xf        ; r5 = attacker's 4-bit value

; target: r1 = [payload+0x10] = target's ColPrm record
0x0216A9DC: ldr  r0, [r1, #0x34]
0x0216A9E4: and  r0, r0, #0xf        ; target's 4-bit value
0x0216A9E8: tst  r2, #0x800          ; target's +0x38
0x0216A9EC: bne  skip                ; target in category 0x800 -> skip outright
0x0216A9F0: ldr  r2, [r1, #0x3c]
0x0216A9F4: and  r2, r2, #0xf
0x0216A9F8: tst  r5, r2
0x0216A9FC: bne  skip                ; any bit overlap -> skip
0x0216AA00: ldr  r2, [r1, #0x17c]
0x0216AA04: cmp  r2, #0
0x0216AA08: cmpne r5, r0
0x0216AA0C: beq  skip                ; skip if +0x17C == 0 OR attacker nibble == target nibble
```

The upshot: a target only gets a shot spawned against it when `+0x17C != 0` **and** the
attacker's nibble differs from the target's nibble **and** nothing overlaps in
`+0x3C & 0xF`.

Three things here matter structurally, because they are exactly the shape a
per-move-attribute hypothesis would need to fit:

1. **`record+0x34`'s low byte packs two 4-bit fields, not one.** When `0x800` is set in
   the attacker's `+0x38`, the upper nibble (`0xF0`) gets shifted down and OR'd into the
   low nibble before masking. A second 4-bit field, folded in conditionally on category.
2. **`+0x3C & 0xF` acts as a mask** (tested with `tst`), but the same `r5` is also used
   as an **equality operand** (`cmpne`) against the target's nibble. Using the same value
   both ways forces it into a small bitfield where "equal" really means "the same single
   bit is set".
3. The comparison genuinely runs **attacker-side value against target-side fields** — the
   exact layout any "attribute of the move versus attribute of the defender" model would
   require.

**The semantics push back hard against calling this nibble an attack nature, though, and
I am not claiming it is one.** The test *drops the target from the spawn set entirely*
when the two nibbles match. A nature-versus-nature system would **scale damage** — it
would not erase the target from the candidate list outright. Removing everything that
shares your own value looks like a **team/side filter**: don't fire a projectile at
your own side. Under that reading, `+0x3C & 0xF` becomes "sides or categories this
record ignores" — an immunity mask in form, but a targeting mask by where it sits in the
code. All of this runs at *spawn selection*, before any damage arithmetic has started.

Confidence: the instruction-level facts above are **CONFIRMED_STATIC**. The team/side
filter interpretation is **PLAUSIBLE**. Attack nature is **not claimed** — and on this
evidence it is the weaker reading. If a per-move nature field exists somewhere, this
spawn filter is the wrong place for it; the place to look is a damage-scaling site.

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

## Reachability — CONFIRMED_STATIC, and a tool blind spot

`query.py xrefs-to 0x0216A7BC` returns **zero** references — no branch, no literal
load, no `functions.json` caller. The constructor looks dead. It is not. The xref
index has a gap.

Three sweeps over `arm9` plus all 15 overlays:

1. **Raw data-word search** for `0x0216A7BC` little-endian: **0 hits**. The constructor
   is not in an init table. (Control: `0x0216AF04` gives exactly **1** hit, in
   `ov06.bin` at file offset `121760` — the literal pool entry the constructor loads.
   The search works.)
2. **ARM `bl` decode** of every word: **0 sites** for `0x0216A7BC` and **0** for
   `Battle_ObjCtrlManCreate` `0x02168B88`. (Control: `Battle_MoveManCreate`
   `0x02082A38` gives exactly **1** site, `arm9 0x020833D0`, encoding `0xEBFFFD98`.)
3. **Thumb `BL`/`BLX(1)` decode** at 2-byte alignment: **1 site each.**

```
0x0214D818: f01b e9b6  blx #0x02168b88   ; Battle_ObjCtrlManCreate
0x0214D81C: ldr r1, [pc, #0x108]         ; = 0x0214D928
0x0214D81E: ldr r2, [r1, #0x0]
0x0214D820: mov r1, #0x43
0x0214D822: lsl r1, r1, #2               ; 0x43 << 2 = 0x10C
0x0214D824: str r0, [r2, r1]             ; -> battle root +0x10C

0x0214D826: f01c efca  blx #0x0216a7bc   ; Battle_ObjShotManCreate
0x0214D82A: ldr r1, [pc, #0xfc]          ; = 0x0214D928
0x0214D82C: mov r2, #0x11
0x0214D82E: ldr r3, [r1, #0x0]
0x0214D830: lsl r2, r2, #4               ; 0x11 << 4 = 0x110
0x0214D832: str r0, [r3, r2]             ; -> battle root +0x110
```

Both sites are **Thumb code in `ov6`**, 14 bytes apart in a single battle-init routine.
Each stores its manager pointer into the battle root through the global root pointer at
**`0x0214D928`**:

| Manager | Battle-root slot |
|---------|------------------|
| ObjCtrl (`0x02168B88`) | `+0x10C` |
| ObjShot (`0x0216A7BC`) | `+0x110` |

Both slots sit inside the battle root's known `0x170` bytes — a consistency check, not
a coincidence. Two BLX pairs 14 bytes apart, landing on two independently-named manager
constructors, each followed by a coherent pointer-store sequence, rules out
data-misread-as-code.

**The blind spot:** `xrefs.json` does not record Thumb `BLX(1)` → ARM call sites. A
`query.py xrefs-to` result of "0 references" on an ARM function does **not** mean
unreachable — it means no *ARM* caller. This compounds the already-recorded hazard that
`callers` double-counts.

**Retraction.** The first draft of this section claimed this was "the first time the
cause has been named." That is **wrong, and retracted.** `findings/thumb-caller-audit.md`
already named, tooled, and measured the blind spot (`find_thumb_callers.py`, iterations
95–96), reporting the same ROM-wide **187** of **3691** figure reproduced here. This
pass discovers nothing about the gap itself. The error is recorded rather than deleted,
per the loop's standing rule.

**What *is* new: `--audit` and `--to` disagree on real callers.** Running
`find_thumb_callers.py --to` on either constructor finds both sites and marks them
**ACCEPTED**:

```
ov6   0x0214d826 thumb blx -> 0x0216a7bc [plausibility: NONE]  ACCEPTED
ov6   0x0214d818 thumb blx -> 0x02168b88 [plausibility: NONE]  ACCEPTED
```

Neither address appears in `--audit`'s output. The cause is at
`find_thumb_callers.py:184`: `--audit` gates on `plausible(...)` returning truthy,
while `--to` reports plausibility but accepts on the impossible-edge filters alone.
**`--audit` therefore silently drops every genuine Thumb caller whose neighbourhood
lacks a `46c0` nop, a `b5xx` push, or a `bdxx` pop.** Both sites here score
`plausibility: NONE` yet are unambiguously real — the full Thumb disassembly above is
coherent instruction-for-instruction, and two BLX pairs 14 bytes apart landing on two
independently-named manager constructors is not a bit-pattern coincidence.

This means the audit's **187** ROM-wide and **16** in-battle-code counts are a
**floor, not a census**. The in-battle figure is demonstrably short by at least these
two. The audit doc's own hedge — "the 16 battle targets are all genuine" marked *not
claimed* — was the right call, but the gap cuts both ways: it also misses real callers.
Any past claim of "0 callers, therefore a function pointer" or "therefore vestigial"
needs a Thumb re-check, and `--audit` alone is not sufficient to clear it; `--to` on
the specific address is.

Spot-checked directly, and **not** rescued by any Thumb caller: `0x0207E864`,
`0x0207F7C8`, `0x0207DD40`, `0x0216B2A0` — zero hits each. The standing "`0x0207E864`
has 0 callers, therefore a function pointer" claim survives this pass.

The ObjShot manager **is** constructed on every battle init. It can be reached from the
battle root at `+0x110`, not only through the singleton `0x021729EC`.

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
