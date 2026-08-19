# The flat −2 is ability 0x09 — both defence candidates are identical

> ## ⛔ REFUTED — the reduction is not ability `0x09`
>
> Current claim: [`jus-reduction-is-quarter-multiplier-xk1`]. The reduction is a **×0.75
> multiplier, 25% of base per gate**, gated on a class table at `0x02092E68` and bit 5 of
> `[r8+0x40]` — it does not come from ability `0x09`, and it is not a flat term. Poking the
> cached ability bitset and the live ability list both did nothing (`jus-w66`).
>
> Kept as a journal entry. See `README.md` in this directory: entries are history, never
> current.


Loop-Atlas iteration 33. Static analysis, settling a caveat the harness session flagged as untestable.

## The caveat

The harness measured resistance as a **flat −2** (Goku's B: `8.000` on コマレッド, `6.000` on ルフィ) but couldn't prove the cause:

> the two targets are *different characters* and may also differ in a per-character defence value.
> Blunt resistance is the likely cause, not a proven one.

Runtime testing couldn't help — resistance resolves at character load, so editing the ability array mid-battle changes damage by exactly zero.

## Both defence candidates match across the two targets

The character-init copy (K3) gives exactly two per-character scalar candidates: `chr_b[0x01]` (→ battle `+0x11`) and `chr_b[0x02]` (→ battle `+0x10`).

| idx | who | `[0x01]` | `[0x02]` | HP (size 4) |
|---|---|---|---|---|
| 0 | 悟空 Goku (attacker) | 2 | 3 | 152 |
| 12 | ルフィ Luffy (blunt-resistant target) | **2** | **5** | 144 |
| 70 | コマレッド (ability-free target) | **2** | **5** | 104 |
| 20 | ナルト Naruto | 2 | 3 | 144 |

**Identical on both fields.** Neither can produce the 2-point gap. So the flat −2 belongs to ability `0x09` (`打撃耐性ＵＰ`, blunt resistance) — Luffy has it, コマレッド (empty ability array) doesn't.

This moves attribution from **weakly supported** to **well supported**: the only two per-character scalars the init copies are equal across both targets.

One caveat remains: a defence value living somewhere the init doesn't copy would still be missed.

## Both fields are categorical, not stat proxies

If `[0x02]` were a power tier it should track base HP. It barely does — mean size-4 HP by value: `2`→118.0, `3`→124.0, `4`→130.5, `5`→129.0, `6`→128.8. Rises then plateaus, and each value spans a wide range (`[0x02]=5` covers HP 64 to 224).

`[0x01]` is worse: `1`→110.5, `2`→133.0, `3`→105.1 — non-monotonic, with `2` holding 56 of 74 characters. That shape fits a **3-way category with a dominant default**, like a light/medium/heavy weight class. `重量級` (heavyweight, ability `0x17`) and `軽量級` (lightweight, `0x18`) exist as abilities, so the concept is real in this game.

Both remain **PLAUSIBLE**, and neither is a stat proxy.

## Damage formula consistency check

The project's formula is `damage = floor(damage1/5) + (tier-2)`. Whichever side supplies `tier`, it's **constant across the two measured moves** — same attacker, same defender:

| move | damage | implication |
|---|---|---|
| B | 8.000 | — |
| DOWN+B | 7.000 | differs by exactly 1 |

The entire 1-point difference sits in `floor(damage1/5)`, meaning the two moves' raw damage values differ by roughly 5. Consistent with the formula's shape.

Can't tell attacker-side from defender-side `tier` without move data:

- attacker-side (Goku `[0x02]`=3): `8 = floor(damage1/5) + 1` → `damage1` ∈ 35..39
- defender-side (both targets `[0x02]`=5): `8 = floor(damage1/5) + 3` → `damage1` ∈ 25..29

Both self-consistent. Distinguishing them needs the per-move damage value, which lives in move script data nobody has located.
