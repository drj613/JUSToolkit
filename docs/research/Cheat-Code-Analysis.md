# Cheat Code Analysis

Memory addresses and structures extracted from Action Replay codes.

---

## Game ID

```
AJUJ-65E1D889
```

---

## Character Struct (In-Battle RAM)

The wifi codes reveal character state is stored at pointer-relative offsets.
Base pointers: `0x021E2A7C`, `0x021E2A80`, `0x021E2A84`, `0x021E2A88` (4
players)

### Character State Offsets

| Offset | Size | Field                 | Source Code                 |
| ------ | ---- | --------------------- | --------------------------- |
| 0x0078 | 1    | Ground/Air state      | "Always on Ground/Air"      |
| 0x0088 | 1    | Positive status ID    | "Have Positive Status"      |
| 0x00A0 | 1    | Negative status flags | "Immune to negative status" |
| 0x00D9 | 1    | Jump counter          | "Infinite Jumps"            |
| 0x00DA | 1    | Air action counter    | "Infinite Air Actions"      |
| 0x0102 | 1    | Defense duration      | "Defense never wears"       |

### Ground/Air State Values

- `0x00` = In Air
- `0x22` = On Ground

### Positive Status IDs

- `0x00` = Nothing
- `0x09` = Invincibility (visual only?)

---

## Battle State Addresses

| Address    | Size | Purpose              | Source                       |
| ---------- | ---- | -------------------- | ---------------------------- |
| 0x021DEA70 | 2    | Battle timer (wifi)  | "Push time back to 99"       |
| 0x021DEA71 | 1    | Battle timer (local) | "Unlimited Time"             |
| 0x021DF1D5 | 1    | Player 1 HP          | "Leader Refill Health"       |
| 0x021DF225 | 1    | Player 2 HP          | "Non-leader Refill Health"   |
| 0x021DF275 | 1    | Player 3 HP          | "Infinite Health (4P)"       |
| 0x021DF2C5 | 1    | Player 4 HP          | "Infinite Health (4P)"       |
| 0x021DF731 | 1    | Special meter 1      | "Unlimited Special"          |
| 0x021DF8B1 | 1    | Special meter 2      | "Unlimited Special"          |
| 0x021DB611 | 1    | Koma sprite (glitch) | "Glitch Battle Koma Sprites" |
| 0x021DB609 | 1    | Koma sprite (glitch) | "Glitch Battle Koma Sprites" |

### Wifi Battle State

| Address    | Size | Purpose                |
| ---------- | ---- | ---------------------- |
| 0x021E29B0 | 2    | Wifi battle timer      |
| 0x021E2A7C | 4    | Player 1 state pointer |
| 0x021E2A80 | 4    | Player 2 state pointer |
| 0x021E2A84 | 4    | Player 3 state pointer |
| 0x021E2A88 | 4    | Player 4 state pointer |

---

## Deck/Menu Addresses

| Address       | Size  | Purpose             | Source               |
| ------------- | ----- | ------------------- | -------------------- |
| 0x020AFEB4    | 4     | Active deck index   | "Use deck XX"        |
| 0x020B0BAC    | array | Koma unlock flags   | "Unlock all komas"   |
| 0x020B0C93    | 4     | Course unlock flags | "Unlock all courses" |
| 0x0228AAB0-C4 | 6×4   | Side koma holder    | "Fill side komas"    |

### Deck Index Values

| Value | Deck    |
| ----- | ------- |
| 0x00  | Deck 1  |
| 0x08  | Deck 9  |
| 0x0F  | Deck 16 |
| 0x10  | Deck 17 |
| 0x13  | Deck 20 |

---

## Currency/Progress

| Address         | Size | Purpose             |
| --------------- | ---- | ------------------- |
| 0x020B76C8      | 4    | Koma points         |
| 0x020B76F0      | 4    | Koma points (alt?)  |
| 0x020B7718-7720 | 3×4  | Gems (type 1-3)     |
| 0x020B7724-772C | 3×4  | Gems (type 4-6)     |
| 0x020B7768-77E0 | 7×4  | Additional currency |

---

## Character Palette/Color

Base pointer: `0x023D7B00`

| Offset  | Size   | Purpose                       |
| ------- | ------ | ----------------------------- |
| 0x02-22 | 2 each | Palette entries (BGRR format) |

---

## Koma ID Table (from "Fill Side Komas" code)

The XXXX values in `021eXXXX` are koma IDs. Pattern analysis:

