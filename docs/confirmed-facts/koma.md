# Koma / kshape — Confirmed Facts

Audience: an engineer reimplementing the JUS koma (deck panel) system from scratch.
Verdict per `docs/confirmed-facts/INVENTORY.md` §8: **portable now** — the two data
files, the placement rule, and the adjacency-ability mechanic are all closed. This doc
owns the on-disk formats and koma semantics. For the editor-side validator call
sequence, the ComicDeck memory block, and deck nodes, see
`docs/confirmed-facts/deck-editor.md` §4–§5 — not repeated here.

Everything below is static analysis of the shipped files plus already-held RAM dumps;
no claim depends on a live emulator run. Unresolved items are marked **OPEN**.

---

## 1. koma.bin — the panel catalogue

`bin/koma.bin`, 10680 bytes = **890 records × 12 bytes**. One record per panel (koma).
Source: `docs/research/findings/koma-format-decoded.md` (field map stands; its
"nature is not in koma.bin" headline was later overturned — see §2). Tool:
`scripts/analysis/dump_koma.py`.

| Off | Type | Name | Status | Meaning |
|---|---|---|---|---|
| `0x0` | u16 | imageId | CONFIRMED | `0..889`, always equals record index — redundant |
| `0x2` | u16 | characterId | CONFIRMED | `1..312`, 312 distinct characters |
| `0x4` | u8 | seriesIdx | CONFIRMED | `1..42`, index into `Koma.NameTable` (`src/JUS.Tool/Graphics/Koma.cs:33`, 43 slots, slot 0 null; strings from ARM9 pointers at `0x0209E840`) |
| `0x5` | u8 | panelOrdinal | CONFIRMED | 0-based panel number within the character; `(seriesIdx, panelOrdinal)` is unique across all 890 |
| `0x6` | u8 | panelType | CONFIRMED | `0` Battle, `1` Support, `2` Helper — cached, fully derivable from size (see below) |
| `0x7` | u8 | abilityId | PLAUSIBLE | meaning depends on panelType (see below) |
| `0x8` | u8 | kshapeGroupId | CONFIRMED | **panel size = value + 1** (66/66 rule, §3) |
| `0x9` | u8 | kshapeElementId | CONFIRMED | which shape of that size |
| `0xA` | u8 | unkA | **OPEN** | `0..8`, always ≤ size; loosely tracks shape bounding box (width 474/890, height 500/890) — render anchor? sort key? |
| `0xB` | u8 | flags | CONFIRMED (high nibble) | **high nibble = per-panel nature override** with sentinel `3` = "use base" (§2). Low nibble **OPEN** (INVENTORY §8 open Q2) |

Derived facts (all zero-exception over 890 records, `koma-format-decoded.md`):

- **panelType is determined by size**: size 1 → Helper (312), size 2–3 → Support
  (188+184), size 4–8 → Battle (62+61+55+16+12).
- **312 characters, each with exactly one 1-cell helper panel** (312/312). 120
  characters have only the helper; only characters with a size-4+ panel are playable.
