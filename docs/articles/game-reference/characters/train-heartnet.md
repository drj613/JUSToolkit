# Train Heartnet (Black Cat) — Character Guide Notes

- Source: "TRAIN HEARTNET CHARACTER FAQ" by FFandMMfan
- Version: 2.0
- GameFAQs FAQ id: gf-46141
- Note: unverified community source (fan-authored, not verified against game code)

## Evolution Chart / Koma Forms

```
    --[S2]--[S3]
    :
[H]---[B4]--[B5P]
          :
          --[B5K]
```
- H = Help Koma (default)
- S2 = Support Koma 2
- S3 = Support Koma 3
- B4 = Battle Koma 4 (Power nature)
- B5P = Battle Koma 5 (Power nature)
- B5K = Battle Koma 5 (Knowledge nature)

## Help Koma

- Effect: grants a nearby targeted character immunity to Shock status (must aim arrow at intended recipient).

## Support Koma

### Support Koma 2 — Shape `[][]`
- Throws a bomb: causes Blindness + damage.
- Damage vs Power: 12, vs Knowledge: 18, vs Laughter: 12

### Support Koma 3 — Shape (L-shape, 3 cells: one on top-right, two on bottom)
- Fires Rail Gun in a straight line, causes Shock. Multi-hit; total damage depends on number of hits connecting (distance-dependent — farther = fewer hits/less damage). Author notes these may be a few points below true max.
- Damage vs Power: 23, vs Knowledge: 34, vs Laughter: 23

## Battle Koma

Passive abilities (always active, no Help Koma needed):
- Wall Jump
- Immune to Shock status effect

All of Train's Special attacks are Power-nature regardless of which Koma is used.

### Battle Koma 4 (Power) — Shape: 2x1 top row of 2, then 2x1 offset below (4 cells total)
- J-Soul (HP): 136
- Nature: Power
- Special A (Rail Gun forward shot, has charge time + lag/recovery after; induces Shock): vs Power 28, vs Knowledge 42, vs Laughter 28
- Special B (charges forward spinning, physical hit with gun; consistent damage unless enemy is guarded/in hit-recovery i-frames): vs Power 31, vs Knowledge 46, vs Laughter 31
- Author opinion (unconfirmed): weaker Rail Gun than 5-Koma versions but more reliable/comboable Special B; recommended for 1v1.

### Battle Koma 5 (Power) — Shape: 2x2 block plus 1 extra cell below-right (5 cells)
- J-Soul: 152
- Nature: Power
- Special A (Rail Gun, charged while held by Saya; large knockback, inflicts Shock): vs Power "Low 50s" (author unconfirmed), vs Knowledge "Mid 70s/Low 80s" (author unconfirmed), vs Laughter "Low 50s" (author unconfirmed)
- Special B (jumps into air at angle, spinning; consistent damage, weaker than Rail Gun): vs Power 32, vs Knowledge 55, vs Laughter 32

### Battle Koma 5 (Knowledge) — Shape: row of 3 + row of 2 (5 cells)
- J-Soul: 152
- Nature: Knowledge
- Special A: same Rail Gun as Power 5-Koma — vs Power "Low 50s" (author unconfirmed), vs Knowledge "Mid 70s/Low 80s" (author unconfirmed), vs Laughter "Low 50s" (author unconfirmed)
- Special B: same move, different numbers — vs Power 35, vs Knowledge 52, vs Laughter 35

### Ultimate Action
- Throws gun into air and catches it. Buffs the standard gunshot moves (Y+Left/Right, Y+Up, aerial Y) from firing 3 hits to 6 hits, but only for the next set of shots fired (single-use buff, consumed after next volley).

## Standard Attacks and Damage

Note (guide's own caveat): figures below are for Power-nature Koma (4 and 5P). For the Knowledge Koma (5K), swap: the heavier damage number applies to Laughter instead of Knowledge (example given: B attacks do 7 to Power and Knowledge, 10 to Laughter, when using Knowledge-nature Train).

- B button attacks: 7 damage vs Power/Laughter, 10 damage vs Knowledge.
  - B+Down (Forced Change Attack, switches opponent's active battle character): long range, can be fired across the screen if opponent is within visible range. Same damage values as other B attacks per the text.
- Y (physical gun hit): 15 damage vs Power/Laughter, 22 vs Knowledge.
- Gunshots (Y+Left/Right, Y+Up, aerial Y): each shot vs Power/Laughter does 5 damage. Vs Knowledge, first shot does 7 damage, and each subsequent shot in the volley does +1 more than the last (shot 2 = 8, shot 3 = 9, etc. — escalating per-hit damage vs Knowledge nature only). Ultimate Action extends a volley from 3 shots to 6. Gunshots ricochet off the ground.
- Y+Down (Guard Break, long range): 14 damage vs Power/Laughter, 21 vs Knowledge.

## Mechanic-Revealing Observations

- "Solid Wall Effect": Rail Gun deals more damage if the enemy is caught in the blast for its full duration (start to end); if the target is far away or near a wall that breaks partway through, they take reduced hits/damage — implies the Rail Gun is a persistent-duration multi-hit beam whose total damage scales with hit-connect count over its lifetime, and terrain (walls) can truncate the beam.
- Aerial Y gunshots fire downward at an angle and bounce/ricochet off the ground back upward (used for "Reflect Shot" setups).
- On ice-floor stages, Train's shots have little inherent knockback normally, but the Rail Gun's knockback becomes drastically stronger on ice, described as very likely to cause a ring-out. This knockback also pushes Train himself backward when he fires it (self-knockback / recoil effect), risking self-ring-out.
- Train cannot launch opponents airborne — none of his moves lift a target more than "a few inches" off the ground (all his hits are grounded/low-launch).
- Guard Break and Forced Change (B+Down) attacks reportedly have about a 1-second charge time before firing, same as other characters' equivalent moves (author states "everyone else's do too").
- After firing the Rail Gun (Special A on any Koma), there is noticeable recovery/lag time leaving Train vulnerable, and he must be grounded to use it (except aerial Y line attacks).

## Support/Help Koma for Other Characters (context, not Train's own kit)

These are Koma from other characters recommended to pair with Train; only numeric ones are extracted:
- Yahiko 2 Koma (Rurouni Kenshin): aerial dive attack; on hit, deals damage and drains 1 SP bar from the target.
- Katsura & Elizabeth, Vegeta, Hyoga, Sena, Ohara, etc.: described only qualitatively (freeze/stop/knockback effects), no numeric values given in source.
