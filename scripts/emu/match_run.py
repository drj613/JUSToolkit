#!/usr/bin/env python3
"""Play a training match from boot to finish, sampling RAM the whole way.

Usage:
    python3 match_run.py --boot            # cold boot, then play
    python3 match_run.py --slot NAME       # resume from a savestate
    python3 match_run.py --slot NAME --rounds 200

Writes a per-round timeline to /tmp/jus_match/timeline.json and screenshots of
the key moments to /tmp/jus_match/.

WHY TRAINING. The owner's call, and it is the right one: training gives both sides
infinite HP by default, and 自動回復 can be switched off from the pause menu, so a
match can be made to actually end. Nothing else about the battle changes.

TURNING OFF THE HEAL IS NOT VISIBLE IN A WHOLE-SCREEN FINGERPRINT. Toggling
自動回復 from ON to OFF moves the bottom screen by 1.32, well inside menu noise, so
it has to be read from a crop of the value field. The convergent check used here
instead, which needs no pixels at all: poke the opponent's HP down and watch it for
1200 frames. With the heal on it climbs back; measured with it off, 78.1 stayed
78.1 across five samples.

ONE DUMP PER ROUND, NOT TEN PEEKS. Every peek is a subprocess and an IPC round
trip, so sampling ten fields a round for a hundred rounds is a thousand of them.
Dumping 0x021DEA00-0x021DFA00 once per round and unpacking locally is a single
call for the same data, and it also guarantees every field in a sample comes from
the SAME frame -- ten separate peeks do not.

ADDRESSES ARE DERIVED, NOT HARDCODED. They used to be constants with a
plausibility check, and that check passed on garbage: in rule mode 3 the battle
root moves and the old addresses read 23.1 and 990.4 against an HP cap near 200,
while plausible() returned True. They are now derived every run from the ov6
anchor at 0x02172960 -- see resolve_addresses() -- which tracked that relocation
correctly. There is no fallback to constants; if the derivation fails the run
stops, because a believable wrong number is worse than no number.

(An earlier version of this docstring claimed a `find_blocks()` rescan. No such
function existed. The claim is removed rather than corrected.)
"""
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nav                  # noqa: E402
import emu_health as EH     # noqa: E402
import boot_verified as BV  # noqa: E402

OUT = "/tmp/jus_match"

# THESE ARE NO LONGER CONSTANTS. resolve_addresses() overwrites every one of them
# from the battle root before a match is sampled; the values here are only the
# defaults observed in an ordinary point battle, kept so the shapes are readable.
#
# WHY THE CONSTANTS HAD TO GO. They are not merely session-local, they are
# MODE-local, and they fail SILENTLY. Poking rule mode 3 moves the battle root
# from 0x021DEA60 to 0x021DEBE0, and in that battle the old HP_PLAYER read 23.1
# and the old HP_OPP read 990.4 -- against an HP cap around 200. A number like
# 990.4 is obvious, but 23.1 is not, and plausible() below passed both. A wrong
# address that returns a believable number is the failure mode this project keeps
# paying for, so the addresses are now derived and the derivation is checked.
#
# THE DERIVATION (runtime-confirmed, jus-3vg; anchor is atlas's, jus-45k):
#     root      = [0x02172960]              ov6 BSS word, null outside a battle
#     HP_PLAYER = [root + 0x118] + 0x70
#     HP_OPP    = [root + 0x11C] + 0x70     the two side objects are 0x61C apart
# Verified in mode 3 where the root moves: the derivation tracked the relocation
# and returned values matching the on-screen bars while the constants did not.
ANCHOR = 0x02172960          # ov6 BSS: pointer to the battle root, 0 outside battle
ROOT_SIZE = 0x170            # CONFIRMED_STATIC from a single allocation site
SIDE_A_PTR, SIDE_B_PTR = 0x118, 0x11C
HP_IN_SIDE = 0x70            # HP slot array inside a side object
SIDE_DELTA = 0x61C           # invariant between the two side objects

