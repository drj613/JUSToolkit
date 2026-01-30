# Deck Memory Structure Research

Analysis of JUS deck builder memory layout from GDB dumps.

## Memory Regions

| Region | Address Range | Size | Contents |
|--------|--------------|------|----------|
| Deck State | 0x020A0C00 - 0x020A1000 | 1KB | Deck state flags, pointers |
| Deck Data | 0x020A1000 - 0x020A3000 | 8KB | Pointer arrays (NOT raw koma IDs) |
| Deck Extended | 0x020A3000 - 0x020A8000 | 20KB | Additional deck data |
| Deck Index | 0x020A8000 - 0x020B0000 | 32KB | Active deck index (0x020AFEB4) |
| Save/Unlocks | 0x020B0000 - 0x020C0000 | 64KB | Koma master table, unlock flags |
| Koma Holder | 0x0228AA00 - 0x0228B000 | 1.5KB | Runtime koma data |

## Koma Master Table (Save Region)

Located at **0x020B9480** in the save region. Sequential list of all koma IDs as 32-bit little-endian values.

Structure: `[koma_id_1, koma_id_2, koma_id_3, ...]` (4 bytes each)

### Eve Example (Black Cat series)
| Address | Koma ID | Name |
|---------|---------|------|
| 0x020B94C0 | 0x1DB0 | Eve 1-koma |
| 0x020B94C4 | 0x1DB4 | (intermediate) |
| 0x020B94C8 | 0x1DB8 | (intermediate) |
| 0x020B94CC | 0x1DBC | Eve 2-koma |
| 0x020B94D0 | 0x1DC0 | (intermediate) |
| ... | ... | ... |
| 0x020B94E4 | 0x1DD4 | Eve 4-koma |
| 0x020B94F0 | 0x1DE0 | Eve 5-koma |

**Pattern:** Each koma size increments by 0x0C (12). Base ID + (size-1) * 0x0C.

## Known Addresses

| Address | Description | Notes |
|---------|-------------|-------|
| 0x020A0C98 | Deck state flag | Changes when modifying deck |
| 0x020A20F6 | Leader marker area | FD FF when empty, 00 00 when set |
| 0x020AFEB4 | Active deck index | Which deck slot (0-7) is selected |
| 0x020B0BAC | Koma unlock flags | Bitmask of unlocked komas |

## Key Findings

### 1. Deck region stores POINTERS, not raw koma IDs
The deck data region (0x020A1000-0x020A3000) contains pointer arrays, not direct koma ID storage. False positives occur when pointer values happen to contain koma ID byte patterns.

Example at 0x020A1094:
```
e4 18 0a 02 | 20 b0 1d 02 | 6c 3b 7c 02
  pointer     pointer       pointer
```
The `b0 1d` in the middle pointer is NOT Eve 1-koma - it's part of address 0x021DB020.

### 2. Koma master table is in save region
All koma IDs are stored sequentially in the save region starting around 0x020B9480. This is likely the master lookup table.

### 3. Active deck index is in unmapped region
Address 0x020AFEB4 falls between the deck region dumps. Updated dump script to include 0x020A8000-0x020B0000.

## Leader Flag Discovery

Diff between "Eve 4-koma as leader" vs "Eve 4-koma in deck, no leader set":

| Address | With Leader | No Leader | Description |
|---------|-------------|-----------|-------------|
| 0x020A0C98 | 0x05 | 0x07 | Deck state flag (bit 1 = no leader) |
| **0x020A2289** | **0x01** | **0x00** | **Leader boolean flag** |
| 0x020A44EC | 0x01 | 0x00 | Secondary battle char flag |
| **0x020A4368** | **0x023CE6C8** | **0x00000000** | **Pointer to leader koma data** |

### Key Findings

1. **0x020A2289** is the primary leader flag (1 = has leader, 0 = no leader)
2. **0x020A4368** holds a pointer to the leader's runtime koma data structure
3. When Eve 4-koma is leader, pointer = 0x023CE6C8 (runtime memory, not in save data)
4. Deck state at 0x020A0C98 encodes leader status in bit 1

### Eve 4-koma Index Calculation
- Eve 4-koma ID: 0x1DD4
- Position in master table: 0x020B94E4
- Master table base: ~0x020B9480
- **Eve 4-koma index: 25 (0x19)**

## Next Steps

1. Dump runtime koma region (around 0x023C0000-0x023E0000) to see leader koma structure
2. Test with different characters as leader to confirm pointer relationship
3. Map the runtime koma data structure at the pointer address
4. Correlate deck slot positions with koma indices

## Related Files

- `scripts/gdb/dump_deck_binary.gdb` - GDB dump script
- `scripts/analyze_deck_dump.py` - Binary analysis tool
- `docs/research/Cheat-Code-Analysis.md` - Memory addresses from cheats
