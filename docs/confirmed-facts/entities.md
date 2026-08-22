# JUS entities and projectiles — confirmed spec (DRAFT)

> **DRAFT.** Built by static mining only (no emulator runs). The subsystem's
> inventory verdict is **partial** (`INVENTORY.md` §4): lifecycle, ownership,
> and the ObjShot dispatch are solid; projectileId decoding and despawn
> identification are open blockers. See the GAPS section at the end.

Reference for the battle entity pool and projectile machinery in Jump
Ultimate Stars (`jus.nds`, AJUJ). Backed by static disassembly of `arm9.bin`
and `arm9_ov06.bin`, cited inline. Beads (`br show <id>`) hold raw logs.

> Battle-Engine-Map.md carries a taint banner; only its
> §projectile-entities claims (verified through 3 lenses, 2026-08-15/17
> updates) are cited here, alongside findings journal entries.

---

## 1. Architecture: three modules, one root object

The subsystem spans three source files, recovered from assert-string symbols
([module-map-and-attribution-limits](../research/findings/module-map-and-attribution-limits.md),
Battle-Engine-Map §projectile-entities):

| layer | module | constructor |
|---|---|---|
| generic object pool | arm9 `BattleObj.cpp` | `Battle_ObjManCreate` `0x02083204` |
| object control | ov6 `BattleObjCtrl.cpp` | `Battle_ObjCtrlManCreate` `0x02168B88` |
| projectile specialisation | ov6 `BattleObjShot.cpp` | `Battle_ObjShotManCreate` `0x0216A7BC` |

All three land in the battle root object (`0x170` bytes, global pointer
`0x02172960`), built by `Battle_Add`
([battle-add-root-object-map](../research/findings/battle-add-root-object-map.md)):

| root slot | manager |
|---|---|
| `+0x108` | Battle_ObjMan |
| `+0x10C` | ObjCtrl manager |
| `+0x110` | ObjShot manager |

(ObjCtrl and ObjShot are wired by two Thumb `blx` pairs 14 bytes apart at
`0x0214D818`/`0x0214D826`. `xrefs.json` does not record Thumb `BLX(1)` → ARM
calls, so both constructors show "0 references" while being live —
never read "0 callers" as "dead" in this subsystem
([objshot-manager-and-the-27-kind-dispatch-table §Reachability](../research/findings/objshot-manager-and-the-27-kind-dispatch-table.md)).)

## 2. Battle_ObjMan — and a naming retraction to know about

`Battle_ObjManCreate` `0x02083204` allocates **`0x42D8`** bytes via the tagged
allocator (`__FILE__ = BattleObj.cpp`), holds an 8-byte-stride table at
`+0x24`–`+0x74`, and its singleton global is `0x0214BE14` (all 22 ROM
references live in `BattleObj.cpp`)
([census-literal-sizes-and-seven-hidden-managers](../research/findings/census-literal-sizes-and-seven-hidden-managers.md),
Battle-Engine-Map §projectile-entities 2026-08-15 note).

> **Retraction to cite, not repeat:** P202 named the live object at
> `0x0220DDE0` "Battle_ObjMan". **Wrong — it is `Battle_ColMan`**
> (`0x219C` bytes, `BattleCol.cpp` / `Battle_ColManCreate`, allocated by
> `0x0207AD3C`). The error was mixing up "constructed by a function called
> from `Battle_ObjManCreate`" with "is the ObjMan"
> ([p203-three-managers-colman-retraction](../research/findings/p203-three-managers-colman-retraction.md)).
> Any doc saying "ObjMan" about `0x0220DDE0`, its `+0x48` list, or the
> 19-slot `0x188`-stride array means the ColMan.

Manager list heads (working model, control-flow only — **never confirmed
against a live dump**, Battle-Engine-Map §projectile-entities open questions):
`+0x0C` active, `+0x14` free, `+0x1C` pending/retire.

## 3. Pooled entity lifecycle

Confirmed static, Battle-Engine-Map §projectile-entities claims 1–2:

- **Constructor `0x020834D4`** (reached via thin shim `0x02083624`):
  dereferences the manager global `0x0214BE14`, NULL-checks the free head
  `+0x14`, pops an entity, invokes a caller-supplied ctor callback via
  `blx ip` storing its return at `entity+0x30`, unlinks from free and appends
  to active `+0x0C` (or `+0x1C` on failure).
