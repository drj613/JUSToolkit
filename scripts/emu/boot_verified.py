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

# Items and gimmicks are both ON by default and both inject randomness into a fight,
# so every measurement run turns them off.
#
# THE OLD PIXEL CHECK PASSED WITH GIMMICKS STILL ON, and it did so on every run since
# it was written. The owner caught it: the stage in these matches spawns projectiles
# as its gimmick, which damage and knock down, and that is where the unexplained
# damage in a なにもしない training match was coming from.
#
# The mechanism is the two-tap rule. A tap on an UNFOCUSED pill only moves focus to
# it; a tap on a focused one toggles it. アイテム starts focused, so the first tap
# turned items off and the second merely focused ギミック. The check then compared the
# toggle row against a stored reference that had been captured in that same
# half-done state, so it agreed with itself. Two whole sessions of measurements ran
# with the stage gimmick live.
#
# The lesson is not "the tolerance was too loose". It is that a reference captured
# from the state you are trying to verify cannot verify it -- and that a rendered
# label was the wrong representation to read. The pill's ON/OFF glyphs are 2 versus
# 3 characters inside a rounded box whose focus border pulses, and every pixel
# statistic tried on it (near-white count, dark-ink count, glyph-column count)
# overlapped between the two states.
#
# So read the flags instead. Each toggle is a byte, found by alternating the toggle
# five times and diffing all of main RAM for a byte that followed the pattern -- one
# clean boolean out of 4MB, sitting 7 and 8 bytes past the known deck_active_slot at
# 0x020AFEB4. Confirmed in both directions: with the screen reading ON/ON the bytes
# read 1/1, and toggling either one moves only its own byte.
#
# Retrying taps IS safe here, unlike the confirm buttons: a toggle is reversible and
# the flag is checked after every single tap, so overshooting is recoverable rather
# than a one-way trip to an unknown screen.
TAP_ITEMS = (73, 51)
TAP_GIMMICK = (165, 51)
RULE_FLAGS = [("items", 0x020AFEBB, TAP_ITEMS),
              ("gimmick", 0x020AFEBC, TAP_GIMMICK)]

# The THIRD rule boolean. atlas decoded a three-bit rule mask, so rules_off() was
# clearing two of three and saying nothing about the third (jus-ovv).
#
# IT HAS NO TAP TARGET, and that is a finding rather than a missing constant. The
# チームせん pill is the third in the same row, and no tap moves it: swept x
# 200-250 and y 44-58, twelve positions, with items (73,51) and gimmick (165,51)
# toggling correctly in the same states as a positive control. It is drawn greyed
# and the match is COM 1人, so team battle is presumably unavailable in a 1v1 and
# the pill is inert rather than mislocated.
#
# So this is VERIFIED, not cleared. It reads 0 in every state measured; if it ever
# reads 1 the run stops, because we have no way to turn it off and a team-battle
# match is not the thing any measurement here assumes.
TEAM_FLAG = 0x020AFEBD


def team_battle_is_off():
    """Check the third rule boolean. We can read it; we cannot set it."""
    return rule_flag(TEAM_FLAG) == 0


def rule_flag(addr):
    """Read one rule toggle. 1 is ON, 0 is OFF."""
    out = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "peek",
                          hex(addr), "1"], capture_output=True, text=True, cwd=HERE)
    if out.returncode != 0:
        raise RuntimeError("peek %s failed: %s%s" % (hex(addr), out.stdout, out.stderr))
    return json.loads(out.stdout)["result"]["value"]


def rules_off(max_taps=6):
    """Tap until items and gimmicks both read OFF in RAM. Returns (taps, flags).

    The flag is re-read after every tap, which is what makes the first tap on an
    unfocused pill (focus only, no toggle) harmless rather than fatal.
    """
    taps = 0
    for name, addr, target in RULE_FLAGS:
        for _ in range(max_taps):
            if rule_flag(addr) == 0:
                break
            nav.tap(target[0], target[1], settle=140)
            taps += 1
        else:
            raise RuntimeError(
                "%s is still ON after %d taps at %s (flag 0x%08X). A tap on an "
                "unfocused pill only moves focus, so two taps per toggle is normal; "
                "six means the taps are not landing."
                % (name, max_taps, target, addr))
    if not team_battle_is_off():
        raise RuntimeError(
            "team battle (0x%08X) reads %d, and there is no way to clear it from "
            "here -- the チームせん pill does not respond to taps (swept 12 "
            "positions with items and gimmick toggling as controls). Every "
            "measurement in this harness assumes a 1v1. Restart from a rule "
            "screen where it is off." % (TEAM_FLAG, rule_flag(TEAM_FLAG)))
    return taps, [rule_flag(a) for _, a, _ in RULE_FLAGS] + [rule_flag(TEAM_FLAG)]


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
            taps, flags = rules_off()
            print("  items+gimmicks OFF after %d taps (flags %s)" % (taps, flags))
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
