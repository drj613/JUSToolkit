# All 57 Abilities from ability.bin + ability_t.bin (task K2b)

Loop-Atlas iteration 5, static analysis only. Closes harness card E1 — all ten previously-Unknown ability IDs now have names.

## Two new parallel tables

Both live in `jus_files/ripped_jus_files/bin/` and weren't in the K1 survey.

| File | Size | Structure |
|---|---|---|
| `ability.bin` | 228 B | **57 entries × 4 bytes**: `(u8 group, u8 sub, s8 param, u8 pad)` |
| `ability_t.bin` | 3788 B | **57 entries × 12 bytes**: three relative s32 string pointers — Title, Description1, Description2. Count = `firstPointer / 12` |

Both yield exactly 57 entries — index-parallel. CONFIRMED.

`ability_t.bin` strings are null-terminated **Shift-JIS**. The pointer base is the offset **of** the pointer field, not after it (`src/JUS.Tool/Texts/JusText.cs:90` — `Stream.Position + ReadInt32()` evaluates `Position` before the read advances it). Getting this wrong shifts every string by 4 bytes and silently eats two leading characters, which looks like "strings share tails" rather than a bug. Existing parser: `src/JUS.Tool/Texts/Formats/AbilityEntry.cs:11` / `Converters/Binary2Ability.cs:50-98`.

## Key finding: Ｊ魂 is HP, and +8 is an ability entry

Index 52 is **`Ｊ魂最大値＋`** — "J-soul maximum value +" — with **param `+8`**.

The owner recalled the HP bonus being called something like "j soul" but flagged it as unverified. Now verified: **Ｊ魂 (J-soul) is the game's name for HP**, and the `+8` bonus from Leader and relationship adjacency is literally this table entry's parameter. That's why both bonuses share a constant — they're the same ability applied twice, consistent with the owner's report that four sources stack to `+32`.

Index 53 is `必殺魂最大値＋` — "special-soul max +", the SP gauge. The game names its two resources Ｊ魂 and 必殺魂.

## ID space resolved

The three `ability.bin` groups map onto the ID scheme in `Cheat-Code-Analysis.md`:

- **group 0** — indices 0–37, sub `0x00`–`0x25`. Matches cheat IDs `0x00`–`0x25` **by name**, one for one (e.g. sub `0x19` = `帯電無効` = "Immunity to Shock"). Index == ID.
- **group 1** — indices 38–48, sub `0x05`–`0x0F`. Eleven entries; cheat IDs `0x26`–`0x30` are exactly eleven slots. SP-trigger passives.
- **group 2** — indices 49–56, sub `0x00`–`0x07`. **Eight entries the old table never covered**, which is why helper `abilityId` values in `koma.bin` reach 55 while the cheat list stopped at `0x30`. Prediction confirmed.

**All ten previously-Unknown IDs now named**: `0x0B` 打撃弱点, `0x0C` 斬撃弱点, `0x11` 浪費, `0x13` 大食い, `0x14` 機械, `0x15` 直撃, `0x17` 重量級, `0x18` 軽量級, `0x24` プラス効果無効, `0x25` 必殺技無制限.

`0x0B`/`0x0C` are **weaknesses**, not resistances — they increase damage taken from blunt and slashing attacks. They sit next to the two resistance passives (`0x09`, `0x0A`), so the positional guess of "more damage-reduction classes" was directionally right but wrong on sign.

### Where my slot guesses were wrong

`Helper-Passives-Catalog.md` predicted the owner's four unclaimed categories (health regen, max HP, +1 max SP, SP-regen-on-field) sat in `0x13`–`0x18` or `0x24`/`0x25`. **REFUTED.** They're all in **group 2**, an ID space the old table didn't reach:

| Owner category | Actual entry | Param |
|---|---|---|
| 24 Increase Max Health | index 52 `Ｊ魂最大値＋` | `+8` |
| 27 Increase Max Special Gauge | index 53 `必殺魂最大値＋` | — |
| 23 Health recovers slowly | index 54 `自己回復` | `+1` |
| 40 SP regen while on field | index 55 `闘争心` (fighting spirit) | `+3` |

