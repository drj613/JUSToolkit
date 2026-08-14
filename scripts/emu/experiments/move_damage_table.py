#!/usr/bin/env python3
"""Tabulate per-move damage against an unresisted dummy.

Method that makes this work at all (both parts matter):

  * **Passive CPU.** The training default `COM設定 なにもしない` leaves the
    opponent standing still, so every trial starts from the same geometry. The
    `戦う` setting makes the AI wander and measurements stop being comparable.
  * **A swept approach.** Hold RIGHT for ~60 frames before attacking. The
    landing window is 40-100 frames wide; below that you are out of range, and
    past ~140 you walk *through* the opponent and end up facing away, at which
    point every attack silently misses.

Damage is read as downward steps in the opponent's HP. With the auto-heal on,
HP recovers within a couple of frames, so the per-frame log is essential -- a
before/after comparison reads zero.

Default target is the savestate created by `boot_to_battle.py training`, whose
opponent is コマレッド (`chr_b[70]`, 112.0 HP, empty ability array) -- about the
cleanest unresisted dummy in the game.

Usage:
    python3 experiments/move_damage_table.py [--slot pos_base] [--approach 60]
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPP_OFFSET = 0x61C

MOVES = [
    ("B", ["B"]),
    ("forward+B", ["RIGHT", "B"]),
    ("back+B", ["LEFT", "B"]),
    ("up+B", ["UP", "B"]),
    ("down+B", ["DOWN", "B"]),
    ("A", ["A"]),
    ("forward+A", ["RIGHT", "A"]),
    ("up+A", ["UP", "A"]),
    ("down+A", ["DOWN", "A"]),
    ("X", ["X"]),
    ("up+X", ["UP", "X"]),
    ("down+X", ["DOWN", "X"]),
    ("Y", ["Y"]),
    ("R", ["R"]),
    ("L", ["L"]),
]


def cli(*args):
    return subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py")] + list(args),
                          capture_output=True, text=True, cwd=HERE).stdout


def peek(addr, length):
    out = cli("peek", hex(addr), str(length))
    try:
        return json.loads(out)["result"]["value"]
    except Exception:
        return None


def player_base():
    """Re-derive the slot base -- addresses are session-local."""
    sys.path.insert(0, HERE)
    import find_battle_structs as f
    f.dump_ram("/tmp/jus_mdt.bin")
    with open("/tmp/jus_mdt.bin", "rb") as fh:
        ram = fh.read()
    hits = f.scan(ram, f.valid_hp_values())
    if not hits:
        raise RuntimeError("no character array found -- are we in a battle?")
    return max(hits, key=lambda h: h[2])[0]


def trial(slot, opp, name, buttons, approach, reps=4):
    cli("state", "load", slot)
    segs = [{"from": 0, "to": approach - 1, "buttons": ["RIGHT"]}]
    f = approach + 4
    for _ in range(reps):
        segs.append({"from": f, "to": f + 3, "buttons": buttons})
        f += 26
    plan = {"name": "mv_" + name.replace("+", "_"), "segments": segs,
            "tail_frames": 150,
            "watches": [{"name": "o", "addr": opp, "len": 2}]}
    with open("/tmp/jus_mv.json", "w") as fh:
        json.dump(plan, fh)
    out = cli("run", "/tmp/jus_mv.json")
    logs = [l[5:].strip() for l in out.splitlines() if l.startswith("log: ")]
    if not logs or not os.path.exists(logs[0]):
        return None
    rows = [json.loads(l) for l in open(logs[0])]
    dips, prev = [], rows[0]["w"]["o"]
    for r in rows:
        v = r["w"]["o"]
        if v < prev:
            dips.append(prev - v)
        prev = v
    return dips


def main():
    args = sys.argv[1:]
    slot = args[args.index("--slot") + 1] if "--slot" in args else "pos_base"
    approach = int(args[args.index("--approach") + 1]) if "--approach" in args else 60

    cli("state", "load", slot)
    base = player_base()
    opp = base + OPP_OFFSET
    cnt = peek(opp + 2, 1)
    print("player slot base 0x%08X, opponent 0x%08X" % (base, opp))
    print("target: chr_b idx=%s  HP=%.1f  abilities=%s\n"
          % (peek(opp + 0x29, 1), (peek(opp, 2) or 0) / 64.0, cnt))
    if cnt:
        print("WARNING: target has %d abilities -- not an unresisted dummy\n" % cnt)

    results = {}
    print("%-12s %-6s %-22s %s" % ("move", "hits", "raw per hit", "displayed"))
    for name, buttons in MOVES:
        dips = trial(slot, opp, name, buttons, approach)
        if dips is None:
            print("%-12s  (run failed)" % name)
            continue
        results[name] = dips
        print("%-12s %-6d %-22s %s"
              % (name, len(dips), str(dips[:5]),
                 [round(d / 64.0, 3) for d in dips[:5]]))

    out = os.path.join(HERE, "experiments", "move_damage_results.json")
    with open(out, "w") as fh:
        json.dump({"slot": slot, "approach_frames": approach,
                   "target_chr_b": peek(opp + 0x29, 1),
                   "results_raw": results,
                   "results_displayed": {k: [d / 64.0 for d in v]
                                         for k, v in results.items()}}, fh, indent=1)
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
