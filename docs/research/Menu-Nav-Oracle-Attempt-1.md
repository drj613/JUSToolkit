# Menu navigation: why a cross-boot golden trace cannot work

**Result:** the idea was to record what each menu screen looks like in RAM, then swap `boot_to_battle.py`'s fixed settle timers for "wait until the screen matches what we expect." That can't work across boots, and the numbers show why: **two runs of the exact same button sequence disagree in about 1.6 million bytes of main RAM — and they already disagree by ~974,000 bytes at the title screen, before a single button is pressed.** Measured 2026-08-17.

> **Corrected below.** The runs did not all reach a battle, which confounds the
> per-step tables. The title-screen measurement survives. Read the correction at
> the end before using any number here.

This is attempt 1 and it failed. The failure tells us something useful, so it's written up instead of deleted.

## What was measured

`capture_boot_trace.py` booted the ROM three times, walked the same 10-step sequence, and dumped all 4MB of main RAM after each step. All three runs reached a real battle, so all three were kept — none was thrown out as desynced.

`find_screen_id.py` then looked for bytes that stay the same across every repeat of a step but differ between steps. That filter is the whole method: millions of bytes differ between any two dumps taken at different moments (frame counters, RNG, animation, audio), so requiring stability within a screen is what separates a screen id from a clock.

It found 4356 such bytes, and **none** of them tells all 11 steps apart. Worse, adjacent steps are nearly identical:

| transition | stable bytes that differ |
|---|---|
| `00_title` → `01_skip_intro` | 2 |
| `01_skip_intro` → `02_to_arena` | **0** |
| `02_to_arena` → `03_enter_arena` | 1 |
| `03_enter_arena` → `04_arena_down0` | **0** |
| `04_arena_down0` → `05_arena_down1` | 3 |
| `05_arena_down1` → `06_arena_down2` | 1 |
| `06_arena_down2` → `07_choose_mode` | **0** |
| `07_choose_mode` → `08_deck_select` | 4352 |
| `08_deck_select` → `09_stage_select` | **0** |
| `09_stage_select` → `10_rule_start` | **0** |

Five of ten transitions are completely invisible. The one big jump — 4352 bytes at `07_choose_mode` → `08_deck_select` — is a mode/overlay load. Those 4356 candidates are basically all just that one event, which is why no single byte separates the finer steps.

There's also no cursor. A targeted search for any byte reading 0, 1, 2, 3 across the three DOWN presses in the arena menu returns **zero candidates**, even though those presses visibly move a cursor three rows.

## Why — the number that explains it

Counting bytes that differ *between runs* at the same step:

| step | r0 vs r1 | r0 vs r2 | r1 vs r2 |
|---|---|---|---|
| `00_title` | 973,944 | 973,944 | 46,573 |
| `03_enter_arena` | 682,519 | 1,632,015 | 1,632,528 |
| `06_arena_down2` | 682,539 | 1,632,158 | 1,632,693 |
| `10_rule_start` | 382,485 | 1,761,637 | 1,643,938 |

Up to 1.7 million bytes — 40% of main RAM — differ between two runs sitting on the *same* screen. At the title screen, before any input, two runs already differ by 974,000 bytes.

So the cursor byte almost certainly exists. It just doesn't land at the same address with the same value across boots, so the stability filter tosses it out along with the real noise. **The filter isn't tuned wrong; it's the wrong tool for data this non-reproducible.** More runs won't fix it — they shrink the surviving set, not improve it.

A caution from the atlas session predicted part of this: START skips the opening intro, so if one run takes the intro and another skips it, the same presses land on different screens and step indices shift. That would produce exactly this pattern. It's not the whole story, though — the title-screen disagreement happens before any press.

Note the asymmetry in the table: run 0 disagrees with runs 1 and 2 far more than they disagree with each other in some places, and less in others. Whatever varies is not a simple boot-time nonce.

## What this rules in and out

**Ruled out:** comparing a live screen against a golden fingerprint recorded on a previous boot. Absolute RAM values aren't portable across boots — the same lesson `find_battle_structs.py` already carries for battle struct addresses, now measured for menu state too, and much larger than expected.

**Still viable, and the next design:** a *delta* oracle that never compares across boots. Within one run:

1. At a screen, dump twice with idle frames between and no input. Bytes that change are frame noise.
2. Press, dump again. Bytes that changed but were *not* in the noise set are state.
3. Wait for that set to change instead of waiting a fixed number of frames.

This needs no cross-boot stability because every comparison happens inside one boot, against memory that has already settled. The pieces are worth keeping: the capture harness and the big-int diff engine both carry over unchanged.

**Also worth pricing:** screenshots would be a far better oracle than any of this, since the screen *is* the ground truth. `jusemu.py screenshot` currently fails with "melonDS window not found (permissions?)" — macOS screen-recording permission for the terminal or melonDS would make menu verification close to trivial. That's a one-time grant a human has to click, so it's worth asking before building the delta oracle.

## Reproducing

```bash
cd scripts/emu
python3 capture_boot_trace.py --runs 3     # ~6 min, discards desynced runs
python3 find_screen_id.py compare
```

Dumps land in `/tmp/jus_screens/` at 4MB each, 11 per run.

## Correction (same day): the runs did not all reach a battle

Everything above assumes all three runs reached a real battle and were kept. That's wrong — a screenshot is what caught it.

Once window capture was working, the emulator left over from the third run was photographed sitting on デッキセレクト — the deck management screen, with the options submenu open (編集 / 名前へんこう / コピー / いれかえ / けす / とじる). Not a battle. Yet the same check that passed during the run still reports success on that screen:

    in_battle() says: 0x02291574
      slot0 hp=10240 (160.0) idx=0

Plausible HP, plausible chr_b index, and completely wrong. The cause isn't bad luck — it's structural: **the deck-select screen holds deck rosters, and a deck roster is HP values plus chr_b indices in 0x50-byte slots — exactly the signature `find_battle_structs.py` looks for.** The scan can't tell a deck roster from a battle character array. That also explains the historical stale-copy false positives that scored 4/4.

What this does to the results above:

- **The per-step tables are confounded.** If runs ended on different screens, the step labels don't describe the same screens across runs. Both the "stable bytes that differ" table and the between-run table mix real cross-boot variation with plain desync. They can't separate the two.
- **The title-screen number survives.** `00_title` is captured after the boot wait and before any button press, so desync can't reach it. There, run 0 and run 1 differ by 973,944 bytes while runs 1 and 2 differ by 46,573. Cross-boot RAM really isn't portable, and the amount of drift varies a lot between boots.
- **The headline claim was overstated.** "A cross-boot golden trace cannot work" is stronger than this evidence supports. The honest version: cross-boot RAM fingerprints are unreliable, by a large and inconsistent margin, and this particular experiment can't measure how unreliable because its later steps are invalid.

The conclusion doesn't need rescuing, because the replacement is better anyway. Fingerprinting the *screen* works: two captures of one static screen differ by 0.588, and a single button press moves the fingerprint by 10.266 — a 17.5x separation. See `screen_fp.py`. Pixels are also the only oracle here that can catch the in_battle() false positive, since by definition RAM signatures are exactly what it fools.

**Wider lesson for this project.** A signature scan validated only against RAM can be structurally fooled by a screen that legitimately contains the same kind of data. The existing advice — "verify functionally: land a known attack and confirm HP dips" — is right, and the ability-bitset work followed it, which is why that result stands. This run didn't, and got a false positive within the hour.
