#!/usr/bin/env python3
"""Menu navigation that waits for the screen instead of trusting a timer.

THE PROBLEM. boot_to_battle.py presses a button and waits a fixed number of
frames. Nothing checks that the press did anything, so a press that lands while a
screen is still animating is simply lost, and every later step is then aimed at
the wrong screen. It desynced 4+ times in one session, and the symptom is
confusing rather than loud -- you end up somewhere plausible, like story mode or a
deck management submenu, with no error.

THE FIX. After each press, poll the screen until it changes, then until it stops
changing. Both halves matter: waiting only for "changed" can return mid-animation
and the next press lands during a transition, which is the original bug wearing a
different hat.

WHY PIXELS. RAM cannot do this job. Two boots on the same screen differ by up to
1.7M bytes of main RAM, and ~974k bytes differ at the title screen before any
input. Worse, RAM signatures can be structurally fooled: the deck-select screen
holds deck rosters (HP plus chr_b indices in 0x50-byte slots), so
find_battle_structs.py reports a battle character array there. A screenshot tells
them apart at a glance. See docs/research/Menu-Nav-Oracle-Attempt-1.md.

A press that legitimately changes nothing (a DOWN at the bottom of a list) is
indistinguishable from a swallowed press. That is not a flaw in the oracle, it is
genuinely ambiguous, so such steps must be declared with expect_change=False
rather than silently tolerated.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screen_fp as FP  # noqa: E402

NOISE = 2.0          # above the 0.588 measured on a static screen, well below
CHANGED = 5.0        # a real press measured 10.266
POLL_FRAMES = 20
MAX_WAIT_FRAMES = 900
SHOT_DIR = "/tmp/jus_nav"


def advance(frames, buttons=None):
    # A plan must carry at least one segment, so a pure wait is a segment with
    # no buttons rather than an empty list.
    plan = {"name": "nav_adv",
            "segments": [{"from": 0, "to": 0, "buttons": buttons or []}],
            "tail_frames": frames}
    path = "/tmp/jus_nav_plan.json"
    with open(path, "w") as f:
        json.dump(plan, f)
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "run",
                        path], capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("advance failed: %s%s" % (r.stdout, r.stderr))


# --- touchscreen ------------------------------------------------------------
# Tapping beats walking a cursor. The top menu is a 4x2 grid that WRAPS, so
# "press UP three times and LEFT five times to reach the corner" does not work:
# tried it, and the cursor ended on オプション (bottom-right) instead of
# Jギャラクシー. With wrapping there is no way to reach a known position by
# relative moves without already knowing where you started -- which is the whole
# problem. A tap names an absolute target, so it does not care.
#
# This is also what makes a 20-step deck-editor flow plausible at all.
#
# Window geometry: 756x942 window, a ~28px title bar, then two 256x192 DS screens
# scaled 600/256 = 2.34x, stacked with a small gap. Measured from captures:
# content x 78..678, top screen y 30..480, bottom screen y 490..940.
BOTTOM_X0, BOTTOM_Y0 = 78, 490
BOTTOM_W, BOTTOM_H = 600, 450
DS_W, DS_H = 256, 192


def window_to_ds(win_x, win_y):
    """Map a pixel in the captured window to bottom-screen DS touch coords."""
    ds_x = int(round((win_x - BOTTOM_X0) * DS_W / float(BOTTOM_W)))
    ds_y = int(round((win_y - BOTTOM_Y0) * DS_H / float(BOTTOM_H)))
    if not (0 <= ds_x < DS_W and 0 <= ds_y < DS_H):
        raise ValueError("window (%d,%d) maps outside the bottom screen -> "
                         "(%d,%d)" % (win_x, win_y, ds_x, ds_y))
    return ds_x, ds_y


def tap(ds_x, ds_y, hold=4, settle=90):
    """Touch the bottom screen at DS coordinates and let the game react."""
    plan = {"name": "nav_tap",
            "segments": [{"from": 0, "to": hold - 1,
                          "touch": {"x": int(ds_x), "y": int(ds_y)}}],
            "tail_frames": settle}
    path = "/tmp/jus_nav_tap.json"
    with open(path, "w") as f:
        json.dump(plan, f)
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "run",
                        path], capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("tap failed: %s%s" % (r.stdout, r.stderr))


def tap_window(win_x, win_y, **kw):
    x, y = window_to_ds(win_x, win_y)
    tap(x, y, **kw)
    return x, y


def shot(tag):
    os.makedirs(SHOT_DIR, exist_ok=True)
    p = os.path.join(SHOT_DIR, "%s.ppm" % tag)
    FP.capture(p)
    return p, FP.fingerprint(p)


def wait_stable(tag="stable", max_frames=MAX_WAIT_FRAMES):
    """Advance until two consecutive captures agree. Returns the fingerprint."""
    prev = None
    waited = 0
    while waited < max_frames:
        _, fp = shot(tag)
        if prev is not None and FP.distance(fp, prev) <= NOISE:
            return fp
        prev = fp
        advance(POLL_FRAMES)
        waited += POLL_FRAMES
    raise RuntimeError("screen never settled after %d frames (still animating? "
                       "see %s/%s.png)" % (max_frames, SHOT_DIR, tag))


def press_and_wait(buttons, tag, expect_change=True,
                   max_frames=MAX_WAIT_FRAMES):
    """One 1-frame press, then wait for the screen to change and settle.

    A 1-frame press is exactly one menu step; a 4-frame hold triggers auto-repeat
    and moves two, which is why this never holds.
    """
    before = wait_stable(tag + "_before")
    advance(1, buttons)
    waited = 0
    while waited < max_frames:
        advance(POLL_FRAMES)
        waited += POLL_FRAMES
        _, fp = shot(tag + "_after")
        if FP.distance(fp, before) >= CHANGED:
            after = wait_stable(tag + "_settled")
            return after, FP.distance(after, before)
    if expect_change:
        raise RuntimeError(
            "%s: pressed %s and the screen never changed in %d frames "
            "(distance stayed under %.1f). The press was probably swallowed -- "
            "an open in-battle menu eats all bridge input and reports ok. "
            "See %s/%s_after.ppm"
            % (tag, "+".join(buttons), max_frames, CHANGED, SHOT_DIR, tag))
    return before, 0.0


def main():
    """Smoke test: press B and confirm the machinery reports a real change."""
    print("waiting for the screen to settle ...")
    fp = wait_stable("smoke")
    print("  settled")
    print("pressing B ...")
    try:
        _, d = press_and_wait(["B"], "smoke_b")
        print("  screen changed by %.3f -- press_and_wait works" % d)
    except RuntimeError as exc:
        print("  %s" % exc)
        print("\nIf B genuinely does nothing on this screen that is expected; "
              "rerun somewhere B goes back.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
