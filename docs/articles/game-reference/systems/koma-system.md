# Koma System (Nature, Sizes, Evolution, Help Skills, Pre-Made Decks)

- **Source guide:** "JUMP! ULTIMATE STARS" FAQ/Walkthrough
- **Author:** Genroh
- **Version:** 2.5 (Last Update 08/07/07)
- **GameFAQs FAQ id:** gf-45856
- **Reliability:** Unverified community claim source (fan-written FAQ). Treat all
  numbers/mechanics below as claims to verify against the actual game/ROM, not
  ground truth.

Extracted from guide sections "C3: All About Koma" and "C7: Pre-Made Decks" only.

## Koma basics

- "Koma" = Japanese for "panel"; koma are the puzzle-piece-shaped units that make
  up a character's portrait/deck entry.
- The deck-building grid ("Koma Screen") is **4 rows x 5 columns = 20 cells**.
- A finished deck visually resembles a manga page (koma pieces tile together).
- Koma vary in shape/size per character.

## Koma roles by size

| Size (cells) | Role | Function |
|---|---|---|
| 1 koma | Help | Passive buff/heal/other beneficial effect, assigned to a specific battle character |
| 2-3 koma | Support | Summon that attacks/applies a status effect, then teleports out |
| 4-8 koma | Battle | Directly controlled character; tag in/out via stylus tap when 2+ are in the deck |

Rules noted by the author:
- Any Support character can also be slotted as a Help character.
- Any Battle character can also be slotted as a Support and/or Help character.

## Koma Nature (damage triangle)

Every Battle/Support character has an inherent nature: **Laughter, Power, or
Knowledge**. Shown in Deck Maker via a kanji glyph colored by nature:

- Red = Power
- Green = Knowledge
- Yellow = Laughter

Triangle (rock-paper-scissors): **Power beats Knowledge, Knowledge beats
Laughter, Laughter beats Power.**

**Damage multiplier: attacking with a nature that is strong against the
target's nature deals 1.5x damage.**

Examples given by the author: Luffy = Power, Bo-bobo = Laughter, Yoh = Knowledge.

Edge case: some characters have specific special moves whose nature differs
from their koma's inherent nature (exceptions must be looked up per-character;
not enumerated in this section).

## Koma Evolution (structure only — gem economy is out of scope)

- Each character has an "Evolution Chart" of koma forms. Notation: `H` = Help
  koma, `S` = Support koma, `B` = Battle koma; number suffix = koma size in
  cells (e.g., `B4` = 4-cell Battle koma, `S3` = 3-cell Support koma).
- Every character's chart roots at a 1-cell Help koma (`H`) with branching
  paths to Support and Battle forms.
- Battle-relevant structural fact: a koma's role/size (and thus its nature and
  stats) is a node in this per-character graph — the deck can only contain
  forms the chart defines. Full per-character charts are in `koma-list.json`.
- How nodes are unlocked (gem purchases, cross-character prerequisites, etc.)
  is progression economy — out of scope; see
  `JUSToolkit/docs/articles/game-reference/` if ever needed.

## Help Character passives

Mechanics:
- All Help koma effects are passive (no activation input).
- Each Help koma has a directional arrow; it must be pointed at the specific
  Battle character who receives its effect.
- **Stacking rule:** two or more Help komas granting the *same* effect on one
  character cancel each other out (net effect = as if neither were equipped).

Catalog of identified Help skills and the characters that grant them
(character → source series in parentheses):

