# Findings: The Nature Hunt — Exclusions, and All 57 Descriptions (task K2c)

Loop-Atlas iteration 6. Static analysis only, now with `jus_files/arm9/arm9.bin` available.

**I didn't find nature, and that's the point.** This doc marks exactly where it *isn't*, so nobody searches the same ground twice. Two real wins alongside: textual proof the HP bonus stacks, and a **bug in the game's own ability text** that would mislead anyone reading it about slash damage.

## Nature: where it is NOT

Every entry below is a checked exclusion, not a guess.

| Location | Verdict | Evidence |
|---|---|---|
| `koma.bin` (890 × 12 B) | **REFUTED** | Naruto's size-2 (笑) and size-3 (力) panels are byte-identical except image/shape/ordinal. Two natures, same bytes |
| `komatxt.bin` (890 × 12 B) | **REFUTED** | Parallel per-koma table, but `Unk1`/`Unk2` are **constant across all 9 of Naruto's panels** |
| `arm9.bin` flat byte table, per-koma | **REFUTED** | Scanned all 692568 bytes for any 890-long window with 3–5 distinct values. **Zero hits.** Also zero for 445-byte nibble-packed |
| `arm9.bin` flat byte table, per-character | **REFUTED for nature** | One 312-long candidate at file `0x0A8640` / runtime `0x020A8640`. That's inside the deck RAM region — looks like uninitialised data. And nature must be *per-panel*, not per-character |
| `piece.bin` (35183 B) | **Not per-koma** | Header is `int32 count = 41`, then ascending offsets that break after 23 entries into a nested `count`+offsets pattern. 41 ≈ the 42 series — it's **per-series grouped**, not one record per koma |
| `chr_b.bin` / `chr_s.bin` | **Cannot be the source** | See below |

### Why the character stat files can't hold it

Two clean confirmations from exact stride arithmetic:

- **`chr_s.bin` = 193 entries × 20 bytes** (3860 B). 193 is exactly the count of distinct support `abilityId` values in `koma.bin`. CONFIRMED.
- **`chr_b.bin` = 74 entries × 60 bytes** (4440 B). 74 is exactly the documented battle-character count. CONFIRMED.

`chr_s.bin` offset `0x00` looked very promising: 3 distinct values split near-evenly across 193 entries — `{0: 63, 1: 67, 2: 63}`. That's what a 3-way Power/Knowledge/Laughter split should look like.

**But it can't be nature.** Naruto's size-2 and size-3 support panels both carry `abilityId = 17`, indexing the *same* `chr_s` record — yet they have different natures (笑 and 力). Same problem for battle: his two size-4 panels both carry `abilityId = 20`. Whatever `chr_s[0x00]` is, it's per-character, and nature isn't.

### What's left

Nature is per-panel, and it's in none of the flat static tables. Remaining possibilities:

1. **Packed at sub-byte level inside a wider record** — my scans were byte-granular, so a 2-bit field inside a larger struct would be invisible.
2. **Computed or table-driven in ARM9 code**, not stored as data. The deck browser picks a nature glyph from somewhere; finding that read site needs disassembly, not a value search.
3. A per-koma table in a file I haven't opened — but `bin/` is fully inventoried (26 files) and the plausible candidates are exhausted.

The evidence that nature is per-panel rests on the owner's Naruto table across **two independent instances**: the size-2/size-3 support pair *and* the size-4 pair. `Deck-System.md` documented the size-4 Power/Laughter split independently years earlier. The premise is solid; the search space is genuinely elsewhere.

**Next route: harness card A1** (runtime diff of two decks differing only in nature), or disassemble the deck-browser glyph-selection path with `query.py`.

## komatxt.bin holds the panel names

`komatxt.bin` is 890 entries × 12 bytes — index-parallel to `koma.bin` — and its first pointer is the **panel display name**.

Naruto's records 497–503 read `ナルト`; records **504 and 505 read `ナルト（九尾）`**.

