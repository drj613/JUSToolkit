# Human Testing Queue

Central tracking for all in-game tests that require human intervention.

> **AGENTS**: Add tests here when you need human verification. Include the
> character file prefix, a clear test description, and priority. Also add the
> test to the character's individual map file.

---

## Quick Stats

| Status      | Count |
| ----------- | ----- |
| PENDING     | 94    |
| IN PROGRESS | 0     |
| COMPLETED   | 33    |

**Last Updated:** 2026-08-14 (+5 harness cards A1/F1/B1/E1/D1)

> **Formula CONFIRMED:** `damage = damage1/5 + (tier-2)` - verified character
> table in Research-Status.md (12 characters)
>
> **NEW:** Naruto series substitution mechanic documented (Naruto, Sasuke,
> Sakura, Kakashi)

---

## Priority Guide

| Priority | Meaning                 | Example                                                         |
| -------- | ----------------------- | --------------------------------------------------------------- |
| P0       | Blocking other research | Damage formula verification needed to interpret all jpower data |
| P1       | High value discovery    | Finding weight storage location                                 |
| P2       | Standard character data | Move damage values for a specific character                     |
| P3       | Nice to have            | Minor mechanic clarification                                    |

---

## Pending Tests (Sorted by Priority)

### P0 - Critical / Blocking

_All P0 tests completed!_

### P1 - High Priority

| ID          | Character   | Test Description                              | Added      | Notes                             |
| ----------- | ----------- | --------------------------------------------- | ---------- | --------------------------------- |
| db_b_09-004 | Gotenks SSJ | Verify charId=54 stat differences vs charId=7 | 2026-01-29 | May reveal what charId represents |

### P2 - Standard

