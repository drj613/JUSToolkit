# Helper Koma Passives — Catalog

**Tier: OBSERVED / owner-supplied.** From the project owner's play knowledge: 42 passive categories, ~304 named helpers. Romanizations are as supplied (only clear typos fixed); Japanese in-game strings aren't yet matched.

Companion docs: `Koma-System-Observed-Behavior.md` (system ground truth), `../design/Koma-Deckbuilder-UX-Spec.md` (UI recreation).

**Relation to existing docs.** `Passives-Reference.md` has a "Helper Koma Effects (Directional)" section from community/GameFAQs data (~20 categories). This doc supersedes it with 42 owner-sourced categories plus the numeric-ID merge below. `Passives-Reference.md` stays the reference for **battle-character** passives — a different thing — and `battle-chars-passives.json` (66 entries) is its machine-readable form. Don't conflate the two: battle panels have an innate ability (Naruto's 忍道); helper panels emit one of these 42 passives.

## How helper passives work

Every **1-cell helper panel** carries exactly one passive. Placing a helper sets a **facing** (up/down/left/right) — that direction picks which battle character receives the buff. So a helper is a directional buff emitter, and deck layout isn't just packing: adjacency and facing decide who gets what.

This explains why the placement flow forces a direction step.

## Why this list matters for RE

Two payoffs beyond the koma sprint:

1. **The status-effect enum falls out of it.** Categories 4–13 are per-status immunities, giving us a discrete status list: **Confusion, Poison, Freeze, Judgment, Blindness, Shock, Burn, Speed-Down, Paralysis, Battle Seal, Support Seal** — 11 values, with both Seal types sharing one immunity passive. Direct lead for the combat-engine phase.
2. **The passive-effect vocabulary is the engine's stat-modifier surface.** Guard strength, max HP, max SP, damage by attack class (punch/kick vs special vs blade), SP gain triggers — each implies a field or hook in the character/battle state struct.

## Confirmed numbers

- **Leader sticker: +8 HP.**
- **Relationship adjacency: +8 HP**, same magnitude as Leader.
- **L / R stickers grant no bonus.** They only make a panel callable from the shoulder button: activate a battle character, fire that character's dream attack if already active, or summon a support.
- **Nature advantage magnitude: ~1.5× damage — owner unsure, treat as SPECULATIVE.**

### This resolves the `144/152` HP readout

An earlier session showed 4-koma Naruto at `144`, then `144/152` after sticker placement — logged as unexplained. With Leader = +8: **144 + 8 = 152**. The readout is **base HP / effective HP after deck bonuses**. Marking PLAUSIBLE-to-CONFIRMED on the arithmetic match — a second data point (a panel with Leader *plus* one relationship, expected `base / base+16`) would settle it.

## Numeric ability IDs — merged with existing RE work

`Cheat-Code-Analysis.md` already had a **numeric ability ID table** (`0x01`–`0x30`) from Action Replay codes, with the runtime array at RAM `0x021DF1D6+`:

| Address | Size | Purpose |
| --- | --- | --- |
| `0x021DF1D6` | 1 | Abilities count (max `0x21` = 33 simultaneously active) |
| `0x021DF1D7` | 1 | First ability ID |
| `0x021DF1D8`–`0x021DF1E8` | 20 | Additional ability ID array |

Merging that table with the owner's 42 categories is a clean win both ways.

**Prediction 3 was already right.** Immunity passives were predicted to be contiguous if IDs follow the game's grouping. They are: `0x19`–`0x22`, all ten, no gaps. CONFIRMED.

**The two sources agree on 38 passives** with no contradictions. The ID table names 38 effects and marks 10 IDs `Unknown`. The owner names 42. So:

### 4 previously-Unknown IDs now have a known effect

These four owner categories appear nowhere in the ID table, so they must fill four of the ten Unknown slots (`0x0B`, `0x0C`, `0x11`, `0x13`, `0x14`, `0x15`, `0x17`, `0x18`, `0x24`, `0x25`):

