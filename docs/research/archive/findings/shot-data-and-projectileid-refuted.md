# Findings: `chr/shot/*` projectile data — and a documented claim refuted

Loop-Atlas iteration 38. Static. Data: 184 `chr/shot/*.bin` files from `chr/ChrBin.aar`, joined
against 281 `chr/col/*.bin` files.

**Headline: the documented link from collision data to shot records is wrong.**
`docs/research/Combat-Mechanics.md:124` and `docs/formats/Combat-Formats.md:167` both say shot
records are "referenced by negative `projectileId` values in collision data". Tested against all
2837 collision records and all 184 shot files, this fails in both directions. A replacement
hypothesis follows.

Second result: the C# exporter has an authoritative collision reader
(`src/JUS.Tool/Combat/Converters/Binary2Collision.cs:74-100`) that **confirms two fields previously
listed as candidates** and validates four others.

---

## 1. Shot record layout — 32-byte stride, and a column profile

The 32-byte stride was **already documented** (`Combat-Mechanics.md:124`). Independent check: 32 is
the GCD of all 184 file sizes, and the smallest file is exactly 32 bytes.

**1258 records** across 184 files (1250 non-zero, 8 all-zero). 1 to 69 records per file.

`Combat-Formats.md` gives the record size but **no field offsets**, so the column profile below is
new. Halfword profile over the 1250 non-zero records:

| off | distinct | range | note |
|---|---|---|---|
| `+0x00` | 133 | 0..64512 | |
| `+0x02` | 5 | 0..65440 | `{0: 1179, 1: 65, 2: 1, 3: 4, 65440: 1}` — near-constant |
| `+0x04` | 63 | 0..65323 | |
| `+0x06` | 88 | 0..800 | |
| `+0x08` | 91 | 0..41984 | |
| `+0x0A` | 10 | 0..64 | small enum or count |
| `+0x0C` | 791 | 0..56197 | array slot 0, magnitude |
| `+0x0E` | 22 | 0..26 | array slot 0, small tag |
| `+0x10` | 82 | 0..55427 | array slot 1, magnitude |
| `+0x12` | 18 | 0..25 | array slot 1, small tag |
| `+0x14` | 100 | 0..55425 | array slot 2, magnitude |
| `+0x16` | 21 | 0..26 | array slot 2, small tag |
| `+0x18` | 6 | 0..51345 | effectively dead: 1243/1250 are zero |
| `+0x1A` | 5 | 0..19 | effectively dead: 1245/1250 are zero |
| `+0x1C` | 139 | 0..57600 | used in ~522 records |
| `+0x1E` | 18 | 0..162 | |

### `+0x0C`/`+0x10`/`+0x14` look like a 3-element array — PLAUSIBLE

Three consecutive 4-byte groups, each `{u16 magnitude, u16 small tag}`, at stride 4. This is the
fourth time this campaign has seen a stride-N array first appear as separate fields (physics window,
`chr_b` per-size block, `chr_b +0x32` array).

Evidence for: all three small-tag columns share **the same value domain** — 22 distinct values, max
26, **18 common to all three**. Slot 0 is populated in 1249 of 1250 records.

Evidence against: slots are **not prefix-filled**. Fill patterns: `(1,0,0)` ×1084, `(1,1,1)` ×86,
**`(1,0,1)` ×63**, `(1,1,0)` ×16. A simple "fill from slot 0" array wouldn't skip slot 1 in 63
records. Either the index is positional (phase 0/1/2) rather than fill-ordered, or tag `0` is
meaningful and my "used" test is wrong. Unresolved.

`+0x18`/`+0x1A` being dead while `+0x1C`/`+0x1E` is live means the array **ends** at `+0x18` —
exactly 3 slots.

## 2. Coverage: which characters have projectiles

Filename key: `<series>_<b|s>_<NN>` (already documented — see §5).

- **67 of 74 battle characters (91%) have projectile data.** 7 do not.
- **117 of 193 support characters (61%) have projectile data.**
- 38 of 42 series have at least one projectile-owning character. 4 have none.

All 184 shot filenames also exist in `chr/col` — the two directories share one namespace with no
orphans in the shot direction.

Largest movesets: `kk_b_01` (69), `mr_b_01` (45), `yo_b_01` (44), `hk_b_01` (37), `hs_b_01` (33).

## 3. REFUTED: negative `ProjectileId` is not a shot-record index

`Binary2Collision.cs:74-100` reads collision records field by field, fixing `ProjectileId` at
**offset `0x03`, `sbyte`**.

Across all 2837 collision records: **211 negative, 24 positive, 2602 zero.**

If negative values indexed per-character shot records, `|v|` (or `|v|-1`) must fall within that
character's record count. It doesn't:

| interpretation | in-bounds | out-of-bounds | character has no shot file |
|---|---|---|---|
| `|v|` | **5 / 211 (2.4%)** | 146 | 60 |
| `|v|-1` | **5 / 211 (2.4%)** | 146 | 60 |

The set relation fails both ways too:

- 120 characters have a negative `ProjectileId`; **31 of them have no shot file.**
- **95 of 184 characters with a shot file have no negative `ProjectileId`.**

Before reading the schema, I also tested `0x0C`, `0x0D`, `0x0E`, `0x0F` as alternative index
fields; best was `0x0E` at 71% in-bounds with 212 out-of-bounds — still a fail. The schema shows
why: those are `Width`, `Height`, `DamageFlags`, `Knockback`.

### What the values actually look like — and a better hypothesis

The negative values form a **contiguous band from −18 to −34**:

```
-34:14  -33: 1  -32:19  -31:28  -30:11  -29: 7  -28:13  -27: 6  -26:10
-25:11  -24:12  -23: 5  -22:12  -21: 7  -20:28  -19:11  -18:16
```

