# Human Testing Queue

Central tracking for all in-game tests that require human intervention.

> **AGENTS**: Add tests here when you need human verification. Include the character
> file prefix, a clear test description, and priority. Also add the test to the
> character's individual map file.

---

## Quick Stats

| Status | Count |
| ------ | ----- |
| PENDING | 120 |
| IN PROGRESS | 0 |
| COMPLETED | 13 |

**Last Updated:** 2026-01-31

> **Formula CONFIRMED:** `damage = damage1/5 + (tier-2)` verified across 12+ characters

---

## Priority Guide

| Priority | Meaning | Example |
| -------- | ------- | ------- |
| P0 | Blocking other research | Damage formula verification needed to interpret all jpower data |
| P1 | High value discovery | Finding weight storage location |
| P2 | Standard character data | Move damage values for a specific character |
| P3 | Nice to have | Minor mechanic clarification |

---

## Pending Tests (Sorted by Priority)

### P0 - Critical / Blocking

| ID | Character | Test Description | Added | Notes |
| -- | --------- | ---------------- | ----- | ----- |
| db_b_12-003 | Majin Buu | Compare B damage to Goku's B (both Block 0) | 2026-01-29 | CRITICAL - proves entry selection mechanism |

### P1 - High Priority

| ID | Character | Test Description | Added | Notes |
| -- | --------- | ---------------- | ----- | ----- |
| CORE-001 | Caramelman | Test if tier=3 gives +1 damage (formula verification) | 2026-01-29 | ds_b_03 is tier=3, 8-koma only |
| ds_b_03-009 | Caramelman | Verify 8-koma only availability | 2026-01-29 | Only 8c portrait exists |
| ds_b_03-010 | Caramelman | Tier 3 damage bonus verification | 2026-01-29 | Compare to tier=2 with same base |
| CORE-002 | Naruto | Test B damage to verify ÷5+tier formula on non-Bleach char | 2026-01-29 | Naruto is tier=2, classId=529, block=17 |
| na_b_01-001 | Naruto | Verify B damage matches jpower/5+tier formula | 2026-01-29 | **TEST CASE for damage formula** - tier=2, block=17 |
| db_b_05-004 | Vegeta SSJ | Compare moveset to base Vegeta | 2026-01-29 | Different jpower block (2 vs 1) unlike Goku/SSJ |
| db_b_07-003 | Gohan SSJ2 | Compare damage to Gotenks (same jpower block) | 2026-01-29 | Tests block sharing with different characters |
| db_b_08-003 | Gotenks | Compare damage to Gohan SSJ2 (same jpower block) | 2026-01-29 | Tests block sharing with different characters |
| db_b_08-004 | Gotenks | Compare damage to Gotenks SSJ (same char, diff form) | 2026-01-29 | Tests form transformation damage changes |
| db_b_09-003 | Gotenks SSJ | Compare damage to base Gotenks (different charId!) | 2026-01-29 | Tests charId=54 vs charId=7 differences |
| db_b_09-004 | Gotenks SSJ | Verify charId=54 stat differences vs charId=7 | 2026-01-29 | May reveal what charId represents |
| db_b_12-001 | Majin Buu | Full moveset damage values | 2026-01-29 | Key to understanding jpower entry selection |
| db_b_12-004 | Majin Buu | Test if ÷7 or ÷5 formula applies | 2026-01-29 | Resolves formula conflict |

### P2 - Standard