### Structure

Each character has sequential koma IDs for different sizes:

- IDs are spaced 0x0C (12) apart
- Base ID + (koma_size - 1) \* 0x0C ≈ koma variant

### Complete Koma ID List

| Character | 1-koma | 2-koma | 3-koma | 4-koma    | 5-koma    | 6-koma    | 7-koma | 8-koma |
| --------- | ------ | ------ | ------ | --------- | --------- | --------- | ------ | ------ |
| Goku      | 1738   | 1744   | 1750   | 175C,1768 | 1774      | 1780      | 178C   | 1798   |
| Ichigo    | 1E70   | 1E7C   | 1E88   | 1E94      | 1EA0      | 1EAC      | 1EB8   | 1EC4   |
| Naruto    | 196C   | 1978   | 1984   | 1990,199C | 19A8      | 19B4      | 19C0   | 19CC   |
| Luffy     | 2890   | 289C   | 28A8   | 28B4      | 28C0      | 28CC,28D8 | 28E4   | 28F0   |
| Vegeta    | 17A4   | 17B0   | 17BC   | 17C8      | 17D4,17E0 | 17EC      | -      | -      |
| Gintoki   | 0694   | 06A0   | 06AC   | 06B8      | 06C4      | 06D0,06DC | 06E8   | -      |
| Kenshin   | 2740   | 274C   | 2758   | 2764      | 2770      | 277C,2788 | -      | -      |
| Dio       | 0F34   | 0F40   | 0F4C   | 0F58      | 0F64,0F70 | 0F7C      | -      | -      |
| Train     | 1DEC   | 1DF8   | 1E04   | 1E10      | 1E1C,1E28 | -         | -      | -      |

### Beta/Debug Komas

| Type                   | Koma            | ID   |
| ---------------------- | --------------- | ---- |
| Battle (4-koma square) | Red Koma Man    | 2B30 |
| Battle                 | Green Koma Man  | 2B3C |
| Battle                 | Yellow Koma Man | 2B48 |
| Battle                 | Taizo Mote      | 2BB4 |
| Support (2-koma)       | Frieza          | 2B78 |
| Support                | Buu             | 2B84 |
| Support                | Sasuke          | 2B90 |
| Support                | Raoh            | 2B9C |
| Support                | Edajima         | 2BA8 |
| Support                | Caramel J Man   | 2BCC |
| Help                   | Help A          | 2AE8 |
| Help                   | Help B          | 2AF4 |
| Help                   | Help C          | 2B00 |

---

## Key Insights

### 1. Character Struct Size

Based on offsets, character state struct is at least **0x102+ bytes** (~260+
bytes). Fields are scattered (not contiguous):

- 0x78 = ground state
- 0x88 = positive status
- 0xA0 = negative status
- 0xD9 = jump count
- 0xDA = air action count
- 0x102 = defense timer

### 2. HP Address Pattern

Player HP addresses: 0x021DF1D5, 0x021DF225, 0x021DF275, 0x021DF2C5

- Spacing: 0x50 (80 bytes) between players
- This suggests a **battle player struct of ~80 bytes**

### 3. Koma ID Encoding

Koma IDs appear to be indices into koma.bin × 12 (entry size):

- Goku 1-koma: 0x1738 = 5944
- 5944 / 12 = 495.3... (not exact)
- Possibly: base_offset + koma_entry × 12

### 4. Pointer-Based State Access

Wifi codes use `B2XXXXXX` (pointer load) followed by offset writes. This
reveals:

- Local battle: direct addresses
- Wifi battle: pointer-indirect (different RAM layout)

---

## Research Applications

1. **Find character struct in ARM9**: Search for code loading from offsets 0x78,
   0xA0, 0xD9
2. **Map HP calculation**: Breakpoint on 0x021DF1D5 writes
3. **Decode koma.bin fully**: Cross-reference koma IDs with known characters
4. **Trace jump mechanics**: Watch 0xD9 offset changes
5. **Understand defense system**: Monitor 0x102 timer decrements

---

## NEW DISCOVERIES (from expanded cheat code research)

### Position/Coordinate System

From teleport codes, the position system uses these addresses:

| Address    | Purpose                                           |
| ---------- | ------------------------------------------------- |
| 0x020A3A6C | Player state pointer (used for position tracking) |
| 0x02181AF8 | Player 1 base coordinates pointer                 |
| 0x02181BDC | Player 2 base reference                           |

