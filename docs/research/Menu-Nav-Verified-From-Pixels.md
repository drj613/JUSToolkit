# Menu navigation, attempt 2: verified from pixels, 3/3 cold boots

**Result:** `boot_verified.py` walks ROM boot to a training battle, confirming every screen before moving on, and lands in a verified battle **3 of 3 cold boots** with items and gimmicks switched off. It replaces `boot_to_battle.py`, which fired buttons on fixed timers, desynced 4+ times in a single session, and whose only check gave false positives. Measured 2026-08-18.

Attempt 1 tried to build the oracle from main RAM and failed (`Menu-Nav-Oracle-Attempt-1.md`). This one reads the screen.

## Where the pixels come from

Not macOS window capture. That path had two independent faults, both producing the same symptom — fingerprints that never change — which is why pulling them apart took a while:

1. **Wrong window.** `jusemu.py` matched "melonDS" against window *titles*, and the terminal was titled "Hand off melonDS runtime harness for JUS". It matched, it was larger, so it won. The harness fingerprinted a terminal and reported confident nonsense, including a fictitious "wobble 0.00" on a screen that was visibly animating.
2. **Stale frames.** `screencapture -l` on an *occluded* window returns a cached backing store. While melonDS sat behind the terminal, every capture came back byte-identical — no button, hold, or tap appeared to do anything — yet the bridge advanced 130 frames in 2 seconds and 13,520 bytes of main RAM changed. The game was responding the whole time.

The fix reads the framebuffer from inside the emulator: `screen.dump(path)`, added to the melonDS-lua fork (`patches/screendump.patch`), writing a 256x384 binary PPM straight from `GPU.GetFramebuffers` — top screen above bottom, physical DS layout. No window, no compositor, no focus stealing, and it works with the window buried.

**The lesson worth keeping:** an unchanging screenshot is never by itself evidence that the game did not respond. Confirm liveness from the bridge — framecount, or a RAM diff — before believing any negative.

## What to fingerprint

The **bottom screen only**, downscaled to a 16x20 grayscale grid, compared by mean absolute difference.

Menus and cursors live on the bottom screen; decorative animation lives on the top. Fingerprinting the whole window on the title screen drifted by up to **63** between consecutive captures — more than a real menu transition moves a static screen (10.266). Coarsening did not help: 16x20, 8x10, 4x5, and 2x3 all showed 63–67, because the animation is a global brightness change, not fine detail.

Screens are recognised against a small library (`screens.json`) holding several samples per screen to cover its animation cycle, plus a tolerance derived from how much that screen actually moves:

| screen | wobble | tolerance |
|---|---|---|
| `top_menu` | 11.86 | 16.01 |
| `arena_menu` | 4.67 | 6.30 |
| `deck_select` | 3.86 | 5.21 |
| `stage_select` | 3.99 | 5.38 |
| `rule_select` | 1.41 | 4.00 |
| `battle` | 3.66 | 4.94 |

Recognition, not change-detection, is the right framing: some screens animate more than a transition changes, so no single global "did it change" threshold exists.

## The route was wrong, in two ways

Both were found by looking at the screen, not by reasoning about it.

**The cursor does not start where the old comments assumed.** The top menu is a **4x2 icon grid**, and the cursor was sitting on デッキメイク. The old logic — "top menu starts on Jギャラクシー, so one RIGHT reaches Jアリーナ" — walked into the deck editor instead. That is exactly where the mysterious 編集 / 名前へんこう / コピー / いれかえ / けす / とじる submenu came from.

**The grid wraps**, so saturating to a corner also fails: UP x3 then LEFT x5 landed on オプション (bottom-right), not the top-left.

The fix stops walking cursors and **taps absolute touchscreen coordinates**, which the plan schema already supported (`touch: {x, y}`). A tap names its target and does not care where the cursor was. That also makes a long deck-editor flow plausible.

Verified route, tap coordinates in DS bottom-screen pixels:

