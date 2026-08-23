# Eve — Character Guide Notes

- Source: "Eve Character FAQ v.1.0/v2.0 for Jump! Ultimate Stars on the Nintendo DS"
- Author: Taoto (Brent Flood)
- Version: v.1.0 (initial), updated to v.2.0 with damage numbers added
- GameFAQs FAQ id: gf-46504
- Note: unverified community source; numbers are player-observed, not from game data files.

## Unlock Condition

Unlocked in J-Space, Black Cat world, Mission 1: collect all stars in 40 seconds or less.

## Evolution Chart

Help Koma (free) branches to:
- 2-space Support Koma
- 3-space Support Koma (off the 2-space koma)
- 4-space Battle Koma
- 5-space Battle Koma (off the 4-space koma)
- Black Cat Stage (unlockable stage, off the 5-space koma)

## Koma Shapes

- Help: 1 tile
- 2-support: 2 tiles side by side
- 3-support: 2 tiles across + 1 below (L-shape, 3 total)
- 4-battle: 2x2 block (4 tiles)
- 5-battle: 3 tiles top row + 2 tiles bottom row (5 total)

## Help/Support Koma Effects

**Help Koma**: Grants an extra jump — battle character can jump 3 times instead of 2 (this is also listed as Eve's own passive/Ultimate-related trait below).

**2-space Support Koma**: Eve appears with a shield; a gray tile appears above the player's character's head, halving all damage taken while active.

**3-space Support Koma**: Player selects an opponent on the touch screen; Eve pops up as a "mermaid" behind the target and punches with her hair, then dives back into the ground.
- Damage vs Power/Knowledge: 32
- Damage vs Laughter: 48

## Eve's Passive Abilities

- Health automatically regenerates over time (nanomachine healing).
- Can jump a maximum of 3 times (triple jump) — described as her "second passive ability."

## Ultimate Action

Select — "Super Jump": crouches, sprouts wings, and jumps to the height of a triple jump. Combined with her innate triple jump, this effectively lets her reach the height of 5 jumps total (author's characterization, not a stated numeric height value).

## Move List

| Input | Move | Dmg vs Power/Knowledge | Dmg vs Laughter | Notes |
|---|---|---|---|---|
| Down | Guard (shield from hands) | - | - | Standard block |
| B | Hair punch forward, ~2 character widths range | 7 | 10 | |
| Forward+B | Hair punch forward, ~4 character widths range | 8 | 12 | |
| Up+B | Hair spikes, hits above/beside at close range | 8 | 12 | |
| Down+B | Hand becomes mace, steps forward, attacks | 7 | 10 | Forces opponent character change on hit (standard Down+B behavior) |
| Y | Hand becomes giant knife, steps forward, slashes | 16 | 24 | |
| Forward+Y | Hair thrust ~4 character widths; grabs enemy at 3–4 widths range and throws over her head ~same distance | 14 | 21 | No effect if target too close or too far; sets up follow-up attacks |
| Up+Y | Wings become fist-shaped + Eve's fist; jumping uppercut counted as one hit | 16 | 24 | Launches opponent into the air, sets up aerial Y |
| Down+Y | Giant mallet slam, few steps forward then slam | 16 | 24 | Guard break |
| Aerial B | Hair fist, 45-degree downward punch, same range as Forward+B | 8 | 12 | |
| Aerial Y | Hair fist, straight-ahead punch, reaches near top-screen edge | 16 | 24 | |

Note: like all characters, Eve stops in midair when performing an aerial attack.

## Specials

### 4-koma
**X — Hair-fist barrage**: repeated taps extend duration and move Eve forward. ~7-8 fists onscreen at once, max 10 hits total.
- vs Power/Knowledge: 18 dmg @ 4 hits, 24 dmg @ 7 hits, 30 dmg @ 10 hits (max)
- vs Laughter: 27 dmg @ 4 hits, 36 dmg @ 7 hits, 45 dmg @ 10 hits (max)
- Author notes these are the "most common" hit counts observed through testing (author unconfirmed as exact/guaranteed values).

**Up+X — Feather blades**: raises wing, fires 6 feather blades forward, up to 6 hits.
- vs Power/Knowledge: 5 damage per hit, max 30 total (6 hits x 5)
- vs Laughter: 5 hits deal some damage each totaling toward 37 (guide text is garbled here: "5 hits do 6 damage, number for doing 7 instead, for a total of 37 damage" — author unconfirmed exact per-hit breakdown, only the 37 total is clear)

### 5-koma
**X — Lance dash ("Lance")**: crouches, wings out, hand becomes large lance, dashes forward skewering enemies; enemy flung off lance when Eve stops. Two hits total: skewer + fling. Causes enemy to spin while falling (ring-out utility).
- vs Power/Knowledge: 10 (first hit) + 26 (second hit) = 36 total
- vs Laughter: 12 (first hit) + 33 (second hit) = 45 total

**Up+X — "Nanoslicer"**: hair becomes two large spearheads, spin-jump attack; tapping X adds hits, max 8 hits. Last hit flings opponent a short distance.
- vs Power/Knowledge: 14 dmg @ 2 hits, 22 @ 4, 26 @ 5, 34 @ 7, 38 @ 8 (max)
- vs Laughter: 17 dmg @ 2 hits, 27 @ 4, 32 @ 5, 42 @ 7, 47 @ 8 (max)
- Author notes these are the "most common" hit-count results from testing (author unconfirmed as exact).

## Ally Boosts (HP scaling)

Boosted by Train and Sven (Black Cat) and Akane-chan (Neuro).
- 4-koma Eve HP: starts 128, then 136, 144, 152 with each boost (4 stages).
- 5-koma Eve HP: starts 144, then 152, 160, 168 with each boost (4 stages).

## Mechanic-Revealing Observations

- Forward+Y hair-grab has a specific effective range window (~3-4 character widths); too close or too far and the grab whiffs entirely — indicates discrete range-banded hit conditions rather than a single continuous hitbox.
- Down+Y is called out as breaking guard, matching a general rule the guide states applies to "everybody else's Down+Y" — implies Down+Y is a guard-break input class-wide.
- Down+B forces an opponent character swap on hit — again described as a general rule ("like everybody else's Down+B attack").
- Guard-break combined with a stun/freeze support (e.g., 3-koma Hitsugaya) into 5-koma Lance is cited by the author as capable of ringing out a full-health opponent from mid-stage — a concrete combo interaction revealing that frozen/stunned opponents cannot mitigate knockback/launch distance.
- 2-space Support Koma applies a flat 50% damage reduction while its shield persists (not a flat damage-absorb value, a percentage modifier).
- All aerial attacks halt the character's horizontal/vertical air momentum ("stops in the air") — a general engine rule noted by the author, not Eve-specific.
