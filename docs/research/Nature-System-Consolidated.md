# The nature system — consolidated

> ## ⚠️ This document's load-bearing conclusion is tainted — 2026-08-19
>
> This file concluded that nature is not read during damage computation
> [`jus-nature-does-not-affect-damage-0c6`], now `state:tainted`. The damage routine does
> read nature: the tables at `0x0209FEF4` and `0x0209FF14` hold `0x0180`, exactly 1.5 in
> 8.8, and the instructions turn a base of 8 into 12.000
> [`jus-nature-is-read-in-damage-path-hbt`].
>
> The measurement in here is not wrong, its scope was. The path reads a **2-bit field** —
> the column from `[r4+0x175]`, one of bits 1:0, 3:2 or 5:4 depending on flags; the row from
> `[r8+0x175] & 3` — on a per-ColPrm-scratch copy, and there is a bypass at `0x020824F4`
> that skips the tables entirely. So a null from poking one byte mid-battle had three
> innocent explanations, and 3/3 bit-identical runs measured reproducibility rather than
> scope. Keep the experiment; drop the generalisation.
>
> **The open caveat in §4 still stands** and is part of the claim: only "the nature byte
> is not read during damage computation" is established. Whether an ability-derived
> value lands at **load** time is untested.


Single authoritative summary, merging findings from two sessions that attacked
this independently: **runtime** experiments via the melonDS agent bridge (this
session) and **static** analysis of the ROM data and code (the battle-engine-atlas
session). Provenance is marked per claim because the two methods have different
failure modes.

**Bottom line: nature is a deck-building property. It does not affect battle
damage.** Two independent methods agree.

## 1. The enum and the triangle

| value | nature | |
|---|---|---|
| `0` | 力 Power | |
| `1` | 知 Knowledge | |
| `2` | 笑 Laughter | |
| `3` | なし Neutral | used as a **no-override sentinel**, not a real value |

Triangle: **力 > 知 > 笑 > 力**.

*Static (atlas):* confirmed from instructions, not from documentation — a loop at
`0x02160944`–`0x021609B8` reads nature from runtime struct `+0x13` and tests the
pairs (0,2), (1,0), (2,1), i.e. every "theirs beats mine" case.

*Runtime (this session):* the enum is corroborated live — struct `+0x13` read `0`
for Goku (a 力 character) and cycled `0 → 1 → 2` as the in-battle
`相手の属性` menu option was stepped through 力 → 知 → 笑.

## 2. How a panel's nature is resolved

*Static (atlas), accessor at `0x0214E480` in **ov05**:*

```
helper  (panelType 2) -> 3 (なし)
battle  (panelType 0) -> nib = (koma.flags[0xB] >> 4) & 0xF
                         nature = nib                       if nib != 3
                         nature = chr_b[abilityId*60 + 0x00] if nib == 3
support (panelType 1) -> chr_s[abilityId*20 + (kshapeGroup-1)*8]
```

So panel nature is **base nature with a per-panel override**, where high nibble
`3` means "no override, inherit from the character". Only **32** battle panels
carry an explicit override; every support and helper inherits.

Whole-game distribution: 力 226, 知 183, 笑 169, なし 312.

**Why every table search failed:** there is no per-koma nature table. Two of the
three inputs were fields already decoded for other purposes (`flags[0xB]`,
`kshapeGroup`), and the third is a fallback. A value-space search cannot find a
computation. The atlas session's earlier "nature is not in `koma.bin`" conclusion
was **wrong** — the field was there, in a nibble it had dismissed as incidental.

## 3. TAINTED — "nature does not affect damage" (scope was wrong, see banner at top)

> Nature **is** read in the damage path [`jus-nature-is-read-in-damage-path-hbt`]. The
> measurement below is sound; it read one byte, and the path reads a 2-bit field on a
> per-ColPrm-scratch copy with a bypass at `0x020824F4`. Kept for the measurement, not the
> conclusion.