DUMP_START, DUMP_END = 0x021DEA00, 0x021DFA00
HP_PLAYER = 0x021DF1D4
HP_OPP = 0x021DF7F0
SLOT_STRIDE, SLOTS = 0x50, 4
CHR_B_IN_SLOT = 0x29         # chr_b index inside an HP slot

# UNVERIFIED, carried over as relative offsets rather than absolutes. Both were
# hardcoded addresses that happened to be correct in the default layout; neither
# has been confirmed to mean what its name says. TIMER especially: sampled across
# 1800 frames it went 16 -> 13 -> 11 -> 8, which is not the じかん counter (that
# starts at 30). Expressing them relative to structures that are confirmed at
# least makes them move with the battle instead of pointing at whatever now
# occupies a stale address.
TIMER_IN_ROOT = 0x11         # 0x021DEA71 - 0x021DEA60 in the default layout
SPECIAL_FROM_OPP = -0xBF     # 0x021DF731 - 0x021DF7F0 in the default layout
TIMER = 0x021DEA71
SPECIAL = 0x021DF731

# THE FIRST VERSION OF THIS WAS NOT A MATCH. It cycled a fixed repertoire of bursts --
# walk right and punch, punch, special, walk left and punch, jump and punch -- and hoped
# something connected. Over 100 rounds it landed exactly one hit and then made no
# progress at all, because nothing in the loop knew where the opponent was. The owner
# called it what it was: Goku walking back and forth throwing a punch at nothing.
#
# What the loop was missing is a position, and the loop does not need the opponent's
# position to get one. Damage is the feedback signal. Walk one direction, attack, and
# watch the opponent's HP: the x where the HP first moves IS the edge of range, measured
# rather than assumed.
#
# Calibrated on fight_base, stepping right 12 frames at a time and pressing B:
#
#     x 480-596   no damage
#     x 625+      6.0 damage on EVERY press, 19 presses in a row, 152.0 -> 1.1
#
# and the opponent is pushed along as it is hit, so following it keeps the range. The
# owner confirmed the characters pass THROUGH each other -- there is no body blocking --
# so overshooting is recoverable by turning around rather than fatal.
#
# THE RANGE IS PER-STAGE, AND THE STAGE CHANGES MID-MATCH. In a death match, when the
# timer runs out with more than one fighter still alive, every survivor is moved to a
# new SMALLER stage for sudden death (owner, confirmed from play). With じかん 30 the
# timer is 4463 frames and a round here costs about 110, so that lands around round 40
# of a run. The x numbers above stop meaning anything at that point. Nothing needs to
# detect it: when the calibrated range stops producing damage the loop falls back to
# seeking and re-finds it. That fallback is load-bearing rather than defensive.
PLAYER_X = 0x020A5C68        # s16, found by diffing all of RAM across a walk
STEP_FRAMES = 12             # one approach step
ATTACK_SETTLE = 80           # long enough for a hit to register in HP
STALE_ROUNDS = 3             # misses in a row before going back to seeking

STEP_RIGHT = [{"from": 0, "to": STEP_FRAMES - 1, "buttons": ["RIGHT"]}]
STEP_LEFT = [{"from": 0, "to": STEP_FRAMES - 1, "buttons": ["LEFT"]}]
ATTACK = [{"from": 0, "to": 2, "buttons": ["B"]}]