| Owner category | Effect | Likely ID slot (SPECULATIVE) |
| --- | --- | --- |
| 23 | Health recovers slowly (regen) | `0x13`–`0x15` or `0x17`–`0x18` |
| 24 | Increase Max Health | `0x13`–`0x15` or `0x17`–`0x18` |
| 27 | Increase Max Special Gauge by 1 | `0x13`–`0x15` or `0x17`–`0x18` |
| 40 | SP regenerates while on the field | `0x24` or `0x25` |

Slot reasoning from existing ID clustering: `0x0B`/`0x0C` sit between "less damage from Blades" (`0x0A`) and "less damage from Specials" (`0x0D`), so they're likely more damage-reduction classes, not stat boosts. `0x11` sits between "more SP from Coins" (`0x10`) and "more Health from Food" (`0x12`) — probably another pickup effect. `0x13`–`0x18` is the stat-boost neighbourhood (ending at `0x16` Guard strength), where the three HP/SP-max passives belong. `0x24`/`0x25` sit just before the SP-trigger block `0x26`–`0x30`, right where an SP-regen trigger fits.

**This is a hypothesis, not a result.** Confirming it needs an in-game check or a cheat-code experiment writing single IDs into `0x021DF1D7` and observing the effect.

### 6 Unknown IDs remain genuinely unidentified

After the four above, six Unknown slots have no owner category: two damage-reduction candidates (`0x0B`, `0x0C`), one pickup candidate (`0x11`), and three others. Either uncatalogued passives or unused IDs. **The owner said "have been identified" — ~6 missing is consistent, not contradictory.**

### Where this changes the decode plan

The passive-ID field in `koma.bin` should hold values in **`0x01`–`0x30`** (48 slots), not "about 42 distinct values". Much sharper filter: for size-1 records only, find a byte whose values all land in `1..48`. Candidates: `0x6`, `0x7`, `0xA`, `0xB`.

Also: the existing table came from **RAM**, not `koma.bin`. So there are two things to find — the static passive ID per koma record, and the runtime array at `0x021DF1D7` collecting a character's active abilities. They may or may not share numbering; worth checking rather than assuming.

## The 42 categories

Counts are the number of helper characters listed per category.

### Mobility (3)

| # | Passive | N | Characters |
|---|---|---|---|
| 1 | **Triple Jump** (tap A three times) | 5 | Devil Bat (Eyeshield 21), Hanamichi Sakuragi (Slam Dunk), Gajira Norimaki (Dr. Slump), Eve (Black Cat), Sipuxiang (Houshin Engi) |
| 2 | **Wall Jump** (tap A when falling next to a wall) | 3 | Linali Lee (D.Gray-man), Naruto Uzumaki (Naruto), Fuusuke (Ninku) |
| 3 | **Air Dash** (tap ←← or →→ in mid-air) | 7 | Sena Kobayakawa (Eyeshield 21), Tsubasa Ozora (Captain Tsubasa), Hien (Sakigake!! Otokojuku), Kaede Rukawa (Slam Dunk), Yoruichi Shihoin (Bleach), Kisuke Urahara (Bleach), Kenshin Himura (Rurouni Kenshin) |

### Status immunity (10 categories, 11 statuses)