- **abilityId by type**: Helper — 47 distinct values in `0..55` (passive id space
  reaches `0x37`, wider than the cheat-code list's `0x30`); Battle — 74 distinct
  values = index into `chr_b.bin` (which has exactly 74 battle-character records);
  Support — 193 distinct in `0..192`, indexes `chr_s.bin` (see §2 support path).
- Worked example (Naruto, characterId 184, records 497–505, sizes `[1,2,3,4,4,5,6,7,8]`)
  verified against the owner's live table 9/9 in `koma-format-decoded.md` and
  `findings/nature-SOLVED.md`.

## 2. Nature (per-panel, sentinel-and-fallback)

Source: `docs/research/findings/nature-SOLVED.md` (deck-editor accessor `0x0214E480`
in ov5; high-nibble predicate `0x02078CB8`). Nature *is* per-panel — the earlier
"not in koma.bin" negative in `koma-format-decoded.md` is retracted (see the banner
correction and bead `jus-yw8m`). Enum: `0` 力 Power, `1` 知 Knowledge, `2` 笑 Laughter,
`3` なし Neutral.

```
helper  (type 2): nature = 3 (なし), unconditionally
battle  (type 0): nib = (flags >> 4) & 0xF
                  nature = nib                        if nib != 3
                  nature = chr_b[abilityId*0x3C + 0]  if nib == 3 (base nature)
support (type 1): nature = chr_s[abilityId*20 + (kshapeGroupId-1)*8]
```

`3` in the nibble is a "no override" sentinel, not a value. Only 32 battle panels
carry an explicit override. Verified 9/9 on Naruto against owner observation. Full
nature semantics (damage-path use etc.): `docs/confirmed-facts/nature.md`.

## 3. kshape.bin — the shape catalogue

`bin/kshape.bin`, 1648 bytes = 0x670. Sources:
`docs/research/findings/p229-koma-shapes-come-from-kshape-bin.md` (**read only the
last three sections** — the middle is self-superseded),
`findings/koma-format-decoded.md` §kshape, beads
`jus-koma-shapes-come-from-kshape-bin-0j2` and `jus-d9a`. Parser:
`src/JUS.Tool/Graphics/Converters/BinaryKShape2SpriteCollection.cs`.

Layout:

| Offset | Size | Contents |
|---|---|---|
| `0x00`–`0x1F` | 32 | `u32 groupStart[8]` = `(0, 1, 3, 9, 21, 35, 49, 62)` — first entry index per size class |
| `0x20`–`0x3F` | 32 | `u32 groupCount[8]` = `(1, 2, 6, 12, 14, 14, 13, 4)`, sum **66** |
| `0x40`+ | 66 × 0x18 | shape records |

**Record base is `0x40`, not `0x54`.** Two earlier claims of base `0x3C` and `0x54`
were both retracted; bead `jus-d9a` (P0, labeled `correction`) settles it by file
size: `0x40 + 66*0x18 = 0x670` fits exactly, while `0x54 + 66*0x18 = 0x684` overruns
the file by `0x14` (and yields a fractional 65.17-record count — the tell). The `0x54`
reading had been "pinned" by a 65-test popcount check that was insensitive: bitmap
*addresses* are identical under both bases, so the check could not fail. Cite
`jus-d9a` before trusting any older base figure (the `0x54` comments on bead
`...-0j2` are superseded).

Each 0x18 record:

| Offset | Size | Contents |
|---|---|---|
| `+0x00` | 4 | real field, byte sequences like `01 02 03 04` loosely tracking cell count — **OPEN**, NOT a size field (only 1/66 records has word == popcount) |
| `+0x00`–`+0x13` | 20 | 20-byte cell map, one byte per grid cell in linear order: `0` = empty, nonzero = 1-based traversal ordinal (value − 1 = tileset index per the C# parser) |
| `+0x14` | 4 | **20-bit polyomino bitmap**, bit `i` = byte `i` of the cell map |

(The first 4 bytes are both the start of the 20-byte cell map and carry the ordinal
structure noted in `jus-d9a`; the map runs `+0x00..+0x13` and the bitmap is `+0x14`.)

Known data quirk: **record 59 has a duplicate ordinal** (repeats 4, skips 5) —
reproduced independently, likely a data bug in the shipped file (bead `jus-tv3a`,
"what survives" list). 65/66 records are clean.

Rules and geometry:

- **Grid is 5 wide × 4 tall (5 columns, 4 rows), 20 cells.** Bit `i` of the bitmap =
  cell `(col = i % 5, row = i / 5)`. Three independent confirmations: placement
  validator bounds, adjacency-gate bounds + `0x14` row stride, and owner live play
  (`docs/design/Koma-System-Design-Brief.md`). A "4 wide × 5 tall" transpose
  correction was **RETRACTED same-wake** (bead `jus-tv3a`): the deciding test is
  connectivity — 66/66 bitmaps are connected polyominoes at width 5, only 30/66 at
  width 4.
- **Size = group + 1**: every entry in group `g` has exactly `g+1` occupied cells,
  66/66 (`koma-format-decoded.md` "P5 CONFIRMED"). So a koma's size is
  `kshapeGroupId + 1`; no separate size field exists.
- **Lookup**: `entryIndex = groupStart[kshapeGroupId] + kshapeElementId`;
  `fileOffset = 0x40 + entryIndex*0x18`. In code: arm9 `0x02076D00` resolves
  `(class, sub-index)` via the cumulative table (bead
  `jus-kshape-lookup-identified-a1j`; its "returns 0x14 short of the record" reading
  was degenerate — corrected by `jus-d9a`: it returns the record exactly, bitmap at
  `+0x14`).
- **Curated set, not all polyominoes**: fixed polyominoes number 1, 2, 6, 19, 63 for
  sizes 1–5; the file holds 1, 2, 6, 12, 14. Sizes 1–3 complete, 4+ hand-picked
  (533 free polyominoes exist for sizes 1–8; the game ships 66). koma.bin uses 64 of
  the 66 (one size-5 and one size-7 shape unused). Owner's size-5 filter screenshot
  showed 13 options — matches.
- The file loads **verbatim** into battle RAM: header + all 65 full records
  byte-identical at `0x021AF100` (file offset 0 → `0x021AF100`; records from
  `0x021AF154`). See §6.

## 4. The placement rule

arm9 `0x02076D30`, `f(deck, id, col, row)` — read end to end in
`docs/research/findings/p228-koma-shape-is-a-20bit-bitmap.md` (bead
`jus-koma-shape-is-a-20bit-bitmap-423`). Reimplementation:

```
reject if col >= 5 or row >= 4
shape = kshape bitmap for id                # via 0x02076C98 / 0x02076D00, [rec+0x14]
profile = union of the shape's four 5-bit row masks
reject if (profile << col) doesn't fit in 5 bits    # width check: no row wrap-around
mask = shape << (col + row*5)
reject if mask has any bit >= 20                    # spills off the bottom
reject if mask & deck.occupancy                     # deck+0x568, 20-bit occupancy mask
else place: return mask (caller ORs it in)
```

Editor-side call sequence, add-entry contract (`0x02076E38`), and the ComicDeck block
this operates on: `docs/confirmed-facts/deck-editor.md` §4–§5.

## 5. Adjacency grants abilities

Source: `docs/research/findings/p225-koma-adjacency-grants-abilities.md` — **read the
final sections**; the middle contains a base-address error and a retracted
"cross-side link" claim, both corrected in-file. Beads
`jus-koma-adjacency-grants-abilities-70l` (gate, 3/3 live hits),
`jus-second-ability-source-0x558-5rp` (the caller).

Mechanic: **a koma grants its ability to the character occupying the adjacent grid
cell in the direction it points.**

- Each side's deck-battle object holds: two unidentified words at `+0x000`; the 5×4
  pointer grid at `+0x008` (20 cells × 4 bytes, row stride `0x14`); **16** node slots
  of stride `0x50` at `+0x058` (count went 19.6 → 18 → 16; the fractional values were
  the error signal; `0x58 + 16*0x50 = 0x558` exactly); chain head pointer at `+0x558`.
  A `0xC0` gap before the other side's object is **OPEN** (unexplained).
- A node carries: own cell at `+0x0E` (low nibble = column, high nibble = row —
  own-cell verified 11/11), direction at `+0x0F` low nibble (`1..4`), type at
  `+0x40`, and `+0x41` = chr_b index (type 0) or ability id (type 2). Nothing in the
  node is safe to read without checking `+0x40` first.
- Gate arm9 `0x020779CC`: reject direction 0 or >4; step `(dx,dy)` from the 8-byte
  table at `0x02092E34` (`1`=down `(0,+1)`, `2`=left `(−1,0)`, `3`=up `(0,−1)`,
  `4`=right `(+1,0)`); reject off-grid (`x'<5`, `y'<4`, both ≥0); return the pointer
  at `grid[y'*5 + x']`, or fail on null. The caller (AddAbility) appends the node's
  ability id to the returned object's ability list (`+0x1A` count / `+0x1B` list —
  matches the established char-struct layout; object identity is one-usage evidence,
  flagged as such in the bead).
- Verified live 3/3 (predicted neighbour addresses matched grid contents), plus a
  perfect 20-cell tiling of the grid by 11 node footprints. The direction field was
  earlier mistaken for the nature enum (both are 1..4-ish); that reading is dead.
- **OPEN**: what writes the `+0x558` chain (the deck→battle bridge — INVENTORY §8
  open Q5); the two words at object `+0x000`.

## 6. ov12 heap — where these files live in battle RAM

Sources: beads `jus-ov12-window-is-a-tagged-heap-95p` (runtime-confirmed) and
`jus-heap-blocks-matched-to-files-v3e` (byte-comparison comments).

The ov12 window `0x021AC700..0x021C13A0` is a contiguous tagged heap of **19 blocks**
(header: tag `0x4D48` at `+0x00`, allocator base `0x021AC200` at `+0x0C`, size incl.
0x20 header at `+0x10`; zero gaps). Allocation granularity: payload `S` satisfies
`B − 0x40 < S ≤ B − 0x20` for block size `B`.

**15 of 19 blocks byte-matched to files** (identities, not size arguments):

| Block | Size | File |
|---|---|---|
| `0x021AC700` | `0x29E0` | `bin/koma.bin` |
| `0x021AF0E0` | `0x06A0` | `bin/kshape.bin` (payload at `0x021AF100`, verbatim) |
| `0x021AF780` | `0x1180` | `bin/chr_b.bin` |
| `0x021B0900` | `0x0F40` | `bin/chr_s.bin` |
| `0x021BA020` | `0x0380` | `chrbin/chr/col/item.bin` |
| `0x021BA3A0` | `0x0220` | `chrbin/chr/col/db_b_01.bin` |
| `0x021BA5C0` | `0x0260` | `chrbin/chr/col/yo_b_01.bin` |
| `0x021BA820` | `0x05A0` | `chrbin/chr/shot/yo_b_01.bin` |
| `0x021BADC0` | `0x03C0` | `chrbin/chr/col/na_b_01.bin` |
| `0x021BB180` | `0x03A0` | `chrbin/chr/shot/na_b_01.bin` |
| `0x021BB520` | `0x01C0` | `chrbin/chr/col/bl_b_03.bin` |
| `0x021BB6E0` | `0x01A0` | `chrbin/chr/shot/bl_b_03.bin` |
| `0x021BDB00` | `0x0320` | `chrbin/chr/col/op_b_01.bin` |
| `0x021BDE20` | `0x03C0` | `chrbin/chr/col/na_b_01.bin` (second copy) |
| `0x021BE1E0` | `0x03A0` | `chrbin/chr/shot/na_b_01.bin` (second copy) |

**OPEN — 4 blocks match no file** (runtime-assembled, not loaded): `0x021B1840`
(`0x85C0`), `0x021B9E00` (`0x0220`), `0x021BB880` (`0x2280`), `0x021BE580` (`0x2E20`).
Unidentified. Related observations, not promoted to claims: per-character blocks
below `0x021BDB00` group as player-side and at/above as opponent-side (na_b_01
appears twice because Naruto was in both chains); shot loading is conditional (Goku's
`0x80`-byte shot file exists on disk but is absent from the heap) — the heap is a
manifest of what has been *touched*, not what a battle needs.

So for a reimplementation: battle loads `koma.bin`, `kshape.bin`, `chr_b.bin`,
`chr_s.bin` whole and verbatim, plus per-fighter col/shot files per side.

## 7. Open items (consolidated)

From INVENTORY §8 and the beads above:

1. **OPEN** koma.bin byte `0xA` (`0..8`, ≤ size — render anchor? sort key?).
2. **OPEN** low nibble of koma.bin `+0xB`.
3. **OPEN** `piece.bin` (35183 bytes, no 890-stride — variable-length or
   offset-indexed; not a per-koma table) and the P7 relationships table.
4. **OPEN** kshape record `+0x00..` — five trailing u32s per record after the shape
   semantics: the 20-byte ordinal map is understood, but the `+0x00` word's structure
   (per `jus-d9a`) is unidentified; record 59's duplicate ordinal is a probable data
   bug.
5. **OPEN** what writes the `+0x558` node chain (deck→battle bridge), and the deck
   object's first two words / trailing `0xC0` gap.
6. **OPEN** do unlocks gate shapes?
7. **OPEN** the four unmatched ov12 heap blocks (§6).
8. Housekeeping (INVENTORY §8 Q4): the koma-side "size×k" HP speculation in
   `docs/research/Koma-System-Observed-Behavior.md` should be deleted — battle HP
   comes from chr_b per-size records (`docs/confirmed-facts/damage.md`).