| ID | Character | Test Description | Added | Notes |
| -- | --------- | ---------------- | ----- | ----- |
| bl_b_03-001 | Rukia | All koma sizes available | 2026-01-29 | Need to verify deck koma options |
| bl_b_03-002 | Rukia | B move damage (neutral, no buffs) | 2026-01-29 | For damage formula verification |
| bl_b_03-003 | Rukia | Complete moveset damage values | 2026-01-29 | All B and Y moves |
| bl_b_03-004 | Rukia | Damage types (use defensive passives) | 2026-01-29 | Slash vs Impact vs unknown |
| bl_b_04-001 | Renji | All koma sizes available | 2026-01-29 | Need to verify deck koma options |
| bl_b_04-002 | Renji | B move damage (neutral, no buffs) | 2026-01-29 | For damage formula verification |
| bl_b_04-003 | Renji | Complete moveset damage values | 2026-01-29 | All B and Y moves |
| bl_b_04-004 | Renji | Damage types (use defensive passives) | 2026-01-29 | Slash vs Impact vs unknown |
| bl_b_04-008 | Renji | Zabimaru extended range mechanics | 2026-01-29 | Test if extending blade has unique properties |
| bl_b_05-001 | Hitsugaya | All koma sizes available | 2026-01-29 | Need to verify deck koma options |
| bl_b_05-002 | Hitsugaya | B move damage (neutral, no buffs) | 2026-01-29 | For damage formula verification |
| bl_b_05-003 | Hitsugaya | Complete moveset damage values | 2026-01-29 | All B and Y moves |
| bl_b_05-004 | Hitsugaya | Damage types (use defensive passives) | 2026-01-29 | Slash vs Impact vs unknown |
| bl_b_05-008 | Hitsugaya | Ice attack effects (freeze? slow?) | 2026-01-29 | Check for unique ice mechanics |
| na_b_01-002 | Naruto | Document all move damage values | 2026-01-29 | Full moveset including shadow clone attacks |
| na_b_01-003 | Naruto | Identify shadow clone attack patterns | 2026-01-29 | 22 type5 entries - document clone behavior |
| na_b_01-004 | Naruto | Test for any buff/powered states | 2026-01-29 | Check for taunt/Y spin buffs |
| na_b_02-001 | Kyuubi Naruto | Verify tier value and damage modifier | 2026-01-29 | Check if tier=1 like Bankai |
| na_b_02-002 | Kyuubi Naruto | Document all move damage values | 2026-01-29 | Full moveset |
| na_b_02-003 | Kyuubi Naruto | Compare moveset to base Naruto | 2026-01-29 | 30 vs 46 collision entries |
| na_b_03-001 | Sasuke | Document all move damage values | 2026-01-29 | Full moveset |
| na_b_03-002 | Sasuke | Verify damage types (slash vs impact) | 2026-01-29 | Mixed damage profile noted |
| na_b_03-003 | Sasuke | Test lightning damage with defensive passive | 2026-01-29 | Check if lightning = energy damage |
| na_b_04-001 | Sakura | Document all move damage values | 2026-01-29 | Full moveset |
| na_b_04-002 | Sakura | Catalog projectile attacks | 2026-01-29 | Throws projectiles per research |
| na_b_05-001 | Kakashi | Document all move damage values | 2026-01-29 | Full moveset |
| na_b_05-002 | Kakashi | Verify shuriken = slash damage | 2026-01-29 | Test with Slash Defense passive |
| na_b_05-003 | Kakashi | Catalog dog summon attacks | 2026-01-29 | Document which moves summon dogs |
| db_b_02-001 | Goku SSJ | Verify moveset matches base Goku | 2026-01-29 | User confirmed, need verification |
| db_b_02-002 | Goku SSJ | X move damage at 6-koma | 2026-01-29 | SSJ specials may differ |
| db_b_02-003 | Goku SSJ | X move damage at 7-koma | 2026-01-29 | SSJ specials may differ |
| db_b_03-001 | Vegetto | Full moveset damage values | 2026-01-29 | Block 1, high koma cost (8) |
| db_b_03-002 | Vegetto | X move damage at 8-koma | 2026-01-29 | Fusion character specials |
| db_b_04-001 | Vegeta | Full moveset damage values | 2026-01-29 | Block 1 character |
| db_b_04-002 | Vegeta | Available koma sizes | 2026-01-29 | Need deck koma options |
| db_b_04-003 | Vegeta | X move damage at each koma | 2026-01-29 | For specials comparison |
| db_b_05-001 | Vegeta SSJ | Full moveset damage values | 2026-01-29 | Block 2 character |
| db_b_05-002 | Vegeta SSJ | Available koma sizes | 2026-01-29 | Need deck koma options |
| db_b_05-003 | Vegeta SSJ | X move damage at each koma | 2026-01-29 | For specials comparison |
| db_b_06-001 | Gohan SSJ | Full moveset damage values | 2026-01-29 | Block 2 (shared with Vegeta SSJ) |
| db_b_06-002 | Gohan SSJ | Available koma sizes | 2026-01-29 | Need deck koma options |
| db_b_06-003 | Gohan SSJ | X move damage at each koma | 2026-01-29 | For specials comparison |
| db_b_06-004 | Gohan SSJ | Compare moveset to Vegeta SSJ (block 2) | 2026-01-29 | Both use same jpower block |
| ds_b_01-001 | Arale | All B move damage values (neutral) | 2026-01-29 | Dr. Slump character |
| ds_b_01-002 | Arale | All Y move damage values (neutral) | 2026-01-29 | Dr. Slump character |
| ds_b_01-003 | Arale | X move damage at each koma size (4,5,6,7) | 2026-01-29 | formType=2, check specials |
| ds_b_01-004 | Arale | up X move damage at each koma size | 2026-01-29 | formType=2, check specials |
| ds_b_01-005 | Arale | Walk speed comparison (vs Goku standard) | 2026-01-29 | |
| ds_b_01-006 | Arale | Dash type (standard vs flash) | 2026-01-29 | |
| ds_b_01-007 | Arale | Weight feel (compare knockback received) | 2026-01-29 | |
| ds_b_01-008 | Arale | Damage type verification (use defense passives) | 2026-01-29 | |
| ds_b_01-009 | Arale | Available koma sizes in deck building | 2026-01-29 | Sprite archives show 4,5,6,7 |
| ds_b_02-001 | Mashirito | All B move damage values (neutral) | 2026-01-29 | Dr. Slump character |
| ds_b_02-002 | Mashirito | All Y move damage values (neutral) | 2026-01-29 | Dr. Slump character |
| ds_b_02-003 | Mashirito | X move damage at each koma size (4,5,6,7) | 2026-01-29 | Type 5 (Summon) entries |
| ds_b_02-004 | Mashirito | up X move damage at each koma size | 2026-01-29 | Type 5 (Summon) entries |
| ds_b_02-005 | Mashirito | Walk speed comparison (vs Goku standard) | 2026-01-29 | |
| ds_b_02-006 | Mashirito | Dash type (standard vs flash) | 2026-01-29 | |
| ds_b_02-007 | Mashirito | Weight feel (compare knockback received) | 2026-01-29 | |
| ds_b_02-008 | Mashirito | Damage type verification (use defense passives) | 2026-01-29 | |
| ds_b_02-009 | Mashirito | Available koma sizes in deck building | 2026-01-29 | Sprite archives show 4,5,6,7 |
| ds_b_02-010 | Mashirito | Summon mechanics (Type 5 collision entries) | 2026-01-29 | Document how summons work |
| ds_b_03-001 | Caramelman | All B move damage values (neutral) | 2026-01-29 | 8-koma only, tier=3 |
| ds_b_03-002 | Caramelman | All Y move damage values (neutral) | 2026-01-29 | 8-koma only, tier=3 |
| ds_b_03-003 | Caramelman | X move damage (8-koma) | 2026-01-29 | 8-koma only |
| ds_b_03-004 | Caramelman | up X move damage (8-koma) | 2026-01-29 | 8-koma only |
| ds_b_03-005 | Caramelman | Walk speed comparison (vs Goku standard) | 2026-01-29 | Likely slow (big character) |
| ds_b_03-006 | Caramelman | Dash type (standard vs flash) | 2026-01-29 | |
| ds_b_03-007 | Caramelman | Weight feel (compare knockback received) | 2026-01-29 | Likely heavy |
| ds_b_03-008 | Caramelman | Damage type verification (use defense passives) | 2026-01-29 | |
| db_b_07-001 | Gohan SSJ2 | Full moveset damage values | 2026-01-29 | Block 3 (shared with Gotenks) |
| db_b_07-002 | Gohan SSJ2 | Available koma sizes | 2026-01-29 | |
| db_b_08-001 | Gotenks | Full moveset damage values | 2026-01-29 | Block 3 (shared with Gohan SSJ2) |
| db_b_08-002 | Gotenks | Available koma sizes | 2026-01-29 | |
| db_b_09-001 | Gotenks SSJ | Full moveset damage values | 2026-01-29 | Unique Block 4, charId=54 |
| db_b_09-002 | Gotenks SSJ | Available koma sizes | 2026-01-29 | |
| db_b_10-001 | Piccolo | Full moveset damage values | 2026-01-29 | Unique Block 5, charId=41 |
| db_b_10-002 | Piccolo | Available koma sizes | 2026-01-29 | |
| db_b_10-003 | Piccolo | Test for stretchy arm reach mechanics | 2026-01-29 | Namekian ability |
| db_b_10-004 | Piccolo | Compare feel to Goku (different charId) | 2026-01-29 | Unique charId=41 |
| db_b_11-001 | Frieza | Full moveset damage values | 2026-01-29 | Unique Block 6, charId=54 |
| db_b_11-002 | Frieza | Available koma sizes | 2026-01-29 | |
| db_b_11-003 | Frieza | Compare feel to Dio (same charId=54) | 2026-01-29 | |
| db_b_11-004 | Frieza | Test dash type (standard or flash) | 2026-01-29 | Dio has flash dash |
| db_b_12-002 | Majin Buu | Available koma sizes | 2026-01-29 | Block 0 (shared with Goku!) |

