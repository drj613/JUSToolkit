#!/usr/bin/env python3
"""Set each ability bit in turn on one target and measure blunt damage taken.

This is the follow-up to `ability_bitset_probe.py`, which found that bits 8-11
(the two blunt/slash resistances and both weaknesses) change blunt damage by
exactly zero -- while bit 4 (オートガード, Auto-Guard) blocks the attack
completely. That contrast is what makes the sweep worth running: the word is
demonstrably live and a single bit can have a large, semantically correct
effect, so a zero here is a real null and not a dead instrument.

One target (chr_b[70], no innate abilities), one attacker (Goku), one move
(B, a punch), 32 conditions. Writes one JSON line per bit so a partial run is
still usable and can be resumed.

Auto-heal is ON, so every damage figure is net of one frame of regen (+128 raw).
Baseline is 384 raw = 6.0 displayed. Differences between conditions are what
matter; a constant offset cancels.

    python3 experiments/ability_bit_sweep.py [--out path] [--bits 0-31]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ability_bitset_probe as P  # noqa: E402

OUT = "/tmp/jus_ability_sweep.jsonl"
# Re-measure the untouched baseline every N bits. Savestate reproducibility is
# only established within a session, and a long sweep is exactly where drift
# would hide -- if baseline moves, everything after it is suspect.
BASELINE_EVERY = 8


def one(mask, tag):
    P.cli("state", "load", P.SLOT)
    if mask:
        P.poke_word(P.OPP_BITSET, mask)
        got = P.peek(P.OPP_BITSET, 4)
        if got != mask:
            return {"tag": tag, "mask": mask, "error": "poke read back 0x%X" % got}
    steps, seen = P.attack_run(tag)
    raw = max(steps) if steps else 0
    rec = {"tag": tag, "mask": mask, "hits": len(steps), "raw": raw,
           "displayed": raw / 64.0, "steps": steps,
           "bits_seen": seen, "void": any(s != mask for s in seen)}
    print("%-10s mask=0x%08X hits=%-2d raw=%-5d disp=%-7s%s"
          % (tag, mask, len(steps), raw, raw / 64.0,
             "  VOID %s" % [hex(s) for s in seen] if rec["void"] else ""))
    sys.stdout.flush()
    return rec


def main():
    out = OUT
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    bits = range(32)
    if "--bits" in sys.argv:
        a, b = sys.argv[sys.argv.index("--bits") + 1].split("-")
        bits = range(int(a), int(b) + 1)
    fh = open(out, "a")

    def emit(rec):
        fh.write(json.dumps(rec) + "\n")
        fh.flush()

    emit(one(0, "base@start"))
    for n, i in enumerate(bits):
        emit(one(1 << i, "bit%02d" % i))
        if (n + 1) % BASELINE_EVERY == 0:
            emit(one(0, "base@%d" % (n + 1)))
    emit(one(0, "base@end"))
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
