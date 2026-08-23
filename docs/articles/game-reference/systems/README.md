# Systems Guides Index

Distilled from GameFAQs source guides in `sources/gamefaqs/raw/`. Each file covers one game system.

- **statistics.md** — Per-move damage, HP-by-koma-tier, and damage rankings for all 63 characters. Source: gf-59773 (Statistics FAQ, SomeoneF, v1.5).
- **support-koma.md** — Every support koma's size, damage, SP cost, status, range, and delay, by series/character. Source: gf-49288 (Support FAQ, shinyspark, v1.1).
- **healing.md** — HP-restore values and mechanics for support koma, specials, and status-duration-reduction help koma. Source: uncited in summary (companion to support-koma.md).
- **ally-boost.md** — Character-to-booster eligibility triples and Ally Boost trigger conditions. Source: 45966-ally-boost-faq.txt.
- **deck-making.md** — Deck-building rules: 17-block battle-koma cap, damage-reduction help koma, nature-per-koma-level, leveling tradeoffs. Source: 48966-deck-making.txt.
- **glitches.md** — Cataloged glitches/exploits and the underlying state-machine bugs they reveal (Time Stop, grab-state, ledge-clipping, stuck animations). Source: gf-47980 (Glitches FAQ, setyman, v1.13).
- **koma-list.md / koma-list.json** — Machine-readable koma list parsed from gf-45856 C5: 41 series, 305 characters, 1188 koma entries with natures, J-Soul, specials, boosts, passives (no gem costs — out of scope). Regenerate with `sources/gamefaqs/parse_koma_list.py`.

Moved out (not battle mechanics): `j-gem.md` (gem economy) and
`wireless-mode.md` (menus/match setup) now live in
`JUSToolkit/docs/articles/game-reference/`. The battle-relevant SP-gauge help
koma effects from the J-Gem FAQ were salvaged into `koma-system.md` first.
- **battle-system.md** — Core battle mechanics: point-scoring KO values, status-effect caps, Critical/Toughen multipliers, Leader rules. Source: gf-45856 (Genroh's JUS guide, C2: How to Play, v2.5).
- **koma-system.md** — Koma nature triangle, deck grid layout, koma-size roles, evolution system, and pre-made deck roster. Source: uncited in summary (companion to battle-system.md, gf-45856).