| ID          | Character     | Test Description                                | Added      | Notes                                         |
| ----------- | ------------- | ----------------------------------------------- | ---------- | --------------------------------------------- |
| bl_b_03-001 | Rukia         | All koma sizes available                        | 2026-01-29 | Need to verify deck koma options              |
| bl_b_03-002 | Rukia         | B move damage (neutral, no buffs)               | 2026-01-29 | For damage formula verification               |
| bl_b_03-003 | Rukia         | Complete moveset damage values                  | 2026-01-29 | All B and Y moves                             |
| bl_b_03-004 | Rukia         | Damage types (use defensive passives)           | 2026-01-29 | Slash vs Impact vs unknown                    |
| bl_b_04-001 | Renji         | All koma sizes available                        | 2026-01-29 | Need to verify deck koma options              |
| bl_b_04-002 | Renji         | B move damage (neutral, no buffs)               | 2026-01-29 | For damage formula verification               |
| bl_b_04-003 | Renji         | Complete moveset damage values                  | 2026-01-29 | All B and Y moves                             |
| bl_b_04-004 | Renji         | Damage types (use defensive passives)           | 2026-01-29 | Slash vs Impact vs unknown                    |
| bl_b_04-008 | Renji         | Zabimaru extended range mechanics               | 2026-01-29 | Test if extending blade has unique properties |
| bl_b_05-001 | Hitsugaya     | All koma sizes available                        | 2026-01-29 | Need to verify deck koma options              |
| bl_b_05-002 | Hitsugaya     | B move damage (neutral, no buffs)               | 2026-01-29 | For damage formula verification               |
| bl_b_05-003 | Hitsugaya     | Complete moveset damage values                  | 2026-01-29 | All B and Y moves                             |
| bl_b_05-004 | Hitsugaya     | Damage types (use defensive passives)           | 2026-01-29 | Slash vs Impact vs unknown                    |
| bl_b_05-008 | Hitsugaya     | Ice attack effects (freeze? slow?)              | 2026-01-29 | Check for unique ice mechanics                |
| na_b_01-002 | Naruto        | Document all move damage values                 | 2026-01-29 | Full moveset including shadow clone attacks   |
| na_b_01-003 | Naruto        | Identify shadow clone attack patterns           | 2026-01-29 | 22 type5 entries - document clone behavior    |
| na_b_01-004 | Naruto        | Test for any buff/powered states                | 2026-01-29 | Check for taunt/Y spin buffs                  |
| na_b_02-001 | Kyuubi Naruto | Verify tier value and damage modifier           | 2026-01-29 | Check if tier=1 like Bankai                   |
| na_b_02-002 | Kyuubi Naruto | Document all move damage values                 | 2026-01-29 | Full moveset                                  |
| na_b_02-003 | Kyuubi Naruto | Compare moveset to base Naruto                  | 2026-01-29 | 30 vs 46 collision entries                    |
| na_b_03-001 | Sasuke        | Document all move damage values                 | 2026-01-29 | Full moveset                                  |
| na_b_03-002 | Sasuke        | Verify damage types (slash vs impact)           | 2026-01-29 | Mixed damage profile noted                    |
| na_b_03-003 | Sasuke        | Test lightning damage with defensive passive    | 2026-01-29 | Check if lightning = energy damage            |
| na_b_04-001 | Sakura        | Document all move damage values                 | 2026-01-29 | Full moveset                                  |
| na_b_04-002 | Sakura        | Catalog projectile attacks                      | 2026-01-29 | Throws projectiles per research               |
| na_b_05-001 | Kakashi       | Document all move damage values                 | 2026-01-29 | Full moveset                                  |
| na_b_05-002 | Kakashi       | Verify shuriken = slash damage                  | 2026-01-29 | Test with Slash Defense passive               |
| na_b_05-003 | Kakashi       | Catalog dog summon attacks                      | 2026-01-29 | Document which moves summon dogs              |
| db_b_02-001 | Goku SSJ      | Verify moveset matches base Goku                | 2026-01-29 | User confirmed, need verification             |
| db_b_02-002 | Goku SSJ      | X move damage at 6-koma                         | 2026-01-29 | SSJ specials may differ                       |
| db_b_02-003 | Goku SSJ      | X move damage at 7-koma                         | 2026-01-29 | SSJ specials may differ                       |
| db_b_03-001 | Vegetto       | Full moveset damage values                      | 2026-01-29 | Block 1, high koma cost (8)                   |
| db_b_03-002 | Vegetto       | X move damage at 8-koma                         | 2026-01-29 | Fusion character specials                     |
| db_b_04-001 | Vegeta        | Full moveset damage values                      | 2026-01-29 | Block 1 character                             |
| db_b_04-002 | Vegeta        | Available koma sizes                            | 2026-01-29 | Need deck koma options                        |
| db_b_04-003 | Vegeta        | X move damage at each koma                      | 2026-01-29 | For specials comparison                       |
| db_b_05-001 | Vegeta SSJ    | Full moveset damage values                      | 2026-01-29 | Block 2 character                             |
| db_b_05-002 | Vegeta SSJ    | Available koma sizes                            | 2026-01-29 | Need deck koma options                        |
| db_b_05-003 | Vegeta SSJ    | X move damage at each koma                      | 2026-01-29 | For specials comparison                       |
| db_b_06-001 | Gohan SSJ     | Full moveset damage values                      | 2026-01-29 | Block 2 (shared with Vegeta SSJ)              |
| db_b_06-002 | Gohan SSJ     | Available koma sizes                            | 2026-01-29 | Need deck koma options                        |
| db_b_06-003 | Gohan SSJ     | X move damage at each koma                      | 2026-01-29 | For specials comparison                       |
| db_b_06-004 | Gohan SSJ     | Compare moveset to Vegeta SSJ (block 2)         | 2026-01-29 | Both use same jpower block                    |
| ds_b_01-001 | Arale         | All B move damage values (neutral)              | 2026-01-29 | Dr. Slump character                           |
| ds_b_01-002 | Arale         | All Y move damage values (neutral)              | 2026-01-29 | Dr. Slump character                           |
| ds_b_01-003 | Arale         | X move damage at each koma size (4,5,6,7)       | 2026-01-29 | formType=2, check specials                    |
| ds_b_01-004 | Arale         | up X move damage at each koma size              | 2026-01-29 | formType=2, check specials                    |
| ds_b_01-005 | Arale         | Walk speed comparison (vs Goku standard)        | 2026-01-29 |                                               |
| ds_b_01-006 | Arale         | Dash type (standard vs flash)                   | 2026-01-29 |                                               |
| ds_b_01-007 | Arale         | Weight feel (compare knockback received)        | 2026-01-29 |                                               |
| ds_b_01-008 | Arale         | Damage type verification (use defense passives) | 2026-01-29 |                                               |
| ds_b_01-009 | Arale         | Available koma sizes in deck building           | 2026-01-29 | Sprite archives show 4,5,6,7                  |
| ds_b_02-001 | Mashirito     | All B move damage values (neutral)              | 2026-01-29 | Dr. Slump character                           |
| ds_b_02-002 | Mashirito     | All Y move damage values (neutral)              | 2026-01-29 | Dr. Slump character                           |
| ds_b_02-003 | Mashirito     | X move damage at each koma size (4,5,6,7)       | 2026-01-29 | Type 5 (Summon) entries                       |
| ds_b_02-004 | Mashirito     | up X move damage at each koma size              | 2026-01-29 | Type 5 (Summon) entries                       |
| ds_b_02-005 | Mashirito     | Walk speed comparison (vs Goku standard)        | 2026-01-29 |                                               |
| ds_b_02-006 | Mashirito     | Dash type (standard vs flash)                   | 2026-01-29 |                                               |
| ds_b_02-007 | Mashirito     | Weight feel (compare knockback received)        | 2026-01-29 |                                               |
| ds_b_02-008 | Mashirito     | Damage type verification (use defense passives) | 2026-01-29 |                                               |
| ds_b_02-009 | Mashirito     | Available koma sizes in deck building           | 2026-01-29 | Sprite archives show 4,5,6,7                  |
| ds_b_02-010 | Mashirito     | Summon mechanics (Type 5 collision entries)     | 2026-01-29 | Document how summons work                     |
| ds_b_03-001 | Caramelman    | All B move damage values (neutral)              | 2026-01-29 | 8-koma only, tier=3                           |
| ds_b_03-002 | Caramelman    | All Y move damage values (neutral)              | 2026-01-29 | 8-koma only, tier=3                           |
| ds_b_03-003 | Caramelman    | X move damage (8-koma)                          | 2026-01-29 | 8-koma only                                   |
| ds_b_03-004 | Caramelman    | up X move damage (8-koma)                       | 2026-01-29 | 8-koma only                                   |
| ds_b_03-005 | Caramelman    | Walk speed comparison (vs Goku standard)        | 2026-01-29 | Likely slow (big character)                   |
| ds_b_03-006 | Caramelman    | Dash type (standard vs flash)                   | 2026-01-29 |                                               |
| ds_b_03-007 | Caramelman    | Weight feel (compare knockback received)        | 2026-01-29 | Likely heavy                                  |
| ds_b_03-008 | Caramelman    | Damage type verification (use defense passives) | 2026-01-29 |                                               |
| db_b_07-001 | Gohan SSJ2    | Full moveset damage values                      | 2026-01-29 | Block 3 (shared with Gotenks)                 |
| db_b_07-002 | Gohan SSJ2    | Available koma sizes                            | 2026-01-29 |                                               |
| db_b_08-001 | Gotenks       | Full moveset damage values                      | 2026-01-29 | Block 3 (shared with Gohan SSJ2)              |
| db_b_08-002 | Gotenks       | Available koma sizes                            | 2026-01-29 |                                               |
| db_b_09-001 | Gotenks SSJ   | Full moveset damage values                      | 2026-01-29 | Unique Block 4, charId=54                     |
| db_b_09-002 | Gotenks SSJ   | Available koma sizes                            | 2026-01-29 |                                               |
| db_b_10-001 | Piccolo       | Full moveset damage values                      | 2026-01-29 | Unique Block 5, charId=41                     |
| db_b_10-002 | Piccolo       | Available koma sizes                            | 2026-01-29 |                                               |
| db_b_10-003 | Piccolo       | Test for stretchy arm reach mechanics           | 2026-01-29 | Namekian ability                              |
| db_b_10-004 | Piccolo       | Compare feel to Goku (different charId)         | 2026-01-29 | Unique charId=41                              |
| db_b_11-001 | Frieza        | Full moveset damage values                      | 2026-01-29 | Unique Block 6, charId=54                     |
| db_b_11-002 | Frieza        | Available koma sizes                            | 2026-01-29 |                                               |
| db_b_11-003 | Frieza        | Compare feel to Dio (same charId=54)            | 2026-01-29 |                                               |
| db_b_11-004 | Frieza        | Test dash type (standard or flash)              | 2026-01-29 | Dio has flash dash                            |
| db_b_12-002 | Majin Buu     | Available koma sizes                            | 2026-01-29 | Block 0 (shared with Goku!)                   |