**Player Position Offsets (from base 0x02181AF8):**

| Offset | Purpose                   |
| ------ | ------------------------- |
| 0x40   | Player 1 X position       |
| 0x44   | Player 1 Y position       |
| 0x48   | Player 1 direction/facing |
| 0x80   | Player 3 X position       |
| 0x84   | Player 3 Y position       |
| 0xC0   | Player 4 X position       |
| 0xC4   | Player 4 Y position       |

**Player Direction Offsets (from base 0x02181BDC):**

| Offset | Player | Purpose        |
| ------ | ------ | -------------- |
| 0x10C  | P2     | Direction byte |
| 0x218  | P3     | Direction byte |
| 0x324  | P4     | Direction byte |

**Direction Values:**

- 0x13 = Facing Right (standing)
- 0x93 = Facing Left (standing)
- 0x01 = Jumping Right
- 0x81 = Jumping Left

---

### Character Abilities System (Help Koma Stats)

Discovered at address `0x021DF1D6`:

| Address               | Size | Purpose                         |
| --------------------- | ---- | ------------------------------- |
| 0x021DF1D6            | 1    | Abilities count (max 0x21 = 33) |
| 0x021DF1D7            | 1    | First ability ID                |
| 0x021DF1D8-0x021DF1E8 | 20   | Additional ability ID array     |

**Complete Ability ID List:**

| ID   | Effect                                                |
| ---- | ----------------------------------------------------- |
| 0x01 | Triple Jump                                           |
| 0x02 | Wall Jump                                             |
| 0x03 | Air Dash                                              |
| 0x04 | Use SP Gauge to Auto-Guard                            |
| 0x05 | Increase SP Gauge when blocking at last moment        |
| 0x06 | Never move when blocking on moving platform           |
| 0x07 | Max Health increases when respawning from KO          |
| 0x08 | Status effect duration reduced                        |
| 0x09 | Decreases damage from Punches and Kicks               |
| 0x0A | Decreases damage from Blades                          |
| 0x0B | Unknown                                               |
| 0x0C | Unknown                                               |
| 0x0D | Decreases damage from Special Attacks                 |
| 0x0E | Attack-Up when health is low                          |
| 0x0F | Gain 1 Special bar when KO'd                          |
| 0x10 | Gain more SP from Coins                               |
| 0x11 | Unknown                                               |
| 0x12 | Gain more Health from Food                            |
| 0x13 | Unknown                                               |
| 0x14 | Unknown                                               |
| 0x15 | Unknown                                               |
| 0x16 | Increase Guard strength                               |
| 0x17 | Unknown                                               |
| 0x18 | Unknown                                               |
| 0x19 | Immunity to Shock                                     |
| 0x1A | Immunity to Freeze                                    |
| 0x1B | Immunity to Burn                                      |
| 0x1C | Immunity to Confusion                                 |
| 0x1D | Immunity to Poison                                    |
| 0x1E | Immunity to Judgment                                  |
| 0x1F | Immunity to Paralysis                                 |
| 0x20 | Immunity to Blindness                                 |
| 0x21 | Immunity to Speed-Down                                |
| 0x22 | Immunity to Battle/Support Seal                       |
| 0x23 | See Invisible characters                              |
| 0x24 | Unknown                                               |
| 0x25 | Unknown                                               |
| 0x26 | Increase SP when attacking/blocking Battle Character  |
| 0x27 | Increase SP when attacking/blocking chain attacks     |
| 0x28 | SP regenerates when idle                              |
| 0x29 | Increase SP when multi-hitting                        |
| 0x2A | Increase SP when breaking Item boxes                  |
| 0x2B | Increase SP when attacking/blocking at low health     |
| 0x2C | SP regenerates without character switching            |
| 0x2D | Increase SP when KO'ing opponent                      |
| 0x2E | Increase SP when attacking/blocking Support Character |
| 0x2F | Increase SP against opposing nature Characters        |
| 0x30 | Increase SP when using multiple Specials quickly      |

---

### SP/Special Gauge Addresses

| Address    | Size | Purpose                        | Source               |
| ---------- | ---- | ------------------------------ | -------------------- |
| 0x020ADAD8 | 4    | Battle state check (SP codes)  | Max/Inf Special      |
| 0x020A282C | 4    | SP gauge base pointer          | Max/Inf Special      |
| 0x000008B0 | -    | SP gauge offset (from pointer) | Max/Inf Special      |
| 0x02172960 | 4    | Character state pointer (alt)  | Infinity Symbol code |
| 0x00000CD2 | 1    | Power/SP flag offset           | Infinity Symbol code |

