# Heihachi Edajima (oj_b_02) - Character Mapping

> **Map status:** STUB — basic IDs/series info only; collision, koma, and damage data not yet extracted or tested.

Deep dive analysis mapping Edajima through all data files.

---

## File Data

### chr_b.bin Entry

**chr_b index 67:**

- File: oj_b_02
- charId: 9
- classId: 420
- jpower block: 164 (classId & 0xFF)

### Series Information

- **Series:** Sakigake!! Otokojuku (Charge!! Men's Private School)
- **Series prefix:** oj (Otokojuku)
- **Character:** Heihachi Edajima - The principal/headmaster of Otokojuku, an incredibly powerful martial artist

---

## Weight Class

**HEAVY** - Documented in research files

Heavy weight characteristics:
- Lower displacement velocity when hit
- Slower walk speed
- More resistance to knockback

---

## Collision File

**Expected file:** oj_b_02.bin (ChrBin.aar/chr/col/)

---

## jpower.bin Analysis

### Block 164

- **classId:** 420
- **Low byte (block):** 164

---

## Koma/Deck Data

### Expected koma.bin entries

Otokojuku series komas should follow standard pattern with consecutive entries for different koma sizes.

---

## Confirmed Unknowns

### To Investigate

1. **Collision file entry count** - Need to extract and analyze oj_b_02.bin
2. **Available koma sizes** - Check sprite archives (oj_b_02_Xc.aar)
3. **Move damage values** - Requires in-game testing
4. **battleParams values** - Extract from chr_b.bin entry 67
5. **tier value** - Affects damage formula (tier-2 modifier)
6. **Heavy weight data location** - Not stored in chr_b battleParams (proven by other character analysis)

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
- Edajima is the legendary headmaster known for extreme strength and durability
- His HEAVY weight classification matches his character design as a large, powerful fighter
- Heavy characters like Edajima and Franky share characteristics of slower movement but higher impact resistance