### P3 - Nice to Have

| ID | Character | Test Description | Added | Notes |
| -- | --------- | ---------------- | ----- | ----- |
| bl_b_03-005 | Rukia | Walk speed (compare to Goku) | 2026-01-29 | Standard reference: Goku |
| bl_b_03-006 | Rukia | Weight class (compare knockback to Goku) | 2026-01-29 | Light/Standard/Heavy |
| bl_b_03-007 | Rukia | Dash type (standard or flash) | 2026-01-29 | Shinigami may use flash step |
| bl_b_04-005 | Renji | Walk speed (compare to Goku) | 2026-01-29 | Standard reference: Goku |
| bl_b_04-006 | Renji | Weight class (compare knockback to Goku) | 2026-01-29 | Light/Standard/Heavy |
| bl_b_04-007 | Renji | Dash type (standard or flash) | 2026-01-29 | Shinigami may use flash step |
| bl_b_05-005 | Hitsugaya | Walk speed (compare to Goku) | 2026-01-29 | May be faster due to small size |
| bl_b_05-006 | Hitsugaya | Weight class (compare knockback to Goku) | 2026-01-29 | May be lighter due to small size |
| bl_b_05-007 | Hitsugaya | Dash type (standard or flash) | 2026-01-29 | Shinigami may use flash step |
| na_b_04-003 | Sakura | Test weight class (light vs standard) | 2026-01-29 | Female characters tend to be lighter |
| db_b_02-004 | Goku SSJ | Confirm tier value (expect 2) | 2026-01-29 | Should match base Goku |
| db_b_03-003 | Vegetto | Movement speed and dash type | 2026-01-29 | Standard or Flash? |
| db_b_03-004 | Vegetto | Weight category verification | 2026-01-29 | Expected standard |
| db_b_04-004 | Vegeta | Movement speed and dash type | 2026-01-29 | Standard or Flash? |
| db_b_04-005 | Vegeta | Compare moveset to Vegeta SSJ | 2026-01-29 | Different jpower blocks |
| db_b_05-005 | Vegeta SSJ | Movement speed and dash type | 2026-01-29 | Standard or Flash? |
| db_b_06-005 | Gohan SSJ | Movement speed and dash type | 2026-01-29 | Standard or Flash? |

