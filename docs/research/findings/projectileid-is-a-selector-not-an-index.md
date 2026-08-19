# Findings: negative `ProjectileId` is a selector, not an index

Loop-Atlas iteration 39. Static. Follows from
`findings/shot-data-and-projectileid-refuted.md`, which refuted the documented reading and
proposed a global 17-entry table as replacement.

**That replacement is now also refuted.** Two new CONFIRMED_STATIC facts show what the field
actually attaches to, and they point away from a data table toward a code-side dispatch.

Field location: `src/JUS.Tool/Combat/Converters/Binary2Collision.cs:81`, collision offset `0x03`,
`sbyte`. Across all 2837 records: 211 negative, 24 positive, 2602 zero. The negatives sit in a
contiguous band from −18 to −34, with nothing between −1 and −17.

---

## 1. REFUTED: there is no 17-entry table in `ChrBin.aar`

The previous iteration predicted a global 17-entry table indexed by `-v-18`. Searched every file
in all four `chr/` subdirectories at strides 8, 12, 16, 20, 24 and 32:

| directory | files | files with exactly 17 records |
|---|---|---|
| `chr/col` | 281 | **0** |
| `chr/ai` | 269 | **0** |
| `chr/shot` | 184 | **0** |
| `chr/effect` | 66 | **0** |

Zero at any stride. The two named candidates both fail:

- **`chr/col/item.bin`** is 860 bytes = **43 records** at stride 20, not 17. It follows normal
  collision format (first record `02 00 00 00 0a 00 00 1e 21 ...`) and **uses the negative band
  itself** — record 3 has `0x03 = 0xED = -19`. It's a consumer, not a source.
- **`chr/effect/*`** — 66 files of 8 to 56 bytes, GCD 8. Too small; none holds 17 of anything.

## 2. REFUTED: the biased per-character index `-v-18`

The previous iteration tested `|v|` and `|v|-1` but never tested the `-v-18` form it actually
proposed. Results:

| interpretation | in-bounds | out-of-bounds | character has no shot file |
|---|---|---|---|
| `|v|` | 5 / 211 (2.4%) | 146 | 60 |
| `|v|-1` | 5 / 211 (2.4%) | 146 | 60 |
| **`-v-18`** | **59 / 211 (28.0%)** | 92 | 60 |

28% is better than 2.4% but still a clear fail — an index must be 100% in-bounds. It couldn't
work anyway: `-v-18` spans 0..16, requiring characters with 17+ shot records, and **only 17 of
184 characters have that many** (45 have exactly one). All per-character index readings are dead.

## 3. CONFIRMED_STATIC: the field sits on projectile and summon records

Cross-tabulating the sign of `ProjectileId` against `CollisionType`:

| type | negative | zero | positive | % negative |
|---|---|---|---|---|
| 0 | 0 | 95 | 0 | 0.0% |
| 1 | 9 | 37 | 19 | 13.8% |
| 2 | 1 | 258 | 1 | 0.4% |
| 3 | 7 | 983 | 0 | 0.7% |
| **4** | **149** | 441 | 4 | **25.1%** |
| **5** | **45** | 784 | 0 | **5.4%** |
| 6 | 0 | 1 | 0 | 0.0% |
| 7 | 0 | 3 | 0 | 0.0% |

**194 of 211 negatives (92%) fall on `CollisionType` 4 or 5.** `Combat-Mechanics.md:126`
independently records "type4 = projectile, type5 = summon". The documented *semantics* were
right — the field is projectile machinery — even though the documented *indexing* was wrong.
Worth separating those two: the previous refutation could be misread as sinking both.

The 17 negatives on types 1/2/3 (mostly 8 records on type 1) are unexplained.

Most projectile records carry `ProjectileId = 0`: only 149 of 594 type-4 records are negative.
Whatever it selects, it's optional.

## 4. CONFIRMED_STATIC: it is one value per character, not one per record

Of the 120 characters with at least one negative `ProjectileId`, **92 (76.7%) use exactly one
distinct negative value across their entire collision file.**

Distinct-value counts per character: `{1: 92, 2: 25, 3: 1, 4: 1, 8: 1}`.

