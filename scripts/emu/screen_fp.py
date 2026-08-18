#!/usr/bin/env python3
"""Fingerprint the DS screen from the emulator's own framebuffer.

WHY PIXELS AND NOT RAM. The first attempt fingerprinted main RAM and failed for a
measurable reason: two boots sitting on the same screen differ by up to 1.7M bytes,
and ~974k bytes differ at the title screen before any input
(docs/research/Menu-Nav-Oracle-Attempt-1.md). Rendered screens, by contrast, look
the same every boot.

Pixels also catch a failure RAM cannot. boot_to_battle.py's in_battle() reports a
battle on the deck-SELECT screen, because a deck roster is HP values plus chr_b
indices in 0x50-byte slots -- exactly the signature it searches for. A screenshot
tells them apart instantly.

WHERE THE PIXELS COME FROM. `jusemu.py screendump`, which reaches into the core via
GPU.GetFramebuffers (see lua/libs/LuaScreendump.cpp in the melonDS fork). Not
macOS window capture, which needed the window frontmost and therefore stole the
user's keyboard focus -- and which silently returned a STALE cached image whenever
the window was occluded. That produced byte-identical captures while the bridge
advanced 130 frames in 2 seconds and 13,520 bytes of RAM changed, i.e. a confident
"the screen never changed" about a game that was plainly responding.

THE LESSON, kept because it cost real time: an unchanging screenshot is never by
itself evidence that the game did not respond. Confirm liveness from the bridge
(framecount, or a RAM diff) before believing any negative.

WHICH PART OF THE SCREEN. The bottom screen only. Menus and cursors live there;
decorative animation lives on the top screen. Fingerprinting the whole window on
the title screen drifted by up to 63 between consecutive captures -- more than a
real menu transition moves a static screen -- and coarsening the grid did not help
(16x20, 8x10, 4x5 and 2x3 all showed 63-67, because the animation is a global
brightness change, not fine detail).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GRID_W, GRID_H = 16, 20
# screendump writes a 256x384 PPM: top screen above bottom screen, physical DS
# layout. The bottom screen is the lower half.
BOTTOM_CROP = "256x192+0+192"
SAME_SCREEN_MAX = 6.0


def capture(path):
    """Grab the framebuffer. Headless: no window, no focus, no compositor."""
    if not path.endswith(".ppm"):
        path = os.path.splitext(path)[0] + ".ppm"
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"),
                        "screendump", path], capture_output=True, text=True,
                       cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("screendump failed: %s%s" % (r.stdout, r.stderr))
    return path


def fingerprint(png):
    """Downscaled grayscale bytes of the bottom screen, GRID_W*GRID_H of them."""
    r = subprocess.run(["magick", png, "-crop", BOTTOM_CROP, "+repage",
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
    # A blank capture is the dangerous failure, not a loud one: two blank images
    # compare equal, so a broken capture reads as "no change". Real game screens
    # have contrast. (Boot screens can legitimately be near-white, so this is a
    # low bar deliberately.)
    if max(fp) - min(fp) < 4:
        raise RuntimeError("%s looks blank (pixel range %d-%d) -- do not read "
                           "this as 'no change'" % (png, min(fp), max(fp)))
    return fp


def grab(tmp="/tmp/jus_fp.ppm"):
    return fingerprint(capture(tmp))


def distance(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / float(len(a))


def same(a, b, threshold=SAME_SCREEN_MAX):
    return distance(a, b) <= threshold


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "dist":
        print("%.3f" % distance(fingerprint(sys.argv[2]),
                                fingerprint(sys.argv[3])))
        return 0
    fp = grab()
    print(json.dumps({"grid": [GRID_W, GRID_H], "range": [min(fp), max(fp)],
                      "fp": list(fp)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
