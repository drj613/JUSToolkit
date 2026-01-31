# Damage Formula Predictions

Hypothesis testing through predicted damage values. Each prediction tests a specific aspect of the formula.

**Current hypothesis:** `jsoul_damage = floor(jpower_total / divisor) + (tier - 2)`

**Known data points:**
| Character | Move | jpower total | Observed Damage | Formula Match |
|-----------|------|--------------|-----------------|---------------|
| Ichigo (tier=2) | B | 50 | 10 | ÷5 ✓ |
| Bankai Ichigo (tier=1) | B | 50 | 9 | ÷5 + tier ✓ |
| Goku (tier=2) | B | ??? | 8 | Neither ÷5 nor ÷7 work! |
| Goku (tier=2) | up Y | 100 | 14 | ÷7 ✓ |
| Goku (tier=2) | down Y | 100 | 14 | ÷7 ✓ |

**THE MYSTERY:** Goku B=8 doesn't fit either formula with Block 0 entries.

---

## Priority 1 Predictions (Most Insightful)

### 1. Piccolo - Tests if DB characters use ÷7

**Character:** Piccolo (DB, Block 5, tier=2)  
**Block 5 pattern:** [7,3,2,1] from jpower-Mapping.md

**Prediction (if ÷5):**
| Move | Predicted Damage | Required jpower total |
|------|------------------|----------------------|
| B (first) | 7 | 35 |
| Other | 3 | 15 |
| Other | 2 | 10 |
| Other | 1 | 5 |

**Prediction (if ÷7):**
| Move | Predicted Damage | Required jpower total |
|------|------------------|----------------------|
| B | 7 | 49 |
| Other | 3 | 21 |
| Other | 2 | 14 |
| Other | 1 | 7 |

**Why insightful:** Piccolo is DB but uses a unique block. If his damage matches ÷5, it suggests Goku is the exception. If it matches ÷7, DB characters might all use ÷7.

**Test:** Record Piccolo's B damage. If 7, test other moves for 3, 2, 1 pattern.

---

### 2. Luffy - Tests One Piece series

**Character:** Luffy (OP, Block 9, tier=2)  
**Block 9 pattern:** [57,7,7,7,7,7,7,7,7,7,14]

**Prediction (if ÷5):**
| Entry Total | Predicted Damage |
|-------------|------------------|
| 57 | 11 |
| 50 | 10 |
| 100 | 20 |

**Prediction (if ÷7):**
| Entry Total | Predicted Damage |
|-------------|------------------|
| 57 | 8 |
| 50 | 7 |
| 100 | 14 |

**Why insightful:** Different series entirely. If Luffy B=10, One Piece uses ÷5. If B=7 or 8, may use ÷7 like (some) DB characters.

**Test:** Record Luffy's B damage and compare to predictions.

---

### 3. Majin Buu - Tests Block 0 entry selection

**Character:** Majin Buu (DB, Block 0, tier=2)  
**Same block as Goku but DIFFERENT moveset!**

**The critical question:** Does Buu get the same damage values as Goku, or different?

**Prediction A (same jpower entries as Goku):**
- Buu B = 8 (same as Goku B)
- Buu Y moves = 14 (same as Goku Y)

**Prediction B (different jpower entry selection):**
- Buu B = 10 (if using total=50 with ÷5)
- Buu B = 7 (if using total=50 with ÷7)

**Why insightful:** This is the P0 CRITICAL test. If Buu B ≠ 8, it proves entry selection varies. If Buu B = 8, the mystery deepens.

**Test:** Compare Buu's B damage to Goku's B (8).

---

### 4. Naruto - Tests Naruto series

**Character:** Naruto (Naruto series, Block 17, tier=2)

**Prediction (if universal ÷5):**
- If Block 17 has total=50 entry: B = 10
- If Block 17 has total=35 entry: B = 7

**Prediction (if ÷7):**
- If Block 17 has total=50 entry: B = 7
- If Block 17 has total=56 entry: B = 8

**Why insightful:** Third major series. Pattern across DB, Bleach, One Piece, Naruto would reveal if divisor is universal or series-specific.

**Test:** Record Naruto's B damage.

---

## Priority 2 Predictions (Confirming)

### 5. Zoro - Tests blade damage

**Character:** Zoro (OP, Block 11, tier=2)  
**Block 11 pattern:** [7,7,7,7,7]

**Observation:** All entries show 7 damage. This suggests:
- All jpower totals are 35 (if ÷5) or 49 (if ÷7)
- OR damage3 (blade) is calculated differently

**Prediction:** Zoro B = 7

**Why insightful:** If Zoro's moves all deal 7 damage, confirms consistent block entries. If any move deals different damage, reveals move-specific selection.

---

### 6. Robin - Tests shared block paradox

**Character:** Robin (OP, Block 9 - SAME as Luffy!, tier=2)

**The paradox:** Robin and Luffy share Block 9 but have completely different movesets (arm spawning vs stretching).

**Prediction:** Robin B = same as Luffy B

**If true:** Block entries are selected by move TYPE, not character
**If false:** Some other mechanism selects entries per-character

**Test:** Compare Robin B to Luffy B.

---

### 7. Caramelman - Tests tier=3 modifier

**Character:** Caramelman (Dr. Slump, Block 102, tier=3)

**Prediction (if tier modifier works):**
- Base damage + 1 (tier 3 = +1 modifier)
- If jpower total = 50: damage = 10 + 1 = **11**

**Why insightful:** Only tested tier=1 (Bankai, -1) and tier=2 (standard). Need tier=3 to confirm the full formula.

**Test:** Record Caramelman B damage and compare to formula.

---

## Quick Test Protocol

For each character, record:
1. **B damage** (neutral, no buffs, same-nature target)
2. **Y damage** (if different from B)
3. **Nature** (for avoiding advantage/disadvantage)

### Test Order (by insight value)

1. **Majin Buu B** - Resolves Block 0 mystery (P0)
2. **Piccolo B + other moves** - Tests DB ÷7 hypothesis
3. **Luffy B** - Tests One Piece series
4. **Naruto B** - Tests Naruto series
5. **Caramelman B** - Tests tier=3 modifier
6. **Robin B** - Tests shared block paradox

---

## Possible Formula Outcomes

After testing, we'll know which of these is true:

**Outcome A: Universal ÷5**
- All characters use ÷5, Goku data is wrong or uses different entry

**Outcome B: Series-specific divisor**
- DB uses ÷7, Bleach uses ÷5, others TBD

**Outcome C: Block-specific divisor**
- Some blocks use ÷5, others use ÷7

**Outcome D: Entry-specific calculation**
- Different jpower entries have different calculation methods

**Outcome E: Something else entirely**
- Additional factors we haven't considered (damage type, attack category, etc.)

---

*Created: 2026-01-31*
