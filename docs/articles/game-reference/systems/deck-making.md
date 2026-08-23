# Deck-Making Guide

- **Source guide:** "Jump Ultimate Stars Deck-Making FAQ/Guide"
- **Author:** Son1cwildfire
- **Version:** copyright 2007 (no version history section; appears to be first/only version)
- **GameFAQs FAQ id:** gf-48966
- **Reliability:** Unverified community claim source — author's own numbers are hedged as guesses in places; treat all specific percentages as (author unconfirmed) unless otherwise noted.

## Deck grid / capacity rules

- Total battle koma block budget: **17 blocks maximum** for battle komas in a deck (separate from help and support koma budgets — exact help/support caps not stated in this guide).
- Koma "level" (the number attached to a character, e.g. "Yusuke 6") consumes that many blocks. Example: Yusuke 6 + Kurama 4 + Yoh 4 = 14 blocks total, leaving 3 blocks of the 17 for battle-koma spend (remaining budget goes to help/support separately, not from the same 17 — guide is ambiguous on whether help/support share this pool or have their own; treat as author's example only, not a confirmed rule).
- A koma can have other help komas "attached" to it (physically placed adjacent on the grid) to grant that character an ally boost — e.g., attaching a koma of a different character to your main koma. This implies grid-adjacency mechanics matter for triggering ally-boost/support effects (not explained mechanically beyond examples).

## Natures (rock-paper-scissors-like typing)

- Three natures exist: **Power, Knowledge, Laughter**.
- Guide analogizes it to Pokémon type advantage: using a koma of the advantaged nature against an opponent's koma nets an advantage (mechanism/multiplier not specified numerically by this guide).
- Some characters have "alternate" versions with a different nature at certain levels (e.g., "Kenshin 5" is power-only with no alternate; "Kenshin 6" has both a power version and a knowledge alternate). Nature-advantage strategy must account for which alternate the opponent is actually using, since guessing wrong means no advantage (or a disadvantage).
- Implementation implication: nature is a per-koma-level attribute, not a per-character attribute — different levels of the same character can have different nature options ("alternates").

## Koma level vs. usefulness (not strictly monotonic)

- Higher-level koma are not always strictly better: example given is Yoh 4 vs Yoh 5 — Yoh 5 has specials that require a support to combo into, while Yoh 4 combos into its X special on its own. Yoh 5's only advantage over Yoh 4 is "a tiny HP boost." Implication for implementation: HP scaling by level is real but small at some steps, and special move properties (combo-ability, startup) can regress at higher levels rather than strictly improve.

## Help komas — damage reduction

- Damage reduction help komas exist in (at least) three separate categories, each reducing a different damage type:
  1. Punch/Kick reduction (example: "Luffy" help koma). Energy blasts (e.g., Yusuke's Spirit Gun) are classified as punch-type for this purpose, not as specials.
  2. Blade/sword reduction (example: "Zoro" help koma, reduces damage from bladed attacks like Bankai Ichigo's slashes).
  3. Special-move damage reduction (example: "Sasuke" help koma).
- Reduction amount for Luffy's punch/kick reduction: author estimates **roughly 20%–30%** (author unconfirmed — guide explicitly says "I'm not too sure about how much damage reduction it gives").
- Stacking example: using both a sword-reduction koma (Zoro) and a special-reduction koma (Sasuke) against a single special attack (Getsuga Tenshou, itself a bladed special) reduces total damage taken to **about 50%** of the unreduced amount (author unconfirmed, and ambiguous whether this is additive stacking of two ~25-30% reductions or an author estimate of the combined effect — no formula given).
- Immunity help komas exist and can prevent status effects: examples cited include anti-stun, anti-support-seal, anti-judgement, and freeze/stun immunity in general. Also "increase guard" and "health regeneration" help komas exist. A "+1 SP" help koma type exists, presumably granting +1 to some SP-related stat/resource per use or per interval (mechanism not detailed).
- "Triple jump" is a help koma effect (grants an extra jump beyond default double-jump, per usage in sample decks — implies default jump count is 2 and this adds a 3rd).

## Support komas

- Support koma level (e.g., "Zoro 3", "Tsuna 2") determines their effect strength/behavior; different levels of the same support character can have very different roles (e.g., Zoro 3 launches opponents upward, used as a setup piece).
- Support koma cost enters the same budgeting logic as other koma types (not itemized numerically beyond the 17-block battle koma cap already noted).
- Recommended support count guidance (author's design opinion, not an enforced game rule): decks "really have no reason to use more than 2 supports"; author personally uses 1 in most decks; "3 really is unnecessary." This is presented as strategy advice, not confirmed as a hard cap — no statement that the game prevents using 3+ supports.
- Kagura 3 (support) is stated to force-switch the opponent's active character after landing **4–5 hits** on them (specific numeric threshold given by the guide for this support's trigger condition).
- Support komas can be "left behind" at a location to persist an effect (e.g., movement-stop, hit zone) while the player's active battle koma moves elsewhere — implies supports occupy independent battlefield state from the active character once deployed.
- Certain supports have conditional bonus effects: e.g., "Sanji 2" grants extra healing specifically when used on a female character.

## Deck archetypes and structural tradeoffs (author's strategic framework, not hard numeric rules)

Deck size categories referenced: solo (1 battle character), 2-character, 3-character, 4-character decks.

- **Solo deck:** all block budget can go into help komas on the single character. Weaknesses: no nature-switch option against a countering nature; total elimination risk from ring-out; single battle style.
- **2-character deck:** more room for help/support koma; potentially able to give damage-reduction koma to both characters. Weakness: less likely to have a nature advantage since fewer nature options are fielded.
- **3-character deck:** author's stated preference. Typically can afford full damage-reduction loadout (all 3 reduction types) on only one "ace" character; other characters get at most partial (e.g., 1 reduction koma each) coverage.
- **4-character deck:** most nature/style versatility, but cannot fit a full 3-type damage-reduction loadout on any single character due to block scarcity.

## Deckbuilding heuristics (strategy, condensed)

- Aim for one battle character per nature (Power/Knowledge/Laughter) when feasible, for matchup flexibility — not mandatory, described as advantageous rather than required.
- Choose battle koma compatible with the support's setup/juggle behavior (e.g., pick characters with aerial specials if the support launches opponents airborne).
- Concentrate all 3 damage-reduction help koma types onto a single "ace" character rather than spreading thin, per the author's recommendation.
- Play non-ace characters first to preserve the resource-intensive ace character from early ring-out risk.

## Sample decks (numeric loadouts only, strategy commentary omitted)

These are example decks from contributing players, included for koma-count/support reference, not as balance data:

- Solo: 6-koma Hitsugaya + Hiruma 2 support + Ryoma 3 support + help komas (triple jump, anti-support-seal, anti-stun, anti-judgement, increase guard or 3x damage reduction, health regen).
- 2-char: 5-koma Hitsugaya (+ Kazuki 1, Kakashi 1 attached) / 6-koma Vegeta (+ Sasuke 1, Piccolo 1, Hyoga 1 attached) + Shishio 3 support.
- 2-char: 6-koma Ichigo (+ Hanamichi 1) / 6-koma Yusuke (+ Kuwabara 1, Devil Bat 1) + Hijikata 3 support + Atobe 2 support (example of a deck intentionally using 2 supports).
- 2-char: 8-koma Edajima / 4-koma Kenshin + Hamii 2 support + Hanamichi 2 support + multiple +1 SP help komas.
- 2-char: 6-koma Luffy / 5-koma Kenshin (+ Neuro 1, Hitsugaya 1, Orohime 1, Light 1 attached) + Rurouni-Kenshin +1 SP help + Hanamichi 2 support + Satsuki 2 support.
- 2-char: 7-koma Ryotsu (+ Eve 1) / 6-koma Yoh (+ Hao 1) + Tezuka 2 support + Josuke 2 support + Shanks 1 help.
- 2-char: 6-koma Kenshin (+ Saito 1, Kaoru 1, Yahiko 1) / 5-koma Hitsugaya (+ Sakura 1) + Sanosuke 3 support + Rouji 2 support.
- 2-char: 6-koma Kakashi (+ Golden Pair 1, Shun 1) / 4-koma Eve (+ Sven 1, Kenshin 1, Eve 1) + Aya 2 support.
- 3-char: 6-koma Yusuke (+ Luffy 1, Zoro 1, Sasuke 1 attached — full triple damage-reduction loadout) / 4-koma Kurama / 4-koma Hiei + Huh Huh Bros 3 support. Total battle koma blocks: 6+4+4 = 14.
- 3-char: 7-koma Sasuke (+ Light 1, Orochimaru 1) / 4-koma Ryotsu / 4-koma Hitsugaya (+ Miranda 1) + Tsuna 2 support. Total: 7+4+4 = 15.
- 3-char: 5-koma Killua / 5-koma Sanji / 7-koma Sasuke (+ Rohan 1) + Nami 2 support. Total: 5+5+7 = 17 (at the stated 17-block cap).
- 3-char: 5-koma Luffy (+ Trunks 1, Sasuke 1) / 5-koma Kurama / 4-koma Ichigo + Zoro 3 support + 1 SP help. Total: 5+5+4 = 14.
- 3-char: 6-koma Vegeta (+ Piccolo 1) / 5-koma Sakura (+ Orochimaru 1) / 4-koma Kurama + Kagura 3 support. Total: 6+5+4 = 15.
- 4-char: 5-koma Kenshin / 4-koma Sanji / 4-koma Zoro / 4-koma Hiei, no supports, no dedicated helps. Total: 5+4+4+4 = 17 (at cap).
- 4-char: 5-koma Robin (+ Kurama 1) / 4-koma Anna / 4-koma Eve / 4-koma Lenalee + Sanji 2 support. Total: 5+4+4+4 = 17 (at cap).

Note: several of these totals independently confirm the 17-block battle-koma cap (multiple decks sum to exactly 17; none exceed it).