17 distinct values spanning exactly 17 integers. **No value between −1 and −17 ever appears.** A
per-character index would start near −1 and scale with each character's record count. A tight band
identical across characters looks like an enum, or an index into something **global** with a bias.

**New hypothesis (PLAUSIBLE):** negative `ProjectileId` is a biased index into a global
projectile/effect table of 17 entries — `index = -v - 18`, giving 0..16 — not into the
per-character shot file. This explains why 31 characters carry negative values but own no shot file:
they reference shared entries.

Untested. Next step: look for a 17-entry table. Candidates: `chr/col/item`, `chr/effect/*`.

The 24 positive values are a separate question, not addressed here.

## 4. Confirmed as a side effect: `HitTier` and `HitProperties`

The same reader settles two fields previously listed as candidates. Full 20-byte collision layout,
authoritative:

```
0x00 CollisionType   0x01 SubType       0x02 ExtFlags     0x03 ProjectileId (sbyte)
0x04 FrameStart      0x05 DurationMult  0x06 Reserved0    0x07 HitModifier
0x08 OffsetX (sbyte) 0x09 OffsetY       0x0A PositionFlags 0x0B Reserved1
0x0C Width (sbyte)   0x0D Height (sbyte) 0x0E DamageFlags  0x0F Knockback
0x10 HitTier         0x11 HitProperties  0x12 Reserved2    0x13 Reserved3
```

`docs/research/findings/collision-subtype-vs-jpower.md` recorded `+0x10` (4 distinct values) and
`+0x11` (7 distinct values) as "`hitTier`/`hitProperties` **candidates only**". They match exactly.
Promoting both to **CONFIRMED_STATIC** on the exporter's authority.

Cross-validation: I had separately found `+0x06`, `+0x0B`, `+0x12`, `+0x13` **uniformly zero**
across all 2837 records — precisely the four `Reserved0`–`Reserved3` fields. Two independent
derivations agreeing on all four reserved slots strengthens both.

## 5. Process failure: the loose-ends rule, instance 5

The rule: **before opening a binary, grep the docs for its name.** I grepped, but too narrowly —
only `docs/articles/specs/`, not `docs/`. A full grep of `docs/` returns:

- `docs/research/Combat-Mechanics.md:124` — the 32-byte stride I re-derived needlessly.
- `docs/formats/Combat-Formats.md:167` — a whole `## Shot Files` section.
- `docs/research/ARM9-Research-Guide.md:44,123-157` — the `<series>_<b|s>_<NN>` character key,
  anchored on an **ARM9 pointer table at `0x0924B0`** and the chain
  `chr_b[39] → collision[39] → bl_b_01.bin (Ichigo)`. I "found" this key by matching file counts
  (74 battle, 193 support in `chr/ai`) — corroboration via a weaker anchor, not a discovery.
- `docs/research/Character-Mapping.md:8` — a `## Series Prefix Reference` table.

Refined rule: **grep `docs/` as a whole, for the concept as well as the filename.** A subdirectory
grep is not a docs grep.

The rule's value is confirmed, not diminished: applying the same instinct to *code* — reading
`Binary2Collision.cs` instead of guessing offsets — produced §3 and §4. Four of five offset guesses
were wrong; the schema corrected them and closed two open fields for free.

## 6. Effect on the projectile-entities subsystem

This task aimed to lift `Battle-Engine-Map.md` claim 5 (`0x0216C958` as projectile despawn) from
PLAUSIBLE. **It cannot be lifted on this data.**

Claim 5's ceiling exists because sibling routines `0x0216E1C0`/`0x0216F398` reuse identical
scaffolding — a code ambiguity that shot records can't resolve. The age threshold in that routine is
hardcoded `0x20`, and no shot field looks like a per-projectile lifetime that would contradict it —
`+0x06` (range 0..800) is the only field where 32 appears often (70 records), but that's not
evidence either way. Claim 5 stays PLAUSIBLE.

The `ProjectileId` refutation matters more: it breaks the assumed data path from a move to its
projectile definition.

## Predictions status

| Claim | Verdict |
|---|---|
| Shot records are 32 bytes | **CONFIRMED** — and already documented; re-derived |
| Negative `ProjectileId` indexes that character's shot records | **REFUTED** — 2.4% in-bounds; fails both set directions |
| `ProjectileId` is at collision offset `0x03` | **CONFIRMED_STATIC** — `Binary2Collision.cs:81` |
| Negative `ProjectileId` = biased index into a global 17-entry table (`-v-18`) | **PLAUSIBLE** — contiguous −18..−34 band, untested |
| Collision `+0x10`/`+0x11` are `HitTier`/`HitProperties` | **CONFIRMED_STATIC** — promoted from candidate |
| Collision `+0x06/0x0B/0x12/0x13` are reserved | **CONFIRMED_STATIC** — schema names them, matches my all-zero finding |
| Shot `+0x0C/+0x10/+0x14` are a 3-element array | **PLAUSIBLE** — shared value domain, but not prefix-filled |
| `0x0216C958` is the projectile despawn (map claim 5) | **still PLAUSIBLE** — shot data cannot discriminate |

## Next angles, ranked

1. **Find the 17-entry global projectile table.** Test `chr/col/item` and `chr/effect/*` for a
   17-record structure. Direct test of the §3 hypothesis; would restore a data path.
2. **Read `ARM9-Research-Guide.md:123-157` properly and use the `0x0924B0` pointer table.** A real
   ARM9 anchor for the character key this campaign has been working around.
3. Explain the 24 positive `ProjectileId` values.
4. Resolve the shot `+0x0C` array question by finding the code that reads it — offset `+0x0C` with
   stride 4 and a 3-iteration bound.
