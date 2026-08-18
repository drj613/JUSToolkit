# The cached ability bitset is read at damage time — but resistance is not in it

**Result:** the bitset at `entity + 0x128` is real, live, and checked during
combat. Setting bit 4 (`0x04` オートガード, Auto-Guard) on a target drives damage
to **zero**. But out of all 32 bits, that is the *only* one that changes blunt
damage taken. Bit 9 (`0x09` 打撃耐性ＵＰ, blunt resistance) does exactly
nothing.

The flat −2.0 from `Damage-Reduction-Is-Flat.md` is **not** coming from
ability `0x09` through this route. Measured 2026-08-17 via the melonDS agent
bridge.

## Why this test was worth running

`Damage-Reduction-Is-Flat.md` proved the reduction is flat, not multiplicative,
but couldn't say *what causes it*: the resisting target (Luffy) and the
unresisted target (`chr_b[70]`) are different characters, so a per-character
defence value fits the data just as well as blunt resistance does. The clean
test — one target, ability on and off — failed, because rewriting the visible
ability array mid-battle changed damage by exactly zero.

`Damage-Path-Codex-Findings.md` §2 explained why and proposed the fix. At load,
`0x0215FB3C` walks the ability list and caches each ID as a *bit* in a word at
`entity + 0x128`. The array is a source record; the bitset is what runtime logic
actually reads. So poke the bitset, not the array.

That prediction is confirmed, and the experiment it unlocked comes back negative.

## Finding the entity — the handoff arithmetic is wrong

`entity + 0x56C = char_struct` does not hold as a fixed offset. Applied to this
battle it puts the opponent's entity at `0x021DF24C`, which lands inside the
*player's* deck array. It was almost certainly a pointer load, `ldr [entity, #0x56C]`,
not a subtraction.

The route that works — verified, not assumed:

1. `char_struct = hp_block − 0x18`. Cross-check: `find_battle_structs.py` reports
   the chr_b index at `hp+0x29`, disassembly puts it at `char+0x41`, and
   `0x41 − 0x29 = 0x18`. Separately, RAM holds many live pointers to
   `0x021DF7B8` (= opponent `hp_block − 0x18`), so this is a real object boundary,
   not an arithmetic coincidence.
2. Scan RAM for u32 pointers to `char_struct + 0x10`. The object holding one is
   the entity.

This session gave player entity `0x022286E0` and opponent entity
`0x0224E1E0`. Both share the same vtable pointers at `+0x04` (`0x0215D3B4`) and
`+0x08` (`0x0215D530`), confirming one class, and each holds a self-pointer at
`+0x00`.

All of these addresses are **session-local**. Re-derive them every time.

## The bitset exists exactly as predicted

| entity | abilities | `entity+0x128` |
|---|---|---|
| Goku, `0x022286E0` | `[7, 15]` | `0x00008080` — bits 7 and 15 |
| dummy `chr_b[70]`, `0x0224E1E0` | none | `0x00000000` |

Bits 7 and 15, nothing else, matching the two abilities Goku carries. A full-RAM
scan for the value `0x00008080` finds it in exactly one live object, so there is
no second mirrored copy to worry about.

## The sweep

One target (`chr_b[70]`, no innate abilities), one attacker (Goku), one move (B,
a punch — blunt), 32 conditions. Each condition reloads `pos_base`, writes a
single bit, and reads the opponent's HP **per frame** — not before/after, because
training regen restores +128 raw per frame and would mask the hit otherwise.

Auto-heal is ON, so every figure is net of one frame of regen. Baseline is 384
raw = 6.0 displayed, which reproduces the documented value exactly.

| bit | ability | hits | raw | displayed | vs baseline |
|---|---|---|---|---|---|
| 4 | `0x04` オートガード Auto-Guard | **0** | **0** | **0.0** | **−6.000** |
| all other 31 | — | 4 | 384 | 6.0 | +0.000 |

Baseline was re-measured six times across the sweep — at the start, after every
eighth bit, and at the end — and read 384 every single time. No drift, no voided
condition, no poke that failed to stick.

Of the four bits that should have mattered:

| bit | ability | expectation | result |
|---|---|---|---|
| 9 | `0x09` 打撃耐性ＵＰ blunt resistance | damage drops ~2.0 | **no change** |
| 11 | `0x0B` 打撃弱点 blunt weakness | damage rises | **no change** |
| 10 | `0x0A` 斬撃耐性ＵＰ slash resistance | no change (control) | no change |
| 8 | `0x08` 状態変化耐性 status resistance | no change (control) | no change |

## Why this null is trustworthy

Seven times in an earlier session a tool reported success while measuring
nothing, so a zero result carries a burden of proof. This one meets it, because
reachability was verified separately from the payload:

- **The measurement fires.** Baseline lands 4 hits at 384 raw, matching the
  independently documented value.
- **The poke sticks.** Read back after every write, and a per-frame watch on the
  bitset word confirms it held the poked value for all 306 frames of every run.
- **The word is live and effective.** Bit 4 sends damage to zero — HP perfectly
  flat where baseline dips 384 and heals back — while the emulator keeps running
  all 306 frames. That is not a crash or a hang; it is Auto-Guard doing exactly
  what Auto-Guard is documented to do.

