# Damage reduction is FLAT (−2), not a multiplier

> ## ⛔ REFUTED — do not use this document's central claim
>
> **The reduction is a ×0.75 multiplier (25% of base per gate), not a flat −2.0.**
> Claim: [`jus-reduction-is-quarter-multiplier-xk1`] (`state:runtime-confirmed`, 2026-08-19).
>
> Refuted by a two-move measurement with the in-session control firing twice: B and
> DOWN+B lost 512 and 448 in 8.8 fixed point — both exactly `base/4`, ratio constant
> at 0.750. This document's **DOWN+B row of 5.000 is wrong** (it measures 5.250), and
> that row was the entire basis of its "non-constant ratio ⇒ flat subtraction"
> argument. The earlier bead `jus-ccb` carried the flat−2.0 headline and is now
> `state:retracted`.
>
> Everything below is kept as the record of how the wrong answer was reached. It is
> **not** current. For the mechanism, read the claim bead.


**Result:** the damage reduction that makes Luffy take less from Goku's blunt
attacks is a **flat −2.0 displayed HP per hit**, not a percentage. Measured
2026-08-14 via the melonDS agent bridge.

This is the question that stayed open all session, and the reason it needed two
moves is that one measurement cannot separate the two hypotheses: against a
6-damage move, both "×2/3" and "−2" predict 4.

## The measurement

Attacker is Goku (`chr_b[0]`) in both cases, same deck, same buttons.

| move | unresisted target | Luffy | difference | ratio |
|---|---|---|---|---|
| B (punch) | **6.000** | 4.000 | **−2.0** | 0.6667 |
| DOWN+B | **5.000** | 3.000 | **−2.0** | 0.6000 |

**The difference is constant at −2.0. The ratio is not constant** (0.667 vs
0.600). A multiplier would hold the ratio; a flat subtraction holds the
difference. It holds the difference.

The unresisted target is `chr_b` index **70**, 112.0 max HP, with an **empty
ability array** (count = 0) — verified by reading the array, not assumed. Luffy
carries `0x09` 打撃耐性ＵＰ (blunt resistance UP) and `0x0C` 斬撃弱点, both read
from RAM earlier.

The 6.000 figure independently matches the owner's report that a punch does
**6** damage, which is a useful external check on the whole measurement chain.

## Also measured, same target

| move | damage |
|---|---|
| B | 6.000 (384 raw) |
| DOWN+B | 5.000 (320 raw) |
| UP+B | multi-hit: 1.0, 2.0, 1.0, 1.0 |

UP+B being a multi-hit string is worth noting — per-hit damage is small, so any
"total damage per move" table has to distinguish hits from strings.

## How the hits were made repeatable — the thing that unblocked this

Every earlier attempt failed because attacks silently missed. Position, not the
harness, was the blocker. What worked:

1. **Use a passive CPU** (`COM設定 なにもしない`, the training default). It does not
   move, so positions stay fixed and trials are comparable.
2. **Sweep the approach distance** instead of reasoning about it. Load the same
   savestate, hold `RIGHT` for N frames, then attack, for N across a range:

   | approach frames | hits |
   |---|---|
   | 0, 20 | none (too far) |
   | **40, 60, 80, 100** | **2 hits, 6.000 each** |
   | 140, 180, 240 | none (walked past; now facing away) |

   The window is wide (40–100) and the damage identical throughout it, so the
   result does not depend on hitting one exact frame.

Anything past ~140 frames walks *through* the opponent and ends up facing the
wrong way, which is the failure that wasted several earlier runs.

## The numbers are net of auto-heal — and the conclusion survives

All four figures were measured with 自動回復 ON, so each is `true − 2.0` (one
frame of regen landing with the hit). True values:

| move | unresisted | Luffy | difference | ratio |
|---|---|---|---|---|
| B | **8.000** | 6.000 | **−2.0** | 0.750 |
| DOWN+B | **7.000** | 5.000 | **−2.0** | 0.714 |