| from | action | to |
|---|---|---|
| title | START, repeated until recognised | `top_menu` |
| `top_menu` | tap (93, 49) Jアリーナ, then A | `arena_menu` |
| `arena_menu` | tap (180, 142) トレーニング, then A | `deck_select` |
| `deck_select` | A | `stage_select` |
| `stage_select` | A | `rule_select` |
| `rule_select` | turn items+gimmicks off, then START | `battle` |

The START count is deliberately not fixed: the title screen cycles into an attract movie and START skips whatever is playing, so the number of presses needed depends on where in that cycle you arrive. Runs took 4, 5, and 6.

## Verify the SOURCE screen, not just the destination

This is the change that actually fixed reliability. Each step waits until the *source* screen is recognised, waits a further 90 frames, presses once, then waits for the destination.

Pressing during a transition is the original desync: the input gets swallowed and every later step aims at the wrong screen. Confirming the source means the press always lands on a settled screen.

**A design that made things worse, recorded because the reasoning was tempting.** One version tried *candidate* actions per step and fell back when one did not land — motivated by a real observation: the stage list's hint bar shows STA/SEL/Y/B with no A at all, yet an A press advanced it once and then stalled for 1200 frames on a later run. Reliability dropped from 2/3 to **0/3**. A failed attempt is not side-effect-free: the speculative START pushed the game to an unknown screen, and the fallback A could not recover. With stateful input, waiting beats guessing.

The exception is a *toggle*, which is reversible and can be checked after every single tap — see below. Guess-and-check is fine when the guess is cheap to undo.

## Items and gimmicks off

Both default to ON and both add randomness to a fight, so runs now switch them off and confirm it. Verifying a two-word change needed a targeted check, because the two obvious approaches both fail:

- **Whole bottom screen:** ON versus both-OFF differ by **0.67**, against a tolerance of 4.00. Indistinguishable — a check built on this would have passed happily with items still ON.
- **Per-pill crops:** the focus highlight moves the crop **more** than the value does (48.1 versus 21.5), so the crop tracks which control is selected, not what it says.

What works is the whole toggle row at 64x8, matched against a reference for one specific target state — both OFF with ギミック focused — wobble 2.88, tolerance 4.31.

Tap semantics, learned by looking: **a tap SELECTS an unfocused control and TOGGLES a focused one.** So the number of taps needed is not fixed, and the loop taps and re-checks until the target state matches. All three runs got there in 2 taps.

## The final check is convergent on purpose

Reaching "battle" requires **both** that the pixels match the battle screen **and** that the RAM signature scan finds a character array.

Each catches what the other misses. Pixels catch the false positive that RAM cannot: `in_battle()` reports a battle on the deck-*select* screen, because a deck roster is HP values plus chr_b indices in 0x50-byte slots — precisely the signature it scans for. It returned `0x02291574` with hp 10240 (160.0) and chr_b index 0 while a deck menu was plainly on screen. RAM catches the opposite case: a screen that looks like a battle but has not finished loading.

## Results

3/3 cold boots reached a verified battle. Per-screen match distances ran 0.00–1.29 against tolerances of 4.00–6.30, except `top_menu` at 10.65–12.53 against 16.01 (it carries an animated character strip). Items and gimmicks OFF after 2 taps every run, row distance 1.95–2.47.

## Also worth knowing

**Rapid repeated savestate loads can hang melonDS.** It froze twice, both times right after "Resetting JIT block cache" in the emulator log. The framecount stops advancing, the game stops responding, and the bridge times out with an INDETERMINATE error. A 36-load sweep earlier in the session was fine, so it is intermittent. Any script doing many loads should check that the framecount is still advancing and restart the emulator if not.

**A blank frame is not an error.** Early in ROM boot the DS screen is genuinely black, and a guard that treated a no-contrast capture as a bug failed 2 of 3 runs on legitimate black boot frames. Blank now means "not yet" while polling, and is only an error when a specific screen was expected.

## Reproducing

```bash
cd scripts/emu
python3 boot_verified.py --runs 3        # cold boot each run, saves savestates
python3 screenlib.py list                # the learned screen library
python3 learn_walk.py                    # re-learn screens if the route changes
```
