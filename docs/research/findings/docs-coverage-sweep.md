# Docs-coverage sweep — chr_b[0x01] is the tier, confirmed

Loop-Atlas iteration 35. The new procedure worked on its first run — it surfaced a fourth doc I'd never opened.

## The sweep

Checked all 26 `bin/` files for docs named after them. Four have one, making them the highest rediscovery risk:

| file | docs named after it |
|---|---|
| `koma.bin` | 11 (including `docs/articles/specs/koma.md`, never read) |
| `chr_b.bin` | 4 — including **`chr_b-Complete-Mapping.md`, never opened** |
| `jpower.bin` | 3 (last iteration's miss) |
| `state.bin` | `Character-State-Struct.md` — used extensively, but never opened the 336-byte file it describes |

Every `bin/` file gets at least some mention, so there are no true gaps — only rediscovery risk.

## chr_b[0x01] is the tier — CONFIRMED

`chr_b-Complete-Mapping.md` already has the tier table:

> - tier 1: -1 modifier (Bankai B = 9)
> - tier 2: +0 modifier (Ichigo B = 10)
> - tier 3: +1 modifier (Caramelman B = 13)

Three tiers, `1/2/3`, modifiers `-1/0/+1`. My `chr_b[0x01]` distribution is `{1:11, 2:56, 3:7}` — **exactly three values, exactly those values.** Last iteration's test adds a second confirmation: Goku and both damage targets read `2`, giving `tier-2 = 0` and `damage = damage1/5` exactly, matching B = 8.000 with `damage1 = 40`.

Two independent derivations from opposite directions, same field. **CONFIRMED**: `chr_b[0x01]` → battle `+0x11` is the tier.

`chr_b[0x02]` stays unknown. The doc suggests walk speed lives in `chr_b.bin` as a "`statC` field, threshold/tier-based" — worth testing against `[0x02]`'s five values.

## Mutual validation: 74/74 series codes agree

The doc has a full `chr_b` index → character → series → classId → jpower-block table, built from the ARM9 string table at `0x0924B0`. My join takes a different path: `koma.bin` `abilityId` → `chr_b` index, with names from `komatxt.bin` and series from `Koma.NameTable`.

**All 74 rows agree on series code.** Two independent derivations of the same index space with zero disagreement — strong mutual validation for both.

## One narrow correction: chr_b[24] is Kyuubi Naruto, not Kakashi

The doc puts Kakashi (`na_b_05`) at `chr_b[24]` and Kyuubi Naruto (`na_b_02`) at `chr_b[21]`. Three independent lines say `chr_b[24]` is Kyuubi Naruto:

1. `koma.bin` records 504 and 505 (sizes 7 and 8) have `abilityId = 24`.
2. `komatxt.bin` names those panels **ナルト（九尾）**.
3. `chr_b[24]`'s per-size HP slots 3 and 4 are **192, 208** — exactly the owner's observed Naruto size-7/8 HP. `chr_b[21]` gives `176, 192`, which doesn't match.

The series column and 74/74 agreement stand; only the character name at these indices is wrong. Likely cause: the doc assumes the `0x020924B0` string-table index equals the `chr_b` index, and `Battle-Engine-Map.md` already **demoted** that assumption — its claim that the table's 6-bit id equals `chr_b`'s `classId` was refuted on a range mismatch. The alignment was never verified.

## On the procedure

Last iteration I wrote the loose-ends rule as a procedure because stating it as an insight hadn't stuck. First application found `chr_b-Complete-Mapping.md`, which contained a confirmation I'd spent two iterations deriving from scratch.

The `state.bin` case is the one to flag next: I've read and edited `Character-State-Struct.md` repeatedly this phase without once opening the 336-byte file it describes.
