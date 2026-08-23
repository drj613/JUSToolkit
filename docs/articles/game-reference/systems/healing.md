# Healing Systems (Jump Ultimate Stars)

- **Source guide**: "Healing FAQ" v1.0
- **Author**: numberOneRookie
- **GameFAQs FAQ id**: gf-47130
- **Reliability**: Unverified community claim source. Author measured HP values by
  ruler-measuring life bar pixel/mm length in training mode and converting via a
  derived HP-per-mm constant; author explicitly flags most values with "~" as
  approximate (accurate to within ~1-2 HP per their claim). All approximate values
  below are marked accordingly; exact author-stated values (no "~") are marked exact.

## Measurement methodology (for calibrating reimplementation)

- Author drained a test character's HP to (assumed) 1 HP, then applied the heal and
  measured the resulting life-bar length with a ruler, in training mode with HP
  regen option OFF.
- Conversion constant derived: **~5.5 HP per mm of life bar**, computed by dividing
  each character's total HP (as shown in deck builder) by their full life-bar length in mm.
- Tested on two characters (Vegeta - male, Lenalee - female) to check for sex-dependent
  healing (relevant to Sanji, see below).
- HP was drained via: Vegeta's 6-koma ^X (self-damage) or repeated use of Killua's
  3-koma "Risky Dice" until HP hit minimum, for Lenalee.
- Special-move heals were measured using only the Risky-Dice-drain method (can't be
  tested cross-character).
- Author's own error bound: ~1 HP, at most ~2 HP (author unconfirmed precision claim).

## 1. Healing Support Koma