### P3 - Nice to Have

| ID          | Character  | Test Description                         | Added      | Notes                                |
| ----------- | ---------- | ---------------------------------------- | ---------- | ------------------------------------ |
| bl_b_03-005 | Rukia      | Walk speed (compare to Goku)             | 2026-01-29 | Standard reference: Goku             |
| bl_b_03-006 | Rukia      | Weight class (compare knockback to Goku) | 2026-01-29 | Light/Standard/Heavy                 |
| bl_b_03-007 | Rukia      | Dash type (standard or flash)            | 2026-01-29 | Shinigami may use flash step         |
| bl_b_04-005 | Renji      | Walk speed (compare to Goku)             | 2026-01-29 | Standard reference: Goku             |
| bl_b_04-006 | Renji      | Weight class (compare knockback to Goku) | 2026-01-29 | Light/Standard/Heavy                 |
| bl_b_04-007 | Renji      | Dash type (standard or flash)            | 2026-01-29 | Shinigami may use flash step         |
| bl_b_05-005 | Hitsugaya  | Walk speed (compare to Goku)             | 2026-01-29 | May be faster due to small size      |
| bl_b_05-006 | Hitsugaya  | Weight class (compare knockback to Goku) | 2026-01-29 | May be lighter due to small size     |
| bl_b_05-007 | Hitsugaya  | Dash type (standard or flash)            | 2026-01-29 | Shinigami may use flash step         |
| na_b_04-003 | Sakura     | Test weight class (light vs standard)    | 2026-01-29 | Female characters tend to be lighter |
| db_b_02-004 | Goku SSJ   | Confirm tier value (expect 2)            | 2026-01-29 | Should match base Goku               |
| db_b_03-003 | Vegetto    | Movement speed and dash type             | 2026-01-29 | Standard or Flash?                   |
| db_b_03-004 | Vegetto    | Weight category verification             | 2026-01-29 | Expected standard                    |
| db_b_04-004 | Vegeta     | Movement speed and dash type             | 2026-01-29 | Standard or Flash?                   |
| db_b_04-005 | Vegeta     | Compare moveset to Vegeta SSJ            | 2026-01-29 | Different jpower blocks              |
| db_b_05-005 | Vegeta SSJ | Movement speed and dash type             | 2026-01-29 | Standard or Flash?                   |
| db_b_06-005 | Gohan SSJ  | Movement speed and dash type             | 2026-01-29 | Standard or Flash?                   |

