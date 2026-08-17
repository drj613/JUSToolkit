#!/usr/bin/env python3
"""Does the flat -2 blunt reduction come from ability 0x09? Poke the CACHED BITSET.

Background. `Damage-Reduction-Is-Flat.md` established that the reduction is flat
(-2.0 displayed), but could not attribute it: the resisting target (Luffy) and
the unresisted target (chr_b[70]) are *different characters*, so a per-character
defence value explains the data just as well. The clean test -- same target with
and without the ability -- failed, because rewriting the visible ability array
mid-battle changes damage by exactly zero.

Codex found why: at load, `0x0215FB3C` walks the ability list and caches each ID
as a *bit* in a word at `entity + 0x128`. The array is a source record; the
bitset is what runtime logic consults. So poke the bitset, not the array.

Confirmed at runtime before writing this: Goku (abilities [7, 15]) has
0x00008080 at his entity+0x128, and the ability-free dummy chr_b[70] has
0x00000000. Bits 7 and 15 set, nothing else. The mechanism is real.

The design. Four conditions on ONE target, so no cross-character confound:

    bit  9 (0x200)  0x09 打撃耐性ＵＰ  blunt resistance  -> damage should DROP 2.0
    bit 11 (0x800)  0x0B 打撃弱点      blunt weakness    -> damage should RISE
    bit 10 (0x400)  0x0A 斬撃耐性ＵＰ  slash resistance  -> punch: NO CHANGE
    bit  8 (0x100)  0x08 状態変化耐性  status resistance -> punch: NO CHANGE

The last two are specificity controls and they are the point of running four
conditions instead of one. A lone "bit 9 lowered damage" result is also
consistent with "any nonzero value in this word lowers damage" -- some parse
artefact, or the word doubling as something else. If 0x200 moves damage and
0x400 does not, that reading is dead: the effect is per-bit and blunt-specific.

Goku's B is a punch, i.e. blunt, which is what makes 0x09/0x0B the live bits and
0x0A the null one.

Auto-heal is ON in pos_base, so every number here is net of one frame of regen
(+128 raw). That is fine -- a constant offset cancels in the between-condition
differences, which is all we compare. Absolute values are net, not true.

Usage (battle running, pos_base saved):
    python3 experiments/ability_bitset_probe.py
    python3 experiments/ability_bitset_probe.py --addrs 0x021DF7D0,0x0224E308
"""
import json
import os
import subprocess
import sys

SLOT = "pos_base"

# Session-local. Defaults are what this session measured; re-derive with
# find_battle_structs.py plus the pointer scan described in the docs, and pass
# --addrs. A stale address reads believable garbage.
OPP_HP = 0x021DF7D0        # opponent HP block (u16, 1/64 units)
OPP_BITSET = 0x0224E308    # opponent entity+0x128, ability bitset word 0
PLAYER_HP = 0x021DF1B4

APPROACH_FRAMES = 60       # 40-100 all land; 140+ walks through and faces away
ATTACK_REPS = 4
SPACING = 40

CONDITIONS = [
    ("baseline", 0x000, "no poke"),
    ("blunt-resist", 0x200, "0x09 -> expect DROP 2.0"),
    ("blunt-weak", 0x800, "0x0B -> expect RISE"),
    ("slash-resist", 0x400, "0x0A -> control, expect NO CHANGE vs baseline"),
    ("status-resist", 0x100, "0x08 -> control, expect NO CHANGE vs baseline"),
]