An instrument that swings damage from 6.0 to 0.0 on a single bit flip is not
dead. When it reads zero for bit 9, the zero is about bit 9.

The `0xFFFFFFFF` case that first surfaced this is worth recording: saturating the
word gives total immunity, and bisection pinned that entirely to bit 4. The
immunity is Auto-Guard, not an accumulation of resistances.

## What this means

**Settled:** the cached bitset at `entity+0x128` is read during combat, and
per-bit — one bit produces one specific documented behaviour. Codex's mechanism
is correct.

**Settled:** blunt resistance is not applied by reading bit 9 of that word at
damage time. Neither are blunt weakness, slash resistance, or status resistance.

**Still open:** what causes the flat −2.0. The confound
`Damage-Reduction-Is-Flat.md` flagged is now the leading hypothesis, not just a
caveat — a per-character defence value, or a stat derived at load from the
ability list and stored somewhere other than this bitset. Ability `0x09` may
still be the ultimate cause through a load-time path; what is ruled out is the
runtime read.

**The obvious next step, and its cost.** The converse test — clear bit 9 on a
real resistor (Luffy) and see whether damage rises — is the one remaining cheap
test of this same route, and it would tell us whether "the bit is inert" or "the
bit only matters when set at load." It needs a fresh battle against Luffy, which
means menu navigation, which desynced 4+ times in one session. That is why nav
reliability is the next piece of work, not this.

Note also that Auto-Guard is documented as costing SP. The zero-damage result
here was measured with SP available; a target with no SP might behave differently.
Not tested.

## Reproducing

```bash
bash scripts/emu/launch_emu.sh
cd scripts/emu
python3 jusemu.py state load pos_base
python3 find_battle_structs.py --no-live      # addresses are session-local
# derive the entity: char = hp_block - 0x18, then find pointers to char+0x10
python3 experiments/ability_bitset_probe.py   # 5 conditions incl. controls
python3 experiments/ability_bit_sweep.py      # all 32 bits, ~35 min
bash scripts/emu/stop_emu.sh
```

Both scripts take `--addrs`/defaults for the session-local addresses; a stale
address reads believable garbage rather than failing.

## The converse test: clearing bit 9 on a real resistor (2026-08-18)

The sweep above added bits to a target that had none. The obvious pushback: maybe a resistance bit only matters on a character whose resistance is actually live. So here's the other direction — Codex's proposed step 2: take a real blunt resistor and strip the bit away.

**The target.** A training battle against Luffy, confirmed from RAM, not assumed — `chr_b[12]`, 152.0 max HP, ability array `[9, 25, 12, 14]`. That includes `0x09` 打撃耐性ＵＰ (blunt resistance) and `0x0C` 斬撃弱点 (slash weakness), exactly the pair earlier notes recorded for Luffy. The attacker is Goku, `chr_b[0]`, abilities `[7, 15]`, carrying neither — a clean attacker with no relevant modifiers.

**Locating the bitset two independent ways.** This matters more than it sounds, so both are recorded:

1. Scan RAM for u32 pointers to `char_struct + 0x10` and grab the object holding one — the same method from the first half of this document.
2. Compute what the bitset *should* be from the four ability IDs before searching for it: bits 9, 12, 14 and 25 give `0x02005200`. Search 4MB of RAM for that exact word.

Method 2 returns **exactly one match**, at `0x02244308`, implying entity `0x022441E0`. Its `entity+0x04` holds vtable `0x0215D3B4` — the same vtable as both entities identified earlier. One method reasons about pointer topology, the other about a predicted bit pattern, and they converge on the same object. That kind of agreement can't come from shared bias. It also lines up with the atlas session's static finding that `entity+0x10` is the record handle.

**The measurement.** One B press (a punch — blunt type) per trial, HP read per frame, three reps per condition, savestate reloaded before each.

| condition | bitset written | raws (3 reps) | delta |
|---|---|---|---|
| baseline | untouched `0x02005200` | 352, 352, 352 | — |
| clear bit 9 (blunt resistance) | `0x02005000` | 352, 352, 352 | **+0.000** |
| clear bit 25 (control) | `0x00005200` | 352, 352, 352 | +0.000 |
| clear bit 12 (slash weakness, control) | `0x02004200` | 352, 352, 352 | +0.000 |

Twelve runs, 352 raw every single time. Removing blunt resistance from a character who demonstrably has it changes incoming blunt damage by exactly nothing.

**Both directions now agree.** Setting bit 9 on a target without it: no effect. Clearing bit 9 on a target with it: no effect. The cached bitset at `entity+0x128` is not consulted when damage is scaled, in either direction, and the flat −2 is not ability `0x09` by way of any runtime read of that word.

The next lead to chase is a per-character defence value, or a stat derived from the ability list at load time and stored somewhere else. The community guide describes *three* separate resistance categories (punch/kick, special attacks, blades), and the atlas session found `record+0x3C`'s low nibble used as an ignore mask — the right shape for a field like that, and three categories fit in four bits comfortably. That's the better thread to pull.

**One honest caveat about the baseline number.** 352 raw here versus 384 against the ability-free dummy earlier aren't comparable: different battle, different mode, different positions, and auto-heal state wasn't equalised between them. Only the within-condition deltas above are being claimed, and those are what the argument rests on.
