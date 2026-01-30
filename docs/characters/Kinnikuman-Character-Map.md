# Kinnikuman (kn_b_01) - Character Mapping

Deep dive analysis mapping Kinnikuman through all data files.

---

## File Data

### chr_b.bin Entry

**chr_b index 65:**

- File: kn_b_01
- charId: 14
- classId: 422
- jpower block: 166 (classId & 0xFF)

### Series Information

- **Series:** Kinnikuman (Muscle Man)
- **Series prefix:** kn (Kinnikuman)
- **Character:** Kinnikuman (Suguru Kinniku) - Main protagonist, a superhero wrestler and prince of Planet Kinniku

---

## Collision File

**Expected file:** kn_b_01.bin (ChrBin.aar/chr/col/)

---

## jpower.bin Analysis

### Block 166

- **classId:** 422
- **Low byte (block):** 166

---

## Koma/Deck Data

### Expected koma.bin entries

Kinnikuman series komas should follow standard pattern with consecutive entries for different koma sizes.

---

## Confirmed Unknowns

### To Investigate

1. **Collision file entry count** - Need to extract and analyze kn_b_01.bin
2. **Available koma sizes** - Check sprite archives (kn_b_01_Xc.aar)
3. **Move damage values** - Requires in-game testing
4. **battleParams values** - Extract from chr_b.bin entry 65
5. **tier value** - Affects damage formula (tier-2 modifier)
6. **Weight class** - Standard assumed unless documented otherwise

---

## Related Characters

### Kinnikuman Series (kn prefix)

| chr_b Index | File    | Character  |
| ----------- | ------- | ---------- |
| 65          | kn_b_01 | Kinnikuman |

---

## Notes

- Single battle character from this series
- Classic wrestling/superhero manga from the 1980s
- Kinnikuman uses wrestling moves and signature techniques like the Kinniku Buster and Kinniku Driver