- **Triple Jump** (tap A x3): Devil Bat (Eyeshield 21), Hanamichi Sakuragi (Slam Dunk), Gajira Norimaki (Dr. Slump), Eve (Black Cat), Sipuxiang (Houshin Engi)
- **Wall Jump** (tap A while falling next to wall): Linali Lee (D.Gray-man), Naruto Uzumaki (Naruto), Fuusuke (Ninku)
- **Air Dash** (double-tap left or right in mid-air): Sena Kobayakawa (Eyeshield 21), Tsubasa Ozora (Captain Tsubasa), Hien (Sakigake!! Otokojuku), Kaede Rukawa (Slam Dunk), Yoruichi Shihoin (Bleach), Kisuke Urahara (Bleach), Kenshin Himura (Rurouni Kenshin)
- **Immunity: Confusion**: Haru Miura (Katekyo Hitman Reborn), Kotaro Katsura (Gintama), Higure Shineruo (KochiKame), Etekichi (Jungle King Ta-chan), Hammer (Pyuu to Fuku! Jaguar), Pogii (Pyuu to Fuku! Jaguar)
- **Immunity: Poison**: Brocken Jr. (Kinnikuman), Kaoru Kaidoh (Prince of Tennis), Alister Crowly (D.Gray-man), Papillon (Busou Renkin), Outenkun (Houshin Engi), Hiei (Yu Yu Hakusho)
- **Immunity: Freeze**: Yukime (Jigoku Sensei Nube), Horo Horo (Shaman King), Hyoga (Saint Seiya), Aisu (Taizo Mote King Saga), Keigo Atobe (Prince of Tennis), Rukia Kuchiki (Bleach), Toushiro Hitsugaya (Bleach)
- **Immunity: Judgment**: Warsman (Kinnikuman), Crystal Boy (Space Adventure Cobra), Amidamaru (Shaman King), Spin (Taizo Mote King Saga), Arale Norimaki (Dr. Slump), Obotchaman (Dr. Slump), Hamii (Pyuu to Fuku! Jaguar), Jirou Hame (Pyuu to Fuku! Jaguar)
- **Immunity: Blindness**: Allen Walker (D.Gray-man), Sai (Naruto), Sousuke Aizen (Bleach), Kaname Tousen (Bleach)
- **Immunity: Shock**: Lambo (Katekyo Hitman Reborn), Killua Zoaldyck (Hunter X Hunter), Train Heartnet (Black Cat)
- **Immunity: Burn**: Doryoku Man (Tottemo! Luckyman), Kyoko Kirisaki (Black Cat), Makoto Shishio (Rurouni Kenshin)
- **Immunity: Speed-Down**: Hayato Honda (KochiKame), Johnny Joestar (Jojo's Bizarre Adventure), Makibaou (Midori no Makibaou), Cascade (Midori no Makibaou)
- **Immunity: Paralysis**: Hatenkou (Bobobo-bo Bo-bobo), Neuro Nogami (Majin Tantei Nogami Neuro)
- **Immunity: Battle and Support Seal**: Rohan Kishibe (Jojo's Bizarre Adventure), Jaguar Junichi (Pyuu to Fuku! Jaguar)
- **Status-effect duration reduced**: Mamori Anzaki (Eyeshield 21), Josuke Higashikata (Jojo's Bizarre Adventure), Mitsuyoshi Anzai (Slam Dunk), Sakura Haruno (Naruto), Tsunade (Naruto), Leorio (Hunter X Hunter), Orihime Inoue (Bleach), X (Majin Tantei Nogami Neuro), Tony Tony Chopper (One Piece)
- **See invisible characters**: Yukimitsu Manabu (Eyeshield 21), Meat-kun (Kinnikuman), Volvo Saigo (KochiKame), Haru Mido (KochiKame), Wan Taaren (Sakigake!! Otokojuku), Joseph Joestar (Jojo's Bizarre Adventure), River Wenham (D.Gray-man), Eishi Sasazuka (Majin Tantei Nogami Neuro)
- **Attack Up when health is low**: Musashi (Eyeshield 21), Cobra (Space Adventure Cobra), Yoh Asakura (Shaman King), Hisashi Mitsui (Slam Dunk), Ryoma Echizen (Prince of Tennis), Raoh (Hokuto no Ken), Muhyo Toru (Muhyo to Rouji)
- **Reduce damage from Punches/Kicks**: Kinnikuman (Kinnikuman), Monkey D. Luffy (One Piece)
- **Reduce damage from Special Attacks**: Jotaro Kujo (Jojo's Bizarre Adventure), Seiya (Saint Seiya), Sasuke Uchiha (Naruto), Kakashi Hatake (Naruto), Kuroro Lucifer (Hunter X Hunter), Sven Volified (Black Cat)
- **Reduce damage from Blades**: Takeshi Yamamoto (Katekyo Hitman Reborn), Robin Mask (Kinnikuman), Shiryu (Saint Seiya), Yuu Kanda (D.Gray-man), Trunks (Dragon Ball), Yahiko Myojin (Rurouni Kenshin), Roronoa Zoro (One Piece), Franky (One Piece)
- **Use Special Gauge to auto-guard**: Genzo Wakabyashi (Captain Tsubasa), Roberto Hongo (Captain Tsubasa), Kamesennin (Dragon Ball), Gaara (Naruto), Biscuit Kruger (Hunter X Hunter), Captain Bravo (Busou Renkin), Page (Muhyo to Rouji), Genkai (Yu Yu Hakusho), Masa-chan (Rokudenashi Blues), Nico Robin (One Piece)
- **No knockback while blocking on a moving platform**: Kurita Ryokan (Eyeshield 21), Daikichi Komusubi (Eyeshield 21), Taizo Hasegawa (Gintama), Sadaharu (Gintama), Yastora Sado (Bleach), Tokoro Tennosuke (Bobobo-bo Bo-bobo)
- **Guard strength increased**: Izumi Isozaki (I"s), Misuzu Sotomura (Ichigo 100%), Sanae Nakasawa (Captain Tsubasa), Ayame Sarutobi (Gintama), Maria (KochiKame), Lady Armaroid (Space Adventure Cobra), Hiroshi Tateno (Jigoku Sensei Nube), Manta Oyamada (Shaman King), Miranda Lott (D.Gray-man), Misa Amane (Death Note), Unchi-kun (Dr. Slump), Tokiko Tsumura (Busou Renkin), Tatsuki Arisawa (Bleach), Yuria (Hokuto no Ken), Akane-chan (Majin Tantei Nogami Neuro), Kaoru Kamiya (Rurouni Kenshin)
- **Health regenerates slowly (passive)**: Leon (Katekyo Hitman Reborn), Ikki (Saint Seiya), Piccolo (Dragon Ball), Majin Buu (Dragon Ball), Orochimaru (Naruto), Kazuki Mutou (Busou Renkin)
- **Max Health increased**: Iori Yoshizuki (I"s), Aya Toujo (Ichigo 100%), Kyoko Sasegawa (Katekyo Hitman Reborn), Otae (Gintama), Reiko Akimoto (KochiKame), Kyoko Inaba (Jigoku Sensei Nube), Haruko Akagi (Slam Dunk), Midori Yamabuki (Dr. Slump), Takane Shirakawa (Pyuu to Fuku! Jaguar), Saya Minatsuki (Black Cat), Rin (Hokuto no Ken), Nana Takenouchi (Muhyo to Rouji), Anzu Mazaki (Yu-Gi-Oh), Botan (Yu Yu Hakusho), Chiaki (Rokudenashi Blues)
- **Max Special Gauge +1**: Edajima Heihachi (Sakigake!! Otokojuku), Gyro Zeppeli (Jojo's Bizarre Adventure), Athena (Saint Seiya), Takanori Akagi (Slam Dunk), Kaiousama (Dragon Ball), Jiraiya (Naruto), Zangetsu (Bleach), Isshin Kurosaki (Bleach), Chuubei (Midori no Makibaou), Seijuro Hiko (Rurouni Kenshin), Shanks (One Piece)
- **Max Health increases on revival after KO**: Jonothan Joestar (Jojo's Bizarre Adventure), Mu (Saint Seiya), Son Goku (Dragon Ball)
- **More Health gained from Food items**: Tsukasa Nishino (Ichigo 100%), Bianchi (Katekyo Hitman Reborn), Matoi Giboshi (KochiKame), Sanji (One Piece)
- **More SP gained from Coin items**: Keiichi Nakagawa (KochiKame), Pedro (Jungle King Ta-chan), Luckyman (Tottemo! Luckyman), Bulma (Dragon Ball)
- **Special Gauge up on breaking item boxes**: Cerberos (Eyeshield 21), Seto Ichitaka (I"s), Junpei Manaka (Ichigo 100%), Kagura (Gintama), Ryotsu Kankichi (KochiKame), Jane (Jungle King Ta-chan), Nami (One Piece)
- **SP up when attacking/blocking with a Battle character**: Monta (Eyeshield 21), Hayato Gokudera (Katekyo Hitman Reborn), Kojiro Hyuuga (Captain Tsubasa), Toshiro Hijikata (Gintama), Ryuji Toramaru (Sakigake!! Otokojuku), Takashi Kawamura (Prince of Tennis), Ichigo Kurosaki (Bleach), Renji Abarai (Bleach), Heppokomaru (Bobobo-bo Bo-bobo), Kazuma Kuwabara (Yu Yu Hakusho), Sanosuke Sagara (Rurouni Kenshin)
- **SP up when attacking/blocking with a Support character**: Doburoku Sakaki (Eyeshield 21), Tsuna & Reborn (Katekyo Hitman Reborn), Isao Kondou (Gintama), Kaipan Deka (KochiKame), Giorno Giovanna (Jojo's Bizarre Adventure), Tezuka Kunimitsu (Prince of Tennis), Kuririn (Dragon Ball), Taikoubou (Houshin Engi), Dengaku Man (Bobobo-bo Bo-bobo), Kiwi & Mozu (One Piece)
- **SP up on multi-hit attacks**: Hah Brothers (Eyeshield 21), I-Pin (Katekyo Hitman Reborn), Otose (Gintama), Ashuraman (Kinnikuman), Daijiro Ohara (KochiKame), Anna Kyoyama (Shaman King), Mello (Death Note), Son Gohan (Dragon Ball), Frieza (Dragon Ball), Bo-bobo (Bobobo-bo Bo-bobo), Ko Patch (Bobobo-bo Bo-bobo), Hiroto Honda (Yu-Gi-Oh), Taison Maeda (Rokudenashi Blues), Yoneji (Rokudenashi Blues)
- **SP regenerates if you don't tag or use Support**: Suzuna Taki (Eyeshield 21), Kyoya Hibari (Katekyo Hitman Reborn), Buffaloman (Kinnikuman), Omito Date (Sakigake!! Otokojuku), Hao Asakura (Shaman King), Dio Brando (Jojo's Bizarre Adventure), Cross Marian (D.Gray-man), Seto Kaiba (Yu-Gi-Oh), Kurama (Yu Yu Hakusho)
- **SP up from using multiple Specials in a short window**: Natsuhiko Taki (Eyeshield 21), Itsuki Akiba (I"s), Satsuki Kitaooji (Ichigo 100%), Chocolove (Shaman King), Superstar Man (Tottemo! Luckyman), Gotenks (Dragon Ball), Hiroyuki (Ninku), Dakki So (Houshin Engi), Don Patch (Bobobo-bo Bo-bobo), Gyorai Girl (Bobobo-bo Bo-bobo), Jonouchi Katsuya (Yu-Gi-Oh)
- **SP regenerates when idle (no move/attack)**: Tetsuo Ishimaru (Eyeshield 21), Sogo Okita (Gintama), Yamazaki (Gintama), Tatsunosuke Sakonji (KochiKame), Terai (KochiKame), J (Sakigake!! Otokojuku), Rabi (D.Gray-man), Kurapica (Hunter X Hunter), Gin Ichimaru (Bleach), Piko (Muhyo to Rouji), Katsuji Yamashita (Rokudenashi Blues)
- **SP up attacking/blocking opposing-nature characters**: Yoichi Hiruma (Eyeshield 21), Hiroshi Sotomura (Ichigo 100%), Terryman (Kinnikuman), Lemon Giboshi (KochiKame), Raiden (Sakigake!! Otokojuku), Inui Sadaharu (Prince of Tennis), Koumi Lee (D.Gray-man), Light Yagami (Death Note), Senbee Norimaki (Dr. Slump), Pochi (Ninku), Yugi Mutou (Yu-Gi-Oh)
- **Special Gauge up attacking/blocking while HP low**: Jaki Daigoin (Sakigake!! Otokojuku), Tao Ren (Shaman King), Jolyne Kujo (Jojo's Bizarre Adventure), Dr. Mashirito (Dr. Slump), Vegeta (Dragon Ball), Service Man (Bobobo-bo Bo-bobo), Enchuu (Muhyo to Rouji), Hajime Saito (Rurouni Kenshin)
- **Special Gauge up on KO of opponent**: Yui Minamito (Ichigo 100%), Kinniku Daiou (Kinnikuman), Genji Togashi (Sakigake!! Otokojuku), Taizo (Taizo Mote King Saga), Mr. Satan (Dragon Ball), Kon (Bleach), Bat (Hokuto no Ken), Yoichi Hiko (Muhyo to Rouji)
- **Gain 1 Special bar when KOed**: Shinpachi Shimura (Gintama), Takeshi Momoshiro (Prince of Tennis), Hisoka (Hunter X Hunter), Piyo Hiko (Pyuu to Fuku! Jaguar), Usopp (One Piece)
- **Special Gauge regenerates while on-field**: Momotaro Tsurugi (Sakigake!! Otokojuku), Nube (Jigoku Sensei Nube), Ta-chan (Jungle King Ta-chan), Gon Freecs (Hunter X Hunter), Kenshiro (Hokuto no Ken), Yusuke Urameshi (Yu Yu Hakusho)
- **Special Gauge up on last-moment (just) block**: Seijuro Shin (Eyeshield 21), Gintoki Sakata (Gintama), Shun (Saint Seiya), Shusuke Fuji (Prince of Tennis), L (Death Note), Near (Death Note), Byakuya Kuchiki (Bleach), Toki (Hokuto no Ken), Gaoh (Bobobo-bo Bo-bobo), Rouji (Muhyo to Rouji)
- **Special Gauge up attacking/blocking chain attacks**: Haruto Sakuraba (Eyeshield 21), Ramenman (Kinnikuman), Haya Isowashi (KochiKame), Ryota Miyagi (Slam Dunk), Oishi & Eiji (Prince of Tennis), Uryuu Ishida (Bleach), Rei (Hokuto no Ken), Softon (Bobobo-bo Bo-bobo)

## Support Character notes

- A Support summon attacks/applies effects then teleports out; can be
  re-summoned repeatedly (no explicit cooldown value given).
- Some Support attacks are conditional on the summon itself being hit first.
- Some Support attacks trigger a target-select UI on the touch screen
  (a numbered 2x2 grid corresponding to players, or a Jump-logo icon in
  place of your own slot); guide labels these "Select a Target" in their
  move descriptions.

## Battle Character notes

- Directly controlled; special attack varies by koma size (4-8 cells).
- Any Battle character can also be used as a Support and/or Help koma.

---

# C7: Pre-Made Decks

Pre-made decks are developer-built decks. They're kept here purely as worked
examples of legal deck construction (how they're unlocked is out-of-scope
progression economy).

Deck layouts are recorded on the 4x5 (20-cell) Koma Screen grid. Repeated
numbers = cells occupied by one multi-cell koma; `X` = unused cell. Each deck
example demonstrates the same structural rules:
- Exactly one character is the **Leader**.
- Exactly one character is bound to the **L button** and one to the **R button**
  (quick-swap/shortcut slots).
- Support/Help komas are frequently marked **"Linked to <character>"**,
  meaning their passive/summon effect is tied to (assigned toward) that
  specific Battle character.
- Total cells used per deck is <= 20; unused cells are left blank (`X`).

Full worked example (Starter Deck):

```
X X 1 2 2
X X 1 2 2
X X 1 3 4
X X 1 5 5
```
1 = Naruto Uzumaki (L button) · 2 = Monkey D. Luffy (Leader) · 3 = Gintoki
Sakata (linked to Naruto) · 4 = Muhyo Toru (linked to Luffy) · 5 = Son Goku
(R button)

The remaining pre-made decks, compacted to: name (theme note), distinct-character
count, Leader, L-button character, R-button character. (Blank = not specified
by the author in that deck's listing — author unconfirmed gap, not necessarily
absent in-game.)

| Deck | # Chars | Leader | L button | R button |
|---|---|---|---|---|
| J-Space (post J-Space) | 10 | Kinnikuman | Allen Walker | Monkey D. Luffy |
| J-Galaxy (post J-Galaxy) | 11 | Kenshin Himura | Hanamichi Sakuragi | Sena Kobayakawa |
| J-Blackhole (post J-Blackhole) | 6 | Ryotsu Kankichi | Cobra | Yusuke Urameshi |
| Ore! Orange (all-orange outfits) | 7 | Naruto Uzumaki | Fuusuke | Don Patch |
| Cool (ice theme) | 7 | Toushiro Hitsugaya | Yukime | Hyoga |
| Knuckle Arm (fist theme) | 7 | Allen Walker | Cobra | Chad |
| Numbering (numbered attack names) | 8 | Gon Freecs | Hisashi Mitsui | Yoruichi Shihoin |
| Sweat & Tears (sports theme) | 8 | Kinnikuman | Sena Kobayakawa | Hah Brothers |
| Oriental (Chinese theme) | 7 | Taikoubou | Son Gohan | Linali Lee |
| "I wont lose!" | 6 | Yugi Mutou | Ichigo Kurosaki | Bo-bobo |
| Horse | 6 | Kurama | Seto Kaiba | Cascade |
| Symmetry | 9 | Renji Abarai | Seto Kaiba | Katsura & Elizabeth |
| Yelling | 7 | Monkey D. Luffy | Bo-bobo | Daijiro Ohara |
| Sniper (long range) | 7 | Train Heartnet | Cobra | Yoichi Hiruma |
| Kicker | 7 | Linali Lee | Kenshiro | Musashi |
| Muteki Sakura | 14 | Sakura Haruno | Bo-bobo | (not specified) |
| Speed King | 8 | Kakashi Hatake | Nami | Kenshin Himura |
| Reincarnation | 6 | Dio Brando | Taikoubou | Yugi Mutou |
| Comedy Deck | 7 | Jaguar Junichi | Taizo Momote | Bo-bobo |
| Ninja | 7 | Fuusuke | Gaara | Hammer |
| Shinigami | 9 | Rukia Kuchiki | Mello | Light Yagami & Ryuuk |
| Robot | 7 | Franky | Lady Armaroid | Warsman |
| Afro | 7 | Gintoki Sakata | Gintoki Sakata | Dr. Mashirito |
| Lucky | 7 | Jaguar Junichi | Yugi Mutou | Iori Yoshizuki |
| Yubisashi (finger pointing) | 6 | Kazuki Mutou | Near | (not specified) |
| Mellorine (Sanji + ladies) | 8 | Sanji | Yukime | Eve |
| Cooks & Gluttons | 7 | Kagura | Kagura | Neuro Nougami |
| Busou Kenshin (Watsuki theme) | 8 | Kenshin Himura | Kazuki Mutou | Sanosuke Sagara |
| Pretty | 7 | Eve | Eve | Tsukasa Nishino |
| Samurai | 7 | Roronoa Zoro | Yoh Asakura | Roronoa Zoro |
| Ora Ora (rapid punches) | 6 | Kenshiro | Jotaro Kujo | J |
| Swirly Boys (rivals) | 6 | Vegeta | Kaede Rukawa | Renji Abarai |
| Itako (spirit-connected) | 8 | Anna Kyoyama | Yusuke Urameshi | Rukia Kuchiki |
| Slacker | 7 | Yoh Asakura | Kagura | Jaguar Junichi |
| Hunter Hakusho (Togashi theme) | 8 | Gon Freecs | Kurama | Killua Zoaldyck |
| Dragon Slump (Toriyama theme) | 8 | Son Gohan | Arale Norimaki | Gatchan |
| Machinegun Train | 11 | Train Heartnet | Sven Vollfied | Roronoa Zoro |
| Strong Girls | 6 | Sakura Haruno | Kagura | Dakki So |
| Football | 9 | Sanji | Genzo Wakabyashi | Kojiro Hyuuga |
| Nanori o agero! (aliases) | 7 | Momotaro Tsurugi | Ayame Sarutobi | SogeKing |
| Purple (same as Orange, purple) | 7 | Linali Lee | Momotaro Tsurugi | Arale Norimaki |
| Harem | 8 | Toushiro Hitsugaya | Yukime | Nami |
| Animal | 10 | Monkey D. Luffy | Devil Bat | Cascade |
| Armor | 7 | Seiya | Shiryu | Lady Armaroid |
| Little (small people) | 7 | Muhyo Toru | Tony Tony Chopper | Toushiro Hitsugaya |
| Couple Land | 10 | Yoh Asakura | Anna Kyoyama | Kazuki Mutou |
| Skinhead (bald) | 12 | Piccolo | Lady Armaroid | Mongol Man |
| Long Hair | 7 | Yusuke Urameshi | Kotaro Katsura | Kurama |
| Defensive | 7 | Nico Robin | L | Hanamichi Sakuragi |
| Outlaw (delinquents) | 8 | Yusuke Urameshi | Josuke Higashikata | Taison Maeda |
| Hat | 9 | Jotaro Kujo | Monkey D. Luffy | Arale Norimaki |
| Illusion | 8 | Killua Zoaldyck | Naruto Uzumaki | Hammer |
| Glasses | 7 | Arale Norimaki | Sousuke Aizen | Ayame Sarutobi |
| The Straw-Hat Pirates (One Piece) | 7 | Monkey D. Luffy | Roronoa Zoro | Usopp |
| Bleach | 7 | Ichigo Kurosaki | Uryuu Ishida | Chad |
| Reborn (Katekyo Hitman Reborn) | 8 | Tsuna & Reborn | Hayato Gokudera | Takeshi Yamamoto |
| Gintama | 6 | Gintoki Sakata | Kotaro Katsura | Shinpachi Shimura |
| Muhyo (Muhyo + Neuro) | 8 | Muhyo Toru | Enchuu | Neuro Nougami |
| Dragon Ball | 6 | Vegetto | Kuririn | Piccolo |
| Seiya (Saint Seiya) | 6 | Seiya | Shiryu | Shun |
| Kinniku (Kinnikuman) | 9 | Kinnikuman | Buffaloman | Terryman |
| KochiKame | 7 | Ryotsu Kankichi | Daijiro Ohara | Reiko Akimoto |
| Intelligence | 8 | (not specified) | Kurapica | Nico Robin |
| Naruto | 6 | Naruto Uzumaki | Gaara | Kakashi Hatake |
| Bo-bobo | 7 | Bo-bobo | Bo-bobo | Tokoro Tennosuke |
| Hokuto (Hokuto no Ken) | 5 | Kenshiro | Raoh | Toki |
| D.Gray-man | 7 | Allen Walker | Yuu Kanda | Rabi |
| Jojo (Jojo's Bizarre Adventure) | 8 | Jotaro Kujo | Josuke Higashikata | Jolyne Kujo |
| Saikyo (Toriyama theme) | 7 | Arale Norimaki | Son Goku | Trunks |
| Man Man (manliest of men) | 8 | Seiya | (not specified) | Kenshiro |
| Legendary Heroes | 8 | Ryotsu Kankichi | Arale Norimaki | Tsubasa Ozora |
| Comedy Deck 2 | 6 | Arale Norimaki | Bo-bobo | Ta-chan |
| Saikyo Deck 2 (Toriyama theme) | — | author states this deck was not yet unlocked/documented (author unconfirmed) |

Note on deck grid sizing: koma cell counts per character are not reproduced in
this table (only per-deck grids in the source show exact shapes); use the
Starter Deck worked example above plus the per-character koma-size rule (Help=1,
Support=2-3, Battle=4-8) to reconstruct any specific deck's exact grid if needed.

## SP-gauge help koma effects (salvaged from gf-52886, Batsu's J-Gem FAQ v1.0)

Battle-relevant SP mechanics cited in an otherwise-economy guide (unverified
community claims, same caveat as the rest of this doc):

- Light Yagami (Death Note): increases SP gauge on attacking or blocking
  characters of an opposing nature.
- Mello (Death Note): increases SP gauge on multi-hit attacks.
- Bulma (Dragon Ball): increases SP gained from picking up coins (coins are a
  drop from defeated opponents, distinct from gems).
- Dio Brando (JoJo): SP gauge regenerates over time, conditional on not
  switching battle characters and not using Support characters.
- Flat "+1 SP Bar" helps: Edajima Heihachi, Gyro Zeppeli, Athena, Takanori
  Akagi, Kaiousama, Jiraiya, Zangetsu, Isshin Kurosaki, Chuubei, Seijuro Hiko,
  Shanks.
- Piko (Muhyo to Rouji) support: restores 3 SP bars at an unspecified HP cost,
  described as slow (author unconfirmed).
- Special-attack KOs (X or Up+X are equivalent for this purpose) are
  distinguished from normal-attack/support KOs by the drop system — evidence
  the engine tracks kill-source category.