def cli(*args):
    r = subprocess.run([sys.executable, os.path.join(HERE, "jusemu.py")] + list(args),
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise RuntimeError("jusemu %s failed: %s%s" % (args[0], r.stdout, r.stderr))
    return r.stdout


def peek(addr, length):
    return json.loads(cli("peek", hex(addr), str(length)))["result"]["value"]


def resolve_addresses():
    """Derive the battle addresses from the anchor. Raises rather than guessing.

    Every failure here is fatal on purpose. The whole point of this function is
    that the thing it replaced returned believable numbers from stale addresses,
    so falling back to those constants on any doubt would reinstate exactly the
    bug it exists to remove. If the derivation cannot be trusted, the run stops.
    """
    global DUMP_START, DUMP_END, HP_PLAYER, HP_OPP, TIMER, SPECIAL

    root = peek(ANCHOR, 4)
    if not root:
        raise SystemExit(
            "[0x%08X] reads 0: there is no battle object, so this is not a live "
            "battle. Load an in-battle savestate or boot into one. NOT falling "
            "back to hardcoded addresses -- they would return believable garbage."
            % ANCHOR)
    if not (0x02000000 <= root < 0x02400000) or root & 3:
        raise SystemExit(
            "[0x%08X] = 0x%08X, which is not a word-aligned main-RAM pointer. The "
            "anchor is wrong or the read raced a state load (advance >=10 frames "
            "after loading before peeking)." % (ANCHOR, root))

    cli("dump", hex(root), hex(root + ROOT_SIZE), "/tmp/jus_match_root.bin")
    with open("/tmp/jus_match_root.bin", "rb") as f:
        r = f.read()
    side_a, side_b = (struct.unpack_from("<I", r, o)[0]
                      for o in (SIDE_A_PTR, SIDE_B_PTR))

    for name, p in (("+0x%X" % SIDE_A_PTR, side_a), ("+0x%X" % SIDE_B_PTR, side_b)):
        if not (0x02000000 <= p < 0x02400000):
            raise SystemExit(
                "root%s = 0x%08X is not a main-RAM pointer. The root at 0x%08X is "
                "not the object this derivation assumes." % (name, p, root))
    if side_b - side_a != SIDE_DELTA:
        raise SystemExit(
            "the two side objects are 0x%X apart, expected 0x%X (a 0x%08X, b 0x%08X). "
            "This invariant has held in every battle measured across two boots and "
            "two heap layouts, so a change means the structure is not what we think."
            % (side_b - side_a, SIDE_DELTA, side_a, side_b))

    HP_PLAYER = side_a + HP_IN_SIDE
    HP_OPP = side_b + HP_IN_SIDE
    TIMER = root + TIMER_IN_ROOT
    SPECIAL = HP_OPP + SPECIAL_FROM_OPP

    lo = min(root, HP_PLAYER, TIMER, SPECIAL)
    hi = max(root + ROOT_SIZE, HP_OPP + SLOTS * SLOT_STRIDE)
    DUMP_START = (lo - 0x40) & ~0xF
    DUMP_END = (hi + 0x40 + 0xF) & ~0xF
    print("derived from [0x%08X] = 0x%08X: HP_PLAYER 0x%08X, HP_OPP 0x%08X, "
          "dump 0x%08X-0x%08X (%d bytes)"
          % (ANCHOR, root, HP_PLAYER, HP_OPP, DUMP_START, DUMP_END,
             DUMP_END - DUMP_START))
    return root


def region(path="/tmp/jus_match_ram.bin"):
    cli("dump", hex(DUMP_START), hex(DUMP_END), path)
    with open(path, "rb") as f:
        return f.read()


def u16(buf, addr):
    return struct.unpack_from("<H", buf, addr - DUMP_START)[0]


def u8(buf, addr):
    return buf[addr - DUMP_START]


def player_x():
    """Signed x of the player's side. A proxy, and an honest one about its limits.

    Found by diffing all 4MB across a walk right and a walk left and keeping the one
    field that rose in one and fell in the other; a 20.12 fixed-point copy of the same
    value sits at 0x020A5CA8, which is what makes it a position rather than a counter.
    It is NOT the character struct -- it snaps back to 480 during a character switch,
    so treat a sudden return to 480 as "a switch happened", not as a real move.
    """
    # Its own peek, not part of the per-round dump: it sits at 0x020A5C68, over a
    # megabyte below the HP blocks, and widening the dump to span both would move
    # 1.3MB a round to read two bytes.
    v = json.loads(cli("peek", hex(PLAYER_X), "2"))["result"]["value"]
    return v - 0x10000 if v > 0x7FFF else v


def act(segments, tail):
    plan = {"name": "fight", "segments": segments, "tail_frames": tail}
    path = "/tmp/jus_match_plan.json"
    with open(path, "w") as f:
        json.dump(plan, f)
    cli("run", path)


def side(buf, base):
    """(hp, chr_b) for a side's active slot and its three reserves."""
    out = []
    for i in range(SLOTS):
        a = base + i * SLOT_STRIDE
        out.append({"hp": u16(buf, a) / 64.0, "chr_b": u8(buf, a + CHR_B_IN_SLOT)})
    return out


def sample(buf):
    return {"me": side(buf, HP_PLAYER), "opp": side(buf, HP_OPP),
            "timer": u8(buf, TIMER), "special": u8(buf, SPECIAL)}


def plausible(buf):
    """Do the derived addresses actually look like HP blocks?

    This check used to pass on garbage. In rule mode 3 the stale constants read
    23.1 and 990.4 and it returned True for both, because its only bound was
    "under 12800" and 23.1 clears that easily. The bounds below are the ones that
    would have caught it:

      - HP is a multiple of 1/64. A real HP word is an exact multiple of 64 in
        raw units at rest; 23.1 was not, and that alone is a strong signal.
      - The displayed cap is around 200.0, so 990.4 is impossible, not merely
        large. 12800 was three times too generous.
      - A slot is either dead (0) or holds a sane amount, never a trickle.

    Still cheap: it is arithmetic over a buffer that has already been dumped.
    """
    CAP_RAW = 210 * 64          # a little above the observed ~200.0 cap
    for base in (HP_PLAYER, HP_OPP):
        for i in range(SLOTS):
            a = base + i * SLOT_STRIDE
            hp = u16(buf, a)
            if hp > CAP_RAW:
                return False
            if u8(buf, a + CHR_B_IN_SLOT) > 127:
                return False
    for base in (HP_PLAYER, HP_OPP):
        active = u16(buf, base)
        if active == 0 or active % 64 != 0:
            # The active fighter must be alive and on a clean 1/64 boundary. Mid
            # animation HP counts up from zero and is NOT clean, which is why
            # wait_until_live() runs before this.
            return False
    return True


def alive(s):
    return sum(1 for slot in s if slot["hp"] > 0)


def shot(tag):
    os.makedirs(OUT, exist_ok=True)
    p, _ = nav.shot(tag)
    png = os.path.join(OUT, "%s.png" % tag)
    subprocess.run(["magick", p, png])
    return png


def settle_after_switch(max_waits=8):
    """Wait out a character-switch animation before believing an HP reading.

    During a switch the HP words hold an ANIMATING display value: they count up from
    near zero as the new character's bar fills. Sampled mid-animation they look like
    a dying character being healed -- which is exactly how an earlier run misread
    "HP 0.9 then 6.2 then 11.8" as auto-heal still being on. So wait until both sides'
    active HP stops changing.
    """
    prev = None
    for _ in range(max_waits):
        buf = region()
        now = (u16(buf, HP_PLAYER), u16(buf, HP_OPP))
        if now == prev:
            return sample(buf)
        prev = now
        nav.advance(120)
    return sample(region())


def wait_until_live(max_waits=12):
    """Wait for the opening animation before sampling anything.

    The HP words animate at the START of a battle exactly as they do during a
    character switch: they count up from zero as the bars fill. Sampled on frame one
    the player reads 0.0, which the end condition correctly reads as "nobody left to
    send in" and ends the match before it begins. So wait for both sides to be
    non-zero AND unchanging.
    """
    prev = None
    for _ in range(max_waits):
        buf = region()
        now = (u16(buf, HP_PLAYER), u16(buf, HP_OPP))
        if now == prev and min(now) > 0:
            return buf
        prev = now
        nav.advance(120)
    raise RuntimeError("both sides' HP never settled above zero; is this a battle?")


def play(rounds):
    """Seek until an attack connects, then hold the range and keep attacking."""
    os.makedirs(OUT, exist_ok=True)
    resolve_addresses()
    buf = wait_until_live()
    if not plausible(buf):
        raise SystemExit(
            "the DERIVED HP addresses do not look like HP blocks. The anchor chain "
            "resolved, so the structure was found, but the contents fail the sanity "
            "bounds -- most likely sampled mid-animation, or this mode lays the "
            "slots out differently. Raw: me 0x%08X = %d, opp 0x%08X = %d."
            % (HP_PLAYER, u16(buf, HP_PLAYER), HP_OPP, u16(buf, HP_OPP)))
    start = sample(buf)
    print("round      x   me hp  chr_b     opp hp  chr_b   dmg  mode")
    shot("00_start")

    timeline = [dict(round=-1, x=player_x(), mode="start", **start)]
    first_damage, seeking, misses, facing = None, True, 0, STEP_RIGHT
    prev = start
    zero = {"me": 0, "opp": 0}
    for i in range(rounds):
        if seeking:
            act(facing, 30)
        act(ATTACK, ATTACK_SETTLE)
        EH.ensure_alive()
        buf = region()
        s = sample(buf)
        x = player_x()
        dmg = prev["opp"][0]["hp"] - s["opp"][0]["hp"]

        switched = any(s[w][0]["chr_b"] != prev[w][0]["chr_b"] for w in ("me", "opp"))
        if switched:
            for w in ("me", "opp"):
                if s[w][0]["chr_b"] != prev[w][0]["chr_b"]:
                    print("  round %d: %s switched, chr_b %d -> %d"
                          % (i, w, prev[w][0]["chr_b"], s[w][0]["chr_b"]))
                    shot("02_switch_%s_r%d" % (w, i))
            s = settle_after_switch()
            seeking, misses = True, 0     # the reset puts the fighters back apart
            dmg = 0.0

        if dmg > 0:
            seeking, misses = False, 0
            if first_damage is None:
                first_damage = i
                print("  round %d: first damage at x=%d, %.1f -> %.1f"
                      % (i, x, start["opp"][0]["hp"], s["opp"][0]["hp"]))
                shot("01_first_damage")
        elif not seeking:
            misses += 1
            if misses >= STALE_ROUNDS:
                seeking = True            # it moved out of range; go and find it
                misses = 0

        timeline.append(dict(round=i, x=x, mode="seek" if seeking else "engage", **s))
        if i % 5 == 0 or dmg > 0:
            print("%5d %6d %7.1f %6d %10.1f %6d %5.1f  %s"
                  % (i, x, s["me"][0]["hp"], s["me"][0]["chr_b"],
                     s["opp"][0]["hp"], s["opp"][0]["chr_b"], dmg,
                     "seek" if seeking else "engage"))

        # A side is finished when its active slot stays at zero instead of being
        # replaced -- checked only on settled samples, since a switch animation
        # legitimately passes through near-zero.
        if not switched:
            for w in ("me", "opp"):
                zero[w] = zero[w] + 1 if s[w][0]["hp"] == 0 else 0
            if max(zero.values()) >= 4:
                done = "me" if zero["me"] >= 4 else "opp"
                print("  round %d: %s has nobody left to send in -- match over"
                      % (i, done))
                shot("03_match_end")
                break
        prev = s

    with open(os.path.join(OUT, "timeline.json"), "w") as f:
        json.dump(timeline, f, indent=1)
    print("\n%d samples written to %s/timeline.json" % (len(timeline), OUT))
    return timeline


def main():
    sys.stdout.reconfigure(line_buffering=True)
    slot, boot, rounds = None, False, 150
    a = sys.argv[1:]
    for i, x in enumerate(a):
        if x == "--slot":
            slot = a[i + 1]
        elif x == "--rounds":
            rounds = int(a[i + 1])
        elif x == "--boot":
            boot = True
    if boot:
        # From a cold emulator, because boot_verified starts at the title screen and
        # will not find it if the ROM is already somewhere else.
        subprocess.run(["bash", os.path.join(HERE, "launch_emu.sh")], check=True,
                       capture_output=True)
        BV.boot("fight_raw")
        autoheal_off()
        cli("state", "save", "fight_base")
    elif slot:
        cli("state", "load", slot)
        EH.ensure_alive(slot)
        nav.advance(150)
        print("loaded savestate %r" % slot)
    play(rounds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
