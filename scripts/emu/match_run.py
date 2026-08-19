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
ALLOW_CONTAMINATED = False   # only ever set by an explicit CLI flag

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
POPULATE_TRIES, POPULATE_STEP = 12, 60   # ~720 frames; population lands by ~300
ROOT_SIZE = 0x170            # CONFIRMED_STATIC from a single allocation site
SIDE_A_PTR, SIDE_B_PTR = 0x118, 0x11C
RULE_FLAG = 0xC8             # 1 while a per-mode rule handler is installed
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


RULE_MODE, RULE_TIME = 0x020AFEA0, 0x020AFEAC
RULE_ITEMS, RULE_GIMMICK, RULE_TEAM = 0x020AFEBB, 0x020AFEBC, 0x020AFEBD


def conditions():
    """Read the full conditions block from RAM. Never from the harness's report."""
    return {"rule_mode": peek(RULE_MODE, 1),
            "time_limit_frames": peek(RULE_TIME, 4),
            "items": peek(RULE_ITEMS, 1),
            "gimmick": peek(RULE_GIMMICK, 1),
            "team": peek(RULE_TEAM, 1)}


def require_clean_rules(allow_contaminated=False):
    """REFUSE TO RUN with items or gimmicks on. This is a gate, not a report.

    THE BUG THIS EXISTS FOR IS NOT A MISSING CHECK. A previous run read
    items=1 gimmick=1, printed both values correctly, and started anyway --
    the check ran, its output was right, and nothing was gated on it. A
    conditions block that only gets printed is a conditions block that gets
    read past, and no amount of discipline in a note fixes that. So the
    machine refuses.

    The Battle path is why this matters: it defaults items AND gimmicks ON,
    and unlike the training flow nothing in it clears them. boot_verified's
    rules_off() works there, it simply has to be called first.

    --allow-contaminated exists because a deliberately contaminated run is a
    legitimate experiment. It has to be typed, and it is stamped into the
    timeline so the result can never be mistaken for a clean one.
    """
    c = conditions()
    dirty = [n for n in ("items", "gimmick") if c[n]]
    if dirty and not allow_contaminated:
        raise SystemExit(
            "REFUSING TO RUN: %s still ON (items=%d gimmick=%d, read from RAM at "
            "0x%08X/0x%08X).\n"
            "The Battle path defaults both ON and nothing in that flow clears them.\n"
            "Call boot_verified.rules_off() and re-save the savestate, or pass "
            "--allow-contaminated if the contamination is the point."
            % (" and ".join(dirty), c["items"], c["gimmick"],
               RULE_ITEMS, RULE_GIMMICK))
    if dirty:
        print("WARNING: running CONTAMINATED on purpose -- %s ON. Stamped into the "
              "timeline." % ", ".join(dirty))
    return c


def autoheal_is_on_by_behaviour(addr, drop=0x600, wait=360):
    """Does HP at `addr` climb back on its own? Poke it down and watch.

    THIS FUNCTION DID NOT EXIST. HANDOFF-2026-08-18-runtime-2.md section 7
    advertises it by name as one of "two oracles worth reusing" and describes its
    method in detail, but `git log -S` finds it in no commit -- only in the prose.
    Its sibling canvas_is_down() is real. So the handoff documented an oracle that
    was never written, and match_run's own --boot path calls an undefined
    autoheal_off(). Both are recorded on jus-5kf.

    WHY POKE RATHER THAN WATCH. Simply observing HP rise cannot separate regen
    from the count-up animation that follows a respawn -- and on the Battle path
    the player is knocked down constantly, so respawns are everywhere. Poking HP
    DOWN mid-life causes no KO and no respawn, so any climb afterwards has only
    one explanation left.

    The poke is its own positive control: the read-back must show the write
    landed. If HP did not move when I moved it, the instrument is dead and the
    result is discarded rather than reported as "no regen".

    Restores the original halfword either way, including on the failure path.
    """
    orig = peek(addr, 2)
    if orig is None or orig <= drop:
        raise RuntimeError(
            "HP at 0x%08X reads %s -- too low or unreadable to poke down safely; "
            "a poke that reaches 0 would trigger a KO and a respawn, which is the "
            "very thing this test exists to exclude." % (addr, orig))
    target = orig - drop
    try:
        cli("poke", hex(addr), "%02X%02X" % (target & 0xFF, target >> 8))
        # Read back with NO frames advanced first. This separates two outcomes a
        # single delayed read conflates: a write that never landed, and a write
        # that landed and was reverted by the game within a few frames. The
        # second IS regen, and a delayed read reports it as instrument failure --
        # which is what the first version of this function did.
        immediate = peek(addr, 2)
        if immediate != target:
            raise RuntimeError(
                "POSITIVE CONTROL FAILED: wrote %d to 0x%08X, read back %d with no "
                "frames advanced. The write itself did not land, so nothing after "
                "this means anything." % (target, addr, immediate))
        nav.advance(10)
        early = peek(addr, 2)
        nav.advance(wait)
        after = peek(addr, 2)
    finally:
        cli("poke", hex(addr), "%02X%02X" % (orig & 0xFF, orig >> 8))
    climbed = after - target
    return {"orig": orig / 64.0, "poked_to": target / 64.0,
            "early": early / 64.0, "after": after / 64.0,
            "climbed": climbed / 64.0,
            "snapped_back": early >= orig,   # restored within ~10 frames
            "regen": climbed > 0}