- The constructor **also wires collision**: at `0x02083560` it calls the
  installer `0x0207C988` and stores the return at `entity+0x10`. There is no
  standalone collision registration
  ([collision-wired-by-the-entity-constructor](../research/findings/collision-wired-by-the-entity-constructor.md)).
- **Destructor `0x02083648`**: sets `entity+0x2C` bit 0 ("marked dead"),
  calls the on-destroy hook, unlinks from active, appends to retire `+0x1C`.
  **30 real call sites** (2 arm9 + 28 ov6) — it is shared pool
  infrastructure, not projectile-specific.

### Entity fields (as known)

| offset | contents | source |
|---|---|---|
| `+0x04` | u16 age counter (per-frame, threshold `0x20` in the despawn candidate) | Battle-Engine-Map claim 5 |
| `+0x10` | the **owner**: a `0x188`-byte ColPrm record — simultaneously the ColObj's owner (ColObj at `owner+0x60`) and the damage pipeline's scratch object. One object, three names. | [entity-0x10-is-the-colobj-owner-and-the-damage-scratch-object](../research/findings/entity-0x10-is-the-colobj-owner-and-the-damage-scratch-object.md) |
| `+0x18` | the `0xA8`-byte NoteTrack (built right after construction) | [character-entity-link-and-a-reversed-setter §3](../research/findings/character-entity-link-and-a-reversed-setter.md) |
| `+0x2C` | bit 0 = marked dead | claim 2 |
| `+0x30` | back-pointer to the character (ctor callback's return) | [character-entity-link](../research/findings/character-entity-link-and-a-reversed-setter.md) |
| `+0x38` | `strb -1` at init; finalizers `0x2083C44`/`0x2083CD8` index a per-category table by it — possible type tag, unexplored | same + Battle-Engine-Map open questions |

## 4. Ownership

All confirmed static
([character-entity-link-and-a-reversed-setter](../research/findings/character-entity-link-and-a-reversed-setter.md),
[allocations-are-tagged-and-the-battle-character-is-0x1F0](../research/findings/allocations-are-tagged-and-the-battle-character-is-0x1F0.md)):

- The ov6 battle character is exactly **`0x1F0` bytes** — attribution from
  the allocator's `__FILE__/__FUNC__/__LINE__` tags, the strongest
  attribution mechanism in the corpus. The arm9 `char+0x56C` HP struct
  belongs to a *different*, arm9-side character object; don't merge the two.
- Bidirectional link, set up synchronously inside `Battle_CharaCreate` via
  callback `0x021570EC`: **`character+0x1A8` = the pooled entity**,
  **`entity+0x30` = the character**.
- **Spawn dispatch** ov6 `0x021574CC`: a 13-way switch on its 3rd argument,
  operating on `char+0x1A4` (hit tally) and `char+0x1A8`; reaches the
  spawn/ownership routine `0x02168CF4`, gated by a one-active-spawn cap on
  `char+0x1AC` (Battle-Engine-Map claim 3).
- **Spawn + ownership** `0x02168CF4` (ObjCtrl module): obtains a wrapper from
  the ov6-local manager (literal `0x02172990`), calls the pool allocator,
  and records ownership on the *wrapper*: `+0x08` new entity, `+0x0C` the
  attacker's MoveInfo pointer, `+0x18` the raw character struct (stored by
  the dispatcher's caller `0x02157720`) (Battle-Engine-Map claim 4).

## 5. ObjShot: the projectile layer

All from
[objshot-manager-and-the-27-kind-dispatch-table](../research/findings/objshot-manager-and-the-27-kind-dispatch-table.md),
CONFIRMED_STATIC, attribution from the constructor's own allocator strings.

### 5.1 Manager (`0x3FD4` bytes, singleton `0x021729EC`)

| offset | contents |
|---|---|
| `+0x00` | active-list head |
| `+0x10` | free-list head |
| `+0x18` | resource/track object from `0x02026F94`, id `0x88000` |
| `+0x1C` | element array: **72 × `0x6C`**, ends `+0x1E7C` |
| `+0x1E7C`… | **`0x2158` bytes unaccounted (54% of the manager)** |

Per-frame entry point `0x0216AF04`, registered via `0x02028384`.
Note these offsets are a *different* struct from the generic pool manager's
`+0x0C`/`+0x14`/`+0x1C` — do not merge.

### 5.2 Shot element (`0x6C` bytes), from initializer `0x0216ACC8`

| offset | width | meaning |
|---|---|---|
| `+0x00` | | link node |
| `+0x08` | word | retained parameter block |
| `+0x10` | word | pointer to a signed byte, decremented when `+0x26 & 8` (ref/slot counter?) |
| `+0x18` | half | lifetime in frames; **default 30** (`0x1E`) when param is zero |
| `+0x1A` | byte | **kind** — the dispatch index |
| `+0x1C` | word | conditional payload (`[r6+0x14]` if `[r6+8] & 1`) |
| `+0x22`/`+0x24` | half | sound-id banks (param byte `0x1D` partitions modes at `0xC8`/`0xDC`) |
| `+0x26` | half | flags; bit 0 set by `0x0216AC10`, bit 3 tested at `0x0216ADF0` |
| `+0x2C` | word | the spawned entity — written by the kind handler; **six kinds (`0x01, 0x05, 0x0E, 0x17, 0x18, 0x19`) carry no entity**, the other 21 do |

### 5.3 The 27-kind dispatch — confirmed arity

Kind byte `elem+0x1A` indexes a **27-entry function-pointer table at
`0x02172864`** (kinds `0x00`–`0x1A`), **no bounds check** in the caller. The
arity is pinned by data on both sides (table start to the
`"BattleObjShot.cpp"` string at `0x021728D0` = exactly `0x6C` bytes).
`0x0216EEF4` serves four kinds (`0x00/0x0F/0x15/0x16` — stub or default,
unread); `0x0216B4F4` serves three. Kind names are unknown — nothing in the
string pool labels them. Kind `0x1A`'s handler `0x0216B2A0` is **missing
from functions.json** (a known binning gap). Full handler table in the
finding. Bead `jus-cvx` queues a live kind-byte walk.

### 5.4 Spawn path `0x0216A944` and the collision interaction

Two arms, selected by a byte at `[[r1+0x10] + slot*32]`:

- **Arm A (multi-target)**: walks a list from `0x0208369C(9)` and filters
  targets by their ColPrm-record fields: skip when target `+0x38 & 0x800`
  (category routing), when `+0x3C & 0xF` overlaps the attacker's nibble,
  when `+0x17C == 0`, or when the attacker's `+0x34` low nibble equals the
  target's. The attacker-vs-target nibble test is a spawn-*selection* filter
  — it drops same-nibble targets outright, which reads as a **team/side
  filter (PLAUSIBLE)**, explicitly *not* an attack-nature system.
- **Arm B (single)**: pops the free head and runs the initializer.

`record+0x17C` was new to the ColPrm map here. On attach, the initializer
stores the shot element into `entity+0x30`, and clears bit `0x200` in the
MoveMan element's flags (`[[entity+0x10]+0x5C]+0x34`) — a sibling of the
known `0x100` snapshot suppressor.

The chain **`entity+0x10 → ColPrm record → record+0x5C → MoveMan element →
element+0x0C position`** is independently re-confirmed by two byte-identical
leaves in this module (`0x0216B3D8`/`0x0216B740`). Collision and damage share
one object: the entity's `+0x10` owner *is* the damage scratch base whose
`+0x40` bit `0x800` gates delta application
([entity-0x10 finding](../research/findings/entity-0x10-is-the-colobj-owner-and-the-damage-scratch-object.md)).

## 6. projectileId — an opaque token. Do not decode it.

Authoring-data field: **sbyte at collision-record offset `0x03`**
(`src/JUS.Tool/Combat/Converters/Binary2Collision.cs:81`). Across all 2837
records: 211 negative (contiguous band −18…−34, nothing in −1…−17),
24 positive, 2602 zero.

What IS confirmed
([projectileid-is-a-selector-not-an-index](../research/findings/projectileid-is-a-selector-not-an-index.md)):

- It attaches to projectile machinery: 92% of negatives sit on
  CollisionType 4 (projectile) / 5 (summon).
- It is **one value per character**, not per record: 92 of 120 characters
  with negatives use exactly one distinct value file-wide.

**Four refuted decodings** — a spec must treat the value as an opaque token:

| hypothesis | verdict | where |
|---|---|---|
| per-character shot-record index (`\|v\|`, `\|v\|-1`) | REFUTED — 2.4% in-bounds | [shot-data-and-projectileid-refuted](../research/findings/shot-data-and-projectileid-refuted.md) |
| biased index `-v-18` into the character's shot file | REFUTED — 28% in-bounds; only 17/184 characters even have 17+ records | [projectileid-is-a-selector-not-an-index §2](../research/findings/projectileid-is-a-selector-not-an-index.md) |
| a global 17-entry table in `ChrBin.aar` | REFUTED — 0 files with 17 records, 4 dirs × 6 strides | same, §1 |
| `chr/col/item.bin` as that table | REFUTED — 43 records; it *consumes* the negative band itself | same, §1 |

Standing hypothesis (**PLAUSIBLE, untested**): a code-side spawn-behaviour
selector dispatched by a switch in ov6 (the 13-way `0x021574CC` shows the
architecture works this way, though 13 ≠ 17). No data-level predictor for
which value a character gets was found.

## 7. Despawn — identified candidates, no promotion (BLOCKER)

Battle-Engine-Map claim 5, **capped PLAUSIBLE**: ov6 `0x0216C958` has four
per-frame kill conditions converging on the destructor `0x02083648` —
(a) a flag/boundary gate; (b) age `entity+0x04` vs 32 frames, suppressible
by `[entity+6] & 0x2`; (c)/(d) a bounded-range check `[0x100, 0x3FF00]` on a
separate field. But two siblings, `0x0216E1C0` and `0x0216F398`, reuse the
identical scaffolding, and all three live inside `BattleObjShot.cpp` — the
static evidence cannot say **which is *the* projectile despawn**. The
mechanics are confirmed; the identity is not. Needs a live GDB census.

---

## GAPS — settle-or-waive candidates for the spec (wayfinder epic, spec bead `.9`)

1. **projectileId semantics** (highest-value blocker). Settle: search ov6 for
   a ~17-case jump table or a `0x12`/`0x22` bias on a signed byte; or
   breakpoint `0x02168CF4` for a known single-value character. Waive: spec
   it as an opaque per-character token copied verbatim (the 4 refutations
   above justify this).
2. **Despawn identification** (blocker). Settle: GDB census across
   `0x0216C958`/`0x0216E1C0`/`0x0216F398`. Waive: spec "a per-frame updater
   destroys via `0x02083648` under the four conditions" without naming which
   routine, since the conditions themselves are CONFIRMED_STATIC.
3. **54% of the ObjShot manager (`0x2158` bytes past `+0x1E7C`) unaccounted**;
   nothing addresses the boundary with a literal.
4. **Pool-manager list semantics** (`+0x0C`/`+0x14`/`+0x1C` =
   active/free/retire) — inferred from control flow only, never checked
   against a live dump. Bead `jus-45k` queues the root/manager live read.
5. **Q5: persistence across character switch** — no owner-liveness check was
   found in the despawn candidates; consistent with persistence, unproven.
6. **`record+0x17C`** — gates the multi-target spawn filter; otherwise
   unexplored.
7. **Kind names for the 27 handlers**; the shared handlers
   `0x0216EEF4`/`0x0216B4F4` unread; kind `0x1A` handler `0x0216B2A0` absent
   from functions.json. Bead `jus-cvx`.
8. **`entity+0x38`** as a projectile-vs-other type tag (finalizer table
   index) — unexplored.
9. **`entity+0x10` residual tension**: the owner record's `+0x68` is claimed
   "vestigial, no writer" while the damage formula walks `[r4+0x68]` live
   (INVENTORY §2 disputes) — inherited from the collision spec, flagged here
   because the entity carries the object.
10. The 17 negatives on non-projectile CollisionTypes 1/2/3, and the 24
    positive projectileId values — unexplained.
11. **ObjCtrl layer** (`0x02168B88`, `BattleObjCtrl.cpp`) — only the spawn
    routine `0x02168CF4` has been read; the manager itself is unmapped.
