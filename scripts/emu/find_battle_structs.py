#!/usr/bin/env python3
"""Locate the battle character array in RAM by signature.

WHY THIS EXISTS: the absolute HP addresses in our older notes
(`0x021DF1D5` and friends) are **not portable between battles**. The same deck
in two different training battles put the player array at `0x021DF1D4` in one
and `0x021DF1B4` in another -- a 0x20 shift. Hardcoding them silently reads
garbage: neighbouring values look plausible enough that you can waste a session
on it.

So: find the array, don't assume it.

Signature. Each character slot is 0x50 bytes:

    +0x00  u16   HP, in 1/64 units (so always a multiple of 64)
    +0x02  u8    ability count
    +0x03  u8[]  ability IDs
    +0x29  u8    chr_b index (the koma abilityId; < 74)

A player deck is four consecutive slots. Requiring the *group* is what makes
this precise -- single slots match over a thousand times in 4MB, mostly inside
ARM9 code, because "a multiple of 64 followed by a small byte" is common. The
group of four with plausible chr_b indices is essentially unique.

Cross-check: HP must equal `chr_b[idx][size-4]`, optionally +8 per active
Ｊ魂+ source (leader / relationship adjacency). We accept +0 or +8 here.

Usage (with a battle running and the bridge up):
    python3 find_battle_structs.py                 # dump RAM, then scan
    python3 find_battle_structs.py --ram dump.bin  # scan an existing dump
"""
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = 0x02000000
RAM_END = 0x02400000
SLOT_STRIDE = 0x50
CHR_B = os.path.join(HERE, "..", "..", "jus_files",
                     "ripped_jus_files", "bin", "chr_b.bin")
HP_SLOTS = (0x10, 0x14, 0x18, 0x1C, 0x20)


def valid_hp_values():
    with open(CHR_B, "rb") as f:
        d = f.read()
    return set(d[i * 60 + o] for i in range(74) for o in HP_SLOTS)


def dump_ram(path):
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "dump",
                        hex(BASE), hex(RAM_END), path],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("dump failed:\n%s%s" % (r.stdout, r.stderr))
    return path


def read_slot(ram, off):
    hp = struct.unpack_from("<H", ram, off)[0]
    return {"hp": hp, "displayed": hp / 64.0, "count": ram[off + 2],
            "ids": list(ram[off + 3:off + 3 + max(ram[off + 2], 0)]),
            "index": ram[off + 0x29]}


def plausible(slot, valid):
    hp, d = slot["hp"], slot["hp"] // 64
    if hp == 0 or hp % 64:
        return False
    if not (100 <= d <= 320):
        return False
    if not (d in valid or (d - 8) in valid):
        return False
    return slot["count"] <= 8 and slot["index"] <= 73


def scan(ram, valid, min_good=3):
    out = []
    for off in range(0, len(ram) - 4 * SLOT_STRIDE, 4):
        slots = [read_slot(ram, off + s * SLOT_STRIDE) for s in range(4)]
        if not plausible(slots[0], valid):
            continue
        good = 1 + sum(1 for s in slots[1:] if plausible(s, valid))
        if good >= min_good:
            out.append((BASE + off, slots, good))
    return out