def cli(*args):
    r = subprocess.run([sys.executable, "jusemu.py"] + list(args),
                       capture_output=True, text=True,
                       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if r.returncode != 0:
        raise RuntimeError("jusemu %s failed: %s%s" % (args, r.stdout, r.stderr))
    return r.stdout


def peek(addr, length):
    return json.loads(cli("peek", hex(addr), str(length)))["result"]["value"]


def poke_word(addr, value):
    b = [(value >> (8 * i)) & 0xFF for i in range(4)]
    cli("poke", hex(addr), "".join("%02x" % x for x in b))


def attack_run(tag):
    """Approach, punch a few times, return every downward HP step (raw units).

    Per-frame steps, never before/after: training regen restores +128 raw per
    frame, so a differenced pair understates damage by one frame of heal at best
    and hides it entirely at worst.
    """
    segs = [{"from": 0, "to": APPROACH_FRAMES - 1, "buttons": ["RIGHT"]}]
    f = APPROACH_FRAMES + 2
    for _ in range(ATTACK_REPS):
        segs.append({"from": f, "to": f + 3, "buttons": ["B"]})
        f += SPACING
    plan = {
        "name": "bitset_" + tag,
        "segments": segs,
        "tail_frames": 120,
        "watches": [
            {"name": "o_hp", "addr": OPP_HP, "len": 2},
            {"name": "p_hp", "addr": PLAYER_HP, "len": 2},
            {"name": "bits", "addr": OPP_BITSET, "len": 4},
        ],
    }
    path = "/tmp/jus_bitset_plan.json"
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
    bits = sorted(set(r["w"]["bits"] for r in rows))
    return steps, bits


def run_condition(name, bit, note):
    cli("state", "load", SLOT)
    before = peek(OPP_BITSET, 4)
    if before != 0:
        print("  !! bitset was 0x%X after load, expected 0 -- state is dirty" % before)
    if bit:
        poke_word(OPP_BITSET, bit)
        after = peek(OPP_BITSET, 4)
        if after != bit:
            raise RuntimeError("poke did not stick: wrote 0x%X, read 0x%X" % (bit, after))
    steps, seen = attack_run(name)
    # If the engine rebuilt or cleared the word mid-run the whole condition is
    # void, so surface it rather than averaging over it.
    unexpected = [s for s in seen if s != bit]
    hit = max(steps) if steps else 0
    print("  %-14s bits=0x%-4X hits=%-2d raw=%-5s displayed=%-7s %s"
          % (name, bit, len(steps), hit, hit / 64.0, note))
    if unexpected:
        print("     !! bitset changed during the run: %s -- condition is void"
              % [hex(s) for s in seen])
    if not steps:
        print("     !! ZERO hits. Nothing was measured -- do not read this as "
              "'no damage'. Check facing/approach before believing any row.")
    return {"name": name, "bit": bit, "steps": steps, "raw": hit,
            "bits_seen": seen, "void": bool(unexpected)}


def main():
    global OPP_HP, OPP_BITSET
    if "--addrs" in sys.argv:
        a, b = sys.argv[sys.argv.index("--addrs") + 1].split(",")
        OPP_HP, OPP_BITSET = int(a, 16), int(b, 16)
    print("Ability bitset probe: opp hp 0x%08X, bitset 0x%08X, slot %r\n"
          % (OPP_HP, OPP_BITSET, SLOT))

    results = [run_condition(*c) for c in CONDITIONS]
    base = results[0]["raw"]

    print("\n%-14s %-8s %-10s %s" % ("condition", "raw", "displayed", "vs baseline"))
    for r in results:
        d = (r["raw"] - base) / 64.0
        flag = " (VOID)" if r["void"] else ("" if r["steps"] else " (no hits)")
        print("%-14s %-8d %-10s %+.3f%s" % (r["name"], r["raw"], r["raw"] / 64.0, d, flag))

    by = {r["name"]: r for r in results}
    if not all(by[n]["steps"] and not by[n]["void"] for n in by):
        print("\nSome condition measured nothing. No verdict.")
        return 1

    resist_d = (by["blunt-resist"]["raw"] - base) / 64.0
    weak_d = (by["blunt-weak"]["raw"] - base) / 64.0
    controls = [(n, (by[n]["raw"] - base) / 64.0)
                for n in ("slash-resist", "status-resist")]
    print()
    if any(abs(d) > 1e-9 for _, d in controls):
        print("CONTROLS MOVED: %s. The word is not a clean per-ability bitset for "
              "damage, or the poke perturbs something else. Do not attribute "
              "anything to 0x09 on this evidence." % controls)
    elif abs(resist_d + 2.0) < 1e-9:
        print("SETTLED: bit 0x200 (ability 0x09) drops blunt damage by exactly "
              "2.0 while the slash and status controls do nothing. The flat -2 "
              "IS blunt resistance, and it is blunt-specific.")
        print("blunt weakness delta: %+.3f" % weak_d)
    elif resist_d < 0:
        print("bit 0x200 lowers damage by %+.3f, not the predicted -2.0. Real "
              "effect, wrong magnitude -- worth a second move to see whether the "
              "reduction is flat at this value or scales." % resist_d)
    else:
        print("bit 0x200 did NOT lower damage (%+.3f). Either resistance is not "
              "read from this word, or it is consulted before the point we can "
              "reach by poking a loaded battle." % resist_d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
