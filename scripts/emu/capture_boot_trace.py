#!/usr/bin/env python3
"""Walk the boot-to-battle sequence and dump RAM after every step, several times.

This is the data-collection half of making menu navigation reliable. The end goal
is to replace `boot_to_battle.py`'s fixed settle timers with "wait until the
screen actually looks like the screen we expect", because a press that lands one
screen early or late silently shifts every later step and the run ends somewhere
unintended.

To do that we need a fingerprint per screen, and screenshots are unavailable here
(melonDS window capture needs screen-recording permission). So the fingerprint
has to come from RAM.

Note we never need to know a screen's *name*. We only need "after step 6 the
machine looks like this," so steps are labelled by the step that produced them.

WHY MULTIPLE RUNS. Any two RAM dumps taken at different moments differ in
millions of bytes -- frame counters, RNG, animation state, audio. Comparing one
dump per screen yields thousands of "screen ids" that are really just clocks.
Repeats let `find_screen_id.py` throw those out: keep only bytes that hold still
across every repeat of a step and still differ between steps.

THE TRAP THIS SCRIPT GUARDS. A run that desyncs mid-navigation files its dumps
under step labels they don't belong to. Each run must therefore end in a real
battle, and if it doesn't, the whole run's dumps are discarded.

Worth being precise about which way that failure actually breaks, because it
decides how much the guard matters. Mismatched labels make a byte look *unstable*
between repeats, so the filter throws it out. The result is fewer candidates, not
wrong ones -- the error is conservative, and it cannot manufacture a fake screen
id. The guard is still worth having (silently losing every candidate is a
miserable thing to debug) but a surviving candidate is not suspect just because
some run may have wobbled.

A related hazard, from the atlas session: START skips the opening intro, so if one
run takes the intro and another skips it, the same presses land on different
screens and step indices shift between runs. Same conservative outcome -- lost
candidates -- but it is the most likely reason for a disappointing result here.

Usage:
    python3 capture_boot_trace.py [--runs 3] [--mode training] [--out DIR]
    python3 find_screen_id.py compare      # then analyse what was captured
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import boot_to_battle as B          # noqa: E402
import find_screen_id as S          # noqa: E402

DEFAULT_RUNS = 3


def dump_to(path):
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "dump",
                        hex(S.BASE), hex(S.RAM_END), path],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("dump failed:\n%s%s" % (r.stdout, r.stderr))


def one_run(run_idx, mode, outdir):
    """Boot, walk the sequence dumping after each step, keep only if it worked."""
    staging = os.path.join(outdir, "_run%d" % run_idx)
    shutil.rmtree(staging, ignore_errors=True)
    os.makedirs(staging, exist_ok=True)

    print("run %d: launching emulator ..." % run_idx)
    subprocess.run(["bash", os.path.join(HERE, "launch_emu.sh")], check=True)

    # The bridge is up within ~2s but the ROM is still booting. Pressing START
    # before the title screen exists desyncs everything after it.
    print("  waiting for ROM boot ...")
    B.press("boot_wait", [], 600)
    dump_to(os.path.join(staging, "00_title.bin"))

    for i, (name, buttons, tail) in enumerate(B.build_steps(mode, B.DECK_INDEX)):
        print("  %02d %-14s %-8s (tail %d)" % (i + 1, name, "+".join(buttons), tail))
        B.press(name, buttons, tail)
        dump_to(os.path.join(staging, "%02d_%s.bin" % (i + 1, name)))

    base = B.in_battle()
    if not base:
        print("  run %d did NOT reach a battle -- DISCARDING its %d dumps. They "
              "would be filed under step labels they don't belong to and would "
              "poison the comparison."
              % (run_idx, len(os.listdir(staging))))
        shutil.rmtree(staging, ignore_errors=True)
        return False

    print("  reached battle (array 0x%08X); keeping dumps" % base)
    for fn in sorted(os.listdir(staging)):
        label = fn[:-4]
        shutil.move(os.path.join(staging, fn),
                    os.path.join(outdir, "%s.%d.bin" % (label, run_idx)))
    shutil.rmtree(staging, ignore_errors=True)
    return True


def main():
    # This script is normally backgrounded with its output redirected to a file,
    # and Python block-buffers stdout when it isn't a terminal -- so progress
    # sits invisible in the buffer for minutes and the run looks hung.
    sys.stdout.reconfigure(line_buffering=True)
    runs = DEFAULT_RUNS
    mode = "training"
    outdir = S.DUMPS
    a = sys.argv[1:]
    for i, x in enumerate(a):
        if x == "--runs":
            runs = int(a[i + 1])
        elif x == "--mode":
            mode = a[i + 1]
        elif x == "--out":
            outdir = a[i + 1]
    os.makedirs(outdir, exist_ok=True)

    ok = 0
    for r in range(runs):
        try:
            if one_run(r, mode, outdir):
                ok += 1
        except Exception as exc:
            print("  run %d blew up: %s" % (r, exc))
    print("\n%d of %d runs reached a battle and were kept." % (ok, runs))
    if ok < 2:
        print("Fewer than 2 usable runs. There is nothing to compare -- every "
              "byte would look stable off a single sample. Rerun.")
        return 1
    print("Now: python3 find_screen_id.py compare   (dumps in %s)" % outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