---

## In Progress

| ID  | Character | Test Description | Started | Tester |
| --- | --------- | ---------------- | ------- | ------ |
|     |           |                  |         |        |

---

## Completed Tests

| ID            | Character     | Test Description          | Result       | Completed  | Notes                                  |
| ------------- | ------------- | ------------------------- | ------------ | ---------- | -------------------------------------- |
| ICHIGO-B      | Ichigo        | Base B damage             | 10           | 2026-01-29 | d1=50, 50/5+0=10 ✓                     |
| ICHIGO-BANKAI | Bankai        | B damage with tier=1      | 9            | 2026-01-29 | d1=50, tier=1, 50/5-1=9 ✓              |
| GOKU-ALL      | Goku          | Full moveset damage       | B=8          | 2026-01-29 | d1=40, 40/5+0=8 ✓                      |
| CORE-002      | Naruto        | B damage formula test     | 8            | 2026-01-30 | d1=40, 40/5+0=8 ✓                      |
| db_b_12-003   | Majin Buu     | B damage (Block 0 test)   | 9            | 2026-01-30 | d1=45, 45/5+0=9 ✓ SOLVED anomaly       |
| db_b_12-004   | Majin Buu     | ÷5 or ÷7 formula          | ÷5           | 2026-01-30 | Confirmed damage1/5 formula            |
| NAMI-B        | Nami          | B damage                  | 6            | 2026-01-30 | d1=30, 30/5+0=6 ✓                      |
| TRAIN-B       | Train         | B damage                  | 7            | 2026-01-30 | d1=35, 35/5+0=7 ✓                      |
| LUFFY-B       | Luffy         | B damage                  | 8            | 2026-01-30 | d1=40, 40/5+0=8 ✓                      |
| ROBIN-B       | Robin         | B damage                  | 8            | 2026-01-30 | d1=40, 40/5+0=8 ✓                      |
| FRANKY-B      | Franky        | B damage                  | 8            | 2026-01-30 | d1=40, 40/5+0=8 ✓                      |
| CARAMELMAN-B  | Caramelman    | B damage (tier=3)         | 13           | 2026-01-30 | d1=60, tier=3, 60/5+1=13 ✓             |
| KYUUBI-B      | Kyuubi Naruto | B damage (tier=1)         | 8            | 2026-01-30 | d1=45, tier=1, 45/5-1=8 ✓              |
| db_b_12-001   | Majin Buu     | Full moveset damage       | All verified | 2026-02-02 | See character map for details          |
| VEGETA-B      | Vegeta        | B damage                  | 10           | 2026-02-02 | d1=50, 50/5+0=10 ✓                     |
| VEGETA-SSJ-B  | Vegeta SSJ    | B damage                  | 10           | 2026-02-02 | d1=50, 50/5+0=10 ✓                     |
| GOHAN-SSJ-B   | Gohan SSJ     | B damage                  | 8            | 2026-02-02 | d1=40, 40/5+0=8 ✓                      |
| GOHAN-SSJ2-B  | Gohan SSJ2    | B damage                  | 8            | 2026-02-02 | d1=40, 40/5+0=8 ✓                      |
| GOTENKS-B     | Gotenks       | B damage                  | 10           | 2026-02-02 | d1=50, 50/5+0=10 ✓                     |
| GOTENKS-SSJ-B | Gotenks SSJ   | B damage                  | 10           | 2026-02-02 | d1=50, 50/5+0=10 ✓                     |
| db_b_07-003   | Gohan SSJ2    | Compare damage to Gotenks | B differs    | 2026-02-02 | Gohan B=8, Gotenks B=10                |
| ds_b_03-ALL   | Caramelman    | Full moveset              | All verified | 2026-02-02 | tier=3, 8-koma only, robot mech        |
| NARUTO-B-ALL  | Naruto        | All B moves               | All 8        | 2026-02-02 | All B moves do 8 damage                |
| bl_b_03-KOMA  | Rukia         | Koma sizes                | 4,5,6        | 2026-02-02 |                                        |
| bl_b_04-KOMA  | Renji         | Koma sizes                | 4,5,6        | 2026-02-02 |                                        |
| bl_b_05-KOMA  | Hitsugaya     | Koma sizes                | 4,5,6        | 2026-02-02 |                                        |
| NARUTO-SUB    | Naruto        | Substitution mechanic     | Confirmed    | 2026-02-02 | Taunt activates log icon, blocks 1 hit |
| na_b_03-SUB   | Sasuke        | Substitution mechanic     | Confirmed    | 2026-02-02 | Same as Naruto                         |
| na_b_04-SUB   | Sakura        | Substitution mechanic     | Confirmed    | 2026-02-02 | Same as Naruto                         |
| na_b_05-SUB   | Kakashi       | Substitution mechanic     | Confirmed    | 2026-02-02 | Same as Naruto                         |
| na_b_02-TAUNT | Kyuubi Naruto | Taunt effect              | SP regen     | 2026-02-02 | Does NOT have substitution             |

