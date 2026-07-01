# Komaman Yellow (dt_b_02) - Debug Character Mapping

> **Map status:** STUB — basic IDs/series info only; collision, koma, and damage data not yet extracted or tested.

Analysis of debug/test character data.

---

## File Data

### chr_b.bin Entry

**chr_b index 71:**

- File: dt_b_02
- charId: 0
- classId: 447
- jpower block: 191 (classId & 0xFF)

### Character Information

- **Type:** Debug/Test Character
- **Series prefix:** dt (Debug/Test)
- **Character:** Komaman Yellow - A colored variant of the Komaman mascot character used for testing

---

## Debug Character Characteristics

- **charId: 0** - Indicates a test/placeholder character ID
- Characters with charId=0 may have minimal or test-only data
- These characters were likely used during development for testing game systems

---

## Collision File

**Expected file:** dt_b_02.bin (ChrBin.aar/chr/col/)

May contain minimal/test collision data.

---

## jpower.bin Analysis

### Block 191

- **classId:** 447
- **Low byte (block):** 191

This is a unique jpower block for Komaman Yellow.

---

## Related Characters

### Debug/Test Characters (dt prefix)

| chr_b Index | File    | Character      | charId | classId | jpower block |
| ----------- | ------- | -------------- | ------ | ------- | ------------ |
| 70          | dt_b_01 | Komaman Red    | 0      | 446     | 190          |
| 71          | dt_b_02 | Komaman Yellow | 0      | 447     | 191          |
| 72          | dt_b_03 | Komaman Green  | 0      | 448     | 192          |
| 73          | dt_b_04 | Taizo          | 0      | 446     | 190          |

---

## Notes

- Debug character used for game development and testing
- Komaman variants (Red, Yellow, Green) are color-swapped versions of the same base character
- All debug characters have charId=0, indicating placeholder/test status
- Yellow has a unique classId (447) and jpower block (191), different from Red/Taizo
- These characters may not be accessible in normal gameplay
- May have been used to test battle mechanics, collision systems, or visual effects
