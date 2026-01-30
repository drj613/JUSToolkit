# Deck System Research

Documentation of the Jump Ultimate Stars deck building system.

## Deck Grid

- **Grid size:** 5 columns × 4 rows (20 total cells)
- **Panels placed on grid** called "koma" (Japanese for "cell" or "panel")

## Panel Types (Koma Sizes)

| Type | Koma Size | Description |
|------|-----------|-------------|
| Helper | 1 | Passive effects, every character has at least one |
| Support | 2-3 | Support attacks, most characters have these |
| Battle | 4-8 | Playable fighters with full movesets |

## Panel Shapes

Panels come in various shapes, not just rectangles.

**Example:** Naruto has two 4-koma panels:
- Vertical line (4×1) - Power nature (default)
- Square (2×2) - Laughter nature (alternate)

Note: Nature variants use the same battle character data but different natures for deck bonuses. The special attacks still use the base nature (Power in Naruto's case).

## Deck Builder Organization

The deck builder shows ALL panel types mixed together, organized by **manga series**.

### Complete Series Order (in deck builder)

| # | Series | Has Battle? | Prefix |
|---|--------|-------------|--------|
| 1 | Eyeshield 21 | No | es |
| 2 | I"s | No | is |
| 3 | Ichigo 100% | No | ig |
| 4 | Katekyo Hitman Reborn | Yes | tr |
| 5 | Captain Tsubasa | No | ct |
| 6 | Gintama | Yes | gt |
| 7 | Kinnikuman | Yes | kn |
| 8 | KochiKame | Yes | kk |
| 9 | Cobra | No | cb |
| 10 | Sakigake Otokojuku | Yes | oj |
| 11 | Hell Teacher Nube | No | nb |
| 12 | Shaman King | Yes | sk |
| 13 | Jungle King Taa-chan | No | tl |
| 14 | JoJo's Bizarre Adventure | Yes | jj |
| 15 | Slam Dunk | No | sd |
| 16 | Saint Seiya | Yes | ss |
| 17 | Taizo Mote King Saga | Debug | tz |
| 18 | Prince of Tennis | No | to |
| 19 | D.Gray-man | Yes | dg |
| 20 | Death Note | No | dn |
| 21 | Dr. Slump | Yes | ds |
| 22 | Tottemo Lucky Man | No | tl |
| 23 | Dragon Ball | Yes | db |
| 24 | Naruto | Yes | na |
| 25 | Ninku | Yes | nk |
| 26 | Hunter x Hunter | Yes | hh |
| 27 | Pyuu to Fuku Jaguar | Yes | pj |
| 28 | Busou Renkin | Yes | bu |
| 29 | Black Cat | Yes | bc |
| 30 | Bleach | Yes | bl |
| 31 | Houshin Engi | Yes | hs |
| 32 | Fist of the North Star | Yes | hk |
| 33 | Bobobo-bo Bo-bobo | Yes | bb |
| 34 | Majin Tantei Nougami Neuro | Yes | nn |
| 35 | Midori no Makibao | No | mo |
| 36 | Muhyo and Roji's Bureau | Yes | mr |
| 37 | Yu-Gi-Oh! | Yes | yo |
| 38 | Yu Yu Hakusho | Yes | yh |
| 39 | Rurouni Kenshin | Yes | rk |
| 40 | Rokudenashi Blues | No | rb |
| 41 | One Piece | Yes | op |
| 42 | Meta/Debug | Debug | dt |

The last character in One Piece is **Kiwi/Mozu**.

### Character Order Within Series

Within each series, characters always appear in a fixed order:
1. First character's helper (1-koma)
2. First character's supports (2-3 koma)
3. First character's battle panels (4-8 koma)
4. Second character's helper
5. Second character's supports
6. Second character's battle panels
7. ... and so on

**Example: Dragon Ball**
| Entry | Character | Type | Koma |
|-------|-----------|------|------|
| 1 | Goku | Helper | 1 |
| 2 | Goku | Support | 2 |
| 3 | Goku | Support | 3 |
| 4 | Goku | Battle | 4 |
| 5 | Goku | Battle | 5 |
| 6 | Goku (SSJ) | Battle | 6 |
| 7 | Goku (SSJ) | Battle | 7 |
| 8 | Vegetto | Battle | 8 |
| ... | ... | ... | ... |

### Debug Characters

Only accessible via hacking:
- Komaman (Red, Yellow, Green)
- Taizo (can only move, no attacks)
- Unfinished support characters
- Debug helpers (e.g., infinite SP helper)

## Helper Mechanics

- Most helpers require **pointing** at a specific battle character to apply their passive
- Only exception: +1 SP helpers affect the whole deck
- Helpers are 1-koma panels

## Support Mechanics

- 2-3 koma panels
- Called in during battle to perform a support attack

## Battle Character Mechanics

- 4-8 koma panels
- Fully playable with complete movesets
- Panel artwork is manga panels from source material translated into shapes

## Notable Exceptions

**Characters with hidden/debug supports:**
- Sasuke
- Frieza

These supports exist but:
- Hidden in debug category at bottom of list
- No panel art (appear as black spaces)
- Make decks "invalid" and unusable in pre-match selector

## Technical Notes

### koma.bin Structure

Each entry (12 bytes) contains:
- `image_id` (offset 0-1): Links to panel image
- `letters` (offset 4): Series/manga index
- `number` (offset 5): Panel index within series

The `letters` field appears to be the series identifier, incrementing for each manga:
- letters=1: First series (Eyeshield 21?)
- letters=2: Second series
- etc.

### Relationship to chr_b.bin

Battle character stats (chr_b.bin) are organized separately from koma data:
- chr_b.bin: 74 battle character stat entries
- koma.bin: 890 panel entries (all helpers, supports, and battle panels)
- Multiple koma entries can reference the same battle character (different panel shapes/sizes)
