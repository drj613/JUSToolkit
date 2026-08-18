#!/usr/bin/env python3
"""Fingerprint the emulator screen from pixels, so menu steps can be verified.

WHY PIXELS AND NOT RAM. The first attempt built fingerprints from main RAM and
failed for a measurable reason: two boots sitting on the *same* screen differ by
up to 1.7M bytes, and ~974k bytes differ at the title screen before any input
(see docs/research/Menu-Nav-Oracle-Attempt-1.md). Absolute RAM values are not
portable across boots. The rendered screen is -- a menu looks the same every
time -- so the screen is the better oracle, and it is also the actual ground
truth a human would check.

It also catches a failure RAM cannot. `boot_to_battle.py`'s in_battle() reports
success on the deck-SELECT screen, because that screen holds deck rosters with HP
values and chr_b indices and therefore matches the battle-array signature exactly.
Pixels tell those apart immediately.

HOW. Capture the melonDS window (see jusemu.py's CoreGraphics route), crop off the
title bar -- it contains a live FPS counter -- then downscale hard to a small
grayscale grid. Downscaling is what makes this robust: it averages away cursor
blink, animated backgrounds and 1px jitter while keeping layout and brightness.
Compare two fingerprints by mean absolute difference per cell, 0-255.

Thresholds are empirical, so measure rather than guess:
  python3 screen_fp.py selftest      # same screen twice, then after a press
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GRID_W, GRID_H = 16, 20
# The window is 756x942 with a ~28px title bar carrying "[60/60] melonDS 1.1".
# The FPS digits change constantly, so crop the bar away or every comparison
# picks up noise that has nothing to do with the game.
CROP = "756x914+0+28"
SAME_SCREEN_MAX = 6.0     # validated by selftest; see docstring


def capture(path):
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"),
                        "screenshot", path], capture_output=True, text=True,
                       cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("screenshot failed: %s%s" % (r.stdout, r.stderr))
    return path


def fingerprint(png):
    """Downscaled grayscale bytes, GRID_W*GRID_H of them."""
    r = subprocess.run(["magick", png, "-crop", CROP, "+repage",
                        "-colorspace", "Gray",
                        "-resize", "%dx%d!" % (GRID_W, GRID_H),
                        "-depth", "8", "gray:-"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("magick failed: %s" % r.stderr.decode()[:300])
    fp = r.stdout
    if len(fp) != GRID_W * GRID_H:
        raise RuntimeError("expected %d bytes, got %d"
                           % (GRID_W * GRID_H, len(fp)))
    return fp


def grab(tmp="/tmp/jus_fp.png"):
    capture(tmp)
    return fingerprint(tmp)


def distance(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / float(len(a))


def same(a, b, threshold=SAME_SCREEN_MAX):
    return distance(a, b) <= threshold


def selftest():
    """Measure the two distances that decide whether any of this works."""
    print("capturing the current screen twice (no input between) ...")
    a = grab("/tmp/jus_fp_a.png")
    b = grab("/tmp/jus_fp_b.png")
    d_same = distance(a, b)
    print("  same screen, two captures: %.3f" % d_same)

    print("pressing B (should close a submenu / go back) ...")
    plan = {"name": "fp_probe",
            "segments": [{"from": 0, "to": 0, "buttons": ["B"]}],
            "tail_frames": 90}
    with open("/tmp/jus_fp_plan.json", "w") as f:
        json.dump(plan, f)
    subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "run",
                    "/tmp/jus_fp_plan.json"], capture_output=True, cwd=HERE)
    c = grab("/tmp/jus_fp_c.png")
    d_diff = distance(a, c)
    print("  after one B press:        %.3f" % d_diff)

    print()
    if d_same > SAME_SCREEN_MAX:
        print("FAIL: two captures of one static screen differ by %.3f, above the "
              "%.1f threshold. Something is animating a lot, or the capture is "
              "unstable. Raise the threshold only after looking at the images."
              % (d_same, SAME_SCREEN_MAX))
        return 1
    if d_diff <= d_same:
        print("FAIL: a B press moved the fingerprint by %.3f, no more than the "
              "%.3f noise floor. Either the press did nothing (was it swallowed "
              "by a menu?) or this crop cannot see the change. Do NOT build "
              "navigation on this until the two separate." % (d_diff, d_same))
        return 1
    print("OK: noise floor %.3f, real change %.3f -- separated by %.1fx."
          % (d_same, d_diff, d_diff / max(d_same, 0.001)))
    print("So 'has the screen changed yet' is answerable from pixels.")
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        return selftest()
    if len(sys.argv) > 2 and sys.argv[1] == "dist":
        return print("%.3f" % distance(fingerprint(sys.argv[2]),
                                      fingerprint(sys.argv[3])))
    fp = grab()
    print(json.dumps({"grid": [GRID_W, GRID_H], "fp": list(fp)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
