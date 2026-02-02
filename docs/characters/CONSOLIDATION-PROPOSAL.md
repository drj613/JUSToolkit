# Character Documentation Consolidation Proposal

## Problem

Currently we have 73 character map files, but many are for form variants that share
the same base moveset. This creates:
- Duplicated information across files
- Risk of docs getting out of sync
- Unclear which file is the "source of truth"

## Analysis

From `Character-Mapping.md`, form variants fall into three categories:

### Category A: Same Kit (Consolidate)

These share jpower block AND classId - mechanically identical except sprites:

| Base | Form | jpower Block | classId | Collision Entries |
|------|------|-------------|---------|-------------------|
| Don Patch | Super Patch | 70 | 582 | 18 / 18 |

**Action:** Merge into single file.

### Category B: Same jpower Block (Consolidate)

Only characters with the SAME jpower block can be consolidated, as they share damage values:

| Base | Form(s) | jpower Block | classId |
|------|---------|-------------|---------|
| Goku | Goku SSJ | 0 | 256 |

**Action:** Merge with form-specific sections for specials and file data.

### Category B2: Different jpower Blocks (Keep Separate)

Despite similar movesets, these use different jpower blocks and thus different damage values:

| Character | jpower Block | classId | Notes |
|-----------|-------------|---------|-------|
| Vegetto | 1 | 257 | Different from Goku |
| Vegeta | 1 | 257 | Different from Vegeta SSJ |
| Vegeta SSJ | 2 | 258 | Different from base |
| Gotenks | 3 | 259 | Different from Gotenks SSJ |
| Gotenks SSJ | 4 | 516 | Different block AND charId! |

**Action:** Keep separate files - damage values differ.

### Category C: Different Movesets (Keep Separate)

These have explicitly different movesets:

| Base | Form | Reason |
|------|------|--------|
| Ichigo | Bankai | "7-8 koma, different moveset" |
| Naruto | Kyuubi Naruto | "7-8 koma, different moveset" |
| Luffy | Gear 2 Luffy | Different entry counts (38 vs 28) |
| Nami | PCT Nami | "6 koma, weather attacks" |
| Yoh | Yoh White Swan | "6 koma, extended range" |
| Seiya | Gold Seiya | "8 koma, neutral Y knockup" |
| Gohan SSJ | Gohan SSJ2 | "Different from SSJ" |
| Bo-bobo | Shinsetsu | "bigger hitboxes" (different collision data) |

**Action:** Keep separate files.

---

## Proposed Consolidated Document Structure

```markdown
# [Character Name] - Character Map

## Overview
| Field | Base Form | Form 2 | Form 3 |
|-------|-----------|--------|--------|
| Collision File | xx_b_01 | xx_b_02 | xx_b_03 |
| chr_b Index | 0 | 1 | 2 |
| Koma Sizes | 4,5,6 | 6,7 | 8 |

## Shared Moveset (All Forms)
[B, Y moves that are identical across forms]

## Form-Specific Data

### Base Form (xx_b_01)
- Specials (X moves)
- Collision data summary
- Form-specific notes

### Form 2 (xx_b_02)
- Specials (X moves)
- Collision data summary
- Form-specific notes

## File Data
[chr_b entries for each form in expandable sections]
```

---

## Implementation Plan

### Phase 1: Test Case (DONE)
1. ✅ Consolidate Don Patch + Super Patch (identical kit - same jpower block 70)

### Phase 2: Goku Family
2. Consolidate Goku + Goku SSJ (same jpower block 0, classId 256)
3. Keep Vegetto separate (different jpower block 1)

### Phase 3: Cleanup
4. Update any cross-references
5. Delete redundant files

**NOT consolidating** (different jpower blocks = different damage values):
- Vegeta / Vegeta SSJ (blocks 1 vs 2)
- Gotenks / Gotenks SSJ (blocks 3 vs 4, also different charId)

---

## Files to Delete After Consolidation

After merging, these files become redundant:
- ✅ `SuperPatch-Character-Map.md` → merged into `DonPatch-Character-Map.md`
- `Goku-SSJ-Character-Map.md` → merged into `Goku-Character-Map.md`

**Total:** 2 files removed.

---

## Decision

Proceed with consolidation? Start with Don Patch as proof of concept.