This alone kills the index reading, independent of the bounds tests. If each projectile move
indexed a different projectile definition, characters with several projectile moves would use
several values. Instead, nearly every character reuses **one** value on every projectile record.
That's the shape of a per-character *selector* or *class*, not a per-record pointer.

## 5. No data-level predictor for which value a character gets

The 17 values spread fairly evenly (2 to 11 characters each) with no visible driver:

- **Not shot record count.** `v=-24` covers characters with 0, 0, 0, 0, 2, 2, 3, 5, 25, and 44
  shot records.
- **Not character ordinal.** `v=-34` spans `b_01`, `s_03`, `s_21`, `s_22`, `s_23`, `s_26`.
- **Not battle-vs-support.** Every value has a mix; support dominates only because support
  characters outnumber battle ones.

Value histogram over the 92 single-value characters:
`{-34:7, -32:5, -31:8, -30:5, -29:5, -28:6, -27:3, -26:4, -25:4, -24:10, -23:2, -22:7, -21:2, -20:8, -19:5, -18:11}`
(`-33` appears only in multi-value characters).

## 6. New hypothesis: a code-side spawn-behavior selector

**PLAUSIBLE.** Negative `ProjectileId` names one of ~17 hardcoded spawn behaviors dispatched by
a `switch` in engine code, not an index into any data table.

This fits: no data file has 17 entries (§1); the value is per-character not per-record (§4); 31
characters use negative values while owning no shot file at all (unexplainable by a data index);
and it attaches to exactly the projectile and summon types (§3).

Corroboration from the existing map: `Battle-Engine-Map.md` projectile-entities claim 3 records
ov6 `0x021574CC` as a **13-way switch on its 3rd argument**, operating on `+0x1a4`/`+0x1a8` and
reaching `0x02168CF4` (the spawn and ownership routine). A small fixed set of spawn behaviors
selected by a switch is exactly this shape. 13 is not 17, so `0x021574CC` may not be *the*
switch — but the architecture already works this way.

**The test:** find a jump table or comparison chain with ~17 cases in ov6, or code applying a
bias of 18 (`0x12`) or 34 (`0x22`) to a signed byte loaded from a collision record. Failing
that, breakpoint `0x02168CF4` and read the argument for a character with a known negative value.

## Predictions status

| Claim | Verdict |
|---|---|
| A global 17-entry projectile table exists in `ChrBin.aar` | **REFUTED** — 0 files with 17 records, 4 directories × 6 strides |
| `chr/col/item.bin` is that table | **REFUTED** — 43 records at stride 20; is itself a consumer of the band |
| `chr/effect/*` is that table | **REFUTED** — 66 files of 8–56 bytes |
| Negative `ProjectileId` indexes shot records as `-v-18` | **REFUTED** — 28.0% in-bounds; needs 17+ records, only 17/184 characters qualify |
| Negative `ProjectileId` is attached to projectile/summon records | **CONFIRMED_STATIC** — 92% on `CollisionType` 4 or 5 |
| Negative `ProjectileId` is one value per character | **CONFIRMED_STATIC** — 92/120 characters use exactly one |
| `ProjectileId` is at collision offset `0x03`, `sbyte` | **CONFIRMED_STATIC** — `Binary2Collision.cs:81` |
| Negative `ProjectileId` selects a hardcoded spawn behavior via a code switch | **PLAUSIBLE** — untested; ov6 `0x021574CC` is a known 13-way switch |
| The field is a per-record index into any data table | **REFUTED** — §4 alone; three bounds tests agree |

## Method note

The previous iteration proposed `-v-18` without testing it; this iteration found it fails. The
lesson: **don't propose a replacement hypothesis in the same breath as a refutation and bank it
as the lead without running the one test it costs.** The refutation work was sound; the
forward-looking half wasn't held to the same standard. When a refutation suggests a successor,
test it before writing it up as the next step.

## Next angles, ranked

1. **Search ov6 for a ~17-case jump table or a `0x12`/`0x22` bias applied to a signed byte.**
   Direct test of §6. Constrain the scan enough to read every hit — offset-only scans have
   failed four times in this campaign.
2. **Explain the 24 positive `ProjectileId` values**, and the 17 negatives on non-projectile types.
3. Breakpoint `0x02168CF4` and log its arguments for a character with a known single negative
   value (e.g. any `v=-18` character). This would settle §6 in one run.