---

## In Progress

| ID | Character | Test Description | Started | Tester |
| -- | --------- | ---------------- | ------- | ------ |
| | | | | |

---

## Completed Tests

| ID | Character | Test Description | Result | Completed | Notes |
| -- | --------- | ---------------- | ------ | --------- | ----- |
| ICHIGO-B | Ichigo | Base B damage | 10 | 2026-01-29 | d1=50, 50/5+0=10 ✓ |
| ICHIGO-BANKAI | Bankai | B damage with tier=1 | 9 | 2026-01-29 | d1=50, tier=1, 50/5-1=9 ✓ |
| GOKU-ALL | Goku | Full moveset damage | B=8 | 2026-01-29 | d1=40, 40/5+0=8 ✓ |
| CORE-002 | Naruto | B damage formula test | 8 | 2026-01-30 | d1=40, 40/5+0=8 ✓ |
| db_b_12-003 | Majin Buu | B damage (Block 0 test) | 9 | 2026-01-30 | d1=45, 45/5+0=9 ✓ SOLVED anomaly |
| db_b_12-004 | Majin Buu | ÷5 or ÷7 formula | ÷5 | 2026-01-30 | Confirmed damage1/5 formula |
| NAMI-B | Nami | B damage | 6 | 2026-01-30 | d1=30, 30/5+0=6 ✓ |
| TRAIN-B | Train | B damage | 7 | 2026-01-30 | d1=35, 35/5+0=7 ✓ |
| LUFFY-B | Luffy | B damage | 8 | 2026-01-30 | d1=40, 40/5+0=8 ✓ |
| ROBIN-B | Robin | B damage | 8 | 2026-01-30 | d1=40, 40/5+0=8 ✓ |
| FRANKY-B | Franky | B damage | 8 | 2026-01-30 | d1=40, 40/5+0=8 ✓ |
| CARAMELMAN-B | Caramelman | B damage (tier=3) | 13 | 2026-01-30 | d1=60, tier=3, 60/5+1=13 ✓ |
| KYUUBI-B | Kyuubi Naruto | B damage (tier=1) | 8 | 2026-01-30 | d1=45, tier=1, 45/5-1=8 ✓ |

---

## Test Methodology

### Damage Testing
1. Use Training Mode if available, or VS mode with known HP
2. Test against a neutral character (no nature advantage)
3. Record each hit separately for multi-hit moves
4. Test with both Slash Defense and Impact Defense passives to identify damage type
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
2. Add test to the character's individual map file under "Human Testing Required"
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
