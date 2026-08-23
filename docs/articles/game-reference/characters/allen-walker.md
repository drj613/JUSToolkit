# Allen Walker

- Source guide: "Jump! Ultimate Stars: Allen Walker FAQ"
- Author: Syfex Blade (guide's legal footer names copyright holder as Logan Murry)
- Version: 1.0 (2007)
- GameFAQs FAQ id: gf-47453
- Note: unverified community source; numbers below are as reported by the guide author and have not been independently verified against the game.

Damage is generally listed as `X (Y to Laughter)` where X = base damage and Y = damage vs. Laughter-nature targets, reflecting Allen's Knowledge-type advantage (except the Power-variant 6-koma, noted separately).

## Evolution chart

Text-rendered evolution tree:
```
    |-[S2]-[S3]
    |
[H]-|-[B4]-[B5]-|-[B6]
                |
                |-[B6]
```
(H=Help, S=Support, B=Battle koma; numbers = koma-space size)

## Passive traits
1. Can see invisible characters.
2. Immune to Blindness status.
3. Gains SP when using any support koma related to Allen (e.g., Kanda, Lenalee, Cross).

## Support boost relationships
- Allen is boosted by: Lenalee, Kanda, Cross.
- Allen boosts: Lenalee only.
- Cross's Help koma: regenerates SP so long as the player does not swap characters out (author recommends it highly).
- Kanda's Help koma: reduces damage taken from "Blade" attacks (author calls it "pretty useless").

## Base moveset (applies across forms; damage vs. Laughter in parens)

| Input | Damage |
|---|---|
| B | 8 (12 to Laughter) |
| Forward + B | 8 (12 to Laughter) |
| Aerial + B | 8 (12 to Laughter) |
| Y | 12 (18 to Laughter) |
| Forward + Y | 12 (18 to Laughter) |
| Aerial + Y | 12 (18 to Laughter) |

- Forward + Y can be charged to deal 36 (54 to Laughter) damage.
- Select input: summons "Timcanpi" (Allen's companion), circles around; on connecting with an opponent, steals a small amount of their SP (author does not give an exact SP-steal amount).

## Help Koma
- Effect: grants immunity to Blindness status.

## Support Koma

### 2-koma Support — "Cross Beam"
- Shape: `[][]`
- Behavior: Allen appears above the player and fires 5 lasers downward.
- Per-laser damage: 4 to Power/Knowledge, 9 to Laughter.
- Cumulative damage by hit count:
  - 1 hit: 4 (9 to Laughter)
  - 2 hits: 8 (18 to Laughter)
  - 3 hits: 12 (27 to Laughter)
  - 4 hits: 16 (36 to Laughter)
  - 5 hits: 20 (45 to Laughter)
- Author notes landing all 5 hits is very difficult (claims to be unable to achieve it even in training mode); realistically 3-4 hits land. Useful as an edge-guard tool against characters hanging on a ledge.

### 3-koma Support — "Cross Grave"
- Shape: `[][][]`
- Behavior: Allen appears directly in front of the player and performs a guard-breaking attack that launches the target upward a good distance.
- Damage: 28 to Power/Knowledge, 42 to Laughter.
- Comes out fast; author claims it is near-guaranteed to connect against an opponent guarding at close range. Downside: the launch height gives the target room to escape before a follow-up combo can land.

## Battle Koma

### 4-koma Allen
- Nature: Knowledge
- J-Soul: 136
- Shape: `[][] / [][]` (2x2)
- Neutral Special (X) — "Cross Beam": fires 5 lasers forward (vs. Support version's downward angle). Cumulative damage by hit count:
  - 1 hit: 8 (12 to Laughter)
  - 2 hits: 16 (24 to Laughter)
  - 3 hits: 24 (36 to Laughter)
  - 4 hits: 32 (48 to Laughter)
  - 5 hits: 40 (60 to Laughter)
  - Author notes: at point-blank range all 5 hits reliably land; combos with Allen's B and Y attacks for a stated total of 60 damage to Power/Knowledge and 90 to Laughter (full combo total, not broken into individual hit values in the source).
- Secondary Special (Up+X) — "Cross Grave": same effect as the 3-koma support (guard break launch).
  - Damage: 30 (45 to Laughter).
  - Requires close range to connect.
- Author's overall verdict: weak J-Soul for a Knowledge character; recommends avoiding this koma unless deck space is constrained.

### 5-koma Allen
- Nature: Knowledge
- J-Soul: 152
- Shape: `[][][] / _[][]` (3 on top row, 2 on bottom, offset)
- Neutral Special (X) — "Cross Beam" (redesigned): straightforward forward-firing beam barrage, single damage value (not hit-count-gated like the 4-koma version).
  - Damage: 42 (63 to Laughter).
  - Can combo into, similar to 4-koma's beam. Loses the downward/edge-guard utility of earlier versions.
- Secondary Special (Up+X) — "Cross Grave": slightly larger hit area than the 4-koma version, easier to combo into.
  - Damage: 38 (57 to Laughter) — 4 more damage than the 4-koma version (per author's explicit comparison).

### 6-koma Allen (Knowledge nature)
- Nature: Knowledge
- J-Soul: 168
- Shape: `_[] / [][] / [][] / _[]` (plus-like/diamond shape, 6 cells)
- Neutral Special (X) — "Destruction Claw": large claw-shaped forward-firing energy beam.
  - Damage: 41 (57 to Laughter).
  - Described as slow to charge but fast-moving once fired; strong ring-out tool, especially against crowds near an edge.
- Secondary Special (Up+X) — "Clown Belt": creates a mass of spinning web-like projections damaging anyone near Allen.
  - Damage: 50 (75 to Laughter).
  - Author calls this Allen's best special in the game; notes it also blocks/absorbs incoming attacks while active (crowd-control/reflect-like property — author unconfirmed precise mechanic, but explicitly stated as "blocks anything coming at you while it's going on").
  - Effective used against falling opponents or from above/below where they don't expect a hit.

### 6-koma Allen (Power variant)
- Nature: Power
- J-Soul: 168 (same as Knowledge variant)
- Shape: `_[] / [][][] / [][]` (7 cells, different layout from Knowledge 6-koma)
- Identical moveset/specials to the Knowledge 6-koma, but nature-swapped: takes extra damage from Laughter instead of Power, and deals extra damage to Knowledge instead of Laughter. (Implies the specials' bonus-damage target becomes Knowledge for this variant, though the guide doesn't restate the numeric bonus table for this swapped case.)
- Author calls this Allen's best overall koma due to removing the common Power-character matchup disadvantage.

## Combos (damage / damage vs. opposing nature)

| Input | Damage (Damage vs. opposing nature) |
|---|---|
| B - Forward+B - Forward+Y | 28 (42) |
| B - Forward+B - Y - Forward+Y | 40 (60) |
| Down+Y - Aerial B - Aerial Y | 34 (51) |
| B - Forward+B - Y - 4-Koma Allen's X | 68 (102) |
| B - Forward+B - Y - 4-Koma Allen's Up+X | 58 (87) |
| B - Forward+B - Y - 5-Koma Allen's Up+X | 66 (99) |
| 2-koma Kanda - 6-koma Allen's X | 59 (71) |
| 2-koma Piccolo - 6-koma Allen's Up+X | 66 (91) |
| 2-koma Gyro - 6-koma Allen's Up+X | 66 (99) |
| B - Y - 3-koma Lavi (support) | 47 (70) |

Notes:
- "Down+Y" is described as Allen's guard-break move, used as a combo starter here.
- The Kanda/Piccolo/Gyro combos rely on those support koma's own guard-break or pull/pop-up properties to set up Allen's specials — evidence that support-koma hitstun/launch states can be chained into a battle character's special moves.

## Recommended support/help synergies (numeric-relevant only)
- 2-koma Kanda: guard break + small pop-up, chains into 6-koma Allen's Up+X.
- 2-koma Gyro: pulls the enemy toward the player, enabling 6-koma Allen specials to connect.
- 2-koma Piccolo: same pull effect as Gyro, shorter range but faster.
- 2-koma Hao: drops food items that heal Allen when collected (amount not specified; can be stolen by opponents).
- 2-koma Josuke: heals; can also turn the target around on hit (author unconfirmed practical value of "healing your enemy for a chance at turning him around").
