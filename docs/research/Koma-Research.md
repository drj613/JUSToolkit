# Koma Research

## DTX 04 - Komas

Research by Pleonex: https://www.youtube.com/watch?v=1KT4u_Kvaws + https://www.youtube.com/watch?v=R2h-UEcO_-k

### Format Description

This format is quite special because several auxiliary files exist:
- **Koma.bin**: Links the .dtx to the KShape file to obtain the shape and image order.
- **KShape**: All sprite information. How to draw the tiles.
- **Arm9.bin**: Although we already have it in Koma.cs, this contains a table with all manga names (NameTable).

### Flow

Deck gives us the koma.bin entry.

**koma.bin** → Gets the koma name using bytes 04 and 05. Looks it up in ARM9 by multiplying letters * 4. The number is used as-is.

**kshape.bin** → We get the initial shape position using the formula. From there we read byte by byte:

- If greater than 0, draw that tile. Otherwise, skip.
- Add 48 to X. If greater than 192, reset to 0 and add 48 to Y.

#### Letters Koma Name Table
```
Address: 0x0209E840
Arm9.bin offset: 0x9E780
Formula: LKN * 4
```

#### Koma.bin

```
Entry ID * 0x0C
Entries are 12 bytes each.

00-01 (short) → image_id (0-889)
04 → letters koma name
05 → number koma name
08 → index group kshape
09 → index element kshape
```

#### KShape

0x14 bytes per image.

1. Take the Index Group KShape, multiply by 4.
2. Read that number, add the Index Element KShape.
3. To position 0x40, add the result of (2) multiplied by 18.

Formula:
```
((index_group * 4) + index_element) + 0x40
```

#### Deck

Entries are 16-bits:
```
00 - 16-bit - ID
03 - 8-bit  - must be 10
```

### Example

```
Koma.bin 0x0 - 0xC: 00 00 01 00 01 00 02 03 00 00 01 30
LKN (0x4) = 01
NKM (0x5) = 00
IGK (0x8) = 00
IEK (0x9) = 00

Arm9.bin 0x9E780 + 01 * 4 = 0x9E784 → "es"
Result: es_00
```

### DTX

Each box has size 48x48 (0x30 x 0x30)
```
06 06 25 00
```
- 25 indicates where that tile starts: 25 * 0x20 (32 decimal = 8 * 8 / 2-bit depth) = 0x4A0 + 0x44 (base position)
- 06 06 → width and height: 6 * 8 = 48

### Implementation

- KShape loop
  - Horizontal tile loop → 192
    - Vertical tile loop → 240
      - Horizontal pixel loop within tile
        - Vertical pixel loop within tile

Implementation steps:

1. Input folder with arm9.bin, koma.bin, komashape.bin and all .dtx files
2. Converter: NodeContainerFormat → NodeContainerFormat
3. Create new NCF
4. Store arm9, koma.bin and komashape.bin in individual variables
5. Iterate through koma.bin
6. Get the .dtx filename using letters koma name and number koma name (looking it up in arm9 using the formula)
7. Get the .dtx from the NCF
8. Get the komashape using index group kshape and index element kshape with its formula
9. Create the new PixelArray using the formula
10. Extract the palette
11. Generate the new file and save it to the NodeContainerFormat