The difference is still exactly −2.0 and the ratio is still not constant
(0.750 vs 0.714), so **the reduction is flat, not multiplicative** — unchanged.
A constant offset applied to both sides cancels in a difference, which is
precisely why the two-move design was robust to a measurement error neither of
us had spotted yet.

The 8.000 figure is verified directly: a breakpoint shows **512** handed to the
HP drain, and with the heal off HP falls 512 per hit cumulatively.

**Restating the owner cross-check:** the owner's independently reported "6
damage" matches the **net-of-regen** number, not true move damage — they were
also observing training mode with the heal on. So the agreement is real and still
validates the HP scale, address derivation and dip-reading, but it validates the
*net* observation, not the raw move value. My earlier phrasing overstated what it
confirmed.

## Bounding the claim honestly

**Solid:** whatever reduces Luffy's incoming damage relative to this target is
**flat, not multiplicative**. Two moves with different base damage, constant −2.0
difference, non-constant ratio. That conclusion holds regardless of mechanism.

**Not established:** that the −2 comes specifically from ability `0x09`. The two
targets are *different characters*, so they may also differ in a per-character
defence value. Attributing the −2 to blunt resistance is the most likely reading,
not a proven one.

The clean version of this test would compare one target with and without the
ability — but that is not currently possible: rewriting the ability array
mid-battle changes damage by exactly zero, because resistance is resolved when
the character loads (see `HP-And-Damage-Runtime-Findings.md` §2c). A load-time
route would be needed.

**Update 2026-08-17 — the cached-bitset route was tried and it fails.**
`Ability-Bitset-Is-Not-Resistance.md` pokes the bitset at `entity+0x128` rather
than the ability array, on one target, so there is no cross-character confound.
All 32 bits, one at a time: only bit 4 (Auto-Guard) changes blunt damage taken,
and it drives it to zero. Bit 9 (blunt resistance) changes it by exactly nothing,
as do blunt weakness, slash resistance and status resistance. The instrument is
demonstrably live, so this is a real null. **The attribution above therefore stays
unproven, and a per-character defence value is now the leading explanation rather
than a caveat.**

**Cross-session caveat:** the 4.000 and 3.000 figures come from an earlier battle
against Luffy, not from the same battle as the 6.000 and 5.000. Same attacker and
same moves, but not the same session, and savestate reproducibility is only
established *within* a session.

## Reproducing

```bash
cd scripts/emu
python3 boot_to_battle.py training --slot pos_base
python3 find_battle_structs.py          # addresses are session-local
# then: load pos_base, hold RIGHT ~60 frames, press B, watch opponent HP dip
```

Opponent HP is at `player_base + 0x61C`. With the auto-heal on, read damage as the
**minimum of the dip**, not before/after.

## What DOWN+B actually is (confirmed 2026-08-18)

`DOWN+B` is a **Forced Change** — it makes the opponent swap to a different battle character. Every battle character has it. It's universal, not part of anyone's individual kit.

It's **not** a "special" the way X moves are. It's a normal attack that happens to force a switch, so there's no reason to think it goes through a different damage pipeline.

**Why this was worth checking.** The two-move argument above only works if both moves hit the *same* reduction step. If `DOWN+B` were scripted or special-cased, "constant −2.0 across two moves" could just be two independent flat offsets that happen to match — and the damage path does have special cases: Codex found a conditional ×0.5 at `0x0215AC28` and a caller feeding the drain a fixed `0x800` (32.0 displayed). Confirming it's an ordinary attack rules that out.

**So the conclusion stands**, with one residual gap stated plainly: neither move used was a plain no-side-effect attack — `B` is a punch, `DOWN+B` forces a switch. Re-running the comparison with a second ordinary attack that has no side effect would close it. `UP+B` isn't a good candidate; it's a multi-hit string (1.0, 2.0, 1.0, 1.0), so per-hit values are small and harder to compare.
