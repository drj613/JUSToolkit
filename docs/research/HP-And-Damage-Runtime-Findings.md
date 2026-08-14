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

### The struct layout around HP (confirmed live)

Reading the bytes just past HP settles the 16-bit question from a second angle:

| offset (opponent) | size | field |
|---|---|---|
| `0x021DF7F0` | u16 | HP, 1/64 units |
| `0x021DF7F2` | u8 | ability count |
| `0x021DF7F3`+ | u8[] | ability IDs |

Live values: Luffy count = 4, IDs = `[9, 25, 12, 14]`. Goku (player, same
layout at `0x021DF1D6` / `0x021DF1D7`) count = 2, IDs = `[7, 15]`.

The ability count sitting immediately after a **two**-byte HP field is what makes
the layout coherent. If HP were a single byte at `0x021DF7F1`, then
`0x021DF7F0` would be an unexplained field wedged in front of it.

Two of Luffy's IDs are decisive, against the ability table in
`docs/research/findings/abilities-all-57-named.md`:

- `0x09` = 打撃耐性ＵＰ, **blunt resistance UP**
- `0x0C` = 斬撃弱点, **slash weakness**

That independently confirms the owner's report that Luffy resists blunt and is
weak to sharp — from RAM, not from play feel. It also means **the 4.000 blunt
number below is a resisted value**, so it cannot be used as a base-damage
baseline. Goku's `[7, 15]` contains neither, so he is a clean *attacker*.

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

## 2b. Every max-HP value is a multiple of 8

All eight deck slots, read as u16 in one pass:

| slot | raw | displayed | ability IDs |
|---|---|---|---|
| P active (Goku) | 10240 | 160.0 | `[7, 15]` |
| P deck1 | 8704 | 136.0 | `[47, 46, 35]` |
| P deck2 | 9216 | 144.0 | `[2, 14, 15]` |
| P deck3 | 8192 | 128.0 | `[3, 26, 46, 24, 10]` |
| O active (Luffy) | 9728 | 152.0 | `[9, 25, 12, 14]` |
| O deck1 (Naruto) | 9216 | 144.0 | `[2, 14, 15, 5]` |
| O deck2 | 512 | 8.0 | `[]` |
| O deck3 | 0 | 0.0 | `[]` |

Two things fall out.

**HP itself carries no fraction.** Every value is an exact multiple of 64 raw, so
the 1/64 units exist for *damage*, not for storing HP. Sub-integer values like
the measured 1.250 hit are produced by the damage path, not read from a table.

**Every non-zero value is a multiple of 8 displayed HP:** 160, 136, 144, 128,
152, 8 = 8 × {20, 17, 18, 16, 19, 1}. This lines up with the `Ｊ魂最大値＋`
ability granting `+8` per stacked source — 8 looks like the game's HP quantum.

### RESOLVED: HP is table data, and my formula below was wrong

Keep reading — everything from "This falsifies" to the end of this section is
**superseded**. The quantum argument was right; the replacement formula was not.

Max HP comes from a per-character, per-size table in `chr_b.bin`, plus the `+8`
bonus. The battle struct carries the table index at **`hp_addr + 0x29`**:

`max_HP = chr_b[index][size − 4] + 8 × (active Ｊ魂+ sources)`

`chr_b.bin` is 74 × 60 bytes, and each record holds five u8 HP values at
`0x10, 0x14, 0x18, 0x1C, 0x20`. Five slots for the five battle panel sizes
(4–8). All 370 of those bytes are multiples of 8, which is where the quantum
comes from.

Verified against six characters in one battle — every one exact:

| slot | index @+0x29 | observed | `chr_b[i][0]` | delta | role |
|---|---|---|---|---|---|
| P active (Goku) | 0 | 160 | 152 | **+8** | active |
| O active (Luffy) | 12 | 152 | 144 | **+8** | active |
| O deck1 (Naruto) | 20 | 144 | 144 | 0 | bench |
| P deck2 (Naruto) | 20 | 144 | 144 | 0 | bench |
| P deck1 | 35 | 136 | 136 | 0 | bench |
| P deck3 | 41 | 128 | 128 | 0 | bench |

The two `+8` rows are exactly the two **active** characters, and the four
zero-delta rows are the bench. That is the leader bonus, visible as data.

Also note the two Naruto slots share index 20 *and* HP — same index, same HP, as
a table model requires.

**Naruto's ladder, `chr_b[20]` = `[144, 160, 176, 144, 144]`:**

| size | displayed | raw |
|---|---|---|
| 4 | 144 | 9216 (observed ✓) |
| 5 | **160** | **10240** |
| 6 | 176 | 11264 |
| 7/8 | 144 | filler — sizes 7–8 use a second record (ナルト（九尾）) |

So the size-5 answer is **160 / raw 10240**, not the 152 predicted below.

