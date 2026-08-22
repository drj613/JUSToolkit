# Findings: Nature Narrowed to One Missing Rule (task K2g)

> ### ⚠️ CORRECTED — see `nature-SOLVED.md`
>
> The **shape** of the model in this doc is right: base nature with a per-panel override. The
> **mechanism is wrong.** The real test is `high nibble of +0xB == 3` (a sentinel), not `bit 0x10
> clear`. My bit test caught nibbles `0` and `2` (25 records) but missed nibble `1` (7 records), so
> it looked close for the wrong reason. There are **32** override panels, not 26. Nature enum is
> `0=力, 1=知, 2=笑, 3=なし`.

Loop-Atlas iteration 10. Static analysis, working from the harness session's disassembly of HP functions (`docs/research/HP-Struct-From-Disassembly.md`).

**We're down to one unknown — the override rule.** Two `chr_b` arrays identified, and the engine's HP ceiling independently confirmed.

## The `0x4000` cap — CONFIRMED

The harness session found max HP clamped to `0x4000` at `0x020784B8`. My table agrees:

- Highest base HP in `chr_b.bin`: **224**
- Maximum bonus: **+32** (four stacking `Ｊ魂最大値＋` sources)
- `224 + 32 = 256`, and `0x4000 / 64 = 256`

Three independently derived numbers — their 1/64 scale, my table max, my stacking model — all land on the same hardcoded constant. That kind of agreement doesn't happen by accident.

## `chr_b` record `+0x2C` is a percentage array — CONFIRMED

The harness disassembly showed a byte array at `+0x2C` and a routine computing `max × pct / 100` (`mul r0, r2, r1` then `mov r1, #0x64`).

Across all 74 records:

| offset | distinct | range | all multiples of 5? |
|---|---|---|---|
| `+0x2C` | 7 | 25..100 | **yes** |
| `+0x2D` | 6 | 0..40 | **yes** |
| `+0x2E` | 6 | 0..30 | **yes** |
| `+0x2F` | 2 | 0..1 | no — a flag |

Every value a multiple of 5, in percentage-shaped ranges, feeding a `/100` divide. These are **percentage thresholds** — almost certainly the low-HP triggers for abilities like `底力` (Attack-Up at low HP) and `闘争心`. CONFIRMED as percentages; specific ability mapping is PLAUSIBLE.

This retroactively explains iteration 6, where I flagged these columns as "multiples of 5, look like percentages" but had no reason why. The disassembly supplied the reason.

## `chr_b` record `+0x24` is not nature

The halfword array at `+0x24` has high cardinality (16–38 distinct values per slot, values up to 12337) and the values look like packed IDs (`0x1025`, `0x2024`, …). Not a 3–4 value enum. Ruled out for nature; probably move or animation references.

## Base nature: strong candidate at offset `0x00` — PLAUSIBLE

| file | entries | offset `0x00` distribution |
|---|---|---|
| `chr_b.bin` | 74 | `{0: 35, 1: 22, 2: 17}` |
| `chr_s.bin` | 193 | `{0: 63, 1: 67, 2: 63}` |

Both are exactly **3-valued** — matching 力 / 知 / 笑 with なし excluded (helpers have no entry). The support split across 193 entries is almost perfectly even, which is what a designed distribution looks like.

Naruto (`chr_b[20]`), ナルト（九尾） (`chr_b[24]`), and 悟空 (`chr_b[0]`) all read `0`, and all three are 力 Power characters — consistent with `0 = 力`, though three same-value samples can't prove the mapping.

This is the nature that `Deck-System.md` says special attacks keep using even on an alternate-nature panel — a *character* property, explicitly **not** the panel nature that drives deck bonuses.

## The flags byte makes sense now

Iteration 4 found Naruto's two size-4 panels differ only in `koma.bin` byte `0xB` (`0x30` vs `0x20`). I guessed bit `0x10` meant "primary variant." That checks out:

Panels with bit `0x10` **clear** (the "alternate variant" marker):

- **26 panels total** (flag values `0x00`×9, `0x01`×3, `0x20`×11, `0x21`×2, `0x42`×1)
- **25 of 26 pair with a same-character, same-size sibling**
- 25 of the 33 duplicated-size groups have exactly **one** alt-flagged member
- Naruto's 笑 size-4 panel (koma record **501**) is among them; his 力 sibling (500) is not

**Bit `0x10` clear marks the alternate of a same-size pair.** 26 alternate panels game-wide is a sensible number for a bonus mechanic. The 8 duplicated-size groups that don't fit are presumably duplicated for a different reason — two shapes at the same size rather than two natures.

## Where nature stands: one rule short

Putting it together:

```
panel nature = base nature (chr_b/chr_s offset 0x00)
               overridden on panels whose koma flags byte 0xB has bit 0x10 clear
```

This explains every structural fact that defeated the table searches:

- No per-koma nature table exists (exhaustively refuted, iterations 9–10) because **only 26 panels need an override** — the other 864 inherit from the character.
- Naruto's size-2 (笑) and size-3 (力) supports share `abilityId 17` yet differ, because one is an alt-flagged override.
- Nature is per-panel in the UI but lives in per-character data underneath.

**The one missing piece is what the override resolves to.** Naruto's base is `0` and his alternate panel shows 笑. If the encoding is `0=力, 1=知, 2=笑`, that's `base + 2 mod 3` — but one sample can't distinguish "+2 mod 3" from "always 笑" from "a 26-entry lookup somewhere."

### Cheapest way to settle it

One data point from a character whose **base nature is not 力**. If a 知 character's alternate panel is 力, the rule is `+2 mod 3` (each nature's alternate is the one it loses to). If every alternate is 笑 regardless of base, it's a constant. Either answer takes one observation.

Candidates: characters with a duplicated size *and* a non-zero offset-`0x00` value. There are 22 battle characters at `1` and 17 at `2`.

## Predictions status

| ID | Prediction | Verdict |
|---|---|---|
| P1 | Nature is a 4-value enum in `koma.bin` | **REFUTED** |
| P1b | Per-koma-indexed nature table in the ROM binaries | **REFUTED** — exhaustive |
| P1c | Compacted 578-entry nature table | **REFUTED** |
| P1d | Nature = character base nature + per-panel override flag | **PLAUSIBLE** — structurally consistent with every prior refutation; override rule unknown |

## Note for the harness session

Their overlay residency work (**ov06 is the battle overlay**, 100% byte match over 154688 bytes) is the more useful half of my extraction and prunes the search space properly: combat is `arm9.bin` + ov06 only.

Worth adding: the deck editor will be a *different* overlay in the `0x0214CD20` set, and the same byte-match trick identifies it — dump RAM while in deck-edit and compare against ov00–ov09. That tells us which overlay to disassemble for the nature override without guessing.
