# Yoh Asakura — Character Research Notes

- **Source guide**: Untitled ASCII-art-headed Jump Ultimate Stars character FAQ (Yoh Asakura FAQ)
- **Author**: Danoh1989 (Daniel Adamic)
- **Version**: 1.0 (Jan. 25th)
- **GameFAQs FAQ ID**: gf-46755
- **Note**: Unverified community source (fan-authored guide, not verified against game data/disassembly).

## Evolution Chart (Koma Forms)

```
     -[S2]----[S3]
    |
[H]---[B4]----[B5]----[B6]
    |
     -[B4A]
```

- Help Koma, Support 2, Support 3, Battle 4, Battle 5, Battle 6, and Battle 4A (alt form) koma exist per this chart.
- Only Anna receives an ally boost from Yoh (per author).

## Help/Support Koma

- **Help Koma**, shape: single cell `[]`. Effect: Attack up when health is low. (No numeric threshold or magnitude given.)
- **Support Koma 2** (Knowledge), shape: 2-cell horizontal `[][]`. Yoh slashes, releasing a wind-blade projectile that travels until it hits something.
  - Damage: 22 vs Power/Knowledge, 33 vs Laughter.
- **Support Koma 3** (Laughter), shape: 1 cell over 2-cell (3 cells total, L-shape). Yoh + Amidamaru (orange ball) throw, causing "movement down" (spike/meteor effect) on impact.
  - Damage: 20 vs Knowledge/Laughter, 30 vs Power.

## Battle Koma — Passive/Innate Abilities
- Cannot be moved while guarding.
- Using Yoh-related support koma raises SP.

## Basic Moveset

Two damage sets are given per move: default (4-Koma base / most forms) vs. "alt 4 koma" (the Knowledge/Laughter-swapped Battle 4A form) — the alt form swaps which nature takes the higher damage.

- **B**: quick horizontal slash. 8 to Power/Knowledge, 12 to Laughter. (Alt 4 Koma: 8 to Knowledge/Laughter, 12 to Power.)
- **Forward+B**: forward thrust step. Same damage numbers as B (8/12 pattern as above).
- **Up+B**: upward sword thrust. Same 8/12 damage pattern.
- **Down+B**: brief startup (green/yellow lines), forward slash, forces character switch. Same 8/12 damage pattern.
- **Y**: vertical slash, slight knockback on unguarded opponent. 16 to Power/Knowledge, 24 to Laughter (alt: 16 Knowledge/Laughter, 24 Power). Author notes: has a lot of ending lag as a standalone move.
- **Forward+Y**: sword slash releasing a forward-traveling wind blade (same projectile as the 2-Koma support); disappears at screen edge. 15 to Power/Knowledge, 22 to Laughter (alt: 15 Knowledge/Laughter, 22 Power).
- **Up+Y**: jump + 360-degree midair slash. 16 to Power/Knowledge, 24 to Laughter (alt swapped). Good setup for aerial follow-up.
- **Down+Y**: red-line startup, jump forward, downward slash; guard break. 16 to Power/Knowledge, 24 to Laughter (alt swapped). Described as "one of the quicker guard breaks."
- **A+B** (air): horizontal midair slash. 8 to Power/Knowledge, 12 to Laughter (alt swapped).
- **A+Y** (air): diagonal dive-bomb slash. 16 to Power/Knowledge, 24 to Laughter (alt swapped). Author warns of edge/ringout risk when used near stage edges.

## Battle Koma Specials

### 4 Koma (Knowledge or Laughter variant)
- J-Soul: 152
- Boosted by: Anna, Manta, Joseph Joestar (Jojo's Bizarre Adventure)
- Shapes: 2x2 square, or 1-cell-over-3-cell L-shape (two different 4-Koma forms noted)
- Ultimate Action: lies down and sleeps; recovers SP very slowly.
- **Special A**: forward thrust similar to Forward+B but stronger; Knowledge-based damage, easy to combo into.
  - Damage: 32 vs Power/Knowledge, 48 vs Laughter.
- **Special B**: Amidamaru throw causing "movement down" on impact; disappears at screen edge; Laughter-based damage. Same numbers as the Support 3 koma.
  - Damage: 20 vs Knowledge/Laughter, 30 vs Power.

### 5 Koma (Knowledge)
- J-Soul: 168
- Boosted by: Anna, Manta, Joseph Joestar
- Shape: two separate cells over a 3-cell row (5 cells total)
- Ultimate Action: same sleep/slow-SP-recovery as above.
- **Special A**: summons a huge sword overhead, vertical slash creating a large shockwave that persists to screen edge and passes through multiple enemies (hits through guard, per author: "even goes through a blocking enemy").
  - Damage: 32 vs Power/Knowledge, 48 vs Laughter.
- **Special B**: sword extends into a "power pole," multi-hit poke attack.
  - Max damage: 36 vs Power/Knowledge, 54 vs Laughter. Author notes the multi-hit structure means max damage is rarely achieved in practice, and the move has no launch/knockback.

### 6 Koma (Knowledge)
- J-Soul: 184
- Boosted by: Anna, Hao, Amidamaru
- Shape: 3x2 rectangle
- Note: distinct sprite — different armguard art, longer sword reach (visual/hitbox-relevant detail).
- Ultimate Action: same sleep/slow-SP-recovery.
- **Special A**: forward thrust; on hit, follow-up diagonal jump strike carrying the opponent upward; second hit applies Blind.
  - 1-hit damage: 10 vs Power/Knowledge, 15 vs Laughter.
  - 2-hit damage: 34 vs Power/Knowledge, 51 vs Laughter.
- **Special B**: multi-hit summon attack (up to 5 hits if fully connected), knocks opponent back toward the user for follow-up setups.
  - Max damage: 48 vs Power/Knowledge, 72 vs Laughter.

## Mechanic-Revealing Observations
- Two 4-Koma variants exist with swapped Nature typing (Knowledge vs Laughter) that mirror the damage-vs-nature assignment — same pattern seen in Gintoki's dual 6-Koma forms, suggesting this "nature-swapped twin Koma" design recurs across characters.
- Charging/comboing removes ending lag: chaining Y into Forward+Y is explicitly said to eliminate the ending-lag window that exists when Y is thrown alone — direct evidence that individual moves carry recovery frames that can be cancelled by transitioning into another attack.
- 5-Koma Special A hits through a blocking opponent (guard-piercing behavior) and can hit multiple enemies in one swing — distinguishes it from typical guarded/blockable attacks.
- Innate ability "cannot be moved while guarding" implies normal characters CAN be pushed/displaced while guarding by default — Yoh is an exception to that base mechanic.
