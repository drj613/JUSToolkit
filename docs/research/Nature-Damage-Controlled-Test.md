# Does panel nature scale damage? A controlled test

**Result: no measurable effect**, and the ×1.5 figure I briefly inferred was
wrong. Measured 2026-08-14 with the melonDS agent bridge.

## The harness is deterministic, which is what makes this test possible

A savestate taken in a configured test battle (`COM設定 戦う`, `自動回復 OFF`)
reproduces **bit-identically**. Three consecutive loads, idling 1200 frames each,
produced the same two incoming hits every time:

| attempt | hits (raw) | displayed |
|---|---|---|
| 0 | 192, 2304 | 3.0, 36.0 |
| 1 | 192, 2304 | 3.0, 36.0 |
| 2 | 192, 2304 | 3.0, 36.0 |

Same values, same order, three for three. So a single-variable change against
this baseline is genuinely attributable.

## The test

Load the same savestate, **poke only the opponent's nature byte** (runtime struct
`+0x13`), verify it took, and re-measure. Player is Goku, nature `0` (力).
Triangle is 力 > 知 > 笑 > 力, so `笑` should have the advantage over the player
and `知` should be at a disadvantage.

| opponent nature | verified byte | hits (raw) | displayed | ratio vs neutral |
|---|---|---|---|---|
| `0` 力 Power | 0 | 192, 2304 | 3.0, 36.0 | 1.00 |
| `1` 知 Knowledge | 1 | 192, 2304 | 3.0, 36.0 | **1.00** |
| `2` 笑 Laughter | 2 | 192, 2304 | 3.0, 36.0 | **1.00** |

**Identical to the raw unit.** No nature effect on damage.

## Retracting my own ×1.5

Before running this, I measured 12.000 incoming damage with the opponent's nature
set to 力 and 18.000 with it set to 笑, and noted that 18/12 = exactly 1.5 — the
same figure the owner had guessed. It was wrong.

The two measurements came from **different CPU attacks**, not the same move under
two natures. The determinism check is what exposed it: reloading the savestate
produced 3.0 and 36.0, values that appear in neither earlier run, proving the
CPU's move choice — and therefore the damage magnitude — depends on position and
timing rather than on nature.

An appealing ratio between two uncontrolled numbers is not a multiplier. 1.5 was
especially seductive because it matched an independent guess, which is exactly
when a number deserves more scrutiny, not less.

## What this does and does not establish

**Does:** the runtime nature byte at `+0x13` is not consulted when damage is
applied. Changing it changes nothing about the damage dealt.

**Does not:** rule out nature affecting damage through a value computed *earlier*.
This is the same pattern already documented for resistances: rewriting a
character's ability array mid-battle also changed damage by exactly zero, because
resistance is resolved when the character loads. If nature feeds a multiplier, it
would likely be baked in the same way, and poking the byte afterwards would be
invisible — precisely as observed.

Supporting evidence from the static side (peer session): the only in-battle code
that reads nature compares the pairs (0,2), (1,0), (2,1) — every "theirs beats
mine" case — and accumulates a **count** into `[r7, #0x60]`. A counter, not a
scale factor. That fits nature feeding SP gain, a deck bonus, or an AI heuristic
rather than damage. And the other in-battle use of the nature predicate merely
selects a sprite archive (`_b.aar`).

So the current best reading is that **nature does not multiply damage**, with the
caveat that a load-time multiplier remains untested.

## How to test the load-time possibility

Poking after load can't answer it. Either:

- set the nature through the `相手の属性` menu (which acts *before* the character
  is re-initialised) and compare the same move — needs a way to force an
  identical CPU move, which is the hard part; or
- find where nature is read during character setup and check whether any scale
  factor is derived from it.

## Reproducing

```bash
cd scripts/emu
python3 jusemu.py state load fight_cfg
python3 jusemu.py poke 0x021DF7CB 02     # opponent nature byte (session-local!)
```

**The addresses are session-local** — re-derive the array base with
`find_battle_structs.py` first. Nature is at `hp_addr - 0x18 + 0x13`, i.e.
`hp_addr - 0x05`.