**Caveats.** The `+8` is confirmed as attaching to the *active* characters, but
this battle can't separate "is the leader" from "is currently active" — both
actives had exactly one source. And the slot→size mapping rests on the
structural argument (5 slots, 5 battle sizes) plus one anchor (Naruto size 4 =
144); sizes 5–8 are not yet directly observed in RAM.

### ~~This falsifies "HP = size × 36" without an experiment~~ (superseded)

The proposed discriminator for the HP-scaling question was that 4-koma Naruto
reads 144, so `144 = 4 × 36` and size-5 should read **180**.

But `180 / 8 = 22.5`. A size-5 panel at 180 would be the only non-multiple-of-8
HP value observed, so **`size × 36` cannot be right** if the quantum holds.

A `+8 per size step` rule fits the same anchor point and respects the quantum:

`HP = 8 × (14 + size)` → size 4 = **144** ✓, size 5 = **152**, size 6 = 160,
size 7 = 168, size 8 = 176.

That also reproduces the reported 4-koma maximum of 176 (144 + 8×4 from leader
plus three relationships), and matches "8-koma panels have the most HP."

**Confidence:** the multiple-of-8 invariant rests on 6 non-zero samples, so it is
strong but not proven. The `14 + size` constant is a *guess* fitted to one known
size — the HP ladder 16..20 seen above could just as easily be per-character base
HP rather than a size ladder. What is solid is the falsification: 152 and 180 are
far apart, so a single size-5 reading decides it.

## 2c. The ability array is informational — damage does not read it

Tested with `scripts/emu/experiments/resistance_probe.py`. **Result: negative,
and well controlled.**

Luffy carries `0x09` (blunt resistance UP). Rewriting his array to remove it and
decrementing the count changed damage by **nothing at all**:

| move | with `0x09` | `0x09` removed |
|---|---|---|
| B | 4.000 | 4.000 |
| DOWN+B | 3.000 | 3.000 |

The reverse direction agrees. Goku's array is `[7, 15]` (no resistance); adding
`0x09` to give `[7, 15, 9]` left incoming damage at exactly **8.000**, measured
twice.

Three controls make this a real result rather than a failed poke:

1. **`poke` demonstrably reaches memory.** Writing Luffy's HP to 8192 read back
   as a lower value immediately, then training-regen restored it to 9728. So
   writes land.
2. **The edit persists.** The stripped array still read `[25, 12, 14]` after 3
   seconds and after further attacks. The game does *not* rewrite it, so the
   modification was live at the moment each hit landed.
3. **Both directions tested** — removing from a resistant target and adding to a
   non-resistant one.

**Conclusion:** the array at `hp_addr+0x03` is a *source list* — good for reading
which abilities a character has, useless for changing behavior. Resistance and
weakness are applied from precomputed state established when the character
loads, not looked up per hit.

Two consequences. Any "poke an ability ID and observe the effect" plan is dead —
it cannot work through this array. And the 4.000 figure still can't be labelled
resisted-or-not from runtime evidence alone: either resistance is baked in
elsewhere, or Goku's B is not blunt and `0x09` never applied to it. Static
disassembly of the damage path is the way to separate those.

## 2d. WARNING: the absolute addresses move between battles

Everything above is correct *for one battle session*. The addresses themselves
are not.

The **same deck** in two different training battles put the player character
array at:

| battle | player array base |
|---|---|
| the `training_luffy` savestate | `0x021DF1D4` |
| a fresh boot, different stage | `0x021DF1B4` |

A **0x20 shift**. Every absolute HP address in `scripts/gdb/README.md` and in
this document is really "the address in the session it was recorded in."

This is nastier than a plain wrong answer, because the neighbouring values look
believable. Reading `0x021DF1D4` in the second battle returned `62072`
(≈969 "HP") from an unrelated array, with the slots below it decrementing by 48
each — tidy enough to look like a real structure.

**Always locate the array, never hardcode it:**

```bash
python3 scripts/emu/find_battle_structs.py     # dumps RAM, prints the base
```

It scans for the real signature — **four consecutive 0x50-byte slots**, each
with HP a multiple of 64, a small ability count, and a `chr_b` index < 74,
cross-checked against the actual `chr_b.bin` HP values. Requiring the *group* is
what makes it precise: single slots match **1167** times in 4MB (mostly inside
ARM9 code, since "multiple of 64 followed by a small byte" is unremarkable),
while the four-slot group is essentially unique.

The `+0x61C` player→opponent offset should also be re-verified per session
rather than trusted.

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
   Now known to be a genuinely resisted measurement: Luffy carries ability
   `0x09` (blunt resistance UP). The clean experiment is the *same* Goku B press
   against a target whose ability array contains neither `0x09` nor `0x0C` —
   check the array at `+0x02`/`+0x03` from the target's HP before trusting any
   baseline. `ability.bin` gives the resistance entries **no parameter**, so the
   magnitude is not in that table; it is either hardcoded in the damage path or
   in the ability description text.
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