---

### Character Modifier System

Used for "Play As" character swap codes:

| Address    | Size | Purpose                    |
| ---------- | ---- | -------------------------- |
| 0x021DF1F0 | 4    | Character pointer (leader) |
| 0x021DF1F8 | 4    | Character state flags      |
| 0x021DF1FD | 1    | Character koma size        |

**Example Character Pointers:**

- Vegeto: 0x021ADC98

---

### Expanded Gem/Currency Addresses

| Address    | Size | Purpose    |
| ---------- | ---- | ---------- |
| 0x020B76C8 | 4    | Gem type 1 |
| 0x020B76CC | 4    | Gem type 2 |
| 0x020B76D0 | 4    | Gem type 3 |
| 0x020B76D4 | 4    | Gem type 4 |
| 0x020B76D8 | 4    | Gem type 5 |
| 0x020B76DC | 4    | Gem type 6 |

Note: Spacing is 4 bytes per gem type.

---

### Stage/Course Unlock (Extended)

| Address    | Size | Purpose                       |
| ---------- | ---- | ----------------------------- |
| 0x020B0C93 | 4    | Course unlock flags (primary) |
| 0x020B0C94 | 4    | Stage flags (secondary)       |
| 0x020B0C98 | 1    | Additional stage flags        |

---

### Alternative Health Code (ASM Injection)

For advanced hacking, health can be modified via code injection:

| Address               | Purpose                               |
| --------------------- | ------------------------------------- |
| 0x021548E2            | Health calculation instruction (ARM9) |
| 0x023FBFC0-0x023FBFD0 | Code injection area                   |
| 0x020543C0            | Enable code flag                      |

---

### Alternative Player State Pointer

| Address    | Purpose                                          |
| ---------- | ------------------------------------------------ |
| 0x023D2A74 | Alternative player state base (ground/air codes) |

Used with offset 0x10 to reach character struct, then standard offsets apply.

---

### Additional Complete Koma ID List

Extended from original findings:

