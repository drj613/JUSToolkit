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
Base pointers: `0x021E2A7C`, `0x021E2A80`, `0x021E2A84`, `0x021E2A88` (4 players)

### Character State Offsets

| Offset | Size | Field | Source Code |
|--------|------|-------|-------------|
| 0x0078 | 1 | Ground/Air state | "Always on Ground/Air" |
| 0x0088 | 1 | Positive status ID | "Have Positive Status" |
| 0x00A0 | 1 | Negative status flags | "Immune to negative status" |
| 0x00D9 | 1 | Jump counter | "Infinite Jumps" |
| 0x00DA | 1 | Air action counter | "Infinite Air Actions" |
| 0x0102 | 1 | Defense duration | "Defense never wears" |

### Ground/Air State Values

- `0x00` = In Air
- `0x22` = On Ground

### Positive Status IDs

- `0x00` = Nothing
- `0x09` = Invincibility (visual only?)

---

## Battle State Addresses

| Address | Size | Purpose | Source |
|---------|------|---------|--------|
| 0x021DEA70 | 2 | Battle timer (wifi) | "Push time back to 99" |
| 0x021DEA71 | 1 | Battle timer (local) | "Unlimited Time" |
| 0x021DF1D5 | 1 | Player 1 HP | "Leader Refill Health" |
| 0x021DF225 | 1 | Player 2 HP | "Non-leader Refill Health" |
| 0x021DF275 | 1 | Player 3 HP | "Infinite Health (4P)" |
| 0x021DF2C5 | 1 | Player 4 HP | "Infinite Health (4P)" |
| 0x021DF731 | 1 | Special meter 1 | "Unlimited Special" |
| 0x021DF8B1 | 1 | Special meter 2 | "Unlimited Special" |
| 0x021DB611 | 1 | Koma sprite (glitch) | "Glitch Battle Koma Sprites" |
| 0x021DB609 | 1 | Koma sprite (glitch) | "Glitch Battle Koma Sprites" |

### Wifi Battle State

| Address | Size | Purpose |
|---------|------|---------|
| 0x021E29B0 | 2 | Wifi battle timer |
| 0x021E2A7C | 4 | Player 1 state pointer |
| 0x021E2A80 | 4 | Player 2 state pointer |
| 0x021E2A84 | 4 | Player 3 state pointer |
| 0x021E2A88 | 4 | Player 4 state pointer |

---

## Deck/Menu Addresses

| Address | Size | Purpose | Source |
|---------|------|---------|--------|
| 0x020AFEB4 | 4 | Active deck index | "Use deck XX" |
| 0x020B0BAC | array | Koma unlock flags | "Unlock all komas" |
| 0x020B0C93 | 4 | Course unlock flags | "Unlock all courses" |
| 0x0228AAB0-C4 | 6×4 | Side koma holder | "Fill side komas" |

### Deck Index Values

| Value | Deck |
|-------|------|
| 0x00 | Deck 1 |
| 0x08 | Deck 9 |
| 0x0F | Deck 16 |
| 0x10 | Deck 17 |
| 0x13 | Deck 20 |

---

## Currency/Progress

| Address | Size | Purpose |
|---------|------|---------|
| 0x020B76C8 | 4 | Koma points |
| 0x020B76F0 | 4 | Koma points (alt?) |
| 0x020B7718-7720 | 3×4 | Gems (type 1-3) |
| 0x020B7724-772C | 3×4 | Gems (type 4-6) |
| 0x020B7768-77E0 | 7×4 | Additional currency |

---

## Character Palette/Color

Base pointer: `0x023D7B00`

| Offset | Size | Purpose |
|--------|------|---------|
| 0x02-22 | 2 each | Palette entries (BGRR format) |

---

## Koma ID Table (from "Fill Side Komas" code)

The XXXX values in `021eXXXX` are koma IDs. Pattern analysis:

### Structure

Each character has sequential koma IDs for different sizes:
- IDs are spaced 0x0C (12) apart
- Base ID + (koma_size - 1) * 0x0C ≈ koma variant

### Complete Koma ID List

| Character | 1-koma | 2-koma | 3-koma | 4-koma | 5-koma | 6-koma | 7-koma | 8-koma |
|-----------|--------|--------|--------|--------|--------|--------|--------|--------|
| Goku | 1738 | 1744 | 1750 | 175C,1768 | 1774 | 1780 | 178C | 1798 |
| Ichigo | 1E70 | 1E7C | 1E88 | 1E94 | 1EA0 | 1EAC | 1EB8 | 1EC4 |
| Naruto | 196C | 1978 | 1984 | 1990,199C | 19A8 | 19B4 | 19C0 | 19CC |
| Luffy | 2890 | 289C | 28A8 | 28B4 | 28C0 | 28CC,28D8 | 28E4 | 28F0 |
| Vegeta | 17A4 | 17B0 | 17BC | 17C8 | 17D4,17E0 | 17EC | - | - |
| Gintoki | 0694 | 06A0 | 06AC | 06B8 | 06C4 | 06D0,06DC | 06E8 | - |
| Kenshin | 2740 | 274C | 2758 | 2764 | 2770 | 277C,2788 | - | - |
| Dio | 0F34 | 0F40 | 0F4C | 0F58 | 0F64,0F70 | 0F7C | - | - |
| Train | 1DEC | 1DF8 | 1E04 | 1E10 | 1E1C,1E28 | - | - | - |

### Beta/Debug Komas

| Type | Koma | ID |
|------|------|-----|
| Battle (4-koma square) | Red Koma Man | 2B30 |
| Battle | Green Koma Man | 2B3C |
| Battle | Yellow Koma Man | 2B48 |
| Battle | Taizo Mote | 2BB4 |
| Support (2-koma) | Frieza | 2B78 |
| Support | Buu | 2B84 |
| Support | Sasuke | 2B90 |
| Support | Raoh | 2B9C |
| Support | Edajima | 2BA8 |
| Support | Caramel J Man | 2BCC |
| Help | Help A | 2AE8 |
| Help | Help B | 2AF4 |
| Help | Help C | 2B00 |

---

## Key Insights

### 1. Character Struct Size

Based on offsets, character state struct is at least **0x102+ bytes** (~260+ bytes).
Fields are scattered (not contiguous):
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

Wifi codes use `B2XXXXXX` (pointer load) followed by offset writes.
This reveals:
- Local battle: direct addresses
- Wifi battle: pointer-indirect (different RAM layout)

---

## Research Applications

1. **Find character struct in ARM9**: Search for code loading from offsets 0x78, 0xA0, 0xD9
2. **Map HP calculation**: Breakpoint on 0x021DF1D5 writes
3. **Decode koma.bin fully**: Cross-reference koma IDs with known characters
4. **Trace jump mechanics**: Watch 0xD9 offset changes
5. **Understand defense system**: Monitor 0x102 timer decrements

---

## Verification Checklist

- [ ] Confirm character state pointer addresses in emulator
- [ ] Test offset 0x78 for ground/air detection
- [ ] Verify koma ID → character mapping
- [ ] Find where character struct is allocated
- [ ] Trace HP damage path from 0x020784FC
