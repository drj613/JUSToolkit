"""Measure what auto-heal actually does, per frame and per hit.

Damage-Reduction-Is-Flat.md corrects four heal-ON readings to "true" values by adding
exactly 2.0 to each ("one frame of regen landing with the hit"). Every number in that
doc's corrected table rests on that one step, and it has never been measured. This
measures it three ways on the SAME target:

  A  regen rate with heal ON, sampled directly (poke HP down, watch it climb)
  B  per-press HP delta with heal ON
  C  per-press HP delta with heal OFF
  D  idle delta over the same window with NO press (separates regen from damage)

If the +2.0 correction is right, C - B == 2.0 and A over the measurement window == 2.0.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.chdir(os.path.dirname(HERE))
import match_run as M
import nav

REPS = 3


def w32(v):
    return "".join("%02X" % ((v >> (8 * i)) & 0xFF) for i in range(4))


def peek(a, n):
    return M.peek(a, n)


def opp_ident(root):
    """(ability list, cached bitset) for the opponent's active character."""
    d = open(dump_root(root), "rb").read()
    import struct
    side = struct.unpack_from("<I", d, 0x11C)[0]
    bo = struct.unpack_from("<I", d, 0xE0)[0]
    cs = side + M.HP_IN_SIDE - 0x18
    cnt = peek(cs + 0x1A, 1) or 0
    lst = [peek(cs + 0x1B + k, 1) for k in range(min(cnt, 8))]
    return side + M.HP_IN_SIDE, bo, lst, peek(bo + 0x128, 4)


def dump_root(root):
    p = "/tmp/heal_root.bin"
    M.cli("dump", hex(root), hex(root + 0x170), p)
    return p


def hp(addr):
    return peek(addr, 2)


def regen_curve(addr, drop=0x400, frames=300, step=10):
    """A: poke HP down, sample every `step` frames, restore. Returns [(frame, raw)]."""
    orig = hp(addr)
    t = orig - drop
    M.cli("poke", hex(addr), "%02X%02X" % (t & 0xFF, t >> 8))
    nav.advance(2)
    out = []
    for f in range(0, frames + 1, step):
        out.append((f, hp(addr)))
        if f < frames:
            nav.advance(step)
    M.cli("poke", hex(addr), "%02X%02X" % (orig & 0xFF, orig >> 8))
    nav.advance(4)
    return orig, out


def into_range(addr, max_steps=24):
    """Walk right until a B press moves the opponent's HP. Returns x, or None."""
    for _ in range(max_steps):
        before = hp(addr)
        M.act(M.ATTACK, M.ATTACK_SETTLE)
        if hp(addr) != before:
            return M.player_x()
        M.act(M.STEP_RIGHT, 2)
    return None


SAMPLE = [0, 2, 4, 6, 8, 10, 12, 16, 20, 26, 32, 40, 50, 60, 80]


def hit_trace(addr, max_steps=24, frames=90):
    """Approach until a B press moves HP, then sample every frame through the recovery.

    One capture holds both halves of the question: how far HP drops on the hit, and how
    much regen gives back over the window a measurement would have used. The poke-based
    version of this could not answer it -- with the heal on, a poked value is restored
    inside two frames, so every sample after the poke read the original back.
    """
    # Seek CHEAPLY -- one peek per attempt. The fine trace costs 15 peeks and is only
    # worth paying once a press is known to connect; tracing every miss made this
    # unrunnable (90 peeks x 24 steps x reps).
    for _ in range(max_steps):
        before = hp(addr)
        M.act(M.ATTACK, 0)
        trace, prev = [], 0
        for f in SAMPLE:
            if f > prev:
                nav.advance(f - prev)
                prev = f
            trace.append((f, hp(addr)))
        if any(v != before for _, v in trace):
            return {"before_raw": before, "x": M.player_x(), "trace": trace,
                    "trace_raw": [v for _, v in trace]}
        M.act(M.STEP_RIGHT, 2)
    return None


def press_deltas(addr, reps=REPS, idle=False):
    """B or D: HP delta across one B press (or an idle window of the same length)."""
    out = []
    for _ in range(reps):
        before = hp(addr)
        if idle:
            nav.advance(3 + M.ATTACK_SETTLE)
        else:
            M.act(M.ATTACK, M.ATTACK_SETTLE)
        after = hp(addr)
        out.append({"before_raw": before, "after_raw": after,
                    "delta_raw": after - before, "delta_disp": (after - before) / 64.0})
    return out


