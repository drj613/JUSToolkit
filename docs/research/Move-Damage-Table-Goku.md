# Measured move damage: Goku vs an unresisted dummy

Enumerated 2026-08-14 with `scripts/emu/experiments/move_damage_table.py`.
Attacker Goku (`chr_b[0]`). Target **コマレッド** (`chr_b[70]`, 112.0 max HP,
**empty ability array**) — no resistances or weaknesses, so these are baseline
numbers.

| input | hits | damage per hit (displayed) | raw |
|---|---|---|---|
| **B** | 2 | **6.0** | 384 |
| forward+B | 2 | **5.0** | 320 |
| back+B | 2 | 6.0 | 384 |
| **up+B** | 6 | 1.0, 2.0, 1.0, 1.0, 2.0 … | 64, 128 |
| **down+B** | 2 | **5.0** | 320 |
| A / forward+A / up+A / down+A | 0 | — | — |
| **X** | 1 | **2.0** | 128 |
| down+X | 1 | 2.0 | 128 |
| up+X | 0 | — | — |
| **Y** | 6 | 2.0, 2.0, 4.0, 2.0, 2.0 … | 128, 256 |
| R | 0 | — | — |
| L | 0 | — | — |

Each row is 4 attack attempts from an identical savestate, so repeated values are
genuine repeats, not one observation.

## What this establishes

**A is jump, B is attack.** Every `A` variant deals zero damage while every `B`
variant except `up+X`'s neighbours deals damage. That settles the control mapping
empirically — earlier work had assumed it.

**`up+B` and `Y` are multi-hit strings.** They produce 6 dips per 4 attempts with
small per-hit values, so any move-damage table has to distinguish *per hit* from
*per string*. A single "damage" number per move would be wrong for these.

**`back+B` equals `B`.** Pressing away from the target turns the character, so it
resolves to the same neutral attack rather than a distinct move.

## This refines the "1/4-HP units" claim

I previously wrote that damage is authored in quarter-HP units and scaled ×16,
inferring it from four values that were all multiples of 16 — including an 80-raw
hit that is not a multiple of 64.

Every direct hit measured here is a multiple of **64**, i.e. a whole number of
displayed HP: 64, 128, 256, 320, 384. So for direct hits the quantum is 64, not
16.

The single sub-integer observation (80 raw = 1.250) was damage to a **benched**
character, which is a different mechanic. So the honest statement is: **direct-hit
damage is whole displayed HP; the one fractional value came from bench/splash
damage.** The ×16 generalisation rested on that one outlier and was too broad.

## Verification targets for static work

If a damage table is recovered from the ROM, it should reproduce, for Goku
against a target with no resistances:

- neutral B = **6**
- forward+B = **5**
- down+B = **5**
- X = **2**
- `up+B` and `Y` as multi-hit strings with 1–2 and 2–4 per hit

And with a blunt-resisting target, each becomes **2 lower** (see
`Damage-Reduction-Is-Flat.md`) — flat, not scaled.

## Reproducing

```bash
cd scripts/emu
python3 boot_to_battle.py training --slot pos_base
python3 experiments/move_damage_table.py --slot pos_base --approach 60
```

The script re-derives the session-local addresses itself. Keep the CPU on the
training default (`COM設定 なにもしない`) — a fighting CPU wanders and the trials
stop being comparable.