---

## Test Methodology

### Damage Testing

1. Use Training Mode if available, or VS mode with known HP
2. Test against a neutral character (no nature advantage)
3. Record each hit separately for multi-hit moves
4. Test with both Slash Defense and Impact Defense passives to identify damage
   type
5. Test at each koma size for specials (X moves)

### Movement Testing

1. Compare walk speed visually against Goku (standard reference)
2. Note if dash is standard (visible movement) or flash (teleport)
3. For weight, observe knockback distance when hit by same attack

### Standard Reference Characters

- **Walk Speed**: Nami (fast), Goku (standard), Franky (slow)
- **Weight**: Nami (light), Goku (standard), Franky/Raoh (heavy)
- **Damage Baseline**: Goku B=8, Ichigo B=10

---

## How to Add Tests

**Agents should:**

1. Add test to this file under appropriate priority section
2. Add test to the character's individual map file under "Human Testing
   Required"
3. Use format: `{{FILE_PREFIX}}-{{NUMBER}} | {{Character}} | {{Description}}`
4. Include any context that helps the tester (e.g., "use 4-koma version")

**Humans should:**

1. Move test to "In Progress" when starting
2. Move to "Completed Tests" with result when done
3. Update the character's map file with findings
4. Update Quick Stats counts

---

## Notes

- Tests for the same character should be batched when possible
- Cross-reference results with jpower/collision data to verify formulas
- When a test reveals unexpected results, flag for deeper investigation

---

# Harness Cards (machine-consumable)

Added by the Atlas static-RE loop for the melonDS harness session. Format agreed with that
session: one section per card, hypotheses must be separable **by a number**, and the card
supplies addresses + discriminator while the harness supplies inputs.

