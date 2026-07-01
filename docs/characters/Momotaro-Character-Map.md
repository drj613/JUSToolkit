# Momotaro Tsurugi (oj_b_01) - Character Mapping

> **Map status:** STUB — basic IDs/series info only; collision, koma, and damage data not yet extracted or tested.

Deep dive analysis mapping Momotaro through all data files.

---

## File Data

### chr_b.bin Entry

**chr_b index 66:**

- File: oj_b_01
- charId: 5
- classId: 428
- jpower block: 172 (classId & 0xFF)

### Series Information

- **Series:** Sakigake!! Otokojuku (Charge!! Men's Private School)
- **Series prefix:** oj (Otokojuku)
- **Character:** Momotaro Tsurugi - Main protagonist, a student at Otokojuku who fights with exceptional martial arts skills

---

## Weight Class

**STANDARD** - Documented in research files

---

## Collision File

**Expected file:** oj_b_01.bin (ChrBin.aar/chr/col/)

---

## jpower.bin Analysis

### Block 172

- **classId:** 428
- **Low byte (block):** 172

---

## Koma/Deck Data

### Expected koma.bin entries

Otokojuku series komas should follow standard pattern with consecutive entries for different koma sizes.

---

## Confirmed Unknowns

### To Investigate

1. **Collision file entry count** - Need to extract and analyze oj_b_01.bin
2. **Available koma sizes** - Check sprite archives (oj_b_01_Xc.aar)
3. **Move damage values** - Requires in-game testing
4. **battleParams values** - Extract from chr_b.bin entry 66
5. **tier value** - Affects damage formula (tier-2 modifier)

---

## Related Characters

### Otokojuku Series (oj prefix)

| chr_b Index | File    | Character         | Weight   |
| ----------- | ------- | ----------------- | -------- |
| 66          | oj_b_01 | Momotaro Tsurugi  | STANDARD |
| 67          | oj_b_02 | Heihachi Edajima  | HEAVY    |

---

## Notes

- One of two battle characters from the Otokojuku series
- Otokojuku is a classic martial arts/delinquent manga from the 1980s
- Momotaro is the primary student fighter, known for his combat skills and sense of justice
- Momotaro is documented as having STANDARD weight (normal displacement velocity)