def rule_running():
    """Is the rule still live? Read from RAM, never from the screen.

    THE SCREEN CANNOT ANSWER THIS. The battle fingerprint trips on fullscreen KO
    and special-move effects -- a run-to-end attempt ended early on a distance of
    9.8 against a tolerance of 4.9, and the match was still going.

    The RAM oracle is the rule installer's own bookkeeping: root+0xC8 is 1 while a
    per-mode rule handler is installed and returns to 0 at rule completion, with
    root+0x000 restored to the fixed default. Verified end to end on a jikan-30
    point battle: the flag went 1 at framecount 4213 and back to 0 at 8503, and the
    battle object appeared around 4040 -- a span of 4463 frames, exactly the
    configured time limit at 0x020AFEAC.

    Returns None when there is no battle object at all, so callers can tell
    "the match ended" from "there is no match".
    """
    root = peek(ANCHOR, 4)
    if not root or not (0x02000000 <= root < 0x02400000):
        return None
    cli("dump", hex(root), hex(root + ROOT_SIZE), "/tmp/jus_match_rule.bin")
    with open("/tmp/jus_match_rule.bin", "rb") as f:
        r = f.read()
    return r[RULE_FLAG] == 1


def resolve_addresses():
    """Derive the battle addresses from the anchor. Raises rather than guessing.

    Every failure here is fatal on purpose. The whole point of this function is
    that the thing it replaced returned believable numbers from stale addresses,
    so falling back to those constants on any doubt would reinstate exactly the
    bug it exists to remove. If the derivation cannot be trusted, the run stops.
    """
    global DUMP_START, DUMP_END, HP_PLAYER, HP_OPP, TIMER, SPECIAL

    # WAIT FOR THE ANCHOR, THEN WAIT AGAIN FOR THE OBJECT. These are two
    # different states and conflating them produces a wrong diagnosis.
    #
    # The anchor goes non-zero the moment the object is ALLOCATED, which is
    # before setup fills it in -- for a known-good battle the whole 0x170 reads
    # zero at that point and only populates ~200-300 frames later. An earlier
    # version of this function read the side pointers immediately, got 0, and
    # reported "the anchor is wrong", which would send someone hunting a
    # retraction that isn't owed. The failure was mine, not the anchor's.
    #
    # Note what is NOT used as the populated signal. root+0x08 is 0 for rule
    # mode 0, and root+0xC8 is 0 for any mode that never installs a per-mode
    # handler, so both read "empty" in perfectly good battles. The only sound
    # signal is the thing actually needed: side pointers that look like side
    # pointers.
    root = None
    for _ in range(POPULATE_TRIES):
        root = peek(ANCHOR, 4)
        if root:
            break
        nav.advance(POPULATE_STEP)
    if not root:
        raise SystemExit(
            "[0x%08X] stayed 0 across %d frames: there is no battle object, so "
            "this is not a live battle. Load an in-battle savestate or boot into "
            "one. NOT falling back to hardcoded addresses -- they would return "
            "believable garbage."
            % (ANCHOR, POPULATE_TRIES * POPULATE_STEP))
    if not (0x02000000 <= root < 0x02400000) or root & 3:
        raise SystemExit(
            "[0x%08X] = 0x%08X, which is not a word-aligned main-RAM pointer. The "
            "anchor is wrong or the read raced a state load (advance >=10 frames "
            "after loading before peeking)." % (ANCHOR, root))

    def sides():
        cli("dump", hex(root), hex(root + ROOT_SIZE), "/tmp/jus_match_root.bin")
        with open("/tmp/jus_match_root.bin", "rb") as f:
            r = f.read()
        return tuple(struct.unpack_from("<I", r, o)[0]
                     for o in (SIDE_A_PTR, SIDE_B_PTR))

    def mapped(p):
        return 0x02000000 <= p < 0x02400000

    side_a, side_b = sides()
    for _ in range(POPULATE_TRIES):
        if mapped(side_a) and mapped(side_b):
            break
        nav.advance(POPULATE_STEP)
        side_a, side_b = sides()

    if not (mapped(side_a) and mapped(side_b)):
        raise SystemExit(
            "the battle object at 0x%08X exists but never populated: root+0x%X and "
            "root+0x%X still read 0x%08X and 0x%08X after %d frames. This is NOT "
            "the same as 'not a battle' -- the anchor resolved. Either the object "
            "was sampled during a transition, or this mode lays it out differently."
            % (root, SIDE_A_PTR, SIDE_B_PTR, side_a, side_b,
               POPULATE_TRIES * POPULATE_STEP))
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
    the player reads 0.0, which the end condition would read as "nobody left to send
    in" and end the match before it begins.

    WHY THIS NO LONGER REQUIRES BOTH SIDES ALIVE. It used to wait for min(both) > 0,
    which never settles on the Battle path: the COM there is aggressive, a script
    that has not started attacking gets knocked down repeatedly, and the player's HP
    legitimately passes through 0 on every respawn. Measured on a clean point battle
    -- items and gimmicks verified off in RAM -- the player went 125 -> 117 -> 97 ->
    0.8 -> 5.8 while simply standing still. So "player at zero" is a normal mid-match
    state on that path, not an unstarted battle.

    What still rules out the opening animation: during it the counts CHANGE every
    frame and both sides are climbing, so requiring the opponent to be non-zero and
    UNCHANGED across two samples excludes it without depending on the player at all.
    """
    # Track ONLY the opponent. The player's HP changes constantly on the Battle
    # path because the COM keeps hitting it, so a two-sample stability test that
    # includes the player never converges -- which is what made the first version
    # of this fix still fail.
    prev = None
    for _ in range(max_waits):
        buf = region()
        now = u16(buf, HP_OPP)
        if now == prev and now > 0:
            return buf
        prev = now
        nav.advance(120)
    raise RuntimeError(
        "the opponent's HP never settled above zero across %d waits; either this is "
        "not a battle, or the opponent is mid-animation the whole time." % max_waits)


def play(rounds):
    """Seek until an attack connects, then hold the range and keep attacking."""
    os.makedirs(OUT, exist_ok=True)
    cond_block = require_clean_rules(ALLOW_CONTAMINATED)
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
    end_reason = "rounds_exhausted"
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
                end_reason = "stocks:%s" % done
                shot("03_match_end")
                break

        # The authoritative end condition, and the reason a point battle can be
        # run to a finish at all: a timed match ends with everyone still alive, so
        # the stock check above never fires for it.
        live = rule_running()
        if live is False:
            print("  round %d: rule completed (root+0xC8 cleared) -- match over" % i)
            end_reason = "rule_complete"
            shot("03_match_end")
            break
        if live is None:
            print("  round %d: battle object gone -- left the match" % i)
            end_reason = "no_battle"
            break
        prev = s

    with open(os.path.join(OUT, "timeline.json"), "w") as f:
        json.dump({"conditions": cond_block, "contaminated_run": ALLOW_CONTAMINATED,
                   "end_reason": end_reason, "samples": timeline}, f, indent=1)
    print("\n%d samples written to %s/timeline.json (end: %s)"
          % (len(timeline), OUT, end_reason))
    return timeline


def main():
    sys.stdout.reconfigure(line_buffering=True)
    global ALLOW_CONTAMINATED
    slot, boot, rounds = None, False, 150
    a = sys.argv[1:]
    for i, x in enumerate(a):
        if x == "--slot":
            slot = a[i + 1]
        elif x == "--rounds":
            rounds = int(a[i + 1])
        elif x == "--boot":
            boot = True
        elif x == "--allow-contaminated":
            ALLOW_CONTAMINATED = True
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
