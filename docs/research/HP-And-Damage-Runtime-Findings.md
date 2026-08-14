# HP and Damage: Runtime Findings

**Status:** measured live, 2026-08-14, via the melonDS agent bridge (`scripts/emu/`).
**Method:** Jump Ultimate Stars, J Arena → Training, deck 1 ("Koma R,G,Y", Goku
active) vs the COM starter deck (Luffy active). Per-frame memory watches logged
to `log.jsonl` while scripted button plans ran. Raw logs under `/tmp/jus_emu/runs/`.

## 1. HP is 16-bit fixed point, 1/64 units

This is the big correction. Earlier docs said "HP is stored at 1/4 scale (160
displayed = 40 stored)". That byte is real, but it's only the **high byte of a
16-bit little-endian HP value**.

| | address | meaning |
|---|---|---|
| low byte | `0x021DF7F0` | fractional HP (1/64 units) |
| high byte | `0x021DF7F1` | the "1/4 scale" byte the old docs describe |

`hp_u16 = displayed_HP × 64`

Verified exactly:

| character | raw u16 | displayed |
|---|---|---|
| Goku (player active) | 10240 | 160.0 |
| Luffy (opponent active) | 9728 | 152.0 |
| Naruto (opponent deck slot 1) | 9216 | 144.0 |

`9216 / 64 = 144`, matching the independently-derived 4-koma Naruto HP of 144
from koma static analysis. Three independent values all land on exact integers
at scale 64 — the scale isn't a coincidence.

**Why it matters:** damage of 6 or 1.25 displayed HP can't be represented at 1/4
scale, so any damage-formula work reading only the high byte silently truncates.
All the sub-integer damage below was invisible before this.

The same +0x50 slot stride and +0x61C player→opponent offset from
`scripts/gdb/README.md` still hold; just read 2 bytes at `addr - 1` instead of
1 byte at `addr`.

### Address table (u16 form)

| slot | player | opponent |
|---|---|---|
| active | `0x021DF1D4` | `0x021DF7F0` |
| deck 1 | `0x021DF224` | `0x021DF840` |
| deck 2 | `0x021DF274` | `0x021DF890` |
| deck 3 | `0x021DF2C4` | `0x021DF8E0` |

## 2. Measured damage values

All against the same savestate, so positions and decks are identical.

| attacker → target | move | raw delta | displayed damage |
|---|---|---|---|
| Goku → Luffy | B (basic, blunt) | 256 | **4.000** |
| Luffy → Goku | COM basic | 512 | **8.000** |
| Goku → Luffy | DOWN+B | 192 | **3.000** |
| Goku → Naruto (opponent deck slot 1) | DOWN+B | 80 | **1.250** |

The Goku→Luffy B hit reproduced 5 times in one run at exactly 256 raw each —
damage is deterministic for a fixed matchup and move.

The owner reports a punch doing **6** damage against a non-resisting target, and
that Luffy **resists blunt** (punch/kick) while being **weak to sharp**. 4 vs 6
fits a 2/3 multiplier on blunt against Luffy, but this is **one data point
against one target and is not yet confirmed** — see open questions.

### DOWN+B also damages a bench character

DOWN+B produced two separate, differently-sized HP drops: 3.000 on the active
opponent (Luffy) and 1.250 on opponent **deck slot 1** (Naruto). So bench koma
can take damage while benched. 1.250 = 80 raw units, which isn't a multiple of
64 — more proof the value is genuine sub-integer fixed point, not a rounding
artifact.

Trying to force a character *swap* with DOWN+B didn't change who was active
(opponent active HP stayed at Luffy's 152 baseline across 6 attempts).

## 3. Training mode heals to full — read damage per frame, not before/after

In Training, HP snaps back to full within a few frames of any hit: it steps up
roughly one 1/4-unit (64 raw) every ~2 frames until full.

What this means for any measurement harness:

- **Don't** diff HP before and after an exchange. It'll read zero.
- Log HP **every frame** and compute damage as `baseline − min(dip)`, or detect
  each downward step. The bridge's per-frame `log.jsonl` does this.
- A hit is visible for only ~2–4 frames. Sampling at even 10 Hz will miss hits.

## 4. Facing decides whether an attack connects at all

The single biggest source of false "0 damage" results. Walking right past the
opponent leaves the player on the far side still facing right, so every attack
whiffs while the opponent keeps landing hits.

Evidence: with the same savestate and adjacent characters, pressing each of
A, B, X, Y, R, L twelve times produced **zero** opponent damage across all six
buttons — while the COM landed an 8.000 hit on us. Prefixing the plan with ~12
frames of LEFT (turn around) made the *same* B press land 5/5 times.

So: **a scripted attack plan must set facing first.** Overlapping sprites aren't
enough — the characters were visually on top of each other in the whiffing runs.

**Related, owner-reported (not yet measured here):** walking *through* another
character slows you down dramatically. Two consequences for scripted plans.
Movement is not a constant speed, so "hold RIGHT for N frames" covers a
different distance depending on whether you overlap the opponent — don't
calibrate approach distance from a clean-field run. And it gives a second reason
the walk-past runs went wrong: the player spends many extra frames inside the
opponent, which is also where attacks whiff. Worth measuring as a movement-speed
multiplier once position addresses are pinned down (see JUS-3am).

## 5. Open questions this raises

1. **Is blunt resistance multiplicative (×2/3) or flat (−2)?** 4 vs 6 fits both.
   Needs a second base-damage value against Luffy, or the same move against a
   non-resisting target measured on this harness (the 6 is owner-reported, not
   yet measured here).
2. **Do resistances stack?** Owner expects sharp+special resistances to stack.
   Untested.
3. **Why does DOWN+B hit a benched character for 1.250?** Splash? A support
   mechanic? A fixed fraction of the main hit (1.25 / 3.0 = 0.4167, not
   obviously clean)?
4. **What sets the 1/64 fraction?** With HP in 1/64 units, damage may be
   computed as a fraction and truncated. `fn_health_calc` at `0x020784FC` is
   the place to look.

## 6. Reproducing

```bash
bash scripts/emu/launch_emu.sh              # boots ROM + bridge, no clicking
cd scripts/emu
python3 jusemu.py state load training_luffy # in-battle savestate
python3 jusemu.py run plans/damage_probe.json
```

Then read the printed `log.jsonl`. Damage events are downward steps in the
watched HP values.

Known harness bug: a plan with `load_state` set (load *inside* a run) stops the
bridge's `_Update` callback. Load as a separate `state load` command first. See
`scripts/emu/README.md`.
