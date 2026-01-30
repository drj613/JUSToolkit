# Neuro Nogami (nn_b_01) - Character Mapping

Deep dive analysis mapping Neuro through all data files.

---

## File Data

### chr_b.bin Entry

**chr_b index 60:**

- File: nn_b_01
- charId: 31
- classId: 669
- jpower block: 157 (classId & 0xFF)

### Series Information

- **Series:** Majin Tantei Nougami Neuro (Demon Detective Neuro)
- **Series prefix:** nn (Nougami Neuro)
- **Character:** Neuro Nogami - Main protagonist, a demon detective who feeds on mysteries

---

## Collision File

**Expected file:** nn_b_01.bin (ChrBin.aar/chr/col/)

---

## jpower.bin Analysis

### Block 157

- **classId:** 669
- **Low byte (block):** 157

---

## Koma/Deck Data

### Expected koma.bin entries

Neuro series komas should follow standard pattern with consecutive entries for different koma sizes.

---

## Confirmed Unknowns

### To Investigate

1. **Collision file entry count** - Need to extract and analyze nn_b_01.bin
2. **Available koma sizes** - Check sprite archives (nn_b_01_Xc.aar)
3. **Move damage values** - Requires in-game testing
4. **battleParams values** - Extract from chr_b.bin entry 60
5. **tier value** - Affects damage formula (tier-2 modifier)
6. **Weight class** - Standard assumed unless documented otherwise

---

## Related Characters

### Neuro Series (nn prefix)

| chr_b Index | File     | Character    |
| ----------- | -------- | ------------ |
| 60          | nn_b_01  | Neuro Nogami |

---

## Notes

- Single battle character from this series
- Series is a supernatural mystery manga
- Neuro uses "Evil Tools" (demonic weapons) in combat
