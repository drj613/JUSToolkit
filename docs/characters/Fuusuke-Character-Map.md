# Fuusuke (nk_b_01) - Character Mapping

> **Map status:** STUB — basic IDs/series info only; collision, koma, and damage data not yet extracted or tested.

Deep dive analysis mapping Fuusuke through all data files.

---

## File Data

### chr_b.bin Entry

**chr_b index 69:**

- File: nk_b_01
- charId: 2
- classId: 435
- jpower block: 179 (classId & 0xFF)

### Series Information

- **Series:** Ninku
- **Series prefix:** nk (Ninku)
- **Character:** Fuusuke - Main protagonist, a young ninja who is the captain of the 1st Ninku Corps specializing in wind techniques

---

## Collision File

**Expected file:** nk_b_01.bin (ChrBin.aar/chr/col/)

---

## jpower.bin Analysis

### Block 179

- **classId:** 435
- **Low byte (block):** 179

---

## Koma/Deck Data

### Expected koma.bin entries

Ninku series komas should follow standard pattern with consecutive entries for different koma sizes.

---

## Confirmed Unknowns

### To Investigate

1. **Collision file entry count** - Need to extract and analyze nk_b_01.bin
2. **Available koma sizes** - Check sprite archives (nk_b_01_Xc.aar)
3. **Move damage values** - Requires in-game testing
4. **battleParams values** - Extract from chr_b.bin entry 69
5. **tier value** - Affects damage formula (tier-2 modifier)
6. **Weight class** - Standard assumed unless documented otherwise

---

## Related Characters

### Ninku Series (nk prefix)

| chr_b Index | File    | Character |
| ----------- | ------- | --------- |
| 69          | nk_b_01 | Fuusuke   |

---

## Notes

- Single battle character from this series
- Ninku is a martial art combining ninjutsu with taijutsu
- Fuusuke specializes in wind-based attacks (Kuuha - Air Wave)
- He is accompanied by a penguin named Hiroyuki (who may appear in attacks)
- Series ran in Weekly Shonen Jump from 1993-1995
