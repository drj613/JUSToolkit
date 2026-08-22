# Helper / passive abilities — DRAFT spec

> **STATUS: DRAFT.** Static mining only (no new emulator runs). Verdict per
> `INVENTORY.md` §9: **partial** — all 57 abilities are named and the three kinds
> are mapped, but the p178-vs-p223 slot-count conflict and the hardcoded passive
> magnitudes are unresolved. Do not build an exporter from this until the GAPS
> section is settled or waived. Feeds spec ticket `jus-wayfinder-map-digi.11`.

Audience: an engineer reimplementing JUS abilities/passives. Sources cited
inline; beads via `br show <id>`.

## 1. Overview

Every ability in the game — mobility passives, status immunities, damage
resistances, SP triggers, stat boosts — lives in one 57-entry catalog
(`ability.bin` + `ability_t.bin`). A battle character gets abilities from two
sources at load time: its `chr_b.bin` record, and the deck's koma-adjacency
chain at `battleObj+0x558`. Kind-0 and kind-1 abilities are appended to a
runtime id list and cached into a bitset; kind-2 abilities never join the list —
they are stat modifiers applied once at load. The damage-relevant abilities feed
the ±25% gate word described in `damage.md` §5.

Helpers themselves are directional single-passive buff emitters: a 1-cell helper
koma grants its one ability to the adjacent cell its facing points at
(`docs/research/findings/p225-koma-adjacency-grants-abilities.md`, bead
`jus-koma-adjacency-grants-abilities-70l`; owner-side description in
`docs/research/Helper-Passives-Catalog.md` §"How helper passives work").

## 2. The catalog files

Source: `docs/research/findings/abilities-all-57-named.md`.

| File | Size | Structure |
|---|---|---|
| `ability.bin` | 228 B | 57 × 4: `(u8 kind, u8 sub/handler-index, s8 param, u8 pad)` |
| `ability_t.bin` | 3788 B | 57 × 12: three relative s32 string pointers (Title, Desc1, Desc2), Shift-JIS |

Parser quirk (CONFIRMED): the `ability_t.bin` pointer base is the offset **of**
the pointer field, not after it — `src/JUS.Tool/Texts/JusText.cs:90` evaluates
`Stream.Position` before the read. Getting this wrong shifts every string 4
bytes and eats two leading characters.

## 3. The three kinds and their dispatch

Source: `findings/p224-two-ability-sources-and-eight-non-abilities.md`
(bead `jus-second-ability-source-0x558-5rp`), `findings/p177-ability-bitset-loader.md`.

| kind | ids | count | behaviour |
|---|---|---|---|
| 0 | 0–37 | 38 | **append** to the runtime id list |
| 1 | 38–48 | 11 | **append** (SP-gain triggers) |
| 2 | 49–56 | 8 | **never append** — dispatch a handler from the table at `0x0209F544`, applied once at load |

Loader: arm9 `0x02077768` (both append call sites live inside it). Append
primitive `AddAbility` = `0x02077A74`: skips id 0, cap 15, count at
`char+0x1A`, ids at `char+0x1B..`. A separate load path in ov6
(`BattleCharaDataLoad.cpp`) walks a 4-byte `{kind, id}` entry array at
`[obj+0x50]` and dispatches through a kind table at `0x02172210`; `table[0]` is
the bitset bit-setter `0x0215FB3C` (see §6). Enumerating that `{kind,id}`
dictionary is still open (INVENTORY §9 Q2).

## 4. On-disk ability list (`chr_b` record `+0x03`)

Source: `findings/p223-ondisk-ability-list-found.md`
(bead `jus-ondisk-ability-list-at-chrb-0x03-kfc`).

- Five one-byte slots at record `+0x03..+0x07`. **Sparse**: zeros are empty
  slots, not terminators — a reader must scan all five (Luffy, record 12, holds
  `09 19 00 00 0C`; 25 of 74 records have an interior zero).
