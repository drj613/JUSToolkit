# Frieza (Dragon Ball) — Character Guide Notes

- Source: "Frieza Character Guide", written by tech_man54 (Omar Siegfried)
- Version: not stated (2009 copyright)
- GameFAQs FAQ id: gf-47666
- **Unverified community source** — numbers below are from a fan-written guide, not verified against game code.

## Koma Forms

- Frieza has only **one koma form**: a 6-koma (Battle), shape:
  ```
  [][]
  [][]
  [][]
  ```
- Evolution chart: `[H] Help -> [6] Battle`
  - Help koma: obtained free by having 5 Support characters in your deck.
- No Support koma exists for Frieza.
- Because there's only one koma, damage values do not shift between nature versions (no Power/Laughter/Knowledge variant swap) — the guide gives two damage numbers per move: one for "Power/Laughter" targets and one (higher) for "Knowledge" targets, implying a damage-vs-nature multiplier (author does not give the underlying ratio, but Knowledge damage numbers are consistently ~1.5x the Power/Laughter numbers, matching the general nature-triangle rule described in other guides).

## Moveset (damage numbers as listed)

Controls: double-tap a direction = Dash ("Flashstep", passes through enemies). Down = Block. A+Down in air = Quick Fall. A = Jump (double jump, triple with right help koma). Select = Ultimate Action (hover + purple aura), restores SP at ~4 SP/second (author unconfirmed precision, guide states "about 4 SP p/ second").

### B Button Attacks
- **B**: tail spin smack. 8 dmg (Power/Laughter), 12 dmg (Knowledge). Quick recovery. Connects into Up+B, which connects to aerial Y.
- **Side B**: forward tail hit. 8 dmg (Power/Laughter), 12 dmg (Knowledge). Minimal recovery, good range.
- **Up B**: dash into air + smack upward, connects into Aerial Y. 8 dmg (Power/Laughter), 12 dmg (Knowledge). Vulnerable during fall-back (mitigated by Quick Fall).
- **Down B**: Force Change (changes opponent's active character). Delayed startup; recovery leaves Frieza open. 10 dmg (Power/Laughter), 15 dmg (Knowledge).

### Y Button Attacks
- **Y**: tail hit + flip back, launches opponent up. Good combo starter/juggle. 10 dmg (Power/Laughter), 15 max dmg (Knowledge).
- **Side Y**: repeated purple beam shots (rapid-press Y to add more shots); damage drops off at long range (author observation, no exact falloff numbers given). 20 MAX dmg (Power/Laughter), 30 MAX dmg (Knowledge).
- **Up Y**: lifts 6 rocks, throws them; max 3 hits per target. Recovery leaves Frieza open. 24 MAX dmg (Power/Laughter), 36 MAX dmg (Knowledge).
- **Aerial Y**: hover + purple sphere shot downward; traps opponent until it lands — good ring-out tool. 18 dmg (Power/Laughter), 27 dmg (Knowledge).
- **Down Y**: delayed forward blast; Guard Breaks. Requires opponent to be somewhat distant to connect. Slow recovery. 20 dmg (Power/Laughter), 30 dmg (Knowledge).

### X Button Attacks (Specials)
- **Special A — X**: ~1 second startup delay, then fast forward shot; on hit, continues blasting rapidly. 8 total hits. Last hit Guard Breaks. 56 dmg (Power/Laughter), 84 dmg (Knowledge).
- **Special B — Up X**: ~2.5 second charge delay, fires an exploding purple orb on contact. Immense knockback (no numeric knockback value given). 38 dmg (Power/Laughter), 57 dmg (Knowledge).

## Combos (with total damage as reported by author)

- **B, Y, Up X** (must be fast or Up X won't connect): 66 max dmg (Power/Laughter), 74 max dmg (Knowledge).
- **B, Side B, X**: 87 max dmg (Power/Laughter), 108 max dmg (Knowledge).
- **B, Side B, Side Y** (no special): 36 max dmg (Power/Laughter), 54 max dmg (Knowledge).
- **Side B, Y, Up B (delay), Y** (no special): 36 dmg (Power/Laughter), 66 dmg (Knowledge).
- **B, Side B, Side Y, Huh Huh Brothers (support, 3-koma), X** ("Ultimate Might" — author's name for the combo result): damage not quantified by author.
- **B, Side B, Y, Seiya (support, 3-koma), Up X**: 88 max dmg (Power/Laughter), 132 max dmg (Knowledge). Requires Seiya activated simultaneously with Y, then repositioning under opponent for Up X.
- **B, Hibari (support, 3-koma) -> Aerial Y** ("noob combo", drags opponent to edge then ring-out via Aerial Y): damage listed only as "DEATH" (i.e., a guaranteed ring-out, not a numeric value).

## Support Koma
Frieza has **no Support koma** of his own.

## Help Koma synergies mentioned (no numeric stat given beyond function)
- Eve (Black Cat), Devil Bat, Hanamichi Sakuragi, Gajira Norimaki, Sipuxiang — each grants a third jump (non-stacking; having more than one does not add extra jumps).
- Orochimaru — restores some HP per second + grants Frieza an ally boost. Alternatives: Majin Buu, Leon, Ikki, Piccolo, Kazuki Mutou.
- Ally boosts for Frieza specifically: Dio, Orochimaru, Sasuke.
- Damage-reduction helps by category: punches/kicks (Luffy, Kinnikuman); swords (Takeshi Yamamoto, Robin Mask, Shiryu, Yuu Kanda, Trunks, Yahiko Myojin, Zoro, Franky); Specials (Jotaro Kujo, Seiya, Sasuke Uchiha, Kakashi Hatake, Kuroro Lucifer, Sven Volified).

## Passive / Mechanic Observations
- Frieza's dash is a "Flashstep": passes through the opponent's body rather than stopping (distinguishes him from characters whose dash gets blocked by opponent's body).
- Ultimate Action grants roughly 4 SP per second while active (author's rough estimate, unconfirmed).
- General strategic note: sacrificing an SP bar to blast with X is suggested as an escape from being "caught in Stop" (a stun/freeze-like state) — implies X has enough startup speed/invincibility or range to counter this specific status window (author unconfirmed mechanism).
