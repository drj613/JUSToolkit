# Guard / SP gauges — spec draft

> **DRAFT.** Bead `jus-wayfinder-map-digi.10`. This subsystem's inventory verdict is
> **thin** ([INVENTORY.md §5](INVENTORY.md)): the *apply machinery* is confirmed at
> instruction level, but the gauge *model* — what the meters are, how they get
> created, and whether SP is deck-shared or per-character — is not settled. A
> reimplementer can build the plumbing below but not the gauge itself yet. See
> §GAPS. Static mining only; no new emulator runs.

Primary source: [Battle-Engine-Map.md §guard-sp-gauges](../research/Battle-Engine-Map.md)
(read its taint banner first; the sections cited here are the Phase-0 spec-B12 claim
table and the P157–P161 updates, none of which are in the banner's tainted list).
Beads: `jus-hp-block-at-char-0x56c-q86`, `jus-wayfinder-map-digi.13`.

---

## 1. What is confirmed: the apply machinery

### 1.1 The clamp-accumulator gauge primitive

One reusable gauge shape, `{+0x16 max (s16), +0x18 current (s16)}`, units 1/64
(raw `0x4000` = 256.0 displayed), with three arm9 accessors:

| addr | name | behaviour |
|---|---|---|
| `0x02078488` | Grow / ApplyDeltaToCurrent | clamped add into `[0, max]` |
| `0x020784B8` | GrowMax | raises max, capped at `0x4000` |
| `0x020784E4` | IsCurrentBelowPercentOfMax | both known callers pass `pct=25` |

Sources: [HP-Struct-From-Disassembly.md](../research/HP-Struct-From-Disassembly.md),
[findings/p173-char-0x56c-is-the-character-struct.md](../research/findings/p173-char-0x56c-is-the-character-struct.md),
bead `jus-hp-block-at-char-0x56c-q86`.

**Warning — do not resurrect the "it's a separate gauge" reading.** P172 floated
that the struct behind `char+0x56C` was a guard/SP gauge rather than HP. **P173
retracted that**: `char+0x56C` points at the character struct and `+0x16`/`+0x18`
are max/current HP; status id 19's −4 drains *current HP*
([p173](../research/findings/p173-char-0x56c-is-the-character-struct.md)). Any
guard/SP gauge instance must therefore live somewhere *other* than `+0x56C`.

### 1.2 Trampolines into the gauge

- **Fill trampoline `0x020783CC`**: loads `r0` from `[char+0x56C]`, tail-jumps into
  Grow. All **8** static call sites enumerated (ov6, unconditional `bl`):
  `0x02157DC0`, `0x021582C4`, `0x02158BC0`, `0x02159274`, `0x021592D0`,
  `0x0215952C`, `0x02159668`, `0x0215A318`
  (Battle-Engine-Map §guard-sp-gauges claim 1, CONFIRMED_STATIC).
- **Drain trampoline `0x020783B8`**: same `+0x56C` target, but negates the delta
  (`rsb r1,r1,#0`) first; caller ov6 `0x0215AC70`. Found only by a manual byte
  sweep — both trampolines jump via `bx ip` through an inline pool word, which
  `xrefs-to`/`pool-values` cannot see (claim 8). A reimplementer's takeaway:
  every "N callers" count in this subsystem is a floor, not a census.
- Deltas at the trampoline boundary are only ever scaled by **constant powers of
  two** (`lsl #6`, `lsl #8`, or unscaled) — there is **no chain-length or other
  non-constant damage scaling anywhere in this subsystem** (P157–P159,
  CONFIRMED_STATIC). Different opcodes deliberately take different units
  (×64 = ids `0x25`/`0x26`, ×256 = `0x27`–`0x29`, unscaled = id `0x04`).
- `0x02078428` sets HP to exactly **1** on every living character when called
  with `r1 = 0` (P157).

### 1.3 The `+0x558` meter-node list (the guard/SP candidate)

The **walker `0x020783DC`** is fully decoded (claim 11, CONFIRMED_STATIC):

- loads a list head from `char+0x558`;
- per node: skips if `node+0x40` (byte) or `node+0x3C` bit 0 is set — generic
  enable/pause gates, *not* a type discriminator (claim 12);
- calls `Grow(node, delta)` on unflagged nodes;
- advances via `node+0x00` (next pointer).

Exactly 2 static call sites reach the walker (`0x02157E0C`, `0x021592B4`).
`char+0x558/+0x55C/+0x560/+0x564` are zero-initialized together in one startup
loop at `0x02075FF8`–`0x02076008` (claims 13–14).

Headline negative result (spec B12): **no second *fixed* struct offset feeds
Grow/GrowMax anywhere in the enumerated call graph** — every path resolves to
`+0x56C` (HP) or to a dynamic `+0x558` node. So the `+0x558` list is the leading
candidate for guard-health/SP meters. Held at plausible, not confirmed: the
sweep that produced it is demonstrably non-exhaustive (it missed the drain
trampoline; claims 7/8/10).

### 1.4 The SP total and the live SP-apply path

- **SP total is a word at `player_slot+0x5C8`**, reached from a character as
  `[[char+0x1B4]+0x5C8]`. `char+0x1B4` is one of four `0x61C`-byte player slots
  starting at ComicDeck`+0x64`
  ([char-0x1b4-is-a-comicdeck-player-slot.md](../research/findings/char-0x1b4-is-a-comicdeck-player-slot.md)).
- **SP-apply `0x020781E4`** is three lines: `[slot+0x5C8] += amount`, refused when
  the amount is negative and the signed byte `slot+0x5CF` is non-zero — i.e.
  `+0x5CF` **blocks SP loss but never SP gain**. `+0x5CC`/`+0x5CD` are read the
  same way (untraced siblings)
  ([player-slot-sp-total-at-0x5c8.md](../research/findings/player-slot-sp-total-at-0x5c8.md),
  which also carries the 14-field slot map; note `+0x558` and `+0x56C` appear in
  that slot map too — the map does not settle which base object "char" is, see
  GAP 5).
- The **view is a live SP-apply path**: view selectors 9/12 tail-call
  `0x020781E4` with a per-slot `int16` from `view+0x16+N*2`; selectors 13/14
  apply the `view+0x64` scratch halfword if non-zero
  ([view-handlers-are-the-live-sp-apply-path.md](../research/findings/view-handlers-are-the-live-sp-apply-path.md)).
  Fine distinction a spec writer will get wrong: the 16-slot view handler
  *table* is dead in retail
  ([the-view-handler-table-is-dead.md](../research/findings/the-view-handler-table-is-dead.md)),
  but the view itself is not — hit resolution and the state dispatcher call it.

### 1.5 The status/effect dispatch around the gauges

(Shared with the damage spec; listed here because guard/SP deltas arrive
through it.)

- 42-entry, 8-byte-stride handler table at ov6 `0x02171168`; effect **ids 1–41,
  0 = none**. Ids `0x01`–`0x11` are gauge effects with no status byte (P157/P159).
- Dispatcher ov6 `0x02158ED0(battleObj, id)`; effect nodes at
  `battleObj+0x7C + slot*0x18`, two slots (P158/P159).
- On-hit flush `0x02158B20`: pending HP delta `scratch+0xE8`, pending second
  gauge `+0x130`, plus two staged effect ids at `X+0x172/0x173` (`+0x173` stored
  negated), `X = [[battleObj+0x1A8]+0x10]` (P159 Route B).
- Duration formula (`0x02158F44`): `duration = base + (base/10)*(stat*2)` —
  scales status *duration*, not damage; the meaning of `stat` is not claimed
  (P158/P160).
- GrowMax has exactly one caller (`0x0215C73C`), gated on bit `0x80` of
  `char+0x128`, fixed +0x400 delta — plausible home of the "max HP on respawn"
  passive, ability `0x07` (claim 9, PLAUSIBLE).

---

## 2. GAPS — what a reimplementer cannot build yet

The plumbing above moves numbers into gauges. **The gauge model itself is
unspecified.** Concretely:

1. **No node-insertion site for `char+0x558` exists in the database.** Of 37
   ROM-wide load/store hits on immediate `0x558`, exactly **1 is a store — the
   zero-init**. Nothing populates the list with a live node (likely a split-base
   `add`+register-offset store, invisible to immediate scans; see INVENTORY
   "Tooling hazards"). A spec cannot say how meters come into existence.
   (Battle-Engine-Map claim 14 + open questions; `GDB-Validation-Queue.md`.)
2. **Node-kind census is statically unresolvable.** How many gauge kinds live in
   the list (guard? SP? one shared "resource" node?) is unknown — the walker has
   no type dispatch (claim 13, SPECULATIVE).
3. **Deck-shared vs per-character SP is unresolved — the biggest design question
   here.** SP is documented as deck-wide (shared across a player's 3-character
   team), and the confirmed SP total does sit on a *per-player* slot
   (`+0x5C8`). But the meter list sits at a per-character `+0x558`. Is SP a
   node aliased across the team's three character structs, or does each
   character feed a shared pool? Do not pick a model in a reimplementation
   without settling this. (Battle-Engine-Map §guard-sp-gauges open questions;
   INVENTORY §5 question 3.)
4. **The `+0x558` node vs `+0x56C` pointer identity dispute** — the campaign's
   top open dispute, **ticketed as `jus-wayfinder-map-digi.13`** ("Settle or
   waive: +0x558 vs +0x56c gauge dispute", GDB card #1). The aliasing lens says
   yes (`0x02077E70` stores a raw candidate node into `char+0x56C` at
   `0x02077FDC`); the disasm-correctness lens says no (disjoint, fully-traced
   caller graphs). Everything in §1.3 that touches identity is contingent on it
   (Battle-Engine-Map §chrb-catalog "TOP OPEN DISPUTE", claims 3/11/16).
5. **Base-object ambiguity.** The guard/SP findings write `char+0x558/+0x56C`,
   while the player-slot map lists `+0x558` and `+0x56C` as fields of the
   `0x61C` ComicDeck player slot. Whether these are one object under two names
   or a genuine offset coincidence is not pinned down in the corpus; it feeds
   directly into gap 3/4.
6. **87% of the player slot (`+0x000`–`+0x557`) is unmapped**, and `+0x059`–`+0x557`
   is untouched by `ComicDeck.cpp` itself — some other module owns it
   ([player-slot-sp-total-at-0x5c8.md](../research/findings/player-slot-sp-total-at-0x5c8.md)).
7. **A fixed-offset guard/SP gauge elsewhere is not excluded** — no byte-pattern
   scanner for the `ldr ip,[pc,#N] / ldr r0,[r0,#M] / bx ip` trampoline shape
   with `M != 0x56C` was ever run (Battle-Engine-Map open questions; claim 10
   held plausible only).
8. **Guard mechanics proper** (what blocking costs, the Auto-Guard interaction
   with an empty SP pool) are untested — Auto-Guard's zero-damage measurement
   was taken with SP available (INVENTORY §9).

Resolution path: gaps 1, 2, and 4 are runtime questions
(`jus-wayfinder-map-digi.13` / GDB card #1); gap 3 may fall out of them.