Support koma that restore HP (some also clear status effects). Values are
"~" (approximate, per author's measurement method) unless noted as exact.

| Heal (HP) | Koma | Size | Manga | Notes |
|---|---|---|---|---|
| ~60 | Sanji 2koma | 2 | One Piece | only to female characters |
| 55 (exact, author states no ~) | Satsuki 2koma | 2 | Ichigo 100% | over ~12 seconds (regen effect, not instant) |
| ~50 | Kurama 3koma | 3 | Yu Yu Hakusho | heals through guard |
| ~41 | Josuke 2koma | 2 | JoJo's Bizarre Adventure | heals via being hit by "Crazy Diamond" punch; also restores some SP (counts as a hit); does NOT heal if blocking during the punch; turns the character around |
| ~41 | Sakura 3koma | 3 | Naruto | also removes status effects; must not be blocking |
| ~41 | Orihime 3koma | 3 | Bleach | heals ALL characters in deck (current + others); no heal if blocking |
| ~41 | Reiko 2koma | 2 | KochiKame | ~2 sec cast (baking a cake) |
| ~33 | Iori 3koma | 3 | I''s | male characters also get attack-boost status ~1s after heal if they wait |
| ~30 | Chopper 2koma | 2 | One Piece | also removes status effects; relatively slow |
| ~30 | Sanji 2koma | 2 | One Piece | to male characters; "sometimes doesn't heal" (author-observed inconsistency, unconfirmed cause) |
| ~25 | Gon 2koma | 2 | Hunter X Hunter | heals OTHER characters in deck only, not the summoner; has charge time |
| ~23 | Ta-chan 2koma | 2 | Jungle No Ohja Ta-chan | heals OTHER characters in deck only, not the summoner |
| ~20 | Wakabyashi 3koma | 3 | Captain Tsubasa | also grants "toughen" status effect; usable in air |
| ~20 | Wakabyashi 2koma | 2 | Captain Tsubasa | heals only as a counter-attack (must be hit while active) |
| ~17 | Seiya 2koma | 2 | Saint Seiya | also removes status effects; heals through guard; very fast animation |
| ~12 | Cascade 2koma | 2 | Midori no Makibaou | also grants "speed up" status; heals OTHER characters in deck only, not the summoner |
| N/A | Killua 3koma | 3 | Hunter X Hunter | see below (random effect, not a fixed heal) |

### Notable per-koma edge cases

- **Josuke 2koma**: Double-use (~3 sec) yields >80 HP total (2x41). Compare Satsuki's
  55 HP over 12 sec — Josuke is faster for burst healing.
- **Satsuki 2koma**: Grants a "regen" status effect lasting 12 seconds, totaling 55 HP
  over that duration (not instant). Regen works through guard. Re-using Satsuki while
  the regen is active does NOT stack/double the heal — it just refreshes the timer
  (same total 55 HP, not 2x). There is a known glitch: using Satsuki alongside a
  battle character that has a healing special produces an abnormally fast regen tick;
  this is described as banned/frowned upon in most JUS tournaments (author unconfirmed
  mechanism, but explicitly notes it is a known glitch).
- **Killua 3koma ("Risky Dice")**: RNG heal-or-harm effect — 3 outcomes:
  1. Full heal (HP set to current max, regardless of current HP).
  2. Full HP loss (HP set to 0 / KO).
  3. HP set to exactly half of max HP.
  Slow start-up. No fixed probabilities given by author.
- **Wakabyashi 2koma**: Only heals as a reactive counter — must be hit by the opponent
  while active to trigger the 20 HP restore.
- **Wakabyashi 3koma**: Usable mid-air; heals 20 HP and applies "toughen" status on landing.
- **Sanji 2koma**: Heal amount is sex-dependent — 30 HP for male characters, 60 HP for
  female characters. Author notes occasional failure to heal male characters (author unconfirmed, possibly a bug).
- **Gon 2koma / Ta-chan 2koma / Cascade 2koma**: All three explicitly exclude the
  summoning character from the heal (only heal "other" deck members); can retarget
  by swapping active character during the cast animation.

## 2. Food Support Koma

Food-type support koma. A subset gives random/unmeasurable amounts. The "Gain More
Health From Food" help koma (section 5.3) adds ~50% to food-sourced heals, with two
notable exceptions (Hao, Volvo) where the bonus does not apply as expected.

| Base Heal | With "Gain More Health From Food" help koma | Koma | Size | Manga |
|---|---|---|---|---|
| ~25 (base, via 5 oranges) | ~38 | Hao 2koma | 2 | Shaman King |
| ~20 | ~30 | Kaipan 2koma | 2 | KochiKame |
| ~20 | ~30 | Monta 3koma | 3 | Eyeshield 21 |
| N/A (random: coins + sometimes fruit/invincibility star) | N/A | Nakagawa 2koma | 2 | KochiKame |
| N/A (random: fruit, coins, power-ups, or bombs) | N/A | Piko 2koma | 2 | Muhyo To Rouji |
| ~32 | ~32 (no bonus applies) | Volvo 2koma | 2 | KochiKame |

### Hao 2koma details (most complex heal in the guide)

- Base: 5 oranges dropped, walking over all = ~25 HP.
- Walking back-and-forth across Hao while he dishes out oranges yields additional
  heals, bringing total to ~80 HP.
- Dashing back-and-forth (double-tap direction) yields further additional heals,
  pushing total to 100+ HP. Amount varies by character's dash properties
  (author unconfirmed exact scaling — described as varying "by character").
  Author suggests summoning Hao mid-dash for characters with long dashes or on
  platforms to maximize hits.
- Author's max observed heal: ~127 HP without the food-boost help koma, ~137 HP
  with it (author unconfirmed as a hard cap — only "a few characters" tested).
- The "Gain More Health From Food" help koma does NOT meaningfully boost Hao's
  total because the bonus heals from dashing/walking don't count as "food" —
  only the base 5 oranges do, giving an extra ~12-13 HP (author-derived, not
  official).

### Volvo 2koma detail

- The meat item does not count as "food" in the game's internal categorization,
  so the "Gain More Health From Food" help koma gives it zero bonus (author-confirmed
  via testing, contrasts with Kaipan/Monta which do get the 50% bonus).

## 3. Support Koma That Only Remove Status Effects (no HP restore)

| Koma | Size | Manga | Notes |
|---|---|---|---|
| Alastair Crowly 2koma | 2 | D. Gray Man | Removes all negative status; counts as a hit (regains some SP); turns character to face away; faster than Seiya 2koma but no HP heal and doesn't work through guard |
| Don Patch 2koma | 2 | Bobobo-bo Bo-bobo | Removes all negative status via a staff hit |
| Taikoubou 2koma | 2 | Houshin Engi | Removes all negative status; must stand adjacent to Taikoubou for ~1 second |

Author's assessment: none of these three are considered worth using over Seiya
2koma (section 1) since Seiya also heals ~17 HP, is fast, and heals through guard.

## 4. Healing Special Moves

Character special moves (not support koma) that restore HP. All approximate
unless noted otherwise.

| Heal (HP) | Special | Size | Manga | Move input | Notes |
|---|---|---|---|---|---|
| 100 (exact) | Kinnikuman 7koma | 7 | Kinnikuman | X | with 2 other battle characters in deck (see formula below) |
| ~80 | Kagura 5koma | 5 | Gintama | ^X | |
| ~72 | Sakura 5koma | 5 | Naruto | ^X | also removes status effects; ~half of Sakura 5koma's own max HP |
| ~60 | Ryotsu 4koma | 4 | KochiKame | ^X | not the fastest cast |
| ~50 | Kagura 4koma | 4 | Gintama | ^X | fairly fast |
| 50 (exact) | Kinnikuman 7koma | 7 | Kinnikuman | X | with 0 or 1 other battle characters in deck |
| ~50 | Piccolo 4koma | 4 | Dragon Ball | ^X | plus ~10 HP to each other character in deck |
| ~50 | Jaguar 4koma | 4 | Pyuu To Fuku! Jaguar | — | plus 22 HP to each other character in deck |
| ~42 | Sakura 6koma | 6 | Naruto | ^X | heals OTHER characters in deck only (not Sakura herself) |
| ~33 | Buu 6koma | 6 | Dragon Ball | ^X | deals damage to opponent while healing Buu; links from Buu's ^Y |
| ~30 | Gintoki 5koma | 5 | Gintama | ^X | counter move — only heals 30 HP if the counter is NOT triggered (no one hits Gintoki for ~1 second) |

### Formulas / multi-target details

- **Kinnikuman 7koma**: Self-heal = 25% of his total max HP per other battle
  character currently in the deck (i.e., 1 other character → 25% max HP = 50 HP;
  2 others → 50% max HP = 100 HP; alone → still 25% max HP = 50 HP). Since he is
  a 7-koma, max deck-mates alongside him is 2 (20-square grid constraint), so
  the maximum self-heal is 100 HP. Additionally, ALL other battle characters in
  the deck receive a flat 41 HP regardless of count. With 2 other characters,
  total party heal = 100 (self) + 41 + 41 = 182 HP.
- **Jaguar 4koma**: Self ~50 HP + 22 HP to each other deck member. In a 4-battle-character
  deck, author states total = 112 HP (50 + 22×3 ≈ 116, author's stated total is 112 — treat as author's own approximation, not exactly reconciled with per-character number).
- **Piccolo 4koma**: Self 50 HP + ~10 HP to each other character. In a 4-character
  deck, author states total restored = 80 HP (50 + 10×3 = 80, consistent).
- **Sakura 6koma**: Heals only OTHER characters (not self) for 42 HP each; with 2
  other characters, total = 84 HP. Cannot self-heal if Sakura is the last character alive.
- **Gintoki 5koma**: Counter-move semantics — 30 HP heal is the "whiff" fallback
  outcome, not the primary counter-hit outcome (counter-hit damage/behavior not detailed in this guide).

## 5. Healing-Related Help Koma

| Help Koma | Effect |
|---|---|
| Health Recovers Slowly | Restores 200 HP over a 90-second match (JUS seconds), assuming the affected character is always active and below max HP. Real-world restoration is lower since characters start at full HP and aren't always in a "need healing" state. |
| Max Health Increases After KO | Increases max HP by 15 HP per KO suffered (author-measured), capped at some max life-bar size (cap value not specified — author unconfirmed exact cap, only that "it doesn't go beyond the maximum size of life bar"). |
| Gain More Health From Food | Increases HP restored by food-support koma by ~50%. Exceptions: Hao (bonus applies only to the base 5 oranges, not to extra dash/walk-triggered heals) and Volvo (no bonus at all, since his meat item is not flagged internally as "food"). |
| Status Effect Time Reduced | Halves the duration of a specific subset of negative status effects (see below). Neither of the halved short-duration effects (e.g. paralysis, freeze) drops below ~1 second after halving, per author observation. |

### Status Effect Time Reduced — exact effect list (author-tested)

Halved by this help koma:
- Poison
- Paralysis
- Shock
- Burn
- Freeze
- Movement Seal
- Attack Seal
- Guard Seal

NOT halved by this help koma:
- Battle Seal
- Support Seal
- Speed-Down
- Confusion
- Blindness
- Auto-Run

This is presented as a directly tested/verified list by the author (not flagged unconfirmed), though it is still an unverified third-party community claim per the overall source reliability note.

## 6. Passive/Background Healing Mechanic (Character Swap)

- Battle characters in the deck but not currently active (i.e., benched) regain HP
  gradually over time. Author estimates ~200 HP distributed among inactive characters
  over a 90-second match (JUS seconds) — explicitly stated as not rigorously
  measured (author unconfirmed / "I've not looked into this in detail").
- Strategic implication (not a hard rule, but constrains expected passive-regen
  balancing): swapping to a full-health character while damaged characters stay
  benched maximizes total passive healing over a match.

## 7. Misc constraints relevant to implementation

- Several heal-on-hit or heal-on-pickup effects are blocked if the receiving
  character is blocking/guarding at the moment of the heal trigger (Josuke 2koma,
  Orihime 3koma, Sakura 3koma all explicitly fail to heal while blocking).
- Some heals bypass guard entirely (Kurama 3koma, Satsuki 2koma's regen, Seiya 2koma)
  — this is inconsistent across koma and appears to be a per-koma authored property
  rather than a general rule.
- Deck grid is 20 squares total; koma "size" (2/3/4/5/6/7) is the number of grid
  squares it occupies, constraining how many characters/support/specials can
  co-exist in a deck (e.g., Kinnikuman at 7-koma leaves room for exactly 2 more
  deck slots at minimum 1-koma size each within the 20-square budget, though a
  practical deck's other allocations reduce this further — not fully specified
  by this guide).
- Sena 3koma "movement seal" status is called out as the dominant status effect
  encountered in online play, motivating specific counter-play/healing choices,
  but no numeric duration for movement seal is given in this guide (see help
  koma section for the fact that its long duration is halved by "Status Effect
  Time Reduced").
