# Jotaro Kujo (JoJo's Bizarre Adventure)

- Source: untitled Jotaro Character FAQ (no version number in text), by Evil.Soldier.347 (contact email in source; author's screen name not otherwise given)
- GameFAQs FAQ id: gf-46754
- Unverified community source — numbers are from a fan-written guide, not verified against the game.

## Help and Support koma

### 1-koma (Help)
- Effect: reduces damage taken from special attacks for characters the deck-construction arrow points to.
- Shape: single cell.

### 2-koma (Support)
- Shape: horizontal 2-cell (`[][]`)
- Nature: Power
- Star Platinum charges forward fist-first; on hit, drags the target a short distance then punches with the other fist.
- Damage: 24 to Power characters, 36 to Knowledge characters, 24 to Laughter characters.
- Notes: while Star Platinum is holding the target, there is a brief window where any other attack (including projectiles/projectile specials) can be added without knocking the target down.

### 3-koma (Support)
- Shape: horizontal 3-cell (`[][][]`)
- Nature: Knowledge
- Iggy (the dog) is flung forward as a projectile with decent travel distance before disappearing; on hit, Iggy holds the opponent while Star Platinum lands a blow that applies the Battle Seal status.
- Damage: 34 to Power characters, 34 to Knowledge characters, 45 to Laughter characters.
- Status effect: Battle Seal.

## Battle koma — shared moveset

Note from source: these damage numbers were measured using Jotaro's 6-koma specifically; other sizes' normals were not independently listed (author's caveat, so treat base-normal numbers as 6-koma-specific unless stated otherwise).

| Input | Description | Damage |
|---|---|---|
| B | Quick hook punch | 8 |
| Forward B | Slide forward + low kick | 9 |
| Up B | Star Finger upward stab | 10 |
| Down B (forced swap) | Star Platinum charges briefly then punches; switches opponent's character | 10 |
| Air B | Star Platinum uppercut | 10 |
| Y | Barrage of punches, mash for more hits | 12-21 |
| Forward Y | Charge forward + overhead punch | 18 |
| Up Y | Barrage of punches at 45-degree upward angle | 12-21 |
| Down Y | Charge briefly then ground pound | 20 |
| Air Y | Barrage of punches at 45-degree downward angle (spikes opponent) | 12-21 |

### Passives / Ultimate Action

- Passive: takes less damage from special attacks.
- Passive: deals the same (unreduced) damage to characters of an opposing nature (i.e., does not take the normal type-effectiveness penalty — author's phrasing; interpreted as Jotaro's own damage output isn't reduced by nature mismatch, exact mechanic unconfirmed).
- Ultimate Action (Select): pose animation, then a small SP gauge regain (no numeric SP amount given).

## Specials by koma size

### 4-koma
Shape: 2x2 block.

- Special A "ORAAA!": Star Platinum charges forward, grabs, and punches — same base move as the 2-koma support but stronger. Damage: 40 to Power/Laughter, 60 to Knowledge. Nature: Power. Holds the opponent in place for a few seconds after connecting (an exploitable combo window per the author).
- Special B "Crossfire Hurricane": Avdol's Red Magician fires 3 burning crosses forward, traveling close together for a decent distance; applies Burn status. Damage: 30 to Power/Laughter, 54 to Knowledge. Nature: Power.

### 5-koma
Shape: 2x2 block plus one extra cell (5 total).
Note: an alternate version of this koma exists with Knowledge nature instead of Power — per the author, to get its numbers, swap the "extra damage vs Knowledge" bonus to apply to Laughter instead.

- Special A "Star Platinum & Silver Chariot": Polnareff's Silver Chariot joins Star Platinum in a barrage. Damage: 13-34 to Power/Laughter, 19-42 to Knowledge (mash for more hits). Nature: Power. Author notes Silver Chariot's hits do more damage than Star Platinum's in this move, so max damage requires the opponent to be positioned to be hit only by Silver Chariot.
- Special B "Emerald Splash": Kakyoin's Hierophant Green fires emeralds in a wide arc (above, below, forward). Damage: 14-52 to Power/Laughter, 21-84 to Knowledge. Nature: Power. Author notes max damage values require point-blank range so all emeralds connect.

### 6-koma
Shape: 3x2 block.

- Special A "Ora Ora of Anger!": punch barrage that finishes by launching the opponent upward at a 45-degree angle; Jotaro poses afterward for about half a second. Damage: 26-49 to Power/Laughter, 39-73 to Knowledge (mash for more hits).
- Special B "Star Platinum: The World" (Za Warudo): Jotaro is engulfed in aura for about 1 real-time second (startup/vulnerability window), then time stops on stage for about 3 real-time seconds — opponents, supports, and projectiles all freeze, but Jotaro can still move/attack freely. Damage: none (utility move). Any attacks landed during the freeze are not "felt" (no damage/knockback applied) until the freeze ends, at which point all queued effects resolve at once.

## Support koma combo notes (numeric, cross-character)

- 3-koma Terryman (Kinnikuman): flying knee drop, ~34 damage average, does not knock the target down (leaves them open to combo). Combined with Jotaro's 4-koma Special A (hotkeyed to activate right after pressing X so Star Platinum's hold window catches Terryman's hit before the follow-up punch): ~80 damage average. Used at the end of 5-koma/6-koma Special A instead: 70-90 damage.
- 3-koma Sogo Okita (Gintama): beetle horn-wave attack, ~70 damage, very long knockback. Combined with Jotaro's Y barrage or 5/6-koma Special A (activated as the barrage starts): author's highest recorded combo total was 134 damage.
- 3-koma Takeshi Yamamoto (Reborn!): circle-of-slashes pull/knockback attack, described as more defensive/crowd-control, no damage number given.
- 2-koma Jirou Kusano "Rouji": circle of glowing cards; on hit applies Stop status AND drains one SP bar from the opponent. No damage number given, described as fast-traveling projectile.
- 4-koma Jotaro Special A + hotkeyed 3-koma Gotenks or 3-koma Zoro: author reports racking up ~115 damage using the hold window.

## Mechanic-revealing observations

- Star Platinum's hold effect (2-koma support and 4-koma Special A) creates a distinct "no knockdown" state during which additional hits (including projectiles) can be freely added — an explicit combo-extension mechanic.
- Jotaro's passive removes the normal nature-based damage penalty for his own attacks against opposing types (author's description — worth verifying against the underlying type-effectiveness formula since other guides describe nature bonuses/penalties as multiplicative, e.g., Sanji guide's 1.5x rule).
- Za Warudo (6-koma Special B) has a two-phase timing structure: ~1 second startup (vulnerable), then ~3 seconds of freeze during which damage dealt is applied retroactively only once the freeze ends — a specific hitstun/frame-timing mechanic worth reverse-engineering precisely.
- 5-koma's alternate Knowledge-nature variant is stated to simply swap which off-type damage bonus applies (Laughter instead of Knowledge), implying the underlying damage table is parameterized by nature rather than hardcoded per koma (author unconfirmed, inferred from guide's instruction).
