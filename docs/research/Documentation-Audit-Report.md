# Documentation Audit Report - Closed Issues

**Date:** 2026-01-31  
**Audit Scope:** All closed beads issues checked against project documentation

---

## Summary

Audited 16 closed issues against project documentation. Found **3 critical discrepancies** and **1 minor discrepancy** where findings from closed issues were not properly propagated to documentation.

---

## Critical Discrepancies

### 1. JUS-9lp.3 & JUS-9lp.4: Damage Formula Documentation Inconsistency

**Issue IDs:** JUS-9lp.3, JUS-9lp.4  
**Finding:** Formula verified as `damage1÷5 + (tier-2)` across **15+ characters**. Key insight: uses `damage1` only, NOT `totalDamage = damage1+damage2+damage3`.

**Documentation Status:** ❌ **INCONSISTENT**

**Problems Found:**

1. **`docs/research/Combat-Mechanics.md`** (Lines 9-15)
   - ❌ Still shows **OUTDATED** formula: `jpower_totalDamage / 5` where `jpower_totalDamage = damage1 + damage2 + damage3`
   - ❌ This contradicts the verified finding that formula uses `damage1` only
   - **Action Required:** Update to use `damage1` only, remove totalDamage references

2. **`docs/research/jpower-Block-Pattern-Analysis.md`** (Lines 107-115)
   - ❌ Still shows **OUTDATED** formula: `damage = floor(jpower_total / 5)` where `jpower_total = damage1 + damage2 + damage3`
   - ❌ Mentions "Alternative formula (Goku Block 0): `damage = floor(jpower_total / 7)`" which was debunked
   - **Action Required:** Update to reflect `damage1` only formula

3. **`docs/research/Research-Status.md`** (Line 315)
   - ⚠️ Contains outdated example: `damageFlags=2 → jpower[2] (ID=6, total=50) → 50/5=10 damage`
   - Should reference `damage1=50` instead of `total=50`
   - **Action Required:** Update examples to use `damage1` field

4. **`docs/research/README.md`** (Line 81)
   - ⚠️ Says "Verified across **12+ characters**" but issue JUS-9lp.3 states "**15+ characters**"
   - **Action Required:** Update count to "15+ characters" or verify actual count

**Correct Documentation:**
- ✅ `docs/research/Damage-Formula-Predictions.md` - CORRECT
- ✅ `docs/research/Combat-Mechanics-Reference.md` - CORRECT
- ✅ `docs/research/Research-Status.md` (main formula section) - CORRECT

---

### 2. JUS-9lp.4: Buu Anomaly Explanation Missing from Some Docs

**Issue ID:** JUS-9lp.4  
**Finding:** Buu B=9 anomaly explained - formula uses `damage1÷5`, not `totalDamage÷5`. Buu uses entry with `damage1=45` (45/5+0=9).

**Documentation Status:** ⚠️ **PARTIALLY DOCUMENTED**

**Problems Found:**

1. **`docs/research/Research-Status.md`** (Lines 354+)
   - ⚠️ Still lists "Buu anomaly" as an open question/unknown
   - Should be moved to "SOLVED" section with explanation
   - **Action Required:** Update to show Buu anomaly is solved

**Correct Documentation:**
- ✅ `docs/research/Damage-Formula-Predictions.md` - Has "Buu B=9 Anomaly" section explaining it's solved

---

## Minor Discrepancies

### 3. JUS-26z: tr_b_01 Identification - Well Documented

**Issue ID:** JUS-26z  
**Finding:** tr_b_01 is Tsuna Sawada & Reborn from 'Katekyo Hitman Reborn' (not Taizo as initially thought).

**Documentation Status:** ✅ **WELL DOCUMENTED**

**Verified Locations:**
- ✅ `docs/AI-ASSISTANT-GUIDE.md` - Has dedicated section "tr_b_01 Identity (SOLVED)"
- ✅ `docs/research/Character-Mapping.md` - Lists tr_b_01 correctly
- ✅ `docs/characters/Tsuna-Character-Map.md` - Complete character documentation
- ✅ `docs/research/chr_b-Mapping.md` - Correctly mapped

**No Action Required** - This finding is properly documented.

---

### 4. JUS-ppu.*: Character Documentation - Complete

**Issue IDs:** JUS-ppu, JUS-ppu.1 through JUS-ppu.8  
**Finding:** All 74 character maps created in `docs/characters/`

**Documentation Status:** ✅ **COMPLETE**

**Verified:**
- ✅ 74 character markdown files exist in `docs/characters/`
- ✅ Template created at `docs/characters/TEMPLATE.md`
- ✅ All series documented (Dragon Ball, One Piece, Naruto, Bleach, Yu-Gi-Oh, Saint Seiya, Rurouni Kenshin, remaining series)

**No Action Required** - Character documentation is complete.

---

## Other Closed Issues - No Documentation Gaps

### JUS-9lp (Epic)
- **Status:** Merged into JUS-cb0, findings documented in child issues
- **No gaps found**

### JUS-0co (Epic)
- **Status:** Merged into JUS-oct
- **No gaps found** - File format documentation is part of data extraction scope

### JUS-az7, JUS-az7.1
- **Status:** Template created, infrastructure complete
- **No gaps found** - Template exists at `docs/characters/TEMPLATE.md`

---

## Recommended Actions

### Priority 1: Fix Critical Formula Documentation

1. **Update `docs/research/Combat-Mechanics.md`**
   - Replace `jpower_totalDamage = damage1 + damage2 + damage3` with `damage1` only
   - Update formula to: `jsoul_damage = floor(jpower.damage1 / 5) + (tier - 2)`
   - Add note: "Uses `damage1` component only, NOT total damage"

2. **Update `docs/research/jpower-Block-Pattern-Analysis.md`**
   - Remove "Alternative formula (Goku Block 0): ÷7" section (debunked)
   - Update formula to use `damage1` only
   - Remove references to `jpower_total = damage1 + damage2 + damage3`

3. **Update `docs/research/Research-Status.md`**
   - Move Buu anomaly to "SOLVED" section
   - Update examples to use `damage1` field instead of `total`
   - Clarify that formula uses `damage1` only

### Priority 2: Verify Character Count

4. **Verify actual verification count**
   - Check if "15+ characters" or "12+ characters" is accurate
   - Update `docs/research/README.md` with correct count

---

## Files Requiring Updates

1. `docs/research/Combat-Mechanics.md` - **CRITICAL** - Outdated formula
2. `docs/research/jpower-Block-Pattern-Analysis.md` - **CRITICAL** - Outdated formula
3. `docs/research/Research-Status.md` - **MEDIUM** - Outdated examples and Buu anomaly status
4. `docs/research/README.md` - **LOW** - Character count discrepancy

---

## Verification Checklist

- [x] JUS-9lp.3 damage formula verification - **NEEDS FIXES**
- [x] JUS-9lp.4 Buu anomaly - **NEEDS FIXES**
- [x] JUS-26z tr_b_01 identification - ✅ Complete
- [x] JUS-ppu.* character documentation - ✅ Complete
- [x] All other closed issues - ✅ No gaps

---

_Generated: 2026-01-31_