- Loader walks exactly five slots (`cmp sb, #5` at `0x02077818`) and dispatches
  each by kind — kind-0/1 slots compact into `char+0x1B..`, kind-2 slots run
  their handler instead.
- All 370 window bytes across 74 records are valid ids (0..56); occupancy is
  0, 2, 3, or 4. The four all-zero records (70–73) are exactly the unselectable
  Debug series — the decisive cross-check.
- **Runtime list ≠ disk list.** Luffy's live list is `[9, 25, 12, 14]`; id 14
  is appended from the second source (the type-2 node chain at
  `battleObj+0x558` — the deck→battle koma bridge, `findings/p224`,
  bead `jus-second-ability-source-0x558-5rp`).

## 5. Load-time bitset at `battleObj+0x128`

Source: `findings/p177-ability-bitset-loader.md`,
`docs/research/Ability-Bitset-Is-Not-Resistance.md` (bead `jus-w66`).

- Writer: ov6 `0x0215FB3C`, reached only through the kind table at
  `0x02172210` (no direct BL). Addressing: word `base+0x8+4*(id>>5)`, bit
  `id & 0x1F`, where `base = battleObj+0x120` — i.e. the bitset starts at
  `battleObj+0x128`.
- The cancel gate `0x02158EB0` reads the same expression — set side and test
  side confirmed against each other.
- **Not stable across a match**: the bitset is re-cached in place on KO/respawn
  (bead `jus-q2y`); a character's ability set is not a constant of the character.
- Of the 32 tested bits, **only bit 4 (Auto-Guard, ability 4) changes blunt
  damage**; damage resistance is NOT read from this bitset in either direction
  (`Ability-Bitset-Is-Not-Resistance.md`, bead `jus-w66`). Resistance instead
  flows through the gate word: abilities set ±25% gate bits via the mask tables
  at `0x02092E78`/`0x02092E90` (`findings/p213-...`, bead
  `jus-bit5-is-ability-10-rxl`). See `damage.md` §5 for the gate mechanism; the
  12 gate-arming abilities get their own test matrix in
  `docs/research/gate-ability-test-matrix.md` (in progress, separate author).

## 6. Kind-2 abilities are stat modifiers

Source: `findings/p227-kind2-abilities-are-stat-modifiers.md`
(bead `jus-kind2-abilities-are-stat-modifiers-bdq`), confirming the INVENTORY
finding that kind-2 entries are load-time stat modifiers.

| id | handler | effect |
|---|---|---|
| 49, 50, 51 | `0x0207793C` | stub — `mov r0,#0; bx lr`, does nothing |
| 52 | `0x02077974` | max HP (`char+0x16` in the `+0x56C` block) += param×64, clamp `0x4000`, then current = max (full heal). param = +8 → +8 displayed HP |
| 53 | `0x020779A4` | `char+0x5CC` += 1, clamp `0x10` (SP-gauge max) |
| 54 | `0x02077944` | `strb param → char+0x4A` (+1, HP regen) |
| 55 | `0x02077954` | `strb param → char+0x4B` (+3, fighting spirit / SP regen) |
| 56 | `0x02077964` | `strb param → char+0x4C` (−3, SP drain) |

Key properties (per p227):

- **Store, not add**: the three single-byte handlers `strb` the value — no
  read-modify-write. Stacking two carriers of the same id would overwrite, not sum.
- **Table-driven parameters**: the +1/+3/−3/+8 come from `ability.bin` byte 2
  (read as `s8` at `4*id + 2`), not from code constants. The handler is generic.
- The loader zeroes `+0x4A/+0x4B/+0x4C` (and the count `+0x1A`) as one 4-store
  group whenever the ability set rebuilds.
- Chr_b carriers: id 54 → records 8, 10, 24, 29, 37, 44; id 55 → 53, 65;
  id 56 → 24, 60, 67. Ids 49–53 are carried by **no** chr_b record.
- Tension, flagged not resolved: `GrowMax 0x020784B8` (Battle-Engine-Map) also
  raises max HP with the same `0x4000` cap, gated on a `char+0x128` badge bit,
  candidate for ability 7 (超回復). Whether ability 7 and id 52 are one effect
  or two is unknown.

