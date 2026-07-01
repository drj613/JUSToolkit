# Taikoubou (hs_b_01) - Character Mapping

> **Map status:** STUB — basic IDs/series info only; collision, koma, and damage data not yet extracted or tested.

Deep dive analysis mapping Taikoubou through all data files.

---

## File Data

### chr_b.bin Entry

**chr_b index 68:**

- File: hs_b_01
- charId: 47
- classId: 684
- jpower block: 172 (classId & 0xFF)

### Series Information

- **Series:** Houshin Engi (Soul Hunter)
- **Series prefix:** hs (Houshin)
- **Character:** Taikoubou - Main protagonist, a Sennin (immortal sage) tasked with sealing away evil immortals

---

## Collision File

**Expected file:** hs_b_01.bin (ChrBin.aar/chr/col/)

---

## jpower.bin Analysis

### Block 172

- **classId:** 684
- **Low byte (block):** 172

**Note:** This is the same jpower block as Momotaro Tsurugi (oj_b_01). Characters can share jpower blocks while having different movesets, similar to how Goku, Goku SSJ, and Majin Buu share block 0.

---

## Koma/Deck Data

### Expected koma.bin entries

Houshin Engi series komas should follow standard pattern with consecutive entries for different koma sizes.

---

## Confirmed Unknowns

### To Investigate

1. **Collision file entry count** - Need to extract and analyze hs_b_01.bin
2. **Available koma sizes** - Check sprite archives (hs_b_01_Xc.aar)
3. **Move damage values** - Requires in-game testing
4. **battleParams values** - Extract from chr_b.bin entry 68
5. **tier value** - Affects damage formula (tier-2 modifier)
6. **Weight class** - Standard assumed unless documented otherwise

---

## Related Characters

### Houshin Engi Series (hs prefix)

| chr_b Index | File    | Character  |
| ----------- | ------- | ---------- |
| 68          | hs_b_01 | Taikoubou  |

---

## Notes

- Single battle character from this series
- Based on the Chinese novel "Fengshen Yanyi" (Investiture of the Gods)
- Taikoubou uses Paopei (magical weapons/tools) in combat, primarily his "Dashinben" (whip)
- Series features a mix of strategy, comedy, and action
