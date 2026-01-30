# Taizo (dt_b_04) - Debug Character Mapping

Analysis of debug/test character data.

---

## File Data

### chr_b.bin Entry

**chr_b index 73:**

- File: dt_b_04
- charId: 0
- classId: 446
- jpower block: 190 (classId & 0xFF)

### Character Information

- **Type:** Debug/Test Character
- **Series prefix:** dt (Debug/Test)
- **Character:** Taizo Momote - Potentially scrapped battle character that there
  wasn't enough time for? He has a helper and supports in the regular list as
  well, but the battle character is hidden in the debug section

---

## Debug Character Characteristics

- **charId: 0** - Indicates a test/placeholder character ID
- Characters with charId=0 may have minimal or test-only data
- These characters were likely used during development for testing game systems

---

## Collision File

**Expected file:** dt_b_04.bin (ChrBin.aar/chr/col/)

May contain minimal/test collision data.

---

## jpower.bin Analysis

### Block 190

- **classId:** 446
- **Low byte (block):** 190

**Note:** Shares the same classId and jpower block as Komaman Red (dt_b_01).
This means both characters reference the same jpower data, suggesting they may
have identical or very similar attack properties.

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
- Shares classId (446) and jpower block (190) with Komaman Red, indicating
  identical attack data
- All debug characters have charId=0, indicating placeholder/test status
- These characters may not be accessible in normal gameplay
- May have been used to test battle mechanics, collision systems, or visual
  effects