This is the load-bearing conclusion, and it rests on two independent legs.

**Runtime leg (this session) — controlled single-variable test.** From a savestate
that reproduces bit-identically within a session (3/3 identical runs), poke *only*
the opponent's runtime nature byte (`+0x13`), verify it took, re-measure:

| opponent nature | verified byte | damage taken (raw) | ratio |
|---|---|---|---|
| `0` 力 | 0 | 192, 2304 | 1.00 |
| `1` 知 | 1 | 192, 2304 | **1.00** |
| `2` 笑 | 2 | 192, 2304 | **1.00** |

Identical to the raw unit. Player was 力, so `笑` should have had the triangle
advantage and `知` the disadvantage. Neither changed anything.

**Static leg (atlas).** Nature is read in only two places during battle, and
neither scales damage:

- The triangle loop accumulates a **count** into `[r7, #0x60]` — a counter, not a
  multiplier. Plausibly SP gain, a deck bonus, or an AI heuristic.
- The other in-battle use of the nature predicate merely selects a **sprite
  archive**: `_b.aar` with a `0x005F2000` VRAM allowance when an explicit nature
  is set, versus `.aar`/`0x005F1000` otherwise. Correct behaviour, since an
  alternate-nature panel has different artwork.

## 4. The one open caveat

The runtime test proves the nature byte **is not consulted when damage is
applied**. It does not rule out nature feeding a multiplier computed **at
character load**.

That is not paranoia — it is the documented behaviour of the *resistance* system,
which sits in the same struct: rewriting a character's ability array mid-battle
changes damage by exactly **zero**, because resistance is resolved at load
(`HP-And-Damage-Runtime-Findings.md` §2c). If nature were baked the same way,
poking `+0x13` afterwards would be invisible — exactly what we observe.

Poking cannot settle this. The route is static: find what reads nature during
**character construction**, as opposed to during a hit.

Given the two static readings above (a counter and a sprite selector) and no
observed runtime effect, "nature does not affect damage" is the best-supported
reading — but it is a *reading*, not a closed proof.

## 5. TAINTED — "a ×1.5 multiplier that does not exist" (it does exist)

> The tables at `0x0209FEF4`/`0x0209FF14` hold `0x0180` = 1.5 in 8.8, and runtime observed the
> 1.5 cell live. January's 1.5× reading was correct and this section's refutation of it was
> not [`jus-nature-is-read-in-damage-path-hbt`]. Kept for the reasoning about seductive
> agreement with an independent guess, which still holds.

Recorded because the near-miss is instructive.

Mid-session I measured 12.000 incoming damage with the opponent's nature set to
力, and 18.000 with it set to 笑. `18/12 = 1.5` — matching the owner's
independently-guessed ~1.5×. It was wrong.

The two numbers came from **different CPU attacks**, not one attack under two
natures. The determinism check exposed it: reloading the savestate produced 3.0
and 36.0, values absent from both earlier runs, proving the CPU's move choice
varies with position and timing.

**An appealing ratio between two uncontrolled numbers is not a measurement** — and
1.5 was especially seductive *because* it matched an independent guess, which is
when a number deserves more scrutiny, not less.

## 6. Remaining unknowns

- What consumes `[r7, #0x60]`, the triangle counter. If nature has any mechanical
  effect, this is the most likely place.
- Whether nature is read during character construction (§4).
- Low nibble of `koma.bin` flags byte `0xB`; `chr_s + 0x10`.

## Sources

- Runtime: `archive/Nature-Damage-Controlled-Test.md`, `HP-And-Damage-Runtime-Findings.md`
  (this session; harness in `scripts/emu/`).
- Static: atlas session, `docs/research/findings/nature-SOLVED.md` and
  `nature-hunt-exclusions.md` on branch `loop/battle-engine-atlas`; the
  "nature NOT in koma.bin" conclusion at commit `171f2c8` is **superseded** by
  `nature-SOLVED.md`.
