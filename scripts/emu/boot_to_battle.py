#!/usr/bin/env python3
"""Drive Jump Ultimate Stars from ROM boot into a battle, hands-free.

Menu navigation only works if you respect two things learned the hard way:

  * A 1-frame press is exactly one menu step. A 4-frame hold triggers
    auto-repeat and moves two steps. All presses here are 1 frame.
  * Screen transitions need slack. Each step carries its own tail so the next
    press doesn't land on a screen that is still animating.

Modes:
  training  J Arena -> トレーニング. Opponent is a dummy, but HP auto-heals to
            full within a few frames of any hit, so damage must be read
            per-frame as the minimum of a dip.
  battle    J Arena -> バトル. No auto-heal, and characters can actually be
            KO'd -- much better for damage work and the only way to observe a
            character switch.

Usage:
    python3 boot_to_battle.py [training|battle] [--slot NAME] [--no-launch]
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PLAYER_HP = 0x021DF1D4
OPP_HP = 0x021DF7F0

# J Arena menu order: ランキング, ミッショントライ, バトル, トレーニング
ARENA_INDEX = {"battle": 2, "training": 3}


def cli(*args, check=True):
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py")] + list(args),
                       capture_output=True, text=True, cwd=HERE)
    if check and r.returncode != 0:
        raise RuntimeError("jusemu %s failed:\n%s%s" % (args, r.stdout, r.stderr))
    return r.stdout


def peek(addr, length):
    return json.loads(cli("peek", hex(addr), str(length)))["result"]["value"]


def press(name, buttons, tail):
    """One 1-frame press followed by `tail` frames of settle time."""
    plan = {"name": name,
            "segments": [{"from": 0, "to": 0, "buttons": buttons}],
            "tail_frames": tail}
    path = "/tmp/jus_boot_step.json"
    with open(path, "w") as f:
        json.dump(plan, f)
    cli("run", path)


def in_battle():
    """Battle HP values are non-zero multiples of 64 for both sides."""
    try:
        p, o = peek(PLAYER_HP, 2), peek(OPP_HP, 2)
    except Exception:
        return False
    return p > 0 and o > 0 and p % 64 == 0 and o % 64 == 0


def main():
    mode = "training"
    slot = None
    launch = True
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a in ARENA_INDEX:
            mode = a
        elif a == "--slot" and i + 1 < len(args):
            slot = args[i + 1]
        elif a == "--no-launch":
            launch = False
    slot = slot or ("battle_" + mode)

    if launch:
        print("launching emulator + bridge ...")
        subprocess.run(["bash", os.path.join(HERE, "launch_emu.sh")], check=True)

    # The bridge comes up within ~2s but the ROM is still booting. Pressing
    # START before the title screen exists desyncs every later step, and the
    # symptom is confusing: you end up back at the title with no error.
    print("  waiting for ROM boot ...")
    press("boot_wait", [], 600)

    steps = [
        ("skip_intro", ["START"], 600),   # Start skips the opening
        # Top menu starts on Jギャラクシー (index 0); Jアリーナ is index 1, so
        # exactly one RIGHT. Pressing LEFT here lands back on Jギャラクシー and
        # the next A drops you into story mode.
        ("to_arena", ["RIGHT"], 120),
        ("enter_arena", ["A"], 300),
    ]
    for n in range(ARENA_INDEX[mode]):
        steps.append(("arena_down%d" % n, ["DOWN"], 40))
    steps += [
        ("choose_mode", ["A"], 300),
        ("deck_select", ["A"], 300),
        ("stage_select", ["A"], 400),
        ("rule_start", ["START"], 600),   # "バトルスタート"
    ]

    for name, buttons, tail in steps:
        print("  %-14s %-8s (tail %d)" % (name, "+".join(buttons), tail))
        press(name, buttons, tail)

    for attempt in range(10):
        if in_battle():
            break
        time.sleep(1)
    else:
        print("NOT in a battle -- HP addresses don't look valid. Screenshot the "
              "window to see which screen it stalled on.")
        return 1

    p, o = peek(PLAYER_HP, 2), peek(OPP_HP, 2)
    print("\nin battle: player HP %d (%.1f), opponent HP %d (%.1f)"
          % (p, p / 64.0, o, o / 64.0))
    print("saving savestate %r ..." % slot)
    print(cli("state", "save", slot).strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
