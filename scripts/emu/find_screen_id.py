#!/usr/bin/env python3
"""Find a RAM byte that identifies which menu screen the game is on.

WHY THIS EXISTS. `boot_to_battle.py` navigates menus by pressing a button and
waiting a fixed number of frames. It has exactly one check -- `in_battle()`, at
the very end. Everything before that is blind, so a press that lands one screen
early or late silently shifts every later step, and the run ends somewhere
unintended (story mode, on one occasion). That desynced 4+ times in a single
session, and it is the blocker for anything longer, like a 20-step deck-editor
flow.

The fix is to verify the screen before each press instead of trusting a timer.
Screenshots would be the obvious oracle but are unavailable here (melonDS window
capture needs screen-recording permission), so the oracle has to come from RAM:
some byte, or small group of bytes, that takes a distinct stable value per screen.

METHOD. Capture several dumps of the same screen, then dumps of other screens,
and keep addresses that are

  * constant across every repeat of the same screen, and
  * different between at least two screens.

The repeats are the important half. Millions of bytes differ between two dumps
taken at different times -- frame counters, RNG, animation state, audio. Without
repeats you get thousands of "screen ids" that are really just clocks. Requiring
stability within a screen is what removes them.

A candidate that survives this is still only a candidate. Confirm it by
navigating to the screen a fresh way and checking the value matches.

USAGE. With the emulator up and the game sitting on a screen:

    python3 find_screen_id.py capture title       # repeat 3x, wait between
    python3 find_screen_id.py capture title
    python3 find_screen_id.py capture title
    ...navigate to the next screen, then...
    python3 find_screen_id.py capture mode_select
    python3 find_screen_id.py capture mode_select
    python3 find_screen_id.py capture mode_select
    python3 find_screen_id.py compare

Dumps land in /tmp/jus_screens/ and are reusable across compare runs.
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DUMPS = "/tmp/jus_screens"
BASE = 0x02000000
RAM_END = 0x02400000
MIN_REPEATS = 2      # below this a "stable" value is just one sample
MAX_REPORT = 40


def capture(label):
    os.makedirs(DUMPS, exist_ok=True)
    n = len(glob.glob(os.path.join(DUMPS, "%s.*.bin" % label)))
    path = os.path.join(DUMPS, "%s.%d.bin" % (label, n))
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "dump",
                        hex(BASE), hex(RAM_END), path],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise SystemExit("dump failed:\n%s%s" % (r.stdout, r.stderr))
    print("captured %s" % path)
    return path


def load_groups():
    groups = {}
    for p in sorted(glob.glob(os.path.join(DUMPS, "*.bin"))):
        label = os.path.basename(p).rsplit(".", 2)[0]
        groups.setdefault(label, []).append(p)
    return groups


def compare():
    groups = load_groups()
    thin = [l for l, ps in groups.items() if len(ps) < MIN_REPEATS]
    if thin:
        print("!! only one dump for: %s -- capture at least %d per screen or "
              "every timer in RAM will look like a screen id"
              % (", ".join(thin), MIN_REPEATS))
    if len(groups) < 2:
        raise SystemExit("need dumps from at least two different screens")

    labels = sorted(groups)
    print("screens: %s" % ", ".join("%s(x%d)" % (l, len(groups[l])) for l in labels))
    data = {l: [open(p, "rb").read() for p in groups[l]] for l in labels}
    size = min(len(b) for bs in data.values() for b in bs)

    # Do the 4MB-scale work with big-int XOR, which runs in C, and take exactly
    # one Python-level pass at the end. The obvious nested loop is
    # labels x repeats x 4M iterations and takes minutes; this takes seconds.
    # XOR is zero at a byte iff the two buffers agree there, and OR keeps a byte
    # nonzero iff any input had it nonzero, so both masks compose bytewise.
    def big(b):
        return int.from_bytes(b[:size], "little")

    unstable = 0            # nonzero byte = moved between repeats of one screen
    for l in labels:
        ref = big(data[l][0])
        for other in data[l][1:]:
            unstable |= ref ^ big(other)

    across = 0              # nonzero byte = differs between two screens
    ref0 = big(data[labels[0]][0])
    for l in labels[1:]:
        across |= ref0 ^ big(data[l][0])

    ub = unstable.to_bytes(size, "little")
    ab = across.to_bytes(size, "little")
    firsts = {l: data[l][0] for l in labels}
    hits = []
    for i, (u, a) in enumerate(zip(ub, ab)):
        if a and not u:
            hits.append((BASE + i, [firsts[l][i] for l in labels]))

    print("\n%d addresses are stable within every screen and differ across "
          "screens" % len(hits))
    distinct = [h for h in hits if len(set(h[1])) == len(labels)]
    print("%d of those give every screen a DISTINCT value (the useful kind)\n"
          % len(distinct))
    show = distinct or hits
    print("%-12s %s" % ("addr", "  ".join("%-10s" % l for l in labels)))
    for addr, vals in show[:MAX_REPORT]:
        print("0x%08X   %s" % (addr, "  ".join("%-10d" % v for v in vals)))
    if len(show) > MAX_REPORT:
        print("... %d more" % (len(show) - MAX_REPORT))
    if show:
        print("\nVERIFY before trusting: reach one screen by a different route "
              "and confirm the value matches. Neighbouring bytes that move "
              "together are probably one multi-byte field, which is fine -- "
              "prefer one that is stable and distinct over one that merely "
              "differs.")
    return 0


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "capture":
        if len(sys.argv) < 3:
            raise SystemExit("capture needs a screen label")
        capture(sys.argv[2])
        return 0
    if sys.argv[1] == "compare":
        return compare()
    raise SystemExit("unknown command %r" % sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