Deck-bonus link: the Leader sticker and each relationship adjacency grant +8 HP,
four sources, additive, cap +32 (`Helper-Passives-Catalog.md` "Confirmed
numbers"); id 52's param is literally that +8
(`findings/abilities-all-57-named.md` — Ｊ魂 "J-soul" is the game's name for HP).
Since no chr_b record carries 52, the presumption is the deck side applies it —
unverified (see GAPS).

## 7. The 57-ability catalog

Source: `findings/abilities-all-57-named.md` (names, kinds, params),
`findings/p224`/`p227` (handlers). Kind-0/1 handler = append (`0x02077A74`);
only kind-2 rows have per-id handlers. "cheat id" = the pre-existing
`Cheat-Code-Analysis.md` numbering (runtime array at `0x021DF1D6+`; status
immunities contiguous at `0x19`–`0x22`).

| id | kind | param | Japanese | English gloss | handler / notes |
|---|---|---|---|---|---|
| 0 | 0 | | なし | none | skipped by append |
| 1 | 0 | | ３段ジャンプ | Triple Jump | |
| 2 | 0 | | 三角飛び | Wall Jump | |
| 3 | 0 | | 空中ダッシュ | Air Dash | |
| 4 | 0 | | オートガード | Auto-Guard (uses SP) | bitset bit 4 — only bit shown to change damage |
| 5 | 0 | | ジャストガード | Just Guard | |
| 6 | 0 | | ふんばり | Solid stance on moving platforms | |
| 7 | 0 | | 超回復 | Max HP up on KO respawn | candidate `GrowMax 0x020784B8` (unsettled vs id 52) |
| 8 | 0 | | 状態変化耐性 | Status duration cut | |
| 9 | 0 | | 打撃耐性ＵＰ | Blunt resistance UP | gate bit 4 (−25%), `damage.md` §5 |
| 10 | 0 | | 斬撃耐性ＵＰ | Slash resistance UP | gate bit 5 (`jus-bit5-is-ability-10-rxl`) |
| 11 | 0 | | 打撃弱点 | Blunt WEAKNESS | **orphan** — wired to add-side gate bit 12, no carrier |
| 12 | 0 | | 斬撃弱点 | Slash WEAKNESS | |
| 13 | 0 | | 見切り | Less damage from Specials | |
| 14 | 0 | | 底力 | Attack-Up at low HP | |
| 15 | 0 | | 逆襲 | +1 SP bar when KO'd | |
| 16 | 0 | | 収集 | More SP from Coins | |
| 17 | 0 | | 浪費 | Waste | |
| 18 | 0 | | 調理 | More HP from Food | |
| 19 | 0 | | 大食い | Big eater | |
| 20 | 0 | | 機械 | Machine | |
| 21 | 0 | | 直撃 | Direct hit | |
| 22 | 0 | | ガード能力＋ | Guard ability + | **orphan** |
| 23 | 0 | | 重量級 | Heavyweight | |
| 24 | 0 | | 軽量級 | Lightweight | |
| 25 | 0 | | 帯電無効 | Immune: Shock | |
| 26 | 0 | | 氷結無効 | Immune: Freeze | |
| 27 | 0 | | 燃え無効 | Immune: Burn | |
| 28 | 0 | | 混乱無効 | Immune: Confusion | |
| 29 | 0 | | 毒無効 | Immune: Poison | |
| 30 | 0 | | 宣告無効 | Immune: Judgment | |
| 31 | 0 | | 行動不能無効 | Immune: Paralysis | |
| 32 | 0 | | 画面妨害無効 | Immune: Blindness | |
| 33 | 0 | | スピードダウン無効 | Immune: Speed-Down | **orphan** |
| 34 | 0 | | チェンジ封印無効 | Immune: Battle/Support Seal | **orphan** |
| 35 | 0 | | 見破り | See invisible | |
| 36 | 0 | | プラス効果無効 | Nullify PLUS effects | **orphan** |
| 37 | 0 | | 必殺技無制限 | Unlimited specials | **orphan** |
| 38 | 1 | | 突撃 | Charge (SP trigger) | |
| 39 | 1 | | コンボ | Combo | |
| 40 | 1 | | 沈着 | Composure | |
| 41 | 1 | | 激怒 | Rage | |
| 42 | 1 | | ハント | Hunt | |
| 43 | 1 | | 反撃 | Counter | |
| 44 | 1 | | 奮戦 | Hard fight | |
| 45 | 1 | | 大活躍 | Great performance | |
| 46 | 1 | | 協力 | Cooperation | |
| 47 | 1 | | 知的 | Intellectual | |
| 48 | 1 | | 爆発 | Explosion | |
| 49 | 2 | | 友情コマ | Friendship koma | `0x0207793C` stub; **orphan** |
| 50 | 2 | | 努力コマ | Effort koma | `0x0207793C` stub; **orphan** |
| 51 | 2 | | 勝利コマ | Victory koma | `0x0207793C` stub; **orphan** |
| 52 | 2 | +8 | Ｊ魂最大値＋ | Max HP +8 | `0x02077974`; **orphan** in chr_b (deck-side carrier presumed) |
| 53 | 2 | | 必殺魂最大値＋ | Max SP gauge +1 | `0x020779A4`; **orphan** in chr_b |
| 54 | 2 | +1 | 自己回復 | HP regen | `0x02077944` → `char+0x4A` |
| 55 | 2 | +3 | 闘争心 | Fighting spirit (SP regen on field) | `0x02077954` → `char+0x4B` |
| 56 | 2 | −3 | 必殺ゲージジワジワ減少 | SP gauge drains | `0x02077964` → `char+0x4C` |

## 8. The 11 orphan ids

Per p227's full-roster recount: 11 of 57 ids (19%) are carried by **no**
`chr_b` record. They feed decision ticket `jus-wayfinder-map-digi.14`.

| id | name | grade of dead |
|---|---|---|
| 11 | 打撃弱点 (Blunt weakness) | kind-0, working append path, wired to gate bit 12, unassigned |
| 22 | ガード能力＋ (Guard ability +) | kind-0, unassigned |
| 33 | スピードダウン無効 (Immune: Speed-Down) | kind-0, unassigned |
| 34 | チェンジ封印無効 (Immune: Seal) | kind-0, unassigned |
| 36 | プラス効果無効 (Nullify PLUS effects) | kind-0, unassigned |
| 37 | 必殺技無制限 (Unlimited specials) | kind-0, unassigned |
| 49 | 友情コマ (Friendship koma) | kind-2, unassigned AND handler is a stub — inert twice over |
| 50 | 努力コマ (Effort koma) | same |
| 51 | 勝利コマ (Victory koma) | same |
| 52 | Ｊ魂最大値＋ (Max HP +8) | kind-2, working handler, no chr_b carrier (deck side presumed) |
| 53 | 必殺魂最大値＋ (Max SP +1) | kind-2, working handler, no chr_b carrier |

Caveats: "orphan" means no chr_b carrier — the `+0x558` koma chain can still
deliver ids (33/34 are helper-catalog immunities, so helper koma presumably
carry them; unproven statically). The p227 stub analysis explicitly cannot
distinguish "removed" from "never implemented". Consequence to carry: presence
in `ability.bin` is not evidence of reachability; the demonstrated-live set is
roughly a dozen of 57 (≈ ids 7, 9, 10, 12, 14, 15, 24, 25, 26, 46 plus a
couple from other chains).

## 9. The 42-category owner taxonomy

`docs/research/Helper-Passives-Catalog.md` (OBSERVED/owner tier) catalogs the 42
helper-passive categories with ~304 named helpers: 3 mobility, 10 status
immunities (11 statuses; both Seals share one), 2 perception/status-handling,
4 offense/resistance, 3 guarding, 5 health, 15 SP-gain triggers. It supersedes
the helper section of `Passives-Reference.md` (~20 GameFAQs categories) — per
INVENTORY, `Passives-Reference.md` remains canon only for **battle-character**
passives (machine form: `battle-chars-passives.json`, 66 entries — guide text,
no ids or magnitudes, 66 ≠ 74 chr_b).

Mapping status: the 42 categories reconcile with the catalog — 38 match the
old cheat-id table by name, and the 4 formerly-unclaimed categories (regen, max
HP, max SP+1, SP-regen-on-field) are group-2 ids 54/52/53/55
(`abilities-all-57-named.md`; the catalog's own `0x13`–`0x18` slot guesses are
REFUTED there, and its "6 Unknown IDs" line is obsolete). Status enum: 10
contiguous immunity ids `0x19`–`0x22` (`Cheat-Code-Analysis.md`). The
attack-class split (punch/kick vs special vs blade) ties to
`DamageFlags-Character-Classification.md` — note INVENTORY flags that doc as
bare-"CONFIRMED" Feb-2026 prose with no beads; treat as unverified.

## GAPS — settle-or-waive candidates

1. **p178-vs-p223 slot-count conflict (blocker for any exporter).**
   `findings/p178-ability-list-is-in-chr_b.md` reads a slot **count at
   `chr_b+0x02`** (values 2–6) with up to **six** slots from `+0x03`;
   `findings/p223` (later, instruction-level) shows the loader walking exactly
   **five** slots from `+0x03` with no count read, and the existing exporter
   labels `+0x03` as `charId`. The loader evidence is stronger, but what byte
   `+0x02` actually is, and whether a sixth data byte at `+0x08` exists unread
   by the loader, is unsettled. INVENTORY §9 open question 1.
2. **Hardcoded passive magnitudes.** Only 3 of 57 ability strings carry a
   number; kind-2 params cover 4 more. Everything else — guard-strength delta,
   attack-up-at-low-HP amount, SP-trigger quantities, status-duration cut — is
   hardcoded somewhere in the damage/SP paths and unlocated (INVENTORY §9 Q4;
   `Helper-Passives-Catalog.md` "Still unknown").
3. **Unlocated consumers.** No consumer found for most bitset bits (only bit 4
   demonstrated); the `{kind,id}` dictionary at `[global]+0x50` is
   unenumerated; what the ability-10/9 residual reduction interacts with
   (per-character defence?) is open; ability 7 vs id 52 double-path unresolved;
   whether the deck side really applies id 52 for Leader/relationship +8 is
   presumed, not shown.
4. Smaller: helper facing single-cell vs row/column (UI vs type-2 chain
   identity unproven); static helper ids vs the runtime `0x021DF1D7` array
   numbering; the queued Edajima test (`jus-5bg`, three predictions from p227)
   unrun; Auto-Guard's no-SP case untested; stacking of two helpers pointing at
   one character unknown (store-not-add suggests overwrite for kind-2).

## Sources

- `docs/research/findings/abilities-all-57-named.md` — names, files, id space
- `docs/research/findings/p223-ondisk-ability-list-found.md` — on-disk list (`jus-ondisk-ability-list-at-chrb-0x03-kfc`)
- `docs/research/findings/p224-two-ability-sources-and-eight-non-abilities.md` — kinds, two sources (`jus-second-ability-source-0x558-5rp`)
- `docs/research/findings/p227-kind2-abilities-are-stat-modifiers.md` — handlers, orphans (`jus-kind2-abilities-are-stat-modifiers-bdq`)
- `docs/research/findings/p177-ability-bitset-loader.md`, `p178-ability-list-is-in-chr_b.md`
- `docs/research/Ability-Bitset-Is-Not-Resistance.md` (`jus-w66`)
- `docs/research/Helper-Passives-Catalog.md` (owner tier); `Passives-Reference.md` (battle section only)
- `docs/research/DamageFlags-Character-Classification.md` (unverified prose — see §9)
- `docs/confirmed-facts/damage.md` §5 — gate word and mask tables (`jus-bit5-is-ability-10-rxl`)