That settles a question from `findings/koma-format-decoded.md`, which noted sizes 7–8 carry a different name and asked whether `nameNum` differed or names came from `komatxt.bin` per-panel. **It's the latter.** Names are per-panel, so a character can change display name at larger sizes without any change in `koma.bin`.

`Unk2` = `characterId - 1` (Naruto: `komatxt` 183 vs `koma.bin` 184), confirming the two files share a character numbering off by one.

## All 57 ability descriptions decoded

Requested by the melonDS harness session as the cheapest shot at resistance magnitudes. **Answer: the text doesn't contain them.** Only 3 of 57 entries mention any number — index 1 (`３段ジャンプ`), index 15 (`逆襲`, "1"), and index 53 (`必殺魂最大値＋`, "+1").

The resistance multiplier isn't in the data files. It's hardcoded in the damage path; the runtime experiment is the only route.

### Stacking rule confirmed in the game's own text

Index 52 `Ｊ魂最大値＋` (param `+8`), description:

> バトルキャラのＪ魂の最大値が増加する能力。　　※複数有効。

**`※複数有効` means "multiple instances are effective"** — it stacks. Index 53 `必殺魂最大値＋` carries the same note. This independently confirms the owner's observation that Leader plus 3 relationships gives `+32`: four applications of a `+8` ability explicitly marked as stackable. The `+8` was never special-cased.

Index 53's text also pins its magnitude: `必殺魂の値（ゲージの所の数字）のＭＡＸが＋１になる` — the SP gauge's **max** goes up by 1.

### A bug in the game's ability text

Index 11 `打撃弱点` (blunt weakness) reads correctly:

> 打撃攻撃を受けた時のダメージが少し大きくなってしまうマイナス能力。
> "A minus ability that makes damage taken from blunt attacks *slightly larger*."

Note `少し` — "slightly". That's the only qualitative hint at magnitude in the table.

Index 12 `斬撃弱点` (slash weakness) reads:

> 剣や刀の相手からの斬られるダメージが軽減される能力。
> "An ability that *reduces* damage taken from swords and blades."

**Wrong text — verbatim copy of index 10 `斬撃耐性ＵＰ` (slash resistance UP).** The title says weakness; the description says resistance. Index 11 is explicitly `マイナス能力` (minus ability) and the two weaknesses are a matched pair, so **index 12 is a weakness and its description is a copy-paste error in the shipped game data.**

This matters: the harness session confirmed from RAM that **Luffy carries `0x0C`**. Anyone resolving the sign by reading the description would conclude Luffy *resists* slashing when he's actually *weak* to it — an inverted conclusion from correct-looking data.

Recorded as CONFIRMED-that-the-text-is-wrong; the underlying effect's sign is PLAUSIBLE from the title plus symmetry, and the harness can settle it with one measurement.

### Two group-2 entries pinned to owner categories

- Index 54 `自己回復` (param `+1`): "during battle, Ｊ魂 recovers at a fixed pace" → owner category 23, health regen. This is a *character ability*, distinct from training mode's own rapid heal (~64 raw units per ~2 frames) that the harness session measured.
- Index 55 `闘争心` (param `+3`): "while on stage (top screen), 必殺魂 gradually increases" → owner category 40, SP regen while on field. Index 56 is its exact negative mirror at `-3`.

Group 2's params are real magnitudes in the same units as the gauge they modify.

## Caution about the existing damage formula

`Human-Testing-Queue.md` carries `damage = damage1/5 + (tier-2)` marked CONFIRMED. The harness session independently flagged this, and the reasoning holds: it was very likely fitted against HP read as the 1/4-scale **high byte**, which can't represent the 1.250 hit they measured. A formula fitted to truncated observations can be right about integers and wrong about the rule. It should be re-derived against u16 HP, not patched.

## Predictions status update

| ID | Prediction | Verdict |
|---|---|---|
| P1 | Nature is a 4-value enum in `koma.bin` | **REFUTED** (iteration 4), now excluded from `komatxt.bin`, flat arm9 tables, `piece.bin`, and both `chr_*` files |
| P7 | Relationships live in a separate table | **Still open.** `piece.bin` is per-series, making it a weaker candidate than before |
