# Collision data found — it was inside an unopened archive

Loop-Atlas iteration 36. The collision files that hitbox-priority chased across three campaigns were sitting inside `chr/ChrBin.aar`, never extracted. New tool: `scripts/analysis/extract_alar.py`.

## How I found it

I went to open `state.bin` (the sweep flagged it as referenced but never read). The docs-first procedure led somewhere better: `docs/articles/specs/summary.md` is a whole-ROM file classification I'd never read. It lists paths I didn't know about:

```
chr/ChrBin.aar/chr/col/*        <- collision data
chr/ChrBin.aar/chr/ai/*         (AIPM)
chr/ChrBin.aar/chr/ai/move/*    (AIMV)
chr/ChrBin.aar/chr/shot/*       <- projectiles
chr/ChrBin.aar/chr/effect/*
```

I'd inventoried `bin/` thoroughly and never looked inside the 322 KB `ChrBin.aar`.

`Battle-Engine-Map.md`'s hitbox-priority open question says: *"Where is the actual runtime CollisionEntry parser — the code that walks the loaded 20-byte-stride collision array at hit-test time? Not located in this campaign at all."* The **code** wasn't found; nobody noticed the **data** was in an unopened container.

## The extractor

`docs/articles/specs/alar.md` documents the format. My earlier hand-rolled attempt on a different `.aar` failed because it assumed fixed-size entries. V3 entries are **variable-length** with the path embedded:

```
0x00 uint id | 0x04 uint data offset | 0x08 uint size | 0x0C uint flags
0x10 ushort path hash | 0x12 char[] NUL-terminated path
```

`ChrBin.aar` is ALAR v3, flags `0x45`, **907 files**, payload 282649 bytes (87.7% of the container). Extracted cleanly:

| category | files |
|---|---|
| `chr/col` | **281** |
| `chr/ai` | 269 |
| `chr/shot` | 184 |
| `chr/effect` | 66 |

## The 20-byte stride is confirmed

Every collision file divides exactly by 20:

| file | bytes | records |
|---|---|---|
| `db_b_01.bin` (Goku) | 500 | 25 |
| `op_b_01.bin` (Luffy) | 760 | 38 |
| `na_b_01.bin` (Naruto) | 920 | 46 |

**2837 collision records** across 281 files. `Battle-Engine-Map`'s 20-byte-stride claim is now validated against real data, not just inferred from code.

## Column profile across all 2837 records

| offset | distinct | notes |
|---|---|---|
| `+0x00` | 8 | `0..7` — **type** |
| `+0x01` | 16 | `0..15` — **subType**; `jpower-Mapping.md` says "collision `subType` selects which jpower entry to use from the block" |
| `+0x02` | 4 | `0..3`, mostly 0 |
| `+0x06` | 1 | **constant 0** |
| `+0x0B` | 1 | **constant 0** |
| `+0x10` | 4 | `0..3`, well spread (392 / 948 / 741 / 756) |
| `+0x11` | 7 | `0..6` |
| `+0x12` | 1 | **constant 0** |
| `+0x13` | 1 | **constant 0** |

Four columns are constant zero across all 2837 records. The effective record is smaller than 20 bytes — consistent with five u32 fields whose upper bytes are mostly unused.

## hitTier candidates — candidates only

`Battle-Engine-Map` notes that *"no two-entity `hitTier`/`hitProperties` comparison was found anywhere"*. Two columns have the right shape: **`+0x10`** (4 values, evenly spread) and **`+0x11`** (7 values).

I am **not** claiming these are `hitTier`/`hitProperties`. That subsystem already has four demoted claims from naming fields on structural resemblance, and my worst errors this phase came from the same move. These are candidates. Confirming either one needs a consumer — the parser nobody has found.

What's changed: the question is now answerable with data in hand, not blocked.

## Next

1. Correlate `subType` (`+0x01`, 16 values) against jpower entry selection — `jpower-Mapping.md` names this as its own open question ("How do characters select specific jpower entries from their assigned block?"), and the collision files are the missing half.
2. Goku has 25 collision records and jpower block 0 has 9 entries — the mapping between them is now a concrete, bounded problem.
3. `chr/shot/*` (184 files) is the projectile-entities subsystem's data, also never opened.