def live_filter(hits, dump_a="/tmp/jus_live_a.bin", dump_b="/tmp/jus_live_b.bin",
                settle_frames=180):
    """Keep only candidates whose memory actually changes over time.

    WARNING -- THIS IS A WEAK SIGNAL, NOT A FILTER. A validated positive case
    (0x021DF1B4, which demonstrably yields real damage) shows **zero** changed
    bytes while the player stands idle at full HP: nothing in the deck slots has
    to move. Gating on liveness therefore rejects the correct answer. It is
    reported as a diagnostic only. The reliable discriminator is functional --
    run a known attack and see which candidate's +0x61C actually dips.

    Original motivation, still valid: the signature alone produces false
    positives. A
    *stale copy* of a previous battle's array — left in memory after the battle
    ended — matches all four slots, carries valid chr_b indices, HP values that
    cross-check against chr_b, and even the correct +8 leader bonus. It scores
    4/4 and is completely dead.

    That fooled an `in_battle()` check into reporting success while the game sat
    on the deck-select screen, and produced a "damage" reading of 7868 raw that
    was identical for every input including no attack at all.

    The discriminator is liveness: a battle's character array has timers and
    counters ticking every frame, so its bytes change. A stale copy is frozen.
    """
    dump_ram(dump_a)
    plan = {"name": "live_probe", "segments": [{"from": 0, "to": 0, "buttons": []}],
            "tail_frames": settle_frames}
    with open("/tmp/jus_live_plan.json", "w") as f:
        json.dump(plan, f)
    subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py"), "run",
                    "/tmp/jus_live_plan.json"], capture_output=True, text=True, cwd=HERE)
    dump_ram(dump_b)
    with open(dump_a, "rb") as f:
        a = f.read()
    with open(dump_b, "rb") as f:
        b = f.read()
    out = []
    for addr, slots, good in hits:
        off = addr - BASE
        changed = sum(1 for i in range(4 * SLOT_STRIDE)
                      if off + i < len(a) and a[off + i] != b[off + i])
        out.append((addr, slots, good, changed))
    return out


def main():
    args = sys.argv[1:]
    ram_path = "/tmp/jus_ram.bin"
    if "--ram" in args:
        ram_path = args[args.index("--ram") + 1]
    else:
        print("dumping 4MB of main RAM ...")
        dump_ram(ram_path)
    with open(ram_path, "rb") as f:
        ram = f.read()
    if len(ram) < RAM_END - BASE:
        print("warning: dump is only %d bytes" % len(ram))

    valid = valid_hp_values()
    hits = scan(ram, valid)
    print("%d candidate deck array(s)" % len(hits))
    live = None
    if "--no-live" not in args:
        print("verifying liveness (a stale copy scores 4/4 but is frozen) ...")
        live = {a: ch for a, _, _, ch in live_filter(hits)}
        alive = [a for a, ch in live.items() if ch > 0]
        print("  %d of %d changed while idle (weak signal: an idle battle at\n"
              "  full HP legitimately shows 0, so this does NOT rule a"
              " candidate out)\n" % len(alive) if False else
              "  %d of %d changed while idle -- WEAK signal only; an idle battle\n"
              "  at full HP legitimately shows 0 changes, so this rules nothing out.\n"
              % (len(alive), len(hits)))
    else:
        print()
    for addr, slots, good in sorted(hits, key=lambda h: -h[2]):
        tag = ""
        if live is not None:
            tag = "  (%d bytes changed while idle)" % live[addr]
        print("player array base 0x%08X  (%d/4 slots plausible)%s" % (addr, good, tag))
        for i, s in enumerate(slots):
            print("   slot%d 0x%08X hp=%-6d %-7s idx=%-3d cnt=%-2d ids=%s"
                  % (i, addr + i * SLOT_STRIDE, s["hp"], s["displayed"],
                     s["index"], s["count"], s["ids"]))
        print("   opponent side is historically +0x61C -> 0x%08X "
              "(verify, don't trust)" % (addr + 0x61C))
        print()
    if hits:
        best = max(hits, key=lambda h: h[2])[0]
        print("Best-scoring candidate (VERIFY FUNCTIONALLY before trusting):")
        print("  player active HP  0x%08X (len 2)" % best)
        print("  chr_b index       0x%08X (len 1)" % (best + 0x29))
        print("  opponent HP       0x%08X (len 2)" % (best + 0x61C))
        print("\nFunctional check: land a known attack and confirm the opponent\n"
              "address dips. A stale copy scores 4/4 and never moves -- one such\n"
              "copy produced an identical bogus 7868 'damage' for every input,\n"
              "including with no attack at all.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