The reasoning was sound — those are stat boosts, and `0x13`–`0x18` is a stat-boost neighbourhood — but it assumed the ID space ended at `0x30`. It doesn't. Recorded rather than deleted, per the charter.

## Group 2 may be the deck-level nature bonus mechanism

Indices 49–51 are **`友情コマ` (friendship), `努力コマ` (effort), `勝利コマ` (victory)** — Weekly Shōnen Jump's three founding principles. These are the only abilities named "koma" rather than after an effect.

`Deck-System.md` carries an unexplained note about "+1 SP helpers affect the whole deck" and nature-driven deck bonuses with no formula. Group 2 containing deck-flavoured entries alongside the `+8` / `+1` / `+3` / `-3` parameters is the best lead for that mechanism. PLAUSIBLE, not confirmed.

Index 56 is `必殺ゲージジワジワ減少` with param **`-3`**: the SP gauge *drains* steadily. A negative ability — this table holds debuffs too.

## The full table

Params shown only where nonzero. "old cheat-code ID" is the pre-existing `Cheat-Code-Analysis.md` numbering.

| idx | ability.bin (grp/sub) | param | Japanese | English gloss | old cheat-code ID |
|---|---|---|---|---|---|
| 0 | g0/`0x00` |  | なし | none | `0x00` |
| 1 | g0/`0x01` |  | ３段ジャンプ | Triple Jump | `0x01` |
| 2 | g0/`0x02` |  | 三角飛び | Wall Jump (triangle jump) | `0x02` |
| 3 | g0/`0x03` |  | 空中ダッシュ | Air Dash | `0x03` |
| 4 | g0/`0x04` |  | オートガード | Auto-Guard (uses SP) | `0x04` |
| 5 | g0/`0x05` |  | ジャストガード | Just Guard - SP on last-moment block | `0x05` |
| 6 | g0/`0x06` |  | ふんばり | Never budge when blocking on moving platform | `0x06` |
| 7 | g0/`0x07` |  | 超回復 | Max HP up on KO respawn | `0x07` |
| 8 | g0/`0x08` |  | 状態変化耐性 | Status-change resistance (duration cut) | `0x08` |
| 9 | g0/`0x09` |  | 打撃耐性ＵＰ | Blunt resistance UP (punch/kick) | `0x09` |
| 10 | g0/`0x0A` |  | 斬撃耐性ＵＰ | Slash resistance UP (blades) | `0x0A` |
| 11 | g0/`0x0B` |  | 打撃弱点 | Blunt WEAKNESS - takes more | `0x0B` |
| 12 | g0/`0x0C` |  | 斬撃弱点 | Slash WEAKNESS - takes more | `0x0C` |
| 13 | g0/`0x0D` |  | 見切り | Evasion - less damage from Specials | `0x0D` |
| 14 | g0/`0x0E` |  | 底力 | Latent power - Attack-Up at low HP | `0x0E` |
| 15 | g0/`0x0F` |  | 逆襲 | Counterattack - gain 1 SP bar when KO'd | `0x0F` |
| 16 | g0/`0x10` |  | 収集 | Collection - more SP from Coins | `0x10` |
| 17 | g0/`0x11` |  | 浪費 | Waste | `0x11` |
| 18 | g0/`0x12` |  | 調理 | Cooking - more HP from Food | `0x12` |
| 19 | g0/`0x13` |  | 大食い | Big eater | `0x13` |
| 20 | g0/`0x14` |  | 機械 | Machine | `0x14` |
| 21 | g0/`0x15` |  | 直撃 | Direct hit | `0x15` |
| 22 | g0/`0x16` |  | ガード能力＋ | Guard ability + | `0x16` |
| 23 | g0/`0x17` |  | 重量級 | Heavyweight | `0x17` |
| 24 | g0/`0x18` |  | 軽量級 | Lightweight | `0x18` |
| 25 | g0/`0x19` |  | 帯電無効 | Immune: Shock (electrified) | `0x19` |
| 26 | g0/`0x1A` |  | 氷結無効 | Immune: Freeze | `0x1A` |
| 27 | g0/`0x1B` |  | 燃え無効 | Immune: Burn | `0x1B` |
| 28 | g0/`0x1C` |  | 混乱無効 | Immune: Confusion | `0x1C` |
| 29 | g0/`0x1D` |  | 毒無効 | Immune: Poison | `0x1D` |
| 30 | g0/`0x1E` |  | 宣告無効 | Immune: Judgment (declaration) | `0x1E` |
| 31 | g0/`0x1F` |  | 行動不能無効 | Immune: Paralysis (incapacitation) | `0x1F` |
| 32 | g0/`0x20` |  | 画面妨害無効 | Immune: Blindness (screen obstruction) | `0x20` |
| 33 | g0/`0x21` |  | スピードダウン無効 | Immune: Speed-Down | `0x21` |
| 34 | g0/`0x22` |  | チェンジ封印無効 | Immune: Change/Battle-Support Seal | `0x22` |
| 35 | g0/`0x23` |  | 見破り | See through - see invisible | `0x23` |
| 36 | g0/`0x24` |  | プラス効果無効 | Nullify PLUS effects (enemy buffs) | `0x24` |
| 37 | g0/`0x25` |  | 必殺技無制限 | Unlimited special moves | `0x25` |
| 38 | g1/`0x05` |  | 突撃 | Charge | `0x26` |
| 39 | g1/`0x06` |  | コンボ | Combo | `0x27` |
| 40 | g1/`0x07` |  | 沈着 | Composure | `0x28` |
| 41 | g1/`0x08` |  | 激怒 | Rage | `0x29` |
| 42 | g1/`0x09` |  | ハント | Hunt | `0x2A` |
| 43 | g1/`0x0A` |  | 反撃 | Counter | `0x2B` |
| 44 | g1/`0x0B` |  | 奮戦 | Hard fight | `0x2C` |
| 45 | g1/`0x0C` |  | 大活躍 | Great performance | `0x2D` |
| 46 | g1/`0x0D` |  | 協力 | Cooperation | `0x2E` |
| 47 | g1/`0x0E` |  | 知的 | Intellectual | `0x2F` |
| 48 | g1/`0x0F` |  | 爆発 | Explosion | `0x30` |
| 49 | g2/`0x00` |  | 友情コマ | Friendship koma | `— not in old table —` |
| 50 | g2/`0x01` |  | 努力コマ | Effort koma | `— not in old table —` |
| 51 | g2/`0x02` |  | 勝利コマ | Victory koma | `— not in old table —` |
| 52 | g2/`0x03` | **+8** | Ｊ魂最大値＋ | J-SOUL (HP) max +8 | `— not in old table —` |
| 53 | g2/`0x04` |  | 必殺魂最大値＋ | Special-soul (SP gauge) max + | `— not in old table —` |
| 54 | g2/`0x05` | **+1** | 自己回復 | Self-recovery (HP regen) | `— not in old table —` |
| 55 | g2/`0x06` | **+3** | 闘争心 | Fighting spirit | `— not in old table —` |
| 56 | g2/`0x07` | **-3** | 必殺ゲージジワジワ減少 | SP gauge drains steadily | `— not in old table —` |

## Still open

- `chr_b.bin` is **74 entries × 60 bytes** (4440 B), matching the 74 battle characters. Searched every 2-byte-aligned offset for Naruto's `9216` raw HP — no clean hit. **HP is not a plain u16 at a fixed offset in chr_b.bin**. Card F1 stands.
- Nature still unlocated. Card A1 stands.
- `piece.bin` (35183 B) still undecoded.
- Descriptions (`Description1`/`Description2`) not transcribed — full Japanese sentences that would triple this doc's size. One script run away if magnitudes are needed.