def run(slot):
    print("\n" + "=" * 66)
    print("SLOT %s" % slot)
    print("=" * 66)
    M.cli("state", "load", slot)
    nav.advance(200)                      # jus-ywt: never read inside 10 frames of a load

    cond = M.conditions()
    print("conditions (RAM, not the harness report): %s" % cond)
    if cond["items"] or cond["gimmick"]:
        print("ABORT: contaminated -- items=%s gimmick=%s" % (cond["items"], cond["gimmick"]))
        return None

    root = peek(M.ANCHOR, 4)
    if not root:
        print("ABORT: not in a battle (anchor 0)")
        return None
    M.resolve_addresses()
    opp_hp, bo, lst, bits = opp_ident(root)
    print("opponent: hp@%s  battleObj=%s  ability list=%s  cached bitset=0x%08X"
          % (hex(opp_hp), hex(bo), lst, bits or 0))
    print("player HP=%.3f  opponent HP=%.3f" % (hp(M.HP_PLAYER) / 64.0, hp(opp_hp) / 64.0))

    heal_on = M.autoheal_is_on_by_behaviour(opp_hp)
    print("auto-heal, measured behaviourally: %s" % heal_on)

    print("\n-- A: regen curve on the opponent (heal reported %s) --" % heal_on)
    orig, curve = regen_curve(opp_hp)
    climbed = [c for c in curve if c[1] > curve[0][1]]
    print("   orig=%d  poked to %d" % (orig, curve[0][1]))
    print("   %s" % " ".join("%d:%d" % c for c in curve))
    if climbed:
        f0, v0 = curve[0]
        fN, vN = curve[-1]
        print("   climb: %d raw over %d frames = %.4f raw/frame (%.4f disp/frame)"
              % (vN - v0, fN - f0, (vN - v0) / max(1, fN - f0), (vN - v0) / 64.0 / max(1, fN - f0)))
    else:
        print("   NO CLIMB -- heal is off, or regen does not act on a poked value")

    print("\n-- D: idle window, no press (isolates regen from damage) --")
    idle = press_deltas(opp_hp, reps=3, idle=True)
    print("   %s" % [d["delta_disp"] for d in idle])

    # ORDER MATTERS. An earlier version set bit 4 BEFORE finding range, so it could
    # never land a hit, and "damage is zero" passed for the wrong reason -- the control
    # could not tell "bit 4 works" from "I never connected". Range first, always.
    print("\n-- B/C: hit + per-frame recovery trace --")
    hits = []
    for r in range(REPS):
        t = hit_trace(opp_hp)
        if t is None:
            print("   rep %d: never connected" % r)
            continue
        tr = t["trace_raw"]
        lo = min(tr)
        drop = t["before_raw"] - lo
        regain = tr[-1] - lo
        i_lo = tr.index(lo)
        print("   rep %d x=%-4s  %7.3f -> min %7.3f (frame %d)  drop %+6.3f | "
              "end %7.3f  regain %+6.3f"
              % (r, t["x"], t["before_raw"] / 64.0, lo / 64.0, i_lo, -drop / 64.0,
                 tr[-1] / 64.0, regain / 64.0))
        uniq = []
        for v in tr:
            if not uniq or uniq[-1][0] != v:
                uniq.append([v, 1])
            else:
                uniq[-1][1] += 1
        print("        %s" % " ".join("f%d:%.3f" % (f, v / 64.0) for f, v in t["trace"]))
        t.update({"drop_raw": drop, "regain_raw": regain, "min_raw": lo, "min_frame": i_lo})
        hits.append(t)
    if not hits:
        print("   NO DAMAGE LANDED -- nothing below is interpretable")
        return None

    print("\n-- positive control: bit 4 (Auto-Guard) set, then cleared --")
    pc = pc_after = None
    if bits is not None:
        M.cli("poke", hex(bo + 0x128), w32(bits | (1 << 4)))
        nav.advance(4)
        pc = [hit_trace(opp_hp, max_steps=10) for _ in range(2)]
        pc = [{"delta_disp": 0.0 if p is None else (min(p["trace_raw"]) - p["before_raw"]) / 64.0,
               "delta_raw": 0 if p is None else min(p["trace_raw"]) - p["before_raw"],
               "connected": p is not None} for p in pc]
        print("   bit 4 SET:     %s" % [d["delta_disp"] for d in pc])
        M.cli("poke", hex(bo + 0x128), w32(bits))
        nav.advance(4)
        pc_after = [hit_trace(opp_hp, max_steps=24) for _ in range(2)]
        pc_after = [{"delta_disp": 0.0 if p is None else (min(p["trace_raw"]) - p["before_raw"]) / 64.0,
                     "delta_raw": 0 if p is None else min(p["trace_raw"]) - p["before_raw"],
                     "connected": p is not None} for p in pc_after]
        print("   bit 4 CLEARED: %s" % [d["delta_disp"] for d in pc_after])
        zeroed = all(d["delta_raw"] == 0 for d in pc)
        back = any(d["delta_raw"] != 0 for d in pc_after)
        if zeroed and back:
            print("   control PASSES: damage -> 0 with bit 4, and RETURNS when cleared")
        elif zeroed and not back:
            print("   control INCONCLUSIVE: zero with bit 4 but damage never came back"
                  " -- could just be out of range")
        else:
            print("   control FAILS: damage still landed with bit 4 set")

    return {"slot": slot, "conditions": cond, "heal_on": heal_on,
            "opponent": {"ability_list": lst, "bitset": bits},
            "A_regen_curve": curve, "positive_control": pc,
            "pc_after_clear": pc_after, "D_idle": idle, "BC_hits": hits, "x": x}


if __name__ == "__main__":
    res = {}
    for slot in (sys.argv[1:] or ["cb_healoff", "cb_battle"]):
        res[slot] = run(slot)
    out = "/tmp/heal_quantum.json"
    with open(out, "w") as f:
        json.dump(res, f, indent=2)
    print("\nraw -> %s" % out)
