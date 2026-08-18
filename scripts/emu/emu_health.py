#!/usr/bin/env python3
"""Detect and recover from a hung emulator.

melonDS intermittently HANGS on savestate load. Observed twice in one session,
both times immediately after "Resetting JIT block cache" in the emulator log. The
symptom is nasty because the process stays alive and the window keeps drawing the
last frame:

  * the bridge heartbeat framecount stops advancing
  * no button, hold or tap has any effect
  * commands eventually fail with "no ack ... INDETERMINATE: the bridge may or may
    not have executed it"

It is intermittent, not deterministic -- a 36-load sweep earlier in the same session
ran clean, and a 12-load experiment hung twice. So it cannot be avoided by being
careful; it has to be detected.

Why the framecount and not a screenshot: a hung emulator keeps showing its last
frame, so pixels look like a perfectly valid screen. The heartbeat is the only
signal that separates "this screen is not changing because nothing is happening"
from "this screen is not changing because the emulator is dead". This is the same
trap as the stale-capture bug, and the same rule applies -- confirm liveness from
the bridge before believing anything about the screen.

Usage:
    python3 emu_health.py check        # exit 0 if advancing, 1 if hung
    python3 emu_health.py ensure       # restart if hung
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
HEARTBEAT = os.path.join(os.environ.get("JUS_EMU_DIR", "/tmp/jus_emu"),
                         "heartbeat.json")


def framecount():
    try:
        with open(HEARTBEAT) as f:
            return json.load(f).get("framecount")
    except (OSError, ValueError):
        return None


def is_advancing(window=2.5):
    """True if the emulated frame counter moves. The authoritative liveness test."""
    a = framecount()
    if a is None:
        return False
    time.sleep(window)
    b = framecount()
    return b is not None and b != a


def relaunch():
    subprocess.run(["bash", os.path.join(HERE, "launch_emu.sh")],
                   check=True, capture_output=True)


def ensure_alive(reload_slot=None, verbose=True):
    """Restart the emulator if it has hung. Returns True if it was restarted.

    reload_slot: savestate to restore after a restart, so a long experiment can
    carry on from where it was instead of losing the run.
    """
    if is_advancing():
        return False
    if verbose:
        print("    emulator is not advancing frames (framecount %s) -- hung on a "
              "savestate load. Restarting." % framecount())
    relaunch()
    if reload_slot:
        r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"),
                            "state", "load", reload_slot],
                           capture_output=True, text=True, cwd=HERE)
        if r.returncode != 0:
            raise RuntimeError("restarted but could not reload %r: %s%s"
                               % (reload_slot, r.stdout, r.stderr))
        if verbose:
            print("    restarted and reloaded %r" % reload_slot)
    return True


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        ok = is_advancing()
        print("framecount %s, %s" % (framecount(),
                                     "advancing" if ok else "NOT ADVANCING"))
        return 0 if ok else 1
    if cmd == "ensure":
        slot = sys.argv[2] if len(sys.argv) > 2 else None
        print("restarted" if ensure_alive(slot) else "healthy")
        return 0
    raise SystemExit("unknown command %r" % cmd)


if __name__ == "__main__":
    sys.exit(main())
