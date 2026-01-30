# Toru Muhyo (mr_b_01) - Character Mapping

Deep dive analysis mapping Muhyo through all data files.

---

## File Data

### chr_b.bin Entry

**chr_b index 59:**

- File: mr_b_01
- charId: 47
- classId: 652
- jpower block: 140 (classId & 0xFF)

### Series Information

- **Series:** Muhyo to Rouji no Mahouritsu Soudan Jimusho (Muhyo & Roji's Bureau of Supernatural Investigation)
- **Series prefix:** mr (Muhyo Rouji)
- **Character:** Toru Muhyo - Main protagonist, an executor of magical law

---

## Collision File

**Expected file:** mr_b_01.bin (ChrBin.aar/chr/col/)

---

## jpower.bin Analysis

### Block 140

- **classId:** 652
- **Low byte (block):** 140

---

## Koma/Deck Data

### Expected koma.bin entries

Muhyo series komas should follow standard pattern with consecutive entries for different koma sizes.

---

## Confirmed Unknowns

### To Investigate

1. **Collision file entry count** - Need to extract and analyze mr_b_01.bin
2. **Available koma sizes** - Check sprite archives (mr_b_01_Xc.aar)
3. **Move damage values** - Requires in-game testing
4. **battleParams values** - Extract from chr_b.bin entry 59
5. **tier value** - Affects damage formula (tier-2 modifier)
6. **Weight class** - Standard assumed unless documented otherwise

---

## Related Characters

### Muhyo Series (mr prefix)

| chr_b Index | File     | Character   |
| ----------- | -------- | ----------- |
| 59          | mr_b_01  | Toru Muhyo  |

---

## Notes

- Single battle character from this series
- Series is a supernatural legal drama/action manga
- Muhyo uses magical law enforcement abilities
