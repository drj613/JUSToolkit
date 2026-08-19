# Koma Data Survey (K1)

Loop-Atlas iteration 1. Static analysis only, no emulator. Three parallel scanners: files on disk, repo parsing code, partial docs.

**Bottom line:** the koma record format is solved and coded. `koma.bin` holds 890 fixed 12-byte records, and `Binary2Koma.cs` reads all 12 bytes. But the fields designers care about — size, cost, and nature/color — aren't among the four named fields. They're hiding in the six bytes labeled `Unknown`, or in `kshape.bin` / `piece.bin`. That's the whole job of K2.

## Where koma data lives

All paths under `jus_files/ripped_jus_files/` (read-only).

| Path | Size | Header | What it is |
|---|---|---|---|
| `bin/koma.bin` | 11 KB | none | **The koma table.** 890 records × 12 bytes. CONFIRMED |
| `bin/komatxt.bin` | 13 KB | none | Koma name/description text, 0xC per entry, indirect strings. CONFIRMED |
| `bin/kshape.bin` | 1.6 KB | none | Panel **geometry** — grid footprint of each shape. PLAUSIBLE |
| `bin/piece.bin` | 35 KB | none | Larger per-piece table, purpose unknown. SPECULATIVE |
| `koma/koma.aar` | 2.8 MB | `ALAR` | ~898 entries — koma panel artwork, one per panel. PLAUSIBLE |
| `bin/InfoDeck.aar` | 570 KB | `ALAR` | ~130 entries — koma-browser UI text/assets. CONFIRMED (parser exists) |
| `deck/Deck.aar` | 46 KB | `ALAR` | ~370 entries — deck-menu assets + `NNN.bin` name records. CONFIRMED |
| `deckselect/`, `deckcheck/`, `deckmake/` | 11–86 KB | `ALAR`, `DSIG`, `ALTM` | Per-screen UI art. Not data. |
| `battle/deck00.dig` + `.atm` | 4.3 + 2.1 KB | `DSIG`, `ALTM` | In-battle deck HUD graphic. Not data. |

Two independent counts agree: 890 records (11 KB ÷ 12 = 890) and ~898 `koma.aar` entries. CONFIRMED the record table and art archive are 1:1 per koma.

Assets are grouped by UI screen, not per character. Per-koma numbering only exists inside `koma.bin` + `komatxt.bin`.

No koma-only JSON in `jus_files/analysis/`. `arm9_tables*.json` mention koma but only as disassembly-derived table labels.

## Record layout (as coded)

From `src/JUS.Tool/Graphics/Converters/Binary2Koma.cs:28` and `src/JUS.Tool/Graphics/KomaElement.cs:25`. Stride 12 bytes, little-endian, count = `stream.Length / 12`. CONFIRMED — shipping code.

```
0x0  u16  ImageId          0..889
0x2  u16  Unknown2         <-- candidate: size / cost / nature
0x4  u8   nameIdx          index into Koma.NameTable (43 entries, from ARM9 0x0209E840)
0x5  u8   nameNum          KomaName = "{name}_{nameNum:D2}"
0x6  u8   Unknown6         <-- candidate
0x7  u8   Unknown7         <-- candidate
0x8  u8   KShapeGroupId    -> kshape.bin
0x9  u8   KShapeElementId  -> kshape.bin
0xA  u8   UnknownA         <-- candidate
0xB  u8   UnknownB         <-- candidate
```

This resolves the doc contradiction. `Deck-System.md` described 3 fields; `Koma-Research.md` described 5 including the kshape pair. Neither was wrong — both were incomplete. The code names 6 fields and leaves 6 unknown.

`komatxt.bin` entry (0xC bytes): `Name` (4-byte string pointer) + `Unk1` i32 + `Unk2` i32. Count = `firstInt32 / 0xC`. CONFIRMED (`Texts/Converters/Binary2Komatxt.cs`).

## Existing tooling

- `jus export-komas --container koma.aar --koma koma.bin --kshape kshape.bin --output DIR` dumps every koma to a named PNG. Entry point `src/JUS.CLI/JUS/CommandLine.cs:52-100`, implemented at `src/JUS.CLI/JUS/Graphics/DtxCommands.cs:242`. `ImportKoma` (line 333) reverses it.
- Text converters exist for `komatxt.bin`, `Deck.aar/deck/NNN.bin` (0x40 header + name, 0x5C total), `p\d{3}.bin` (0x14 header + name + i32 at 0x34, 0x40 total), and `InfoDeck.aar/bin/deck/XX.bin` (10 string pages per entry). All have PO export.
- **Gap:** nothing dumps `koma.bin` fields to text or JSON. The CLI only makes images. A field dumper is the cheapest K2 step.
- `scripts/analyze_deck_dump.py` is a RAM-dump scanner, not a format parser. Useful for K3, not K2.

## What the docs already claim (check in K2)

CONFIRMED (from `Deck-Memory-Structure.md` RAM dumps): 8 deck slots (index 0–7 at `0x020AFEB4`); koma master table base `0x020B9480`, sequential 32-bit LE IDs; deck state flag `0x020A0C98` (0x05 = leader, 0x07 = no leader); unlock bitmask `0x020B0BAC`; leader runtime pointer `0x020A4368`.

PLAUSIBLE (from `Deck-System.md` / `Koma-Research.md`): grid is 5×4 = 20 cells. Helper = 1 koma, Support = 2–3, Battle = 4–8 — so size is the panel-type discriminator, no separate type-ID field. Shapes aren't all rectangles (Naruto 4-koma exists as 4×1 and 2×2). KShape images are 0x14 bytes, 48×48 px tiles. Name table at `0x0209E840` (arm9.bin offset `0x9E780`), formula `LKN * 4`. `letters=1` → "Eyeshield 21" is a guess with a question mark.

## Still unknown after K1

1. **Nature / color system — nothing found.** No nature list, no bonus formula, no thresholds in any doc or code. Single largest hole; may not live in `koma.bin` at all.
2. **Costs and limits.** No cost table anywhere. Only "+1 SP helpers affect the whole deck," named without a value.
3. **Which unknown byte is size?** Size may be derivable from `kshape.bin` geometry and not stored in `koma.bin`.
4. `piece.bin` (35 KB) — unexamined. Big enough for per-koma placement or cost data.
5. Exact `kshape.bin` layout. `Koma-Research.md` gives `((group * 4) + element) + 0x40` and separately "position 0x40 + result × 18" — inconsistent. Real answer is in `DtxCommands.KShapeSprites`.
6. `type4` / `type5` attack categories in `Character-Mapping.md` — never defined.
7. Runtime koma struct at the leader pointer; deck-slot ↔ koma-index mapping.

## K2 plan

1. Read `DtxCommands.KShapeSprites` and nail down the real `kshape.bin` layout. Cheap, and likely gives us shape and size.
2. Add a `koma.bin` → JSON field dumper, then look at the distribution of each unknown byte across all 890 records. A field with 4–8 distinct values is a nature or size; ~74 distinct values means character index.
3. Cross-check 3+ characters whose panels are known from `Deck-System.md`. Naruto (two natures, two shapes) is the best test case — it isolates nature from shape.
4. Only then decide whether `piece.bin` needs opening.
