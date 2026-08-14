#!/usr/bin/env python3
"""Is blunt resistance multiplicative or flat?

One damage measurement can't tell those apart: against a 6-damage move, both
"x2/3" and "-2" predict 4. So measure TWO different moves, each with and
without the resistance ability, and compare:

  constant ratio      -> multiplicative
  constant difference -> flat

The resistance comes from ability 0x09 (blunt resistance UP) in the target's
ability array, which sits right after its HP:

  <hp_addr>+0  u16  HP (1/64 units)
  <hp_addr>+2  u8   ability count
  <hp_addr>+3  u8[] ability IDs

We remove 0x09 by rewriting the array without it and decrementing the count.
If damage doesn't budge, the game baked resistance into a derived stat at battle
start and this whole approach is void -- which is itself worth knowing.

Run from scripts/emu with a battle savestate already saved:
    python3 experiments/resistance_probe.py [slot]
"""
import json
import os
import subprocess
import sys

OPP_HP = 0x021DF7F0
PLAYER_HP = 0x021DF1D4
BLUNT_RESIST = 0x09
SLOT = sys.argv[1] if len(sys.argv) > 1 else "training_luffy"

# Turn to face the target first -- without this every attack whiffs and the
# whole run silently reads zero damage.
TURN_FRAMES = 12

MOVES = {
    "B": ["B"],
    "DOWN+B": ["DOWN", "B"],
}


def cli(*args):
    r = subprocess.run([sys.executable, "jusemu.py"] + list(args),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("jusemu %s failed: %s%s" % (args, r.stdout, r.stderr))
    return r.stdout


def peek(addr, length):
    out = cli("peek", hex(addr), str(length))
    return json.loads(out)["result"]["value"]


def abilities(hp_addr):
    count = peek(hp_addr + 2, 1)
    if count == 0:
        return count, []
    ids = peek(hp_addr + 3, 8)
    if isinstance(ids, int):
        ids = [ids]
    return count, ids[:count]


def poke(addr, byte_values):
    hexstr = "".join("%02x" % b for b in byte_values)
    cli("poke", hex(addr), hexstr)


def strip_ability(hp_addr, drop_id):
    """Rewrite the target's ability array without drop_id."""
    count, ids = abilities(hp_addr)
    if drop_id not in ids:
        return False, ids
    kept = [i for i in ids if i != drop_id]
    poke(hp_addr + 3, kept + [0] * (len(ids) - len(kept)))
    poke(hp_addr + 2, [len(kept)])
    return True, kept


def run_move(name, buttons, reps=6, spacing=30):
    """Attack with one move; return every downward HP step observed."""
    segs = [{"from": 0, "to": TURN_FRAMES - 1, "buttons": ["LEFT"]}]
    f = TURN_FRAMES + 2
    for _ in range(reps):
        segs.append({"from": f, "to": f + 3, "buttons": buttons})
        f += spacing
    plan = {
        "name": "resist_" + name.replace("+", "_"),
        "segments": segs,
        "tail_frames": 120,
        "watches": [{"name": "o_hp", "addr": OPP_HP, "len": 2},
                    {"name": "p_hp", "addr": PLAYER_HP, "len": 2}],
    }
    path = "/tmp/jus_resist.json"
    with open(path, "w") as fh:
        json.dump(plan, fh)
    out = cli("run", path)
    log = None
    for line in out.splitlines():
        if line.startswith("log: "):
            log = line[5:].strip()
    if not log or not os.path.exists(log):
        raise RuntimeError("no log produced: %s" % out[-300:])
    rows = [json.loads(l) for l in open(log)]
    steps, prev = [], rows[0]["w"]["o_hp"]
    for r in rows:
        v = r["w"]["o_hp"]
        if v < prev:
            steps.append(prev - v)
        prev = v
    return steps


def measure(label, strip):
    cli("state", "load", SLOT)
    count, ids = abilities(OPP_HP)
    note = "abilities=%s" % ids
    if strip:
        ok, kept = strip_ability(OPP_HP, BLUNT_RESIST)
        if not ok:
            print("  !! 0x09 not present, nothing to strip")
        _, now = abilities(OPP_HP)
        note = "abilities=%s (was %s)" % (now, ids)
    results = {}
    for name, buttons in MOVES.items():
        steps = run_move(name, buttons)
        best = max(steps) if steps else 0
        results[name] = best
        print("  %-8s hits=%-2d raw=%-5s displayed=%s"
              % (name, len(steps), best, best / 64.0))
    print("  %s -> %s" % (label, note))
    return results


def main():
    print("Resistance probe against slot %r\n" % SLOT)
    print("WITH resistance (0x09 present):")
    resisted = measure("with 0x09", strip=False)
    print("\nWITHOUT resistance (0x09 removed):")
    plain = measure("0x09 stripped", strip=True)

    print("\n%-8s %-12s %-12s %-8s %s"
          % ("move", "resisted", "unresisted", "diff", "ratio"))
    verdicts = []
    for name in MOVES:
        r, p = resisted[name], plain[name]
        if not r or not p:
            print("%-8s %-12s %-12s  (a measurement was 0 -- inconclusive)"
                  % (name, r, p))
            continue
        diff = (p - r) / 64.0
        ratio = r / p
        print("%-8s %-12s %-12s %-8s %.4f"
              % (name, r / 64.0, p / 64.0, diff, ratio))
        verdicts.append((name, diff, ratio))

    if len(verdicts) < 2:
        print("\nNeed two moves with non-zero damage both ways to decide.")
        return
    diffs = [v[1] for v in verdicts]
    ratios = [v[2] for v in verdicts]
    print()
    if all(abs(d) < 1e-9 for d in diffs):
        print("NO EFFECT: stripping 0x09 changed nothing, so the ability array "
              "is not read at damage time -- resistance is precomputed "
              "elsewhere. This is NOT 'equal base damage'; see "
              "docs/research/HP-And-Damage-Runtime-Findings.md.")
        return
    if max(ratios) - min(ratios) < 0.02 and max(diffs) - min(diffs) > 0.5:
        print("VERDICT: MULTIPLICATIVE (ratio constant at ~%.3f)" % ratios[0])
    elif max(diffs) - min(diffs) < 0.02 and max(ratios) - min(ratios) > 0.02:
        print("VERDICT: FLAT (difference constant at ~%.3f)" % diffs[0])
    else:
        print("INCONCLUSIVE: ratios %s, diffs %s" % (ratios, diffs))
        print("Both moves may share the same base damage -- pick moves with "
              "clearly different base damage and rerun.")


if __name__ == "__main__":
    main()