| # | Immune to | N | Characters |
|---|---|---|---|
| 4 | **Confusion** | 6 | Haru Miura (Katekyo Hitman Reborn), Kotaru Katsura (Gintama), Higure Shineruo (KochiKame), Etekichi (Jungle King Ta-chan), Hammer (Pyuu to Fuku! Jaguar), Pogii (Pyuu to Fuku! Jaguar) |
| 5 | **Poison** | 6 | Brocken Jr. (Kinnikuman), Kaoru Kaidoh (Prince of Tennis), Alister Crowly (D.Gray-man), Papillon (Busou Renkin), Outenkun (Houshin Engi), Hiei (Yu Yu Hakusho) |
| 6 | **Freeze** | 7 | Yukime (Jigoku Sensei Nube), Horo Horo (Shaman King), Hyoga (Saint Seiya), Aisu (Taizo Mote King Saga), Keigo Atobe (Prince of Tennis), Rukia Kuchiki (Bleach), Toushiro Hitsugaya (Bleach) |
| 7 | **Judgment** | 8 | Warsman (Kinnikuman), Crystal Boy (Space Adventure Cobra), Amidamaru (Shaman King), Spin (Taizo Mote King Saga), Arale Norimaki (Dr. Slump), Obotchaman (Dr. Slump), Hamii (Pyuu to Fuku! Jaguar), Jirou Hame (Pyuu to Fuku! Jaguar) |
| 8 | **Blindness** | 4 | Allen Walker (D.Gray-man), Sai (Naruto), Sousuke Aizen (Bleach), Kaname Tousen (Bleach) |
| 9 | **Shock** | 3 | Lambo (Katekyo Hitman Reborn), Killua Zoaldyck (Hunter X Hunter), Train Heartnet (Black Cat) |
| 10 | **Burn** | 3 | Doryoku Man (Tottemo! Luckyman), Kyoko Kirisaki (Black Cat), Makoto Shishio (Rurouni Kenshin) |
| 11 | **Speed-Down** | 4 | Hayato Honda (KochiKame), Johnny Joestar (Jojo's Bizarre Adventure), Makibaou (Midori no Makibaou), Cascade (Midori no Makibaou) |
| 12 | **Paralysis** | 2 | Hatenkou (Bobobo-bo Bo-bobo), Neuro Nogami (Majin Tantei Nogami Neuro) |
| 13 | **Battle Seal + Support Seal** (both) | 2 | Rohan Kishibe (Jojo's Bizarre Adventure), Jaguar Junichi (Pyuu to Fuku! Jaguar) |

### Status handling and perception (2)

| # | Passive | N | Characters |
|---|---|---|---|
| 14 | **Status effect duration cut** | 9 | Mamori Anzaki (Eyeshield 21), Josuke Higashikata (Jojo's Bizarre Adventure), Mitsuyoshi Anzai (Slam Dunk), Sakura Haruno (Naruto), Tsunade (Naruto), Leorio (Hunter X Hunter), Orihime Inoue (Bleach), X (Majin Tantei Nogami Neuro), Tony Tony Chopper (One Piece) |
| 15 | **See invisible characters** | 8 | Yukimitsu Manabu (Eyeshield 21), Meat-kun (Kinnikuman), Volvo Saigo (KochiKame), Haru Mido (KochiKame), Wan Taaren (Sakigake!! Otokojuku), Joseph Joestar (Jojo's Bizarre Adventure), River Wenham (D.Gray-man), Eishi Sasazuka (Majin Tantei Nogami Neuro) |

### Offense and damage resistance (4)

| # | Passive | N | Characters |
|---|---|---|---|
| 16 | **Attack-Up when health is low** | 7 | Musashi (Eyeshield 21), Cobra (Space Adventure Cobra), Yoh Asakura (Shaman King), Hisashi Mitsui (Slam Dunk), Ryoma Echizen (Prince of Tennis), Raoh (Hokuto no Ken), Muhyo Toru (Muhyo to Rouji) |
| 17 | **Less damage from Punches and Kicks** | 2 | Kinnikuman (Kinnikuman), Monkey D. Luffy (One Piece) |
| 18 | **Less damage from Special Attacks** | 6 | Jotaro Kujo (Jojo's Bizarre Adventure), Seiya (Saint Seiya), Sasuke Uchiha (Naruto), Kakashi Hatake (Naruto), Kuroro Lucifer (Hunter X Hunter), Sven Volified (Black Cat) |
| 19 | **Less damage from Blades** | 8 | Takeshi Yamamoto (Katekyo Hitman Reborn), Robin Mask (Kinnikuman), Shiryu (Saint Seiya), Yuu Kanda (D.Gray-man), Trunks (Dragon Ball), Yahiko Myojin (Rurouni Kenshin), Roronoa Zoro (One Piece), Franky (One Piece) |

Note category 17/18/19: damage is classified by **attack class** — punch/kick, special, blade. Ties to `DamageFlags-Character-Classification.md`.

### Guarding (3)

| # | Passive | N | Characters |
|---|---|---|---|
| 20 | **Use Special Gauge to Auto-Guard** | 10 | Genzo Wakabyashi (Captain Tsubasa), Roberto Hongo (Captain Tsubasa), Kamesennin (Dragon Ball), Gaara (Naruto), Biscuit Kruger (Hunter X Hunter), Captain Bravo (Busou Renkin), Page (Muhyo to Rouji), Genkai (Yu Yu Hakusho), Masa-chan (Rokudenashi Blues), Nico Robin (One Piece) |
| 21 | **Never move when blocking on a moving platform** | 6 | Kurita Ryokan (Eyeshield 21), Daikichi Komusubi (Eyeshield 21), Taizo Hasegawa (Gintama), Sadaharu (Gintama), Yasutora Sado (Bleach), Tokoro Tennosuke (Bobobo-bo Bo-bobo) |
| 22 | **Increase Guard strength** | 16 | Izumi Isozaki (I"s), Misuzu Sotomura (Ichigo 100%), Sanae Nakasawa (Captain Tsubasa), Ayame Sarutobi (Gintama), Maria (KochiKame), Lady Armaroid (Space Adventure Cobra), Hiroshi Tateno (Jigoku Sensei Nube), Manta Oyamada (Shaman King), Miranda Lott (D.Gray-man), Misa Amane (Death Note), Unchi-kun (Dr. Slump), Tokiko Tsumura (Busou Renkin), Tatsuki Arisawa (Bleach), Yuria (Hokuto no Ken), Akane-chan (Majin Tantei Nogami Neuro), Kaoru Kamiya (Rurouni Kenshin) |

### Health (5)

| # | Passive | N | Characters |
|---|---|---|---|
| 23 | **Health recovers slowly** (regen) | 6 | Leon (Katekyo Hitman Reborn), Ikki (Saint Seiya), Piccolo (Dragon Ball), Majin Buu (Dragon Ball), Orochimaru (Naruto), Kazuki Mutou (Busou Renkin) |
| 24 | **Increase Max Health** | 15 | Iori Yoshizuki (I"s), Aya Toujo (Ichigo 100%), Kyoko Sasegawa (Katekyo Hitman Reborn), Otae (Gintama), Reiko Akimoto (KochiKame), Kyoko Inaba (Jigoku Sensei Nube), Haruko Akagi (Slam Dunk), Midori Yamabuki (Dr. Slump), Takane Shirakawa (Pyuu to Fuku! Jaguar), Saya Minatsuki (Black Cat), Rin (Hokuto no Ken), Nana Takenouchi (Muhyo to Rouji), Anzu Mazaki (Yu-Gi-Oh), Botan (Yu Yu Hakusho), Chiaki (Rokudenashi Blues) |
| 25 | **Max Health increases when you come back from a KO** | 3 | Jonathan Joestar (Jojo's Bizarre Adventure), Mu (Saint Seiya), Son Goku (Dragon Ball) |
| 26 | **Gain more Health from Food** | 4 | Tsukasa Nishino (Ichigo 100%), Bianchi (Katekyo Hitman Reborn), Matoi Giboshi (KochiKame), Sanji (One Piece) |
| 27 | **Increase Max Special Gauge by 1** | 11 | Edajima Heihachi (Sakigake!! Otokojuku), Gyro Zeppeli (Jojo's Bizarre Adventure), Athena (Saint Seiya), Takanori Akagi (Slam Dunk), Kaiousama (Dragon Ball), Jiraiya (Naruto), Zangetsu (Bleach), Isshin Kurosaki (Bleach), Chuubei (Midori no Makibaou), Seijuro Hiko (Rurouni Kenshin), Shanks (One Piece) |

### SP / Special Gauge gain triggers (15)

The largest family — 15 distinct trigger conditions. This is the game's main build-craft lever.

| # | Trigger | N | Characters |
|---|---|---|---|
| 28 | **Gain more SP from Coins** | 4 | Keiichi Nakagawa (KochiKame), Pedro (Jungle King Ta-chan), Luckyman (Tottemo! Luckyman), Bulma (Dragon Ball) |
| 29 | **Breaking Item boxes** | 7 | Cerberos (Eyeshield 21), Seto Ichitaka (I"s), Junpei Manaka (Ichigo 100%), Kagura (Gintama), Ryotsu Kankichi (KochiKame), Jane (Jungle King Ta-chan), Nami (One Piece) |
| 30 | **Attacking with or blocking a Battle character** | 11 | Monta (Eyeshield 21), Hayato Gokudera (Katekyo Hitman Reborn), Kojiro Hyuuga (Captain Tsubasa), Toshiro Hijikata (Gintama), Ryuji Toramaru (Sakigake!! Otokojuku), Takashi Kawamura (Prince of Tennis), Ichigo Kurosaki (Bleach), Renji Abarai (Bleach), Heppokomaru (Bobobo-bo Bo-bobo), Kazuma Kuwabara (Yu Yu Hakusho), Sanosuke Sagara (Rurouni Kenshin) |
| 31 | **Attacking with or blocking a Support character** | 10 | Doburoku Sakaki (Eyeshield 21), Tsuna & Reborn (Katekyo Hitman Reborn), Isao Kondou (Gintama), Kaipan Deka (KochiKame), Giorno Giovanna (Jojo's Bizarre Adventure), Tezuka Kunimitsu (Prince of Tennis), Kuririn (Dragon Ball), Taikoubou (Houshin Engi), Dengaku Man (Bobobo-bo Bo-bobo), Kiwi & Mozu (One Piece) |
| 32 | **Multi-hitting** | 14 | Hah Brothers (Eyeshield 21), I-Pin (Katekyo Hitman Reborn), Otose (Gintama), Ashuraman (Kinnikuman), Daijiro Ohara (KochiKame), Anna Kyoyama (Shaman King), Mello (Death Note), Son Gohan (Dragon Ball), Frieza (Dragon Ball), Bo-bobo (Bobobo-bo Bo-bobo), Ko Patch (Bobobo-bo Bo-bobo), Hiroto Honda (Yu-Gi-Oh), Taison Maeda (Rokudenashi Blues), Yoneji (Rokudenashi Blues) |
| 33 | **Regen if you don't change characters or use Supports** | 9 | Suzuna Taki (Eyeshield 21), Kyoya Hibari (Katekyo Hitman Reborn), Buffaloman (Kinnikuman), Omito Date (Sakigake!! Otokojuku), Hao Asakura (Shaman King), Dio Brando (Jojo's Bizarre Adventure), Cross Marian (D.Gray-man), Seto Kaiba (Yu-Gi-Oh), Kurama (Yu Yu Hakusho) |
| 34 | **Multiple Special Attacks in a short time** | 11 | Natsuhiko Taki (Eyeshield 21), Itsuki Akiba (I"s), Satsuki Kitaooji (Ichigo 100%), Chocolove (Shaman King), Superstar Man (Tottemo! Luckyman), Gotenks (Dragon Ball), Hiroyuki (Ninku), Dakki So (Houshin Engi), Don Patch (Bobobo-bo Bo-bobo), Gyorai Girl (Bobobo-bo Bo-bobo), Jonouchi Katsuya (Yu-Gi-Oh) |
| 35 | **Regen when you don't move or attack** | 11 | Tetsuo Ishimaru (Eyeshield 21), Sogo Okita (Gintama), Yamazaki (Gintama), Tatsunosuke Sakonji (KochiKame), Terai (KochiKame), J (Sakigake!! Otokojuku), Rabi (D.Gray-man), Kurapica (Hunter X Hunter), Gin Ichimaru (Bleach), Piko (Muhyo to Rouji), Katsuji Yamashita (Rokudenashi Blues) |
| 36 | **Attacking or blocking characters of an opposing nature** | 11 | Yoichi Hiruma (Eyeshield 21), Hiroshi Sotomura (Ichigo 100%), Terryman (Kinnikuman), Lemon Giboshi (KochiKame), Raiden (Sakigake!! Otokojuku), Inui Sadaharu (Prince of Tennis), Koumi Lee (D.Gray-man), Light Yagami (Death Note), Senbee Norimaki (Dr. Slump), Pochi (Ninku), Yugi Mutou (Yu-Gi-Oh) |
| 37 | **Attacking or blocking while your health is low** | 8 | Jaki Daigoin (Sakigake!! Otokojuku), Tao Ren (Shaman King), Jolyne Kujo (Jojo's Bizarre Adventure), Dr. Mashirito (Dr. Slump), Vegeta (Dragon Ball), Service Man (Bobobo-bo Bo-bobo), Enchuu (Muhyo to Rouji), Hajime Saito (Rurouni Kenshin) |
| 38 | **KO an opponent** | 8 | Yui Minamito (Ichigo 100%), Kinniku Daiou (Kinnikuman), Genji Togashi (Sakigake!! Otokojuku), Taizo (Taizo Mote King Saga), Mr. Satan (Dragon Ball), Kon (Bleach), Bat (Hokuto no Ken), Yoichi Hiko (Muhyo to Rouji) |
| 39 | **Gain 1 Special bar when you're KOed** | 5 | Shinpachi Shimura (Gintama), Takeshi Momoshiro (Prince of Tennis), Hisoka (Hunter X Hunter), Piyo Hiko (Pyuu to Fuku! Jaguar), Usopp (One Piece) |
| 40 | **Regen while you're on the field** | 6 | Momotaro Tsurugi (Sakigake!! Otokojuku), Nube (Jigoku Sensei Nube), Ta-chan (Jungle King Ta-chan), Gon Freecs (Hunter X Hunter), Kenshiro (Hokuto no Ken), Yusuke Urameshi (Yu Yu Hakusho) |
| 41 | **Blocking at the last moment** (just-guard) | 10 | Seijuro Shin (Eyeshield 21), Gintoki Sakata (Gintama), Shun (Saint Seiya), Shusuke Fuji (Prince of Tennis), L (Death Note), Near (Death Note), Byakuya Kuchiki (Bleach), Toki (Hokuto no Ken), Gaoh (Bobobo-bo Bo-bobo), Rouji (Muhyo to Rouji) |
| 42 | **Attacking or blocking chain attacks** | 8 | Haruto Sakuraba (Eyeshield 21), Ramenman (Kinnikuman), Haya Isowashi (KochiKame), Ryota Miyagi (Slam Dunk), Oishi & Eiji (Prince of Tennis), Uryuu Ishida (Bleach), Rei (Hokuto no Ken), Softon (Bobobo-bo Bo-bobo) |

## Predictions for the data decode

1. **Helper-panel count ≈ 304.** Size-1 records in `koma.bin` should be near 304. The owner's list may be incomplete — above 304 is expected, well below flags a problem with the size-field hypothesis.
2. **Passive-ID field holds values in `0x01`–`0x30`.** For size-1 records only, find a byte whose values all land in `1..48`. Candidates: `0x6`, `0x7`, `0xA`, `0xB`.
3. ~~Passive IDs cluster by family.~~ **CONFIRMED** — immunities are contiguous at `0x19`–`0x22` in `Cheat-Code-Analysis.md`. Any candidate field should show a dense cluster of ten values for the ten immunity helpers.
4. **A status-effect enum of ~11 values exists in the battle code.** Confusion, Poison, Freeze, Judgment, Blindness, Shock, Burn, Speed-Down, Paralysis, Battle Seal, Support Seal. Look for an 11-or-16-wide bitmask or a jump table of that arity. Immunity is probably a bitmask on the character state struct, since one passive covers both Seal types.
5. **Attack-class damage typing exists**: punch/kick, special, blade. Cross-check against `DamageFlags-Character-Classification.md`.
6. **+8 HP is a shared constant** for both Leader and relationship bonuses. A literal `8` near HP setup code, applied twice, is a findable signature — try `query.py search-imm 8` scoped to deck/HP init functions.

## Still unknown

- Numeric IDs for any passive — nothing here ties to a byte value yet.
- Whether passive **magnitudes** (how much guard strength, how much max HP) are per-passive constants or per-character.
- Whether facing picks a single adjacent battle character or a whole row/column.
- Nature damage multiplier — owner guesses ~1.5×, unverified.
- Whether the 42 categories are exhaustive or a 43rd exists with no identified members.
- How helper passives stack when two helpers point at the same battle character.