> ### ⚠️ Absolute addresses in these cards are SESSION-LOCAL. Discover them, don't hardcode.
>
> The harness session found the player character array at `0x021DF1D4` in one battle and
> `0x021DF1B4` in another — **a `0x20` shift** with the same deck. This fails silently: reading the
> stale address returned `62072` from an unrelated array whose neighbouring slots decremented by a
> tidy 48, which looks exactly like a real struct.
>
> **Always locate the array first** with `scripts/emu/find_battle_structs.py`, which scans for the
> repeating-group signature (four consecutive `0x50`-byte slots, each with HP a multiple of 64, a
> small ability count, and a `chr_b` index < 74, cross-checked against `chr_b.bin`). A single slot
> matches ~1167 times in 4 MB; the group of four is unique.
>
> **CORRECTED 2026-08-14 — `+0x61C` is valid.** An earlier revision of this warning said not to
> trust the player→opponent offset. That was wrong: it had been applied to a stale base from a
> different session. A GDB breakpoint gave both structs directly — player `0x021df19c`, opponent
> `0x021df7b8`, difference exactly `0x61C` — and struct `+0x18` = HP confirmed live. The scanner's
> base equals `struct + 0x18`, so **max HP is at `scan_base - 2`**.
>
> Also corrected: in that savestate the opponent's HP was at **`0x021DF7D0`**, not `0x021DF7F0`.
> Watching the latter reads unrelated memory, which is what made opponent-side watches look flat.

Structure these cards rely on (verified against a running emulator). **HP is u16 little-endian in
1/64 units** — read 2 bytes, not 1. Within a slot: HP at `+0x00`, ability count at `+0x02`,
ability IDs from `+0x03`, `chr_b` index at `+0x29`. Deck-slot stride `+0x50`. The addresses below
are the *recorded* ones from one session — re-discover before use. Note the ability-count byte at `0x021DF1D6` sits immediately
after the HP u16, so HP and the ability list are adjacent fields in the same struct.

Known reference values: Naruto 4-koma = `9216` raw = `144.0`. Goku = `10240` = `160.0`.
Luffy = `9728` = `152.0`.

---

### CARD A1: Where is per-panel nature stored?

Static analysis has **refuted** nature living in `koma.bin` (see
`findings/koma-format-decoded.md`): Naruto's size-2 panel is 笑 Laughter and his size-3 is 力
Power, yet both records are byte-identical in every field except image/shape/ordinal. So a
per-panel source exists and I can't find it offline.

This is a **diff experiment**, not a search.

- Hypotheses: **A** = per-panel runtime struct holds nature (a byte/nibble differs between two
  same-size, different-nature panels). **B** = nature is derived from something else entirely
  and no runtime byte differs in the koma region.
- Watch: `name=koma_holder addr=0x0228AA00 len=512` (region is `0x0228AA00`–`0x0228B000`, 1.5 KB
  total — this exceeds the per-frame budget, so take it as **three one-shot dumps** of 512 B at
  `0x0228AA00`, `0x0228AC00`, `0x0228AE00`, not a per-frame watch)
- Watch: `name=leader_koma_ptr addr=0x020A4368 len=4` (documented as a pointer to the leader's
  runtime koma data — deref and dump 128 B at the target too, if chains work)
- Setup: two saved decks **identical in every way except** the Naruto battle panel: deck 1 uses
  the 4-koma 力 Power variant, deck 2 uses the 4-koma 笑 Laughter variant. In `koma.bin` these
  are records **500** (Power, shape elem 2) and **501** (Laughter, shape elem 0). Same leader,
  same support, same helper, same grid positions.
- Inputs: enter deck edit / deck select with deck 1 active, dump; switch to deck 2, dump.
- Discriminator: **A** if the diff is small and localised (1–4 bytes differing at the same
  offset within one koma record-sized stride). **B** if the only differences are the koma ID and
  image ID. Report the differing offsets and values either way — a null result is still
  publishable and I'll record it as a refutation.

---

### CARD F1: Is HP `size × k`, or tabulated per panel? — ✅ CLOSED 2026-08-14

> **Do not run this card.** Answer: **tabulated.** `max_HP = chr_b[index][size-4] + 8 × (active
> Ｊ魂+ sources)`, where `index` is `koma.bin` byte `0x7`. Verified against 6 RAM slots by the
> harness session, which also found the `chr_b` index at `hp_addr + 0x29`. All 74 characters'
> full HP curves are now tabulated offline in `findings/hp-all-74-characters.md`.
> Naruto size-5 = `160` (raw `10240`). Kept below for provenance.

Same missing table as A1, approached from the cheap side. Naruto's size-4, size-5 and size-6
panels all share `abilityId = 20` (`koma.bin` byte `0x7`) yet have different HP, and `koma.bin`
has no HP field.

- Hypotheses: **A** = HP is computed as `size × k` with a per-character `k` (for Naruto
  `k = 2304` raw = 36.0 displayed). **B** = HP is tabulated per panel, so values won't be clean
  multiples.
