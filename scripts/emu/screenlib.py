#!/usr/bin/env python3
"""Recognise which menu screen the game is on, from pixels.

WHY NOT "WAIT UNTIL THE SCREEN STOPS CHANGING". That was the first design and it
does not survive contact with this game. Measured on the title screen, bottom-DS-
screen crop, ten samples 30 frames apart with no input: consecutive fingerprints
differ by 20-32 and up to 35.1 pairwise. The screen never settles, because it is
animated. Meanwhile a real menu transition moved a static screen by only 10.266.
So "changed" and "animating" are not separable by any single global threshold --
some screens animate more than a transition changes.

(An earlier measurement of 0.00 noise on this same screen was a trap: the samples
all happened to land in a dark phase of the animation. Two consecutive identical
captures do not prove a screen is static.)

WHAT WORKS. Treat it as recognition, not change detection. For each screen, store
several fingerprints spanning its animation cycle, plus a tolerance derived from
how much that screen actually moves. To identify the current screen, take the
distance to the NEAREST stored sample of each screen and pick the best. An
animated screen is then perfectly recognisable -- you just need a sample near its
current phase.

This also gives navigation something stronger than "something changed": it can
assert "I am on the deck select screen", which is what catches a desync into story
mode or a submenu. And unlike RAM signatures, it cannot be fooled by the deck
select screen containing battle-shaped data.

Fingerprints are pixels, so they ARE portable across boots -- unlike main RAM,
where two boots on the same screen differ by up to 1.7M bytes.

Usage:
    python3 screenlib.py learn title        # capture the current screen
    python3 screenlib.py identify
    python3 screenlib.py list
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screen_fp as FP  # noqa: E402
import nav  # noqa: E402

LIB = os.path.join(HERE, "screens.json")
SAMPLES = 8
SPACING = 30
# A screen matches only if it beats its own measured wobble by this margin.
TOL_SLACK = 1.35
MIN_TOL = 4.0


def load():
    if not os.path.exists(LIB):
        return {}
    with open(LIB) as f:
        return json.load(f)


def save(lib):
    with open(LIB, "w") as f:
        json.dump(lib, f, indent=1, sort_keys=True)


def learn(name, samples=SAMPLES, spacing=SPACING):
    """Capture the current screen several times to cover its animation cycle."""
    fps = []
    for i in range(samples):
        _, fp = nav.shot("learn_%s_%d" % (name, i))
        fps.append(list(fp))
        if i < samples - 1:
            nav.advance(spacing)
    wobble = max(FP.distance(a, b) for a in fps for b in fps)
    tol = max(MIN_TOL, wobble * TOL_SLACK)
    lib = load()
    lib[name] = {"samples": fps, "wobble": round(wobble, 2), "tol": round(tol, 2)}
    save(lib)
    print("learned %-18s wobble=%.2f tol=%.2f (%d samples)"
          % (name, wobble, tol, samples))
    return lib[name]


def nearest(fp, entry):
    return min(FP.distance(fp, s) for s in entry["samples"])


def safe_fp(tag):
    """Fingerprint the current screen, or None if the frame is blank.

    Blank happens legitimately during boot and some transitions, so polling code
    needs "not yet" rather than an exception.
    """
    try:
        _, fp = nav.shot(tag)
        return fp
    except FP.BlankCapture:
        return None


def identify(fp=None):
    """(name, distance) of the best-matching known screen, or (None, dist)."""
    if fp is None:
        fp = safe_fp("identify")
    if fp is None:
        return None, float("inf")
    lib = load()
    if not lib:
        return None, float("inf")
    scored = sorted(((nearest(fp, e), n, e) for n, e in lib.items()))
    d, name, entry = scored[0]
    if d > entry["tol"]:
        return None, d
    return name, d


def wait_for(name, max_frames=1200, poll=20):
    """Poll until the named screen is recognised. Raises on timeout."""
    lib = load()
    if name not in lib:
        raise KeyError("screen %r not in %s -- learn it first" % (name, LIB))
    waited = 0
    seen = []
    d = float("inf")
    while waited <= max_frames:
        fp = safe_fp("wait_%s" % name)
        if fp is not None:
            d = nearest(fp, lib[name])
            if d <= lib[name]["tol"]:
                return d
        if fp is None:
            seen.append("blank")
        else:
            got, gd = identify(fp)
            seen.append(got or "unknown(%.1f)" % gd)
        nav.advance(poll)
        waited += poll
    raise RuntimeError(
        "never reached screen %r in %d frames (nearest distance %.1f, tol %.1f). "
        "Saw: %s. Screenshot: %s/wait_%s.ppm"
        % (name, max_frames, d, lib[name]["tol"],
           " ".join(dict.fromkeys(seen[-6:])), nav.SHOT_DIR, name))


def press_until(buttons, expect, tag=None, max_frames=1200):
    """Press once, then wait until `expect` is recognised.

    A 1-frame press is exactly one menu step; a 4-frame hold triggers auto-repeat
    and moves two.
    """
    tag = tag or ("press_" + "_".join(buttons))
    nav.advance(1, buttons)
    d = wait_for(expect, max_frames=max_frames)
    print("  %-10s -> %-18s (distance %.2f)"
          % ("+".join(buttons), expect, d))
    return d


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "learn":
        learn(sys.argv[2])
        return 0
    if cmd == "identify":
        name, d = identify()
        print("%s (distance %.2f)" % (name or "UNKNOWN", d))
        return 0 if name else 1
    if cmd == "list":
        for n, e in sorted(load().items()):
            print("%-20s wobble=%-7.2f tol=%-7.2f samples=%d"
                  % (n, e["wobble"], e["tol"], len(e["samples"])))
        return 0
    raise SystemExit("unknown command %r" % cmd)


if __name__ == "__main__":
    sys.exit(main())
