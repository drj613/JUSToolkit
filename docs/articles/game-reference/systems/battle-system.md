# Battle System (Controls, Gauges, Victory, Items/Status)

- **Source guide**: "Jump! Ultimate Stars" FAQ/Walkthrough
- **Author**: Genroh
- **Version**: 2.5
- **GameFAQs FAQ id**: gf-45856
- **Reliability**: Unverified community claim source — fan-authored, not verified against game code/data. Treat all numbers as hypotheses to confirm.

Scope: distilled from section "C2: How to Play" only.

## Controls

- B = Weak Attack
- Y = Strong Attack
- X = Special Attack A
- Up + X = Special Attack B
- A = Jump; A, A = Double Jump
- Down = Guard
- Down + A = Get off platform
- Down, Down = Fast-fall while airborne
- Left,Left or Right,Right = Dash
- Left/Right + B or Y = Side Attack
- Down + B = Forced Change (forces opponent to switch characters)
- Down + Y = Guard Break (breaks opponent's guard)
- Down + X = Push Attack (counterattack that pushes opponent back)
- Up + B or Y = Down Attack
- Select = Ultimate Action
- L/R = Character hot-keys
- Touch screen = call Support characters and use Help characters
- Ledge grab: press B when knocked off a ledge to grab a nearby ground ledge (does NOT work on platforms). Character can hang for a few seconds before falling. Press Left/Right to climb up and roll, or Up to climb up without rolling.

## Gauges

- **J-Soul (health) gauge**: yellow bar. Empties → character is KO'd and leaves battle.
  - KO'd character's portrait turns black-and-white with a small recovery bar; once that bar fills, the character can be called back in.
  - If the whole team is KO'd, J-Coins scatter near the body; after a few seconds all characters are revived at full health.
- **Special (SP) gauge**: blue bar. Powers Special Attacks, Support Characters, and Help Characters. Refill sources:
  - Dealing damage to the opponent
  - Collecting J-Coins (bigger coin = more SP)
  - Collecting a Pirate Head (restores exactly 1 full SP bar)
  - Certain Help Koma speed up passive gauge recovery rate
  - Certain Support Koma restore gauge energy directly
  - Some Ultimate Actions refill the Special Gauge
  - Some Special Attacks themselves restore SP energy
- **Nature icon**: kanji shown top-left of the portrait indicating the character's Koma nature (interacts with nature strength/weakness system, detailed elsewhere).

## Victory/point systems (selectable per mode: Battle, Versus, Wireless, Wifi)

### Point System
- All players start at 0 points.
- KO an enemy (non-leader) character with a non-leader character: attacker +1 point, victim's controller −1 point.
- KO an enemy character using your **Leader** character: attacker +2 points, victim's controller −2 points.
- KO an enemy **Leader** character (with any of your characters): attacker +2 points.
- If your whole team is KO'd: additional −2 points penalty.
- When the timer expires, highest point total wins.
- Winning with 0 or negative points is possible; if all players have negative totals, the player with the least-negative (closest to zero) total wins.

### Elimination
- King-of-the-hill style: KO all of an opponent's characters to eliminate them; last player(s) standing wins. Most common mode in Wifi play.

### J-Symbol
- Every player starts with 1 star; an additional star drops into the stage middle periodically.
- KOing an opponent makes them drop one of their stars for you to collect.
- Player with the most stars when time expires wins.

### Sudden Death (tiebreaker)
- Triggered when tied players need a decider.
- Players dropped onto a platform with no walls and no ground.
- Forced to fight using ONLY their Leader character — no secondary/support/help character bonuses.
- SP gauge starts at 0.

## Hot-key & Leader system

- Two characters can be bound to quick-select hot-keys (L and R buttons) from the Koma deck page; not limited to Battle characters — Support and Help Koma can also be hot-keyed.
- **Leader** character:
  - Is the character you start the match with.
  - Is the ONLY character usable during Sudden Death.
  - KOing an opponent while playing as your Leader grants an extra win point (i.e., the 2-point KO bonus described in Point System above).
  - KOing an opponent's Leader (with any of your characters, not necessarily your own Leader) grants 2 win points.
  - Requirement: a Battle character can only be set as Leader if it has a Help Koma placed adjacent to it in the deck.
  - Leader character receives a health bonus (amount not specified by author).
- A Leader MUST be assigned or the deck cannot be used in battle.
- Assignment flow: after building the deck, press L or R to open Leader/Hot-Key selection; pick the Leader with the cursor and assign hot-keys to other characters.

## Status effects

Rules:
- Effects apply to the whole team once any character on the field is afflicted — switching in another character carries the effect over.
- A character with an "immunity" koma removes the effect when switched in.
- Maximum of 1 positive and 1 negative status effect active at once. Gaining a new effect of the same polarity (positive/negative) cancels/replaces the previous one.

### Positive effects
- **Attack-Boost**: increases attack power (icon: red boxing glove, up arrow).
- **Deck Power**: increases attack power scaled by number of characters in your deck (icon: red boxing glove + red "Deck" kana).
- **Speed-Boost**: increases movement speed (icon: sneaker, up arrow).
- **Critical**: every other hit deals at least double normal attack power (icon: blue boxing glove with "!"). (author unconfirmed exact mechanic wording: "every other hit")
- **Toughen**: incoming damage is halved (icon: spinning metal tile).
- **Invisibility**: character becomes invisible to opponents (icon: invisible character silhouette).
- **Invincibility**: character can no longer be harmed (icon: star overhead).
- **Regain**: gradual health regeneration (icon: blue kanji overhead).
- **Infinite**: Special Gauge becomes effectively infinite (icon: gold kanji overhead).
- **Null-Nature**: removes the Battle character's Koma nature — removes both weakness to an opposing nature AND strength against another nature (icon: clear/blank kana overhead).
- **Kinniku Power** (Kinnikuman-exclusive): combined effect of Critical + Toughen simultaneously (icon: "Kinniku" kanji overhead).
- **Ensastu** (Hiei-exclusive): increased attack damage, flame effects turn black (icon: black & white kanji overhead).
- **Mellorine** (Sanji-exclusive): attack boost scaling with number of female characters in the deck (icon: three pink hearts overhead).

### Negative effects
- **Speed-Down**: reduced movement speed (icon: sandal, down arrow).
- **Confusion**: left/right input directions reversed (icon: "?" pair overhead).
- **Poison**: gradual health loss (icon: skull overhead).
- **Auto-Run**: character cannot stop running (icon: running man overhead).
- **Paralysis**: cannot fight or move (icon: two lightning bolts overhead).
- **Blindness**: battle screen blacked/whited out (icon: slashed eye or whited-out DS top screen).
- **Shock**: random shocks that can cancel actions and deal damage (icon: word balloon with bolt).
- **Burn**: gradual health loss AND cannot stop running (icon: word balloon with flame).
- **Freeze**: cannot fight or move (icon: word balloon with snowflake) — mechanically same as Paralysis per author's description.
- **Stop**: cannot move, turn around, or jump (icon: walking man with slash).
- **Attack Seal**: cannot attack or use Specials (icon: boxing glove with slash).
- **Guard Seal**: cannot block (icon: shield with slash).
- **Battle Seal**: cannot switch Battle characters (icon: red kana with slash).
- **Support Seal**: cannot call in Support characters (icon: blue kana with slash).
- **SP Drain**: Special Gauge gradually drains (icon: gold kanji, down arrow).
- **Judgment**: countdown timer from 10 to 0 appears overhead; character is instantly KO'd when the timer hits 0, OR is instantly KO'd if attacked while the timer reads 0.

### Items (field pickups) and their effects
- Orange, Apple, Strawberry, Banana, Grapes, Melon: restore a small amount of health.
- Meat: restores a larger amount of health.
- First Aid Kit: restores a little health to ALL Battle characters in the deck (not just the active one).
- J-Coins: restore a small amount of SP energy.
- Bombs: explode, damaging anyone nearby.
- Pirate Head: grants exactly 1 full SP bar.
- Red Boxing Glove → Attack-Boost effect.
- Blue Boxing Glove → Critical effect.
- Sneaker → Speed-Boost effect.
- Bubble → Invisibility effect.
- Star → Invincibility effect.
- Jump Magazine → Infinite effect.
- Sandal → Speed-Down effect.
- Mushroom → Confusion effect.
- Purple Bottle → Poison effect.
- Chili Pepper → Auto-Run effect.
- Ink → drops ink on ALL players, causing Blindness.
- Hammer → drops hammers on ALL players' heads, causing Paralysis.
- Weight → drops weights on ALL players' heads, causing Speed-Down.
- Gems → currency used to buy more Koma and Data features (not a battle status effect).

## Ultimate Actions

- Select button triggers an Ultimate Action; functions like a taunt but some grant special benefits: health restoration, SP/energy recovery, or counterattacks (exact per-character values not given in this section).

## Dream Combo

- Requires 2 or more Battle Characters in the deck to use.
- Procedure (example using Goku/Luffy/Ichigo, with Goku as current on-field character):
  1. Tap the Koma of the current Battle Character (Goku).
  2. Tap the 2nd character's Koma (Luffy).
  3. Tap the 3rd character's Koma (Ichigo).
  4. All of this must be done quickly, or it just functions as a normal tag in/out instead of a Dream Combo.
  5. Tapped characters are highlighted in red as you select them.
  6. Finally, tap the first character tapped (Goku) again to unleash the combo.