- Watch: `name=hp_slot1 addr=0x021DF840 len=2`
- Setup: a deck whose slot-1 battle panel is **Naruto 5-koma** (`koma.bin` record **502**).
  Then repeat with **6-koma** (record 503) if the first is ambiguous.
- Inputs: none beyond reaching a battle with that deck. Read at rest, before any damage.
- Discriminator (**UPDATED 2026-08-14** — `180` is dead, HP is quantised to 8 displayed units so
  `22.5 × 8` is impossible). Three hypotheses, two still live:
  | Source | Rule | size-5 raw / displayed |
  |---|---|---|
  | ~~Atlas iter 4~~ | ~~`size × 36`~~ | ~~`11520` / `180.0`~~ REFUTED |
  | Harness session | `8 × (14 + size)` | `9728` / `152.0` |
  | **Atlas iter 7** | `chr_b[20]` slot 1 (see `findings/hp-per-size-chr_b.md`) | **`10240` / `160.0`** |
  `152` and `160` are one quantum apart, so this needs an exact u16 read. If it reads `160`, HP is
  per-character-per-size **table data** in `chr_b.bin` and all 74 characters' HP curves become
  readable offline. If `152`, my stride-4 grouping is noise that happens to fit Naruto.
- Note: read at rest. Training mode heals ~64 raw units every ~2 frames, so a value sampled
  mid-recovery is meaningless.

---

### CARD B1: Nature damage multiplier

Deliberately designed as **two matchups sharing one base move**, per the harness session's
warning that a single number can't separate a multiplier from a flat subtraction when
resistances are in play.

Also relevant: this repo's `Human-Testing-Queue.md` already claims a **CONFIRMED** formula
`damage = damage1/5 + (tier-2)`. That has an additive term, which may be exactly the ×2/3-vs-−2
ambiguity currently open on the Goku→Luffy `4.000` measurement. Worth testing against.

