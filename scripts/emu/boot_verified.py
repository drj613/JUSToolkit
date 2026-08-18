#!/usr/bin/env python3
"""Boot into a training battle, verifying every screen before moving on.

Replaces boot_to_battle.py's blind press-and-wait-N-frames. That version desynced
4+ times in one session and its only check was at the very end -- a check that
itself false-positives, because in_battle() finds a "battle character array" on the
deck-SELECT screen (a deck roster is HP values plus chr_b indices in 0x50-byte
slots, exactly the signature it scans for).

Three changes make this reliable:

1. VERIFY EACH STEP from the emulator's framebuffer, so a wrong screen stops the
   run instead of silently shifting every later step.
2. TAP, DON'T WALK. The top menu is a 4x2 grid that WRAPS and whose cursor does
   not start where the old comments assumed -- it was found on デッキメイク, so
   "one RIGHT to reach Jアリーナ" walked into the deck editor. Wrapping also kills
   the usual trick of saturating to a corner: UP x3 + LEFT x5 landed on
   オプション. Absolute taps sidestep cursor state entirely.
3. WAIT FOR THE TARGET, not a fixed number of frames.

The final battle check is deliberately CONVERGENT: the pixels must say "battle"
AND the RAM signature scan must find a character array. Those two disagree in
exactly the cases that have burned this project -- pixels catch the deck-roster
false positive, and RAM catches a battle-looking screen that has not finished
loading. Agreement across two representations is worth much more than either alone.

Usage:
    python3 boot_verified.py [--slot NAME] [--no-launch] [--runs N]
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import json             # noqa: E402
import nav              # noqa: E402
import screen_fp as FP  # noqa: E402
import screenlib as SL  # noqa: E402
import boot_to_battle as B  # noqa: E402

SETTLE = 240
MAX_START_PRESSES = 8

# DS bottom-screen coordinates (256x192).
TAP_ARENA = (93, 49)      # Jアリーナ, row 1 col 2 of the top-menu grid
TAP_TRAINING = (180, 142)  # トレーニング, 4th row of the J Arena menu

# (from_screen, actions, to_screen). Every step VERIFIES THE SOURCE SCREEN first,
# then presses once, then waits for the destination.
#
# Checking the source is the part that matters, and it took a wrong turn to see
# why. Pressing during a transition is the original desync: the input is eaten and
# every later step is aimed at the wrong screen. Waiting until the source screen is
# recognised means the press always lands on a settled screen.
#
# An earlier version instead tried CANDIDATE actions and fell back when one did not
# land. That made things strictly worse -- 0/3 runs, down from 2/3 -- because a
# failed attempt is NOT side-effect-free. The speculative START pushed the game to
# an unknown screen, and the fallback A could not get back. With stateful input,
# guessing costs more than waiting.
STEPS = [
    ("top_menu",     [("tap",) + TAP_ARENA, ("btn", ["A"])],    "arena_menu"),
    ("arena_menu",   [("tap",) + TAP_TRAINING, ("btn", ["A"])], "deck_select"),
    ("deck_select",  [("btn", ["A"])],                          "stage_select"),
    ("stage_select", [("btn", ["A"])],                          "rule_select"),
    ("rule_select",  [("btn", ["START"])],                      "battle"),
]

# Items and gimmicks are ON by default and both inject randomness into a fight, so
# every measurement run turns them off. The target state is specific: both OFF with
# ギミック focused, captured in rules_target.json.
#
# Why a whole-row reference instead of reading each toggle: at 16x20 over the whole
# bottom screen, items/gimmicks ON versus both OFF differ by just 0.67 against a
# tolerance of 4.00 -- indistinguishable, so a naive check would pass with items
# still ON. Cropping to individual pills does not work either, because the focus
# highlight moves the crop MORE than the value does (48.1 versus 21.5). The toggle
# row as a whole, at higher resolution, separates cleanly.
#
# Retrying taps IS safe here, unlike the confirm buttons: a toggle is reversible and
# the state is checked after every single tap, so overshooting is recoverable rather
# than a one-way trip to an unknown screen.
TAP_ITEMS = (73, 51)
TAP_GIMMICK = (165, 51)
RULES_TARGET = os.path.join(HERE, "rules_target.json")


def _rules_cfg():
    with open(RULES_TARGET) as f:
        return json.load(f)


def rules_distance(cfg):
    p, _ = nav.shot("rules_row")
    fp = FP.fingerprint_crop(p, cfg["crop"], cfg["grid"][0], cfg["grid"][1])
    return min(FP.distance(fp, s) for s in cfg["samples"])


def rules_off(max_rounds=5):
    """Tap until items and gimmicks are both OFF. Returns the number of taps."""
    cfg = _rules_cfg()
    d = rules_distance(cfg)
    if d <= cfg["tol"]:
        return 0, d
    taps = 0
    for _ in range(max_rounds):
        for target in (TAP_ITEMS, TAP_GIMMICK):
            nav.tap(target[0], target[1], settle=90)
            taps += 1
            d = rules_distance(cfg)
            if d <= cfg["tol"]:
                return taps, d
    raise RuntimeError(
        "could not get items and gimmicks both OFF after %d taps (nearest %.2f, "
        "tol %.2f). A tap SELECTS an unfocused control and TOGGLES a focused one, "
        "so the count needed varies; see /tmp/jus_nav/rules_row.ppm"
        % (taps, d, cfg["tol"]))


# Extra frames after the source screen is recognised, so an entry animation that
# the fingerprint cannot see has finished before we press.
PRE_PRESS_SETTLE = 90

def act(action):
    if action[0] == "tap":
        nav.tap(action[1], action[2], settle=SETTLE)
    else:
        nav.advance(1, action[1])
        nav.advance(SETTLE)


def reach_top_menu():
    """Press START until the top menu appears.

    The count is not fixed: the title screen cycles into an attract movie, and
    START skips whatever is playing, so how many presses are needed depends on
    where in that cycle you arrive.
    """
    for i in range(MAX_START_PRESSES):
        nav.advance(1, ["START"])
        nav.advance(150)
        name, d = SL.identify()
        if name == "top_menu":
            return i + 1, d
    raise RuntimeError("never reached top_menu after %d START presses; last "
                       "screen was %s (%.1f)" % (MAX_START_PRESSES, name, d))


def boot(slot):
    n, d = reach_top_menu()
    print("  top_menu       after %d START presses (distance %.2f)" % (n, d))
    for src, actions, dst in STEPS:
        ds = SL.wait_for(src)
        nav.advance(PRE_PRESS_SETTLE)
        if src == "rule_select":
            taps, rd = rules_off()
            print("  items+gimmicks OFF after %d taps (row distance %.2f)"
                  % (taps, rd))
        for a in actions:
            act(a)
        d = SL.wait_for(dst, max_frames=1500)
        print("  %-14s -> %-14s verified (src %.2f, dst %.2f)"
              % (src, dst, ds, d))

    # Convergent check: pixels AND the RAM signature must agree.
    base = B.in_battle()
    if not base:
        raise RuntimeError(
            "pixels say 'battle' but the RAM signature scan found no character "
            "array. Do not trust either alone -- screenshot and investigate.")
    hp = B.peek(base, 2)
    idx = B.peek(base + 0x29, 1)
    print("  RAM agrees: array 0x%08X, active hp %d (%.1f), chr_b idx %d"
          % (base, hp, hp / 64.0, idx))
    out = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"),
                          "state", "save", slot], capture_output=True, text=True,
                         cwd=HERE)
    if out.returncode != 0:
        raise RuntimeError("savestate failed: %s%s" % (out.stdout, out.stderr))
    print("  saved savestate %r" % slot)
    return base


def main():
    sys.stdout.reconfigure(line_buffering=True)
    slot = "verified_training"
    launch = True
    runs = 1
    a = sys.argv[1:]
    for i, x in enumerate(a):
        if x == "--slot":
            slot = a[i + 1]
        elif x == "--no-launch":
            launch = False
        elif x == "--runs":
            runs = int(a[i + 1])

    ok = 0
    for r in range(runs):
        print("run %d:" % r)
        if launch:
            subprocess.run(["bash", os.path.join(HERE, "launch_emu.sh")],
                           check=True, capture_output=True)
        try:
            boot("%s%s" % (slot, "" if runs == 1 else "_%d" % r))
            ok += 1
            print("  OK")
        except Exception as exc:
            print("  FAILED: %s" % exc)
    print("\n%d/%d runs reached a verified battle." % (ok, runs))
    return 0 if ok == runs else 1


if __name__ == "__main__":
    sys.exit(main())