| Character    | 1K   | 2K     | 3K   | 4K        | 5K        | 6K        | 7K   | 8K        |
| ------------ | ---- | ------ | ---- | --------- | --------- | --------- | ---- | --------- |
| Tsuna        | 04C0 | 04CC   | 04D8 | 04E4      | 04F0      | 04FC,0508 | -    | -         |
| Kagura       | 06F4 | 0700   | 070C | 0718      | 0724      | 0730,073C | -    | -         |
| Kinnikuman   | 085C | 0868   | 0874 | 0880,088C | 0898      | 08A4      | 08B0 | 08BC      |
| Ryotsu       | 09DC | 09E8   | 09F4 | 0A00,0A0C | 0A18      | 0A24      | 0A30 | 0A3C      |
| Edajima      | 0C10 | -      | -    | -         | -         | -         | -    | 0C1C      |
| Momotaro     | 0C28 | 0C34   | 0C40 | 0C4C      | 0C58      | 0C64,0C70 | -    | -         |
| Yoh          | 0D9C | 0DA8   | 0DB4 | 0DC0,0DCC | 0DD8      | 0DE4      | -    | -         |
| Anna         | 0DF0 | 0DFC   | 0E08 | 0E14      | 0E20,0E2C | -         | -    | -         |
| Jotaro       | 0EE0 | 0EEC   | 0EF8 | 0F04      | 0F10,0F1C | 0F28      | -    | -         |
| Seiya        | 1114 | 1150   | 115C | 1168      | 1174      | 1180      | 118C | 1198      |
| Allen        | 13E4 | 13F0   | 13FC | 1408      | 1414      | 1420,142C | -    | -         |
| Lenalee      | 1438 | 1444   | 1450 | 145C      | 1468      | -         | -    | -         |
| Arale        | 15C4 | 15D0   | 15DC | 15E8      | 15F4      | 1600,160C | 1618 | -         |
| Dr.Mashirito | 1624 | 1630   | 163C | 1648,1654 | 1660      | 166C      | 1678 | 1684      |
| Gohan        | 17F8 | 1804   | 1810 | 181C      | 1828      | -         | -    | -         |
| Gotenks      | 1834 | 1840   | 184C | 1858      | 1864,1870 | -         | -    | -         |
| Piccolo      | 187C | 1888   | 1894 | 18A0      | 18AC      | -         | -    | -         |
| Frieza       | 18B8 | 2B78\* | -    | -         | -         | 18C4      | -    | -         |
| Boo          | 18D0 | -      | -    | -         | -         | 18DC,18E8 | -    | -         |
| Sasuke       | 19D8 | -      | -    | -         | -         | -         | 19E4 | 19F0,19FC |
| Sakura       | 1A08 | 1A14   | 1A20 | 1A2C      | 1A38      | 1A44,1A50 | -    | -         |
| Kakashi      | 1A5C | 1A68   | 1A74 | 1A80      | 1A8C      | 1A98,1AA4 | -    | -         |
| Fuusuke      | 1B04 | 1B10   | 1B1C | 1B28      | 1B34,1B40 | -         | -    | -         |
| Gon          | 1B64 | 1B70   | 1B7C | 1B88      | 1B94      | 1BA0      | -    | -         |
| Killua       | 1BAC | 1BB8   | 1BC4 | 1BD0      | 1BDC      | -         | -    | -         |
| Jaguar       | 1C6C | 1C78   | 1C84 | 1C90      | 1C9C      | 1CA8      | -    | -         |
| Kazuki       | 1D44 | 1D50   | 1D5C | 1D68      | 1D74      | 1D80      | -    | -         |
| Eve          | 1DB0 | 1DBC   | 1DC8 | 1DD4      | 1DE0      | -         | -    | -         |
| Rukia        | 1ED0 | 1EDC   | 1EE8 | 1EF4      | 1F00      | 1F0C      | -    | -         |
| Renji        | 1F18 | 1F24   | 1F30 | 1F3C      | 1F48      | 1F54      | -    | -         |
| Hitsugaya    | 1F60 | 1F6C   | 1F78 | 1F84      | 1F90      | 1F9C      | -    | -         |
| Taikoubou    | 20E0 | 20EC   | 20F8 | 2104      | 2110      | 211C,2128 | -    | -         |
| Kenshiro     | 2170 | 217C   | 2188 | 2194      | 21A0      | 21AC      | 21B8 | 21C4      |
| Raoh         | 21D0 | -      | -    | -         | -         | 21E8      | 21F4 | 2200      |
| BoBoBo       | 226C | 2278   | 2284 | 2290      | 229C      | 22A8,22B4 | 22C0 | -         |
| Don Patch    | 22CC | 22D8   | 22E4 | 22F0      | 22FC      | 2308      | 2314 | -         |
| Neuro        | 23F8 | 2404   | 2410 | 241C,2428 | 2434      | -         | -    | -         |
| Muhyo        | 24B8 | 24C4   | 24D0 | 24DC      | 24E8      | 24F4      | 2500 | -         |
| Yugi         | 25B4 | 25C0   | 25CC | 25D8      | 25E4      | 25F0      | -    | -         |
| Yusuke       | 2644 | 2650   | 265C | 2668      | 2674      | 2680      | -    | -         |
| Kurama       | 268C | 2698   | 26A4 | 26B0      | 26BC      | -         | -    | -         |
| Hiei         | 26C8 | 26D4   | 26E0 | 26EC      | 26F8      | -         | -    | -         |
| Zoro         | 28FC | 2908   | 2914 | 2920      | 292C,2938 | 2944      | -    | -         |
| Nami         | 2950 | 295C   | 2968 | 2974,2980 | 298C      | 2998      | -    | -         |
| Sanji        | 29A4 | 29B0   | 29BC | 29C8      | 29D4,29E0 | 29EC      | -    | -         |
| Nico Robin   | 29F8 | 2A04   | 2A10 | 2A1C      | 2A28      | 2A34      | -    | -         |
| Franky       | 2A40 | 2A4C   | 2A58 | 2A64      | 2A70,2A7C | -         | -    | -         |

\*Note: Frieza 2B78 is a beta 2-koma support variant

---

## Verification Checklist

- [ ] Confirm character state pointer addresses in emulator
- [ ] Test offset 0x78 for ground/air detection
- [ ] Verify koma ID → character mapping
- [ ] Find where character struct is allocated
- [ ] Trace HP damage path from 0x020784FC
- [ ] Test position offsets 0x40/0x44 for coordinate manipulation
- [ ] Verify ability ID assignments in battle
- [ ] Map SP gauge addresses in different battle modes
- [ ] Cross-reference teleport addresses with character struct