- Hypotheses: **A** = advantage is multiplicative ~1.5× (owner's guess, SPECULATIVE).
  **B** = additive. **C** = neither; advantage affects something other than raw damage.
- Watch: `name=hp_target addr=<discover> len=2` (one session read `0x021DF7D0`; **not** `0x021DF7F0`, which is unrelated memory) (per-frame; damage = baseline − min dip)
- Setup: same attacker, same single move, two targets that differ **only** in nature relative to
  the attacker — one neutral matchup, one advantaged matchup. Natures: 力 Power beats 知
  Knowledge beats 笑 Laughter beats 力 Power; なし Neutral is outside the triangle, which makes a
  Neutral target the ideal baseline.
- Inputs: turn to face the target (~12 frames of the opposite direction first — the harness
  session lost a whole probe to walking past and whiffing), then the one move. Repeat ≥5× and
  take the mode.
- Discriminator: let `d_neutral` and `d_advantaged` be the measured dips. **A** if
  `d_advantaged / d_neutral ≈ 1.5`. **B** if the difference is a constant across two different
  base moves. Run it with a second base move of different magnitude — that's what separates
  ratio from constant.

---

### CARD E1: Name the unnamed ability IDs — ✅ CLOSED STATICALLY 2026-08-14

> **Also note:** the harness session later proved the runtime ability array is **not read at
> damage time** (removing `0x09` from Luffy and adding it to Goku both changed nothing, with
> three controls). So poking IDs could never have worked — the array is a read-only source list
> and resistance is precomputed at character load. The "write an ID and observe" method is
> retired for all cards.
>
> **Do not run this card.** All 57 abilities were named offline from `ability.bin` +
> `ability_t.bin`. See `findings/abilities-all-57-named.md` for the full table, including all
> ten previously-Unknown IDs. Kept below for provenance.

**Try the static route first — this card may be unnecessary.** I have just found
`jus_files/ripped_jus_files/bin/ability.bin` (228 B = **57 entries × 4 bytes**) and
`ability_t.bin` (3788 B, a text table). Entry format `(u8 group, u8 sub, s8 param, u8 pad)`:

- indices 0–37 = group 0, sub `0x00`–`0x25` (38 entries)
- indices 38–48 = group 1, sub `0x05`–`0x0F` (11 entries)
- indices 49–56 = group 2, sub `0x00`–`0x07` (8 entries)
- **params are nonzero only at index 52 (`+8`), 54 (`+1`), 55 (`+3`), 56 (`-3`)**

Two things line up. `Cheat-Code-Analysis.md` lists ability IDs `0x01`–`0x30` with **10 marked
Unknown**, and 48 − 10 = 38 named — the same count as group 0. And `koma.bin` helper `abilityId`
values run 0..55 with 47 distinct, which fits indexing 0..56 but **not** a table that stops at
`0x30`. So the cheat-code "ability ID" is probably the `ability.bin` **record index**, and
indices 49–56 were simply never catalogued because the old table stopped short.

The nonzero params are suggestive: index 54 `+1` matches "Increase Max Special Gauge **by 1**",
and index 52 `+8` matches "Increase Max Health" — both of which are categories I had predicted
sit in the Unknown slots. I'm decoding `ability_t.bin` now, which should name all 57 offline.

If that fails, the runtime poke is the fallback:

- Hypotheses: each unknown index maps to one of the 4 unclaimed owner categories — health
  regen, increase max HP, +1 max SP gauge, SP regen while on field (see
  `Helper-Passives-Catalog.md`).
- Watch: `name=ability_count addr=0x021DF1D6 len=1`, `name=ability_ids addr=0x021DF1D7 len=20`
- Watch: `name=hp_player addr=0x021DF1D4 len=2`
- Setup: any training battle.
- Inputs: write count=1 at `0x021DF1D6` and a single test ID at `0x021DF1D7`, then observe.
- Discriminator: for the four candidate effects, HP-max and SP-max changes are directly readable
  as numbers; the two regen effects show as HP/SP rising with no input. **Ten unknown IDs to
  test:** `0x0B`, `0x0C`, `0x11`, `0x13`, `0x14`, `0x15`, `0x17`, `0x18`, `0x24`, `0x25`. My
  narrowed guesses: `0x13`–`0x15` or `0x17`–`0x18` hold the three HP/SP stat boosts (that range
  ends at `0x16` = Guard strength, so it's the stat-boost neighbourhood), and `0x24`/`0x25` hold
  SP-regen-on-field (they sit immediately before the SP-trigger block `0x26`–`0x30`).

---

### CARD D1: Helper facing semantics

Lowest priority — needs the most menu automation. Every 1-cell helper carries exactly one
passive, and the facing set at placement picks which battle character receives it.

- Hypotheses: **A** = the passive goes to the single adjacent panel in the faced direction.
  **B** = it goes to every battle panel in that row/column.
- Watch: `name=ability_count addr=0x021DF1D6 len=1`, `name=ability_ids addr=0x021DF1D7 len=20`
- Setup: a deck with **two** battle panels in the same column, and one helper below both, facing
  up. Use a helper whose passive is unmistakable in the ability list.
- Inputs: none beyond entering battle and switching between the two battle characters.
- Discriminator: **A** if only the nearer character's ability list contains the helper's ID.
  **B** if both do. Bonus: two helpers facing the same target answers whether passives stack —
  count duplicates in the ID array.

### CARD D1b: Is `+0x134` the pending-damage field? — HIGHEST VALUE, single number

Supersedes the refuted accumulator card. Static work found a **second** HP trampoline at
`0x020783B8` that negates its delta (`rsb r1,r1,#0x0`), so damage passes a **positive magnitude**.
Its magnitude is loaded from `+0x134` off the same chain as the `+0x140` heal field you already
watched — see `findings/c5-damage-field-0x134.md`.

- Hypotheses: **A** = `+0x134` is the pending HP damage. **B** = it isn't, and damage arrives another
  way again.
- Watch: `name=dmg addr=<[character + 0x1A8] -> +0x10 -> +0x134> len=4` per frame. You already know
  how to resolve this chain — it's identical to the `+0x140` one, one field earlier.
- Alternative if the watch masks a same-frame write/consume: breakpoint **`0x0215AC08`**
  (`ldr r4,[r1,#0x134]`) and log `r4`; or `0x0215AC70` and log `r1`.
- Setup: the deterministic `fight_cfg` savestate, `自動回復 OFF`, the known 6.000 punch.
- Discriminator: **A** if it reads a positive magnitude on the landed hit. **CONFIRMED 2026-08-14: it
  reads 512** (8.000) one frame before each HP drop, with `+0x138`/`+0x140`/`+0x144` all zero. Note
  512, not the 384 I first predicted — the observed dip was net of one +2.0 auto-heal frame.
- Log unconditionally, not just non-zero. Your own rule from the last run.

The object holds a family of pending deltas, so watching all four at once would map the set in one go:
`+0x134` HP damage, `+0x138` SP drain, `+0x140` HP heal, `+0x144` SP add.
