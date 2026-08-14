# melonDS Agent Control Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a Claude session drive melonDS unattended (inputs, savestates, memory watches, screenshots) via a Lua bridge + Python CLI, per `docs/superpowers/specs/2026-08-14-melonds-agent-control-design.md`.

**Architecture:** A patched build of NPO-197's melonDS-lua fork runs `agent_bridge.lua`, which executes frame-accurate input plans and logs per-frame memory watches. A Python CLI (`jusemu.py`) talks to it through rename-published files in `/tmp/jus_emu/`. The existing GDB stub stays as a second, sequential control plane.

**Tech Stack:** Lua 5.4 (inside melonDS), Python 3 stdlib only (`unittest`, no pip deps), CMake/clang for the emulator build, `screencapture` for screenshots.

**Key facts verified from fork source (2026-08-14, do not rediscover):**
- `memory.read_u8/read_u16_le/read_u32_le(addr, domain)` and `memory.read_bytes_as_array(addr, len, domain)` exist. Pass domain `"ARM9 System Bus"` to use full CPU-visible addresses like `0x021DF1D5` (it routes through BizHawk-derived safe-peek). The default `"Main RAM"` domain is *offset-based* (subtract `0x02000000`). **Never call `memory.usememorydomain`** — it stores a pointer to a stack local (fork bug); always pass the domain string per call.
- `savestate.save(path)` / `savestate.load(path)` are **asynchronous**: they emit Qt signals; the actual save/load happens later on another thread. The bridge must detect settling (Task 7 spike S4).
- `_Update()` is a global Lua function the fork calls once per frame while the script runs. `emu.framecount()` returns the emulated frame counter.
- `joypad` is read-only (`joypad.get`); button injection does not exist and is added by our patch (Task 8).
- Button name order used by `input.getjoy`: `A,B,Select,Start,Right,Left,Up,Down,R,L,X,Y`.

**Human checkpoints (unavoidable, flag to user when reached):**
- Task 5: ROM/BIOS paths on this machine; confirming the emulator window opens.
- Task 10: navigating once to a free-battle training scenario so the bridge can save the bootstrap savestate.

---

### Task 1: Address book (`jus_addresses.py`)

Single source of truth for known addresses and pointer chains, ported from `scripts/gdb/README.md`.

**Files:**
- Create: `scripts/emu/jus_addresses.py`
- Test: `scripts/emu/tests/test_jus_addresses.py`
- Create: `scripts/emu/tests/__init__.py` (empty)

- [ ] **Step 1: Write the failing test**

```python
# scripts/emu/tests/test_jus_addresses.py
import unittest
from jus_addresses import ADDRESSES, CHAINS, WATCH_PRESETS, resolve_watch


class TestAddresses(unittest.TestCase):
    def test_known_hp_address(self):
        self.assertEqual(ADDRESSES["hp_player_active"], 0x021DF1D5)

    def test_player_chain(self):
        self.assertEqual(CHAINS["player"], [0x023D2A74, 0x10])

    def test_opponent_chain(self):
        self.assertEqual(CHAINS["opponent"], [0x023D2A74, 0x00, 0x10])

    def test_preset_expands_to_specs(self):
        specs = resolve_watch("hp_all")
        names = [s["name"] for s in specs]
        self.assertIn("hp_all.p1", names)
        spec = next(s for s in specs if s["name"] == "hp_all.p1")
        self.assertEqual(spec["addr"], 0x021DF1D5)
        self.assertEqual(spec["len"], 1)

    def test_struct_preset_uses_chain(self):
        specs = resolve_watch("player_struct")
        spec = next(s for s in specs if s["name"] == "player_struct.0x78")
        self.assertEqual(spec["chain"], [0x023D2A74, 0x10])
        self.assertEqual(spec["offset"], 0x78)

    def test_unknown_preset_raises(self):
        with self.assertRaises(KeyError):
            resolve_watch("nonsense")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts/emu && python3 -m unittest tests.test_jus_addresses -v`
Expected: FAIL / ERROR with `ModuleNotFoundError: No module named 'jus_addresses'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/emu/jus_addresses.py
"""Known JUS memory addresses and pointer chains.

Ported from scripts/gdb/README.md (the GDB watcher is the historical
source; this file is the go-forward single source of truth).
HP values are stored at 1/4 scale (160 displayed = 40 stored).
"""

ADDRESSES = {
    # Battle state
    "battle_timer": 0x021DEA71,
    "special_meter_1": 0x021DF731,
    # HP, your side (active + deck slots, 0x50 apart)
    "hp_player_active": 0x021DF1D5,
    "hp_player_deck1": 0x021DF225,
    "hp_player_deck2": 0x021DF275,
    "hp_player_deck3": 0x021DF2C5,
    # HP, opponent side (+0x61C from yours)
    "hp_opp_active": 0x021DF7F1,
    "hp_opp_deck1": 0x021DF841,
    "hp_opp_deck2": 0x021DF891,
    "hp_opp_deck3": 0x021DF8E1,
    # Deck builder
    "deck_state_flag": 0x020A0C98,
    "deck_leader_bool": 0x020A2289,
    "deck_active_slot": 0x020AFEB4,
    # Code
    "fn_health_calc": 0x020784FC,
}

# Pointer chains: [base, off1, off2...] means read u32 at base, add off1,
# read u32, add off2... final value is the struct base address.
# Verified for offline/training mode (scripts/gdb/README.md, 2026-02-03).
CHAINS = {
    "player": [0x023D2A74, 0x10],
    "opponent": [0x023D2A74, 0x00, 0x10],
}

# Character-struct offsets worth watching (scripts/gdb/README.md).
_STRUCT_OFFSETS = {
    "0x78": (0x78, 1),   # ground/air state (0x22 ground, 0xC0 hitstun)
    "0x88": (0x88, 1),   # positive status id
    "0xA0": (0xA0, 2),   # negative status flags / timer pair 2
    "0x98": (0x98, 2),   # timer pair 1
    "0xD9": (0xD9, 1),   # jump counter
    "0x102": (0x102, 2), # defense timer
}

WATCH_PRESETS = {
    "hp_all": [
        {"name": "hp_all.p1", "addr": ADDRESSES["hp_player_active"], "len": 1},
        {"name": "hp_all.o1", "addr": ADDRESSES["hp_opp_active"], "len": 1},
    ],
    "player_struct": [
        {"name": "player_struct.%s" % k, "chain": CHAINS["player"],
         "offset": off, "len": ln}
        for k, (off, ln) in _STRUCT_OFFSETS.items()
    ],
    "opponent_struct": [
        {"name": "opponent_struct.%s" % k, "chain": CHAINS["opponent"],
         "offset": off, "len": ln}
        for k, (off, ln) in _STRUCT_OFFSETS.items()
    ],
    "battle": [
        {"name": "battle.timer", "addr": ADDRESSES["battle_timer"], "len": 1},
        {"name": "battle.special1", "addr": ADDRESSES["special_meter_1"], "len": 1},
    ],
}


def resolve_watch(name):
    """Expand a preset name into a list of concrete watch specs.

    Raises KeyError for unknown names.
    """
    return [dict(s) for s in WATCH_PRESETS[name]]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts/emu && python3 -m unittest tests.test_jus_addresses -v`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/jus_addresses.py scripts/emu/tests/
git commit -m "feat(emu): address book with watch presets and pointer chains"
```

---

### Task 2: Plan validation (`jus_plan.py`)

Validates `plan.json` per spec §5, converts it to the Lua-literal form the bridge consumes.

**Files:**
- Create: `scripts/emu/jus_plan.py`
- Test: `scripts/emu/tests/test_jus_plan.py`

- [ ] **Step 1: Write the failing test**

```python
# scripts/emu/tests/test_jus_plan.py
import unittest
from jus_plan import validate_plan, plan_to_lua, PlanError

GOOD = {
    "name": "walk_and_b",
    "load_state": "training",
    "segments": [
        {"from": 0, "to": 20, "buttons": ["RIGHT"]},
        {"from": 21, "to": 23, "buttons": ["B"]},
    ],
    "tail_frames": 120,
    "watches": ["hp_all"],
}


class TestValidate(unittest.TestCase):
    def test_good_plan_passes(self):
        p = validate_plan(GOOD)
        self.assertEqual(p["total_frames"], 24 + 120)

    def test_overlapping_segments_rejected(self):
        bad = dict(GOOD, segments=[
            {"from": 0, "to": 10, "buttons": ["A"]},
            {"from": 10, "to": 20, "buttons": ["B"]},
        ])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_reversed_range_rejected(self):
        bad = dict(GOOD, segments=[{"from": 5, "to": 3, "buttons": ["A"]}])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_bad_button_rejected(self):
        bad = dict(GOOD, segments=[{"from": 0, "to": 1, "buttons": ["Z"]}])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_opposite_dpad_rejected(self):
        bad = dict(GOOD, segments=[
            {"from": 0, "to": 1, "buttons": ["LEFT", "RIGHT"]}])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_touch_segment_ok(self):
        p = dict(GOOD, segments=[
            {"from": 0, "to": 5, "touch": {"x": 128, "y": 96}}])
        validate_plan(p)  # should not raise

    def test_too_many_watches_rejected(self):
        bad = dict(GOOD, watches=[
            {"name": "w%d" % i, "addr": 0x02000000 + i, "len": 1}
            for i in range(40)])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_watch_byte_budget_rejected(self):
        bad = dict(GOOD, watches=[
            {"name": "big", "addr": 0x02000000, "len": 600}])
        with self.assertRaises(PlanError):
            validate_plan(bad)


class TestLuaEmit(unittest.TestCase):
    def test_emits_loadable_lua_table(self):
        lua = plan_to_lua(validate_plan(GOOD))
        self.assertTrue(lua.startswith("return {"))
        self.assertIn('name = "walk_and_b"', lua)
        self.assertIn("Right", lua)  # RIGHT normalized to fork's casing

    def test_watch_preset_expanded(self):
        lua = plan_to_lua(validate_plan(GOOD))
        self.assertIn("hp_all.p1", lua)
        self.assertIn("0x21DF1D5".lower(), lua.lower())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts/emu && python3 -m unittest tests.test_jus_plan -v`
Expected: ERROR, `No module named 'jus_plan'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/emu/jus_plan.py
"""Plan validation and conversion to the Lua literal the bridge loads.

Spec: docs/superpowers/specs/2026-08-14-melonds-agent-control-design.md §5.
Limits: <=32 watches, <=512 watched bytes/frame, chain depth <=3.
"""
from jus_addresses import resolve_watch

# CLI accepts uppercase; fork's joypad table uses these exact casings.
BUTTONS = {
    "A": "A", "B": "B", "SELECT": "Select", "START": "Start",
    "RIGHT": "Right", "LEFT": "Left", "UP": "Up", "DOWN": "Down",
    "R": "R", "L": "L", "X": "X", "Y": "Y",
}
MAX_WATCHES = 32
MAX_WATCH_BYTES = 512
MAX_CHAIN_DEPTH = 3
MAIN_RAM = (0x02000000, 0x02400000)


class PlanError(ValueError):
    pass


def _check_watch(spec):
    if "chain" in spec:
        if len(spec["chain"]) - 1 > MAX_CHAIN_DEPTH:
            raise PlanError("chain too deep: %s" % spec["name"])
    elif "addr" in spec:
        if not (MAIN_RAM[0] <= spec["addr"] < MAIN_RAM[1]):
            raise PlanError("addr outside main RAM: %s" % spec["name"])
    else:
        raise PlanError("watch needs addr or chain: %s" % spec)
    if not (1 <= spec.get("len", 0) <= MAX_WATCH_BYTES):
        raise PlanError("bad len: %s" % spec["name"])


def validate_plan(plan):
    """Return a normalized copy of the plan, or raise PlanError."""
    out = {"name": plan["name"], "load_state": plan.get("load_state"),
           "tail_frames": int(plan.get("tail_frames", 0))}

    segs, last_end = [], -1
    for seg in sorted(plan["segments"], key=lambda s: s["from"]):
        f, t = int(seg["from"]), int(seg["to"])
        if t < f:
            raise PlanError("segment to < from: %s" % seg)
        if f <= last_end:
            raise PlanError("segments overlap at frame %d" % f)
        last_end = t
        norm = {"from": f, "to": t}
        if "buttons" in seg:
            btns = []
            for b in seg["buttons"]:
                if b.upper() not in BUTTONS:
                    raise PlanError("unknown button %r" % b)
                btns.append(BUTTONS[b.upper()])
            if ("Left" in btns and "Right" in btns) or \
               ("Up" in btns and "Down" in btns):
                raise PlanError("contradictory d-pad in segment %s" % seg)
            norm["buttons"] = btns
        if "touch" in seg:
            norm["touch"] = {"x": int(seg["touch"]["x"]),
                             "y": int(seg["touch"]["y"])}
        if "buttons" not in norm and "touch" not in norm:
            raise PlanError("segment has neither buttons nor touch: %s" % seg)
        segs.append(norm)
    if not segs:
        raise PlanError("plan has no segments")
    out["segments"] = segs
    out["total_frames"] = last_end + 1 + out["tail_frames"]

    watches = []
    for w in plan.get("watches", []):
        watches.extend(resolve_watch(w) if isinstance(w, str) else [dict(w)])
    if len(watches) > MAX_WATCHES:
        raise PlanError("too many watches (%d > %d)" % (len(watches), MAX_WATCHES))
    for w in watches:
        _check_watch(w)
    if sum(w["len"] for w in watches) > MAX_WATCH_BYTES:
        raise PlanError("watch byte budget exceeded")
    out["watches"] = watches
    return out


def _lua(v):
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return "0x%X" % v if v > 255 else str(v)
    if isinstance(v, str):
        return '"%s"' % v.replace("\\", "\\\\").replace('"', '\\"')
    if isinstance(v, list):
        return "{" + ", ".join(_lua(x) for x in v) + "}"
    if isinstance(v, dict):
        parts = []
        for k, val in v.items():
            if val is None:
                continue
            parts.append('["%s"] = %s' % (k, _lua(val)))
        return "{" + ", ".join(parts) + "}"
    raise TypeError(type(v))


def plan_to_lua(normalized):
    """Emit the validated plan as a Lua literal chunk ('return {...}')."""
    body = _lua(normalized)
    # keep name readable for humans debugging the file
    return "return " + body.replace('["name"] =', 'name =', 1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts/emu && python3 -m unittest tests.test_jus_plan -v`
Expected: all 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/jus_plan.py scripts/emu/tests/test_jus_plan.py
git commit -m "feat(emu): plan validation and Lua-literal emission"
```

---

### Task 3: IPC layer (`jus_ipc.py`)

File-based protocol: epochs, command ids, rename-publication, heartbeat interpretation. Pure functions + a small client class; fully unit-testable with `tmp` dirs.

**Files:**
- Create: `scripts/emu/jus_ipc.py`
- Test: `scripts/emu/tests/test_jus_ipc.py`

- [ ] **Step 1: Write the failing test**

```python
# scripts/emu/tests/test_jus_ipc.py
import json, os, tempfile, time, unittest
from jus_ipc import IpcClient, BridgeState, interpret_heartbeat


class TestHeartbeat(unittest.TestCase):
    def hb(self, age_s, state="idle", pid_alive=True):
        return interpret_heartbeat(
            {"session": "abc", "framecount": 100, "wallclock": time.time() - age_s,
             "state": state},
            emulator_alive=pid_alive)

    def test_fresh_idle(self):
        self.assertEqual(self.hb(0.5), BridgeState.IDLE)

    def test_stale_but_process_alive_is_paused(self):
        self.assertEqual(self.hb(30, pid_alive=True), BridgeState.PAUSED)

    def test_stale_and_dead_process_is_dead(self):
        self.assertEqual(self.hb(30, pid_alive=False), BridgeState.DEAD)

    def test_running_plan(self):
        self.assertEqual(self.hb(0.5, state="plan_running"),
                         BridgeState.PLAN_RUNNING)


class TestClient(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        with open(os.path.join(self.dir, "heartbeat.json"), "w") as f:
            json.dump({"session": "epoch1", "framecount": 1,
                       "wallclock": time.time(), "state": "idle"}, f)
        self.c = IpcClient(self.dir)

    def test_adopts_epoch_from_heartbeat(self):
        self.assertEqual(self.c.epoch, "epoch1")

    def test_command_ids_monotonic(self):
        a, b = self.c.next_id(), self.c.next_id()
        self.assertGreater(b, a)

    def test_publish_is_rename_based(self):
        cid = self.c.publish_command("status", {})
        inbox = os.path.join(self.dir, "cmd", "inbox.lua")
        self.assertTrue(os.path.exists(inbox))
        content = open(inbox).read()
        self.assertIn('"status"', content)
        self.assertIn("epoch1", content)
        self.assertIn(str(cid), content)
        # no temp files left behind
        tmps = [f for f in os.listdir(os.path.join(self.dir, "cmd"))
                if f != "inbox.lua"]
        self.assertEqual(tmps, [])

    def test_refuses_second_unacked_command(self):
        self.c.publish_command("status", {})
        with self.assertRaises(RuntimeError):
            self.c.publish_command("status", {})

    def test_wait_ack_reads_and_clears(self):
        cid = self.c.publish_command("status", {})
        ackdir = os.path.join(self.dir, "ack")
        with open(os.path.join(ackdir, "tmp"), "w") as f:
            json.dump({"id": cid, "ok": True, "result": {"state": "idle"}}, f)
        os.rename(os.path.join(ackdir, "tmp"),
                  os.path.join(ackdir, "%d.json" % cid))
        ack = self.c.wait_ack(cid, timeout=2)
        self.assertTrue(ack["ok"])
        self.assertFalse(os.path.exists(
            os.path.join(self.dir, "cmd", "inbox.lua")))

    def test_wait_ack_timeout_is_indeterminate(self):
        cid = self.c.publish_command("status", {})
        with self.assertRaises(TimeoutError):
            self.c.wait_ack(cid, timeout=0.2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts/emu && python3 -m unittest tests.test_jus_ipc -v`
Expected: ERROR, `No module named 'jus_ipc'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/emu/jus_ipc.py
"""File-based IPC with the agent_bridge.lua running inside melonDS.

Layout under the IPC dir (default /tmp/jus_emu):
  heartbeat.json      bridge-owned; {session, framecount, wallclock, state}
  cmd/inbox.lua       client-owned; one pending command as a Lua literal
  ack/<id>.json       bridge-owned; one ack per command id
  stop.flag           client-owned sentinel; bridge aborts active plan
  runs/, states/      run artifacts and savestates

Commands are published as Lua literals so the bridge needs no JSON
parser; acks/heartbeats come back as JSON written by a tiny Lua encoder.
Delivery is at-most-once: on timeout the command's fate is unknown and
the caller must check status before reissuing (spec §3).
"""
import enum, json, os, subprocess, time

HEARTBEAT_STALE_S = 5.0
DEFAULT_DIR = os.environ.get("JUS_EMU_DIR", "/tmp/jus_emu")


class BridgeState(enum.Enum):
    IDLE = "idle"
    PLAN_RUNNING = "plan_running"
    FLUSHING = "flushing"
    PAUSED = "paused"    # heartbeat stale, emulator process alive (GDB stop?)
    DEAD = "dead"


def emulator_process_alive():
    out = subprocess.run(["pgrep", "-if", "melonDS"],
                         capture_output=True, text=True)
    return out.returncode == 0


def interpret_heartbeat(hb, emulator_alive):
    age = time.time() - hb["wallclock"]
    if age > HEARTBEAT_STALE_S:
        return BridgeState.PAUSED if emulator_alive else BridgeState.DEAD
    return {"idle": BridgeState.IDLE,
            "plan_running": BridgeState.PLAN_RUNNING,
            "flushing": BridgeState.FLUSHING}.get(hb["state"], BridgeState.DEAD)


def _lua_literal(value):
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return '"%s"' % value.replace("\\", "\\\\").replace('"', '\\"')
    if isinstance(value, list):
        return "{" + ", ".join(_lua_literal(v) for v in value) + "}"
    if isinstance(value, dict):
        return "{" + ", ".join('["%s"] = %s' % (k, _lua_literal(v))
                               for k, v in value.items()) + "}"
    raise TypeError(type(value))


class IpcClient:
    def __init__(self, ipc_dir=DEFAULT_DIR):
        self.dir = ipc_dir
        for sub in ("cmd", "ack", "runs", "states"):
            os.makedirs(os.path.join(self.dir, sub), exist_ok=True)
        self.epoch = self._read_heartbeat()["session"]
        self._id = int(time.time() * 1000) % 10**9

    def _read_heartbeat(self):
        with open(os.path.join(self.dir, "heartbeat.json")) as f:
            return json.load(f)

    def state(self):
        try:
            hb = self._read_heartbeat()
        except (OSError, ValueError):
            return BridgeState.DEAD, None
        return interpret_heartbeat(hb, emulator_process_alive()), hb

    def next_id(self):
        self._id += 1
        return self._id

    def publish_command(self, op, args):
        inbox = os.path.join(self.dir, "cmd", "inbox.lua")
        if os.path.exists(inbox):
            raise RuntimeError(
                "unacked command already pending; run `jusemu status` "
                "and clear %s if it is stale" % inbox)
        cid = self.next_id()
        body = "return " + _lua_literal(
            {"epoch": self.epoch, "id": cid, "op": op, "args": args})
        tmp = inbox + ".tmp"
        with open(tmp, "w") as f:
            f.write(body)
        os.rename(tmp, inbox)
        return cid

    def wait_ack(self, cid, timeout=10.0):
        ack_path = os.path.join(self.dir, "ack", "%d.json" % cid)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(ack_path):
                with open(ack_path) as f:
                    ack = json.load(f)
                os.remove(ack_path)
                inbox = os.path.join(self.dir, "cmd", "inbox.lua")
                if os.path.exists(inbox):
                    os.remove(inbox)  # bridge consumed logically; clear it
                return ack
            time.sleep(0.05)
        raise TimeoutError(
            "no ack for command %d after %.1fs — INDETERMINATE: the bridge "
            "may or may not have executed it. Check `jusemu status`." %
            (cid, timeout))

    def request_stop(self):
        flag = os.path.join(self.dir, "stop.flag")
        with open(flag + ".tmp", "w") as f:
            f.write("stop")
        os.rename(flag + ".tmp", flag)
```

Note for the implementer: the bridge (Task 9) deletes `cmd/inbox.lua` itself after reading it; the client-side delete in `wait_ack` only covers the race where the ack lands first. Both deletes are idempotent.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts/emu && python3 -m unittest tests.test_jus_ipc -v`
Expected: all 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/jus_ipc.py scripts/emu/tests/test_jus_ipc.py
git commit -m "feat(emu): file IPC client with epochs, acks, heartbeat states"
```

---

### Task 4: CLI (`jusemu.py`)

Argparse front end wiring Tasks 1–3 together. Emulator-dependent behavior is exercised later (Task 9+); here we test argument handling and run-directory creation.

**Files:**
- Create: `scripts/emu/jusemu.py`
- Test: `scripts/emu/tests/test_jusemu.py`

- [ ] **Step 1: Write the failing test**

```python
# scripts/emu/tests/test_jusemu.py
import json, os, tempfile, time, unittest
import jusemu


class TestCli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        with open(os.path.join(self.dir, "heartbeat.json"), "w") as f:
            json.dump({"session": "e1", "framecount": 5,
                       "wallclock": time.time(), "state": "idle"}, f)

    def test_build_parser_has_all_subcommands(self):
        p = jusemu.build_parser()
        for cmd in ["run", "peek", "poke", "state", "dump", "watch",
                    "screenshot", "status", "stop"]:
            args = p.parse_args([cmd] + jusemu.SMOKE_ARGS[cmd])
            self.assertEqual(args.command, cmd)

    def test_peek_builds_command(self):
        op, args = jusemu.build_peek(addr="0x021DF1D5", length=1, chain=None)
        self.assertEqual(op, "peek")
        self.assertEqual(args["addr"], 0x021DF1D5)

    def test_peek_with_chain(self):
        op, args = jusemu.build_peek(addr="0x78", length=2, chain="player")
        self.assertEqual(args["chain"], [0x023D2A74, 0x10])
        self.assertEqual(args["offset"], 0x78)

    def test_run_timeout_scales_with_frames(self):
        self.assertGreater(jusemu.run_timeout(total_frames=3600),
                           jusemu.run_timeout(total_frames=60))

    def test_make_run_dir_writes_meta(self):
        plan = {"name": "t", "total_frames": 10, "segments": [],
                "watches": [], "tail_frames": 0, "load_state": None}
        rd = jusemu.make_run_dir(self.dir, plan, cmd_id=7, epoch="e1")
        meta = json.load(open(os.path.join(rd, "meta.json")))
        self.assertEqual(meta["epoch"], "e1")
        self.assertIn("plan_sha256", meta)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts/emu && python3 -m unittest tests.test_jusemu -v`
Expected: ERROR, `No module named 'jusemu'`

- [ ] **Step 3: Write the implementation**

```python
# scripts/emu/jusemu.py
"""Claude-facing CLI for driving melonDS via agent_bridge.lua.

Usage examples:
  python3 jusemu.py status
  python3 jusemu.py peek 0x021DF1D5 1
  python3 jusemu.py peek 0x78 2 --chain player
  python3 jusemu.py state save training
  python3 jusemu.py run plans/example_walk_and_b.json
  python3 jusemu.py screenshot /tmp/shot.png
"""
import argparse, hashlib, json, os, subprocess, sys, time

from jus_addresses import CHAINS
from jus_ipc import IpcClient, BridgeState, DEFAULT_DIR
from jus_plan import validate_plan, plan_to_lua

# minimal valid argv per subcommand, used by tests and --help sanity
SMOKE_ARGS = {
    "run": ["p.json"], "peek": ["0x02000000", "1"],
    "poke": ["0x02000000", "ff"], "state": ["save", "s"],
    "dump": ["0x02000000", "0x02000010", "out.bin"],
    "watch": ["set", "w.json"], "screenshot": ["out.png"],
    "status": [], "stop": [],
}


def build_parser():
    p = argparse.ArgumentParser(prog="jusemu")
    p.add_argument("--ipc-dir", default=DEFAULT_DIR)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run"); r.add_argument("plan")
    pk = sub.add_parser("peek")
    pk.add_argument("addr"); pk.add_argument("length", type=int)
    pk.add_argument("--chain", choices=sorted(CHAINS))
    po = sub.add_parser("poke")
    po.add_argument("addr"); po.add_argument("hexbytes")
    st = sub.add_parser("state")
    st.add_argument("action", choices=["save", "load"])
    st.add_argument("slot")
    d = sub.add_parser("dump")
    d.add_argument("start"); d.add_argument("end"); d.add_argument("outfile")
    w = sub.add_parser("watch")
    w.add_argument("action", choices=["set"]); w.add_argument("spec")
    sc = sub.add_parser("screenshot"); sc.add_argument("outfile")
    sub.add_parser("status")
    sub.add_parser("stop")
    return p


def build_peek(addr, length, chain):
    a = int(addr, 0)
    if chain:
        return "peek", {"chain": CHAINS[chain], "offset": a, "len": length}
    return "peek", {"addr": a, "len": length}


def run_timeout(total_frames):
    # plans run at emulated speed; assume >=30fps effective + slack
    return total_frames / 30.0 + 15.0


def make_run_dir(ipc_dir, plan, cmd_id, epoch):
    rd = os.path.join(ipc_dir, "runs", "%s-%d" % (plan["name"], cmd_id))
    os.makedirs(rd, exist_ok=True)
    blob = json.dumps(plan, sort_keys=True).encode()
    with open(os.path.join(rd, "plan.json"), "w") as f:
        json.dump(plan, f, indent=1)
    meta = {"epoch": epoch, "cmd_id": cmd_id, "created": time.time(),
            "plan_sha256": hashlib.sha256(blob).hexdigest()}
    for extra in ("build_info.json",):  # written by build script if present
        src = os.path.join(os.path.dirname(__file__), extra)
        if os.path.exists(src):
            meta["build"] = json.load(open(src))
    with open(os.path.join(rd, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return rd


def do_screenshot(outfile):
    # find the melonDS window id via CoreGraphics through osascript-free route
    script = (
        'tell application "System Events" to tell (first process whose '
        'name contains "melonDS") to get id of first window')
    win = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True)
    if win.returncode != 0:
        # fallback: interactive window picker
        return subprocess.run(["screencapture", "-w", outfile]).returncode
    return subprocess.run(
        ["screencapture", "-l", win.stdout.strip(), outfile]).returncode


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "screenshot":
        sys.exit(do_screenshot(args.outfile))

    client = IpcClient(args.ipc_dir)

    if args.command == "status":
        state, hb = client.state()
        print(json.dumps({"state": state.value, "heartbeat": hb}, indent=1))
        return
    if args.command == "stop":
        client.request_stop()
        print("stop requested")
        return

    if args.command == "run":
        plan = validate_plan(json.load(open(args.plan)))
        cid = client.next_id()  # reserve id for the run dir name
        rd = make_run_dir(args.ipc_dir, plan, cid, client.epoch)
        lua_path = os.path.join(rd, "plan.lua")
        with open(lua_path, "w") as f:
            f.write(plan_to_lua(plan))
        cid = client.publish_command(
            "run_plan", {"plan_path": lua_path, "run_dir": rd})
        try:
            ack = client.wait_ack(cid, timeout=run_timeout(plan["total_frames"]))
        except TimeoutError:
            state, _ = client.state()
            if state == BridgeState.PAUSED:
                print("emulator paused (GDB?) — plan frozen, not failed. "
                      "Resume the emulator and re-check `jusemu status`.")
                return
            raise
        print(json.dumps(ack, indent=1))
        print("log: %s" % os.path.join(rd, "log.jsonl"))
        return

    if args.command == "peek":
        op, a = build_peek(args.addr, args.length, args.chain)
    elif args.command == "poke":
        op, a = "poke", {"addr": int(args.addr, 0),
                         "bytes": [int(args.hexbytes[i:i+2], 16)
                                   for i in range(0, len(args.hexbytes), 2)]}
    elif args.command == "state":
        op, a = "state_" + args.action, {"slot": args.slot}
    elif args.command == "dump":
        op, a = "dump", {"start": int(args.start, 0), "end": int(args.end, 0),
                         "outfile": os.path.abspath(args.outfile)}
    elif args.command == "watch":
        op, a = "set_watches", {"specs": json.load(open(args.spec))}
    cid = client.publish_command(op, a)
    print(json.dumps(client.wait_ack(cid), indent=1))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd scripts/emu && python3 -m unittest discover tests -v`
Expected: all tests from Tasks 1–4 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/jusemu.py scripts/emu/tests/test_jusemu.py
git commit -m "feat(emu): jusemu CLI wiring plans, IPC, and screenshots"
```

---

### Task 5: Build the fork (`build_melonds_lua.sh`) — human checkpoint

**Files:**
- Create: `scripts/emu/build_melonds_lua.sh`
- Create: `scripts/emu/README.md` (skeleton; grows in later tasks)

- [ ] **Step 1: Write the build script**

```bash
#!/usr/bin/env bash
# scripts/emu/build_melonds_lua.sh
# Builds the pinned melonDS-lua fork with GDB stub, applies our patches.
set -euo pipefail

REPO_URL="https://github.com/NPO-197/melonDS-lua"
# PINNED_COMMIT is set in step 3 after the first successful build.
PINNED_COMMIT="${PINNED_COMMIT:-master}"
SRC_DIR="${SRC_DIR:-$HOME/src/melonDS-lua}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

brew list lua@5.4 >/dev/null 2>&1 || brew install lua@5.4
brew list cmake  >/dev/null 2>&1 || brew install cmake
# Qt6 + SDL2 per upstream BUILD.md
for pkg in qt@6 sdl2 libarchive libslirp zstd; do
  brew list "$pkg" >/dev/null 2>&1 || brew install "$pkg"
done

if [ ! -d "$SRC_DIR" ]; then git clone "$REPO_URL" "$SRC_DIR"; fi
cd "$SRC_DIR"
git fetch --all
git checkout "$PINNED_COMMIT"
git reset --hard && git clean -fd

for p in "$SCRIPT_DIR"/patches/*.patch; do
  [ -e "$p" ] || continue
  echo "Applying $p"
  git apply "$p"
done

cmake -B build -DENABLE_GDB_STUB=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(sysctl -n hw.ncpu)"

COMMIT=$(git rev-parse HEAD)
PATCHES=$(cd "$SCRIPT_DIR/patches" 2>/dev/null && shasum -a 256 *.patch 2>/dev/null || echo none)
cat > "$SCRIPT_DIR/build_info.json" <<EOF
{"fork_commit": "$COMMIT", "patches": "$(echo "$PATCHES" | tr '\n' ';')",
 "built_at": "$(date -u +%FT%TZ)"}
EOF
echo "Built: $SRC_DIR/build/melonDS.app (commit $COMMIT)"
```

- [ ] **Step 2: Run the build**

Run: `bash scripts/emu/build_melonds_lua.sh`
Expected: successful build ending in `Built: .../melonDS.app`. If CMake or compile errors occur, this is the spec's M1 timebox: spend up to a day; document each fix in `scripts/emu/README.md`. If truly blocked, STOP and consult the user about the keystroke-automation fallback.

- [ ] **Step 3: Pin the commit**

Edit `build_melonds_lua.sh`: replace `PINNED_COMMIT="${PINNED_COMMIT:-master}"` with the concrete hash printed by the build (e.g. `PINNED_COMMIT="${PINNED_COMMIT:-<hash>}"`).

- [ ] **Step 4: Human checkpoint — boot the game**

Ask the user to: (1) open the built melonDS.app, (2) point it at BIOS/firmware/ROM (paths they already use for stock melonDS), (3) enable the GDB stub (Config → Emu Settings → Devtools, ARM9 port 3333), (4) load the JUS ROM, (5) open the Lua console (Tools menu) and confirm it exists.
Record ROM/BIOS/firmware SHA-256 hashes and file paths in `scripts/emu/README.md`.

- [ ] **Step 5: Write README skeleton and commit**

`scripts/emu/README.md` must contain: purpose (one paragraph), build instructions (`bash build_melonds_lua.sh`), the pinned commit, hash table (ROM/BIOS/firmware), an empty "Verified behavior (spike findings)" section, and an empty "Combined Lua+GDB workflow" section.

```bash
git add scripts/emu/build_melonds_lua.sh scripts/emu/README.md scripts/emu/build_info.json
git commit -m "feat(emu): pinned melonDS-lua build script + README skeleton"
```

---

### Task 6: Spike S1–S2 (callback thread + I/O safety)

**Files:**
- Create: `scripts/emu/spike/s1_s2_update_probe.lua`
- Modify: `scripts/emu/README.md` (Verified behavior section)

- [ ] **Step 1: Write the probe script**

```lua
-- scripts/emu/spike/s1_s2_update_probe.lua
-- S1: does _Update() fire per frame? during pause? during GDB stop?
-- S2: is synchronous file I/O safe and fast enough from the callback?
local count = 0
local t0 = os.clock()
local worst = 0

function _Update()
    count = count + 1
    local a = os.clock()
    -- representative I/O: rewrite a small file via rename (heartbeat-like)
    local f = io.open("/tmp/jus_emu_spike.tmp", "w")
    f:write(string.format('{"count":%d,"frame":%d,"os_time":%d}',
            count, emu.framecount(), os.time()))
    f:close()
    os.rename("/tmp/jus_emu_spike.tmp", "/tmp/jus_emu_spike.json")
    -- representative memory load: 512 bytes over the ARM9 bus
    local bytes = memory.read_bytes_as_array(0x021DF000, 512, "ARM9 System Bus")
    local dt = os.clock() - a
    if dt > worst then worst = dt end
    if count % 300 == 0 then
        print(string.format(
            "frames=%d framecount=%d worst_cb=%.4fs avg_fps=%.1f",
            count, emu.framecount(), worst, count / (os.clock() - t0)))
    end
end
```

- [ ] **Step 2: Run the experiments**

With the game running (any screen), load the script in the Lua console. Then:
1. Watch the console for 30 s. Record `worst_cb` (budget: must stay well under 0.016 s) and whether `framecount` advances by 1 per callback.
2. Pause the emulator from the frontend menu. Does `/tmp/jus_emu_spike.json` `os_time` keep updating? Record yes/no.
3. Connect GDB (`arm-none-eabi-gdb`, `target remote localhost:3333` — this halts the core). Does the file keep updating? Record yes/no. Then `continue`, `Ctrl+C`, record again. Disconnect.

- [ ] **Step 3: Document findings**

Write results into `scripts/emu/README.md` "Verified behavior": callback thread behavior during pause and GDB stop, worst callback time, framecount-per-callback relation. If `_Update()` does NOT fire during GDB stops, note that the heartbeat's `paused` inference (jus_ipc) is correct as designed. If callbacks are too slow (worst_cb > ~8 ms), STOP and consult the user — the bridge design needs the Qt-timer fallback from spec §12 before proceeding.

- [ ] **Step 4: Commit**

```bash
git add scripts/emu/spike/s1_s2_update_probe.lua scripts/emu/README.md
git commit -m "spike(emu): S1/S2 callback thread + I/O timing findings"
```

---

### Task 7: Spike S3–S5 (input sampling, savestate settling, GDB survival)

**Files:**
- Create: `scripts/emu/spike/s4_savestate_probe.lua`
- Modify: `scripts/emu/README.md`

- [ ] **Step 1: Write the savestate probe**

```lua
-- scripts/emu/spike/s4_savestate_probe.lua
-- S4: what does async savestate.load() do to framecount and Lua state?
-- Usage: set MODE below, reload script. Run once with MODE="save" while
-- in-game, then MODE="load".
local MODE = "load"  -- "save" | "load"
local issued_at = nil
local lua_marker = math.random(1, 1e9)  -- survives load? (it should: VM untouched)

function _Update()
    local fc = emu.framecount()
    if issued_at == nil then
        issued_at = fc
        print("marker=" .. lua_marker .. " issuing " .. MODE .. " at frame " .. fc)
        if MODE == "save" then
            savestate.save("/tmp/jus_emu_spike_state.mln")
        else
            savestate.load("/tmp/jus_emu_spike_state.mln")
        end
    elseif fc < issued_at or fc > issued_at + 1 then
        -- discontinuity = load settled (or big skip); log once
        print(string.format(
            "settled: issued_at=%d now=%d delta_cb_frames=%d marker=%d",
            issued_at, fc, fc - issued_at, lua_marker))
        issued_at = fc  -- keep logging further jumps
    end
end
```

- [ ] **Step 2: Run S4**

In a battle, run with `MODE="save"`, then `MODE="load"`. Record: how many callbacks between issuing `load` and the framecount discontinuity; whether `lua_marker` is unchanged (Lua VM not part of savestate); whether framecount is restored to the saved value. This yields the `STATE_SETTLE` detection rule the bridge uses (Task 9): *after issuing load, wait for a framecount discontinuity, max 60 callbacks*.

- [ ] **Step 3: Run S5 (GDB vs savestate)**

With GDB connected and a breakpoint set (`break *0x020784FC`), issue a `savestate.load` from the Lua console. Record: does GDB stay connected? does the breakpoint still fire after load? If not, README gets the documented procedure "disconnect GDB before state loads."

- [ ] **Step 4: Run S3 (input sampling offset) — deferred hook**

S3 needs `joypad.set` to exist, so it runs inside Task 8's acceptance test: the readback log shows the offset between "latch set on plan frame N" and "core sees the press." Note this in README now so the section isn't forgotten.

- [ ] **Step 5: Document findings + commit**

```bash
git add scripts/emu/spike/s4_savestate_probe.lua scripts/emu/README.md
git commit -m "spike(emu): S4/S5 savestate settling and GDB-survival findings"
```

---

### Task 8: `joypad.set` patch (M2)

**Files:**
- Create: `scripts/emu/patches/joypad-set.patch`
- Create: `scripts/emu/spike/s3_input_readback.lua`

- [ ] **Step 1: Locate the input commit point in the fork source**

Run in the fork checkout (`$SRC_DIR`):
```bash
grep -rn "SetKeyMask\|keyMask\|inputMask" src/frontend/qt_sdl/ src/NDS.h | head -30
```
Expected: an `EmuInstance` member holding the 12-bit mask and a call like `nds->SetKeyMask(...)` in the emu-thread frame loop or `EmuInstanceInput.cpp`. That call site is where the override applies.

- [ ] **Step 2: Implement the patch**

Working diff (adjust member/function names to what Step 1 found; the shape is fixed):

In `EmuInstance.h` (public members near other input state):
```cpp
// Lua input override (agent bridge): when active, replaces host input.
bool luaInputOverride = false;
uint32_t luaInputMask = 0xFFF; // active-low, bit order: A,B,Sel,Start,R,L,U,D,R,L,X,Y
```

At the located commit point (where the host mask is passed to the core), e.g. in `EmuInstanceInput.cpp`:
```cpp
uint32_t mask = inputMask; // existing host-derived mask
if (luaInputOverride) mask = luaInputMask;
nds->SetKeyMask(mask);
```

In `src/frontend/qt_sdl/lua/libs/LuaInput.cpp`, register on the existing `joypad` library:
```cpp
// bit order matches input.getjoy's key list
static const char* joyOrder[12] = {
    "A","B","Select","Start","Right","Left","Up","Down","R","L","X","Y"};

int Lua_setJoy(lua_State* L)
{
    LuaBundle* bundle = get_bundle(L);
    EmuInstance* inst = bundle->getEmuInstance();
    if (lua_isnoneornil(L,1))
    {
        inst->luaInputOverride = false;
        inst->luaInputMask = 0xFFF;
        return 0;
    }
    luaL_checktype(L,1,LUA_TTABLE);
    uint32_t mask = 0xFFF; // all released (active low)
    for (int i = 0; i < 12; i++)
    {
        lua_getfield(L,1,joyOrder[i]);
        if (lua_toboolean(L,-1)) mask &= ~(1u << i);
        lua_pop(L,1);
    }
    inst->luaInputMask = mask;
    inst->luaInputOverride = true;
    return 0;
}
AddJoypadFunction(Lua_setJoy,set);
```

Generate the patch: `cd $SRC_DIR && git diff > <repo>/scripts/emu/patches/joypad-set.patch`, then rebuild via `build_melonds_lua.sh`.

- [ ] **Step 3: Write the edge-accuracy readback test (also settles S3)**

```lua
-- scripts/emu/spike/s3_input_readback.lua
-- Press B for exactly frames 60-62 (relative); read back via joypad.get.
local start, log = nil, {}
function _Update()
    local fc = emu.framecount()
    if start == nil then start = fc end
    local rel = fc - start
    if rel >= 60 and rel <= 62 then
        joypad.set({B = true})
    elseif rel == 63 then
        joypad.set(nil)
    end
    local held = joypad.get()
    if rel >= 55 and rel <= 70 then
        log[#log+1] = string.format("rel=%d B=%s", rel, tostring(held.B))
    end
    if rel == 71 then
        for _, line in ipairs(log) do print(line) end
    end
end
```

- [ ] **Step 4: Run and evaluate**

Load the script with the game in a battle. Expected: exactly the frames where `joypad.set` latched B show `B=true` in the readback (and the character visibly acts). Record the offset between latch frame and readback frame in README as the **S3 finding**; if the offset is nonzero, record the constant `INPUT_APPLY_OFFSET = <n>` — Task 9's executor subtracts it. Also verify: hold Right 20 frames → character walks; Left+physical-keyboard input during the latch is ignored.

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/patches/joypad-set.patch scripts/emu/spike/s3_input_readback.lua scripts/emu/README.md
git commit -m "feat(emu): joypad.set input-injection patch, edge-accurate (M2)"
```

---

### Task 9: The bridge (`agent_bridge.lua`) + live verification (M3)

The largest file. Written in one task because its pieces (heartbeat, command loop, plan executor) share state and can only be tested against the live emulator anyway. Python-side pieces were already TDD'd.

**Files:**
- Create: `scripts/emu/agent_bridge.lua`

- [ ] **Step 1: Write the bridge**

```lua
-- scripts/emu/agent_bridge.lua
-- Agent control bridge. Load once in melonDS's Lua console.
-- Protocol: see scripts/emu/jus_ipc.py docstring and spec §3.

local IPC_DIR = os.getenv("JUS_EMU_DIR") or "/tmp/jus_emu"
local BUS = "ARM9 System Bus"
local POLL_INTERVAL = 10          -- frames between idle polls
local STATE_SETTLE_MAX = 60       -- max callbacks to wait for load settle
local FLUSH_EVERY = 600           -- frames between mid-plan log flushes
local MAIN_RAM_LO, MAIN_RAM_HI = 0x02000000, 0x02400000

local session = tostring(os.time()) .. "-" .. tostring(math.random(1e6))
local state = "idle"              -- idle|plan_running|loading_state|flushing
local tick = 0
local plan, plan_frame, log_buf, run_dir, plan_cmd_id = nil, 0, {}, nil, nil
local settle_issued_fc, settle_waited = nil, 0
local watches = {}

-- ---------- tiny JSON encoder (encode only; commands arrive as Lua) ------
local function jenc(v)
    local t = type(v)
    if v == nil then return "null" end
    if t == "number" then return string.format("%.17g", v) end
    if t == "boolean" then return tostring(v) end
    if t == "string" then
        return '"' .. v:gsub('[\\"]', '\\%0'):gsub('\n', '\\n') .. '"'
    end
    if t == "table" then
        if #v > 0 or next(v) == nil then
            local parts = {}
            for _, x in ipairs(v) do parts[#parts+1] = jenc(x) end
            return "[" .. table.concat(parts, ",") .. "]"
        end
        local parts = {}
        for k, x in pairs(v) do
            parts[#parts+1] = jenc(tostring(k)) .. ":" .. jenc(x)
        end
        return "{" .. table.concat(parts, ",") .. "}"
    end
    error("unencodable: " .. t)
end

local function write_atomic(path, content)
    local f = assert(io.open(path .. ".tmp", "w"))
    f:write(content)
    f:close()
    os.remove(path)          -- os.rename won't clobber on all platforms
    assert(os.rename(path .. ".tmp", path))
end

local function heartbeat()
    write_atomic(IPC_DIR .. "/heartbeat.json", jenc({
        session = session, framecount = emu.framecount(),
        wallclock = os.time(), state = state }))
end

local function ack(id, ok, payload)
    write_atomic(IPC_DIR .. "/ack/" .. id .. ".json",
        jenc({ id = id, ok = ok,
               result = ok and payload or nil,
               error  = (not ok) and payload or nil }))
end

-- ---------- input ---------------------------------------------------------
local function neutral_input()
    joypad.set(nil)
    input.NDSTapUp()
end

-- ---------- memory helpers -------------------------------------------------
local function valid_ptr(p)
    return p >= MAIN_RAM_LO and p < MAIN_RAM_HI and p % 4 == 0
end

local function resolve_chain(chain)
    -- chain = {base, off1, ...}: read u32 at base, add off, repeat
    local p = chain[1]
    for i = 2, #chain do
        if not (p >= MAIN_RAM_LO and p < MAIN_RAM_HI) then return nil end
        p = memory.read_u32_le(p, BUS)
        if not valid_ptr(p) then return nil end
        p = p + chain[i]
    end
    return p
end

local function read_watch(w)
    local addr
    if w.chain then
        local base = resolve_chain(w.chain)
        if base == nil then return nil end
        addr = base + (w.offset or 0)
    else
        addr = w.addr
    end
    if w.len == 1 then return memory.read_u8(addr, BUS) end
    if w.len == 2 then return memory.read_u16_le(addr, BUS) end
    if w.len == 4 then return memory.read_u32_le(addr, BUS) end
    return memory.read_bytes_as_array(addr, w.len, BUS)
end

-- ---------- logging --------------------------------------------------------
local function flush_log()
    if run_dir == nil or #log_buf == 0 then return end
    state = "flushing"
    local f = assert(io.open(run_dir .. "/log.jsonl", "a"))
    f:write(table.concat(log_buf, "\n"))
    f:write("\n")
    f:close()
    log_buf = {}
end

-- ---------- plan executor --------------------------------------------------
local function abort_plan(reason)
    neutral_input()
    if run_dir then
        log_buf[#log_buf+1] = jenc({ aborted = reason,
                                     f = plan_frame })
        flush_log()
    end
    if plan_cmd_id then ack(plan_cmd_id, false, reason) end
    plan, run_dir, plan_cmd_id, state = nil, nil, nil, "idle"
end

local function finish_plan()
    neutral_input()
    flush_log()
    write_atomic(run_dir .. "/done.json",
                 jenc({ frames = plan_frame, ok = true }))
    ack(plan_cmd_id, true, { frames = plan_frame,
                             log = run_dir .. "/log.jsonl" })
    plan, run_dir, plan_cmd_id, state = nil, nil, nil, "idle"
end

local function plan_step()
    -- input for this frame (INPUT_APPLY_OFFSET from S3 findings; 0 default)
    local offset = plan.input_apply_offset or 0
    local eff = plan_frame + offset
    local mask, touch = nil, nil
    for _, seg in ipairs(plan.segments) do
        if eff >= seg["from"] and eff <= seg["to"] then
            if seg.buttons then
                mask = {}
                for _, b in ipairs(seg.buttons) do mask[b] = true end
            end
            touch = seg.touch
        end
    end
    if mask then joypad.set(mask) else joypad.set(nil) end
    if touch then input.NDSTapDown(touch.x, touch.y) else input.NDSTapUp() end

    -- watches
    local w = {}
    for _, spec in ipairs(watches) do w[spec.name] = read_watch(spec) end
    local pressed = {}
    if mask then for b in pairs(mask) do pressed[#pressed+1] = b end end
    log_buf[#log_buf+1] = jenc({ f = plan_frame, ["in"] = pressed, w = w })

    if #log_buf >= FLUSH_EVERY then flush_log(); state = "plan_running" end
    plan_frame = plan_frame + 1
    if plan_frame >= plan.total_frames then finish_plan() end
end

-- ---------- commands -------------------------------------------------------
local handlers = {}

function handlers.status(args)
    return { state = state, framecount = emu.framecount(),
             session = session, plan = plan and plan.name or nil }
end

function handlers.peek(args)
    local v = read_watch({ chain = args.chain, offset = args.offset,
                           addr = args.addr, len = args.len })
    if v == nil then error("pointer chain invalid (not in battle?)") end
    return { value = v }
end

function handlers.poke(args)
    memory.write_bytes_as_array(args.addr, args.bytes, BUS)
    return { written = #args.bytes }
end

function handlers.dump(args)
    local f = assert(io.open(args.outfile, "wb"))
    local addr, remaining = args.start, args["end"] - args.start
    while remaining > 0 do
        local n = math.min(remaining, 4096)
        local bytes = memory.read_bytes_as_array(addr, n, BUS)
        local chars = {}
        for i = 1, n do chars[i] = string.char(bytes[i]) end
        f:write(table.concat(chars))
        addr, remaining = addr + n, remaining - n
    end
    f:close()
    return { bytes = args["end"] - args.start, outfile = args.outfile }
end

function handlers.state_save(args)
    savestate.save(IPC_DIR .. "/states/" .. args.slot .. ".mln")
    return { slot = args.slot, note = "save is async; verify with state_load" }
end

function handlers.set_watches(args)
    watches = args.specs
    return { count = #watches }
end

function handlers.selftest(args)
    local t0 = os.clock()
    local bytes = memory.read_bytes_as_array(0x021DF000, 512, BUS)
    savestate.save(IPC_DIR .. "/states/_selftest.mln")
    return { framecount = emu.framecount(), read_ok = #bytes == 512,
             cb_time = os.clock() - t0, session = session }
end

-- state_load and run_plan need multi-frame settling; handled specially.
local function begin_state_load(id, slot_path, then_plan)
    savestate.load(slot_path)
    settle_issued_fc = emu.framecount()
    settle_waited = 0
    state = "loading_state"
    -- stash continuation
    plan_cmd_id = id
    plan = then_plan  -- may be nil for a bare state_load
end

local function settle_step()
    settle_waited = settle_waited + 1
    local fc = emu.framecount()
    local jumped = fc < settle_issued_fc or fc > settle_issued_fc + settle_waited + 1
    if jumped or settle_waited >= STATE_SETTLE_MAX then
        if not jumped then
            abort_plan("state load did not settle in " ..
                       STATE_SETTLE_MAX .. " frames")
            return
        end
        if plan then
            plan_frame = 0
            log_buf = {}
            watches = plan.watches or {}
            state = "plan_running"
        else
            ack(plan_cmd_id, true, { loaded = true, framecount = fc })
            plan_cmd_id, state = nil, "idle"
        end
    end
end

local function poll_commands()
    local inbox = IPC_DIR .. "/cmd/inbox.lua"
    local f = io.open(inbox, "r")
    if f == nil then return end
    local content = f:read("a"); f:close()
    os.remove(inbox)
    local chunk, err = load(content, "cmd", "t", {})
    if chunk == nil then return end -- can't even parse: no id to ack
    local ok, cmd = pcall(chunk)
    if not ok or type(cmd) ~= "table" then return end
    if cmd.epoch ~= session then
        ack(cmd.id, false, "stale epoch " .. tostring(cmd.epoch))
        return
    end
    if cmd.op == "run_plan" then
        local pf = io.open(cmd.args.plan_path, "r")
        if pf == nil then ack(cmd.id, false, "plan file missing"); return end
        local pchunk = load(pf:read("a"), "plan", "t", {})
        pf:close()
        local pok, p = pcall(pchunk)
        if not pok then ack(cmd.id, false, "plan parse error"); return end
        run_dir = cmd.args.run_dir
        if p.load_state then
            begin_state_load(cmd.id,
                IPC_DIR .. "/states/" .. p.load_state .. ".mln", p)
        else
            plan, plan_cmd_id, plan_frame, log_buf = p, cmd.id, 0, {}
            watches = p.watches or {}
            state = "plan_running"
        end
        return
    end
    if cmd.op == "state_load" then
        begin_state_load(cmd.id,
            IPC_DIR .. "/states/" .. cmd.args.slot .. ".mln", nil)
        return
    end
    local h = handlers[cmd.op]
    if h == nil then ack(cmd.id, false, "unknown op " .. tostring(cmd.op)); return end
    local hok, result = pcall(h, cmd.args)
    ack(cmd.id, hok, result)
end

local function check_stop()
    local f = io.open(IPC_DIR .. "/stop.flag", "r")
    if f then
        f:close()
        os.remove(IPC_DIR .. "/stop.flag")
        if state == "plan_running" or state == "loading_state" then
            abort_plan("stopped by client")
        end
    end
end

-- ---------- main loop ------------------------------------------------------
os.execute("mkdir -p " .. IPC_DIR .. "/cmd " .. IPC_DIR .. "/ack " ..
           IPC_DIR .. "/runs " .. IPC_DIR .. "/states")
neutral_input()
heartbeat()
print("agent_bridge up, session " .. session)

function _Update()
    tick = tick + 1
    local ok, err = pcall(function()
        if state == "plan_running" then plan_step() end
        if state == "loading_state" then settle_step() end
        if tick % POLL_INTERVAL == 0 then
            heartbeat()
            check_stop()
            if state == "idle" then poll_commands() end
        end
    end)
    if not ok then
        -- cleanup invariant: neutral input before anything else
        pcall(neutral_input)
        pcall(abort_plan, "lua error: " .. tostring(err))
    end
end
```

- [ ] **Step 2: Live smoke test (bridge idle loop)**

With the game at any screen, load `agent_bridge.lua` in the Lua console. Then from the repo:

```bash
cd scripts/emu
python3 jusemu.py status          # expect state=idle, live framecount
python3 jusemu.py peek 0x021DEA71 1    # battle timer (any value; no error)
```
Expected: JSON acks within a second. Then start a battle and:
```bash
python3 jusemu.py peek 0x78 1 --chain player   # ground/air state, expect 0x22 on ground
python3 jusemu.py state save smoketest
python3 jusemu.py state load smoketest         # expect ok with settle
```

- [ ] **Step 3: Fix what breaks**

Common expected issues to check systematically: `os.rename` clobber semantics, `load()` sandbox env blocking `math`/string functions inside plan chunks (the empty `{}` env is intentional — plans/commands are pure literals and need no globals), heartbeat staleness threshold vs POLL_INTERVAL at low fps. Use superpowers:systematic-debugging if anything is mysterious.

- [ ] **Step 4: Commit**

```bash
git add scripts/emu/agent_bridge.lua
git commit -m "feat(emu): agent bridge — command loop, plan executor, heartbeat (M3)"
```

---

### Task 10: Bootstrap savestate + acceptance test (M4) — human checkpoint

**Files:**
- Create: `scripts/emu/plans/example_walk_and_b.json`

- [ ] **Step 1: Human checkpoint — create the training savestate**

Ask the user to boot into a free battle / training scenario (ideally Goku vs a CPU or idle dummy, per the Phase1 guide's recommendation), then run:
```bash
python3 jusemu.py state save training_goku
```

- [ ] **Step 2: Write the acceptance plan**

```json
{
  "name": "accept_walk_and_b",
  "load_state": "training_goku",
  "segments": [
    {"from": 0, "to": 20, "buttons": ["RIGHT"]},
    {"from": 21, "to": 23, "buttons": ["B"]}
  ],
  "tail_frames": 120,
  "watches": ["hp_all", "player_struct", "opponent_struct"]
}
```
Save as `scripts/emu/plans/example_walk_and_b.json`. (The B press may need position adjustment to actually connect — iterate `from`/`to` frames until the log shows the hit; that iteration is itself the point: it must be doable *without touching the emulator by hand*.)

- [ ] **Step 3: Run acceptance**

```bash
python3 jusemu.py run plans/example_walk_and_b.json
```
PASS criteria (inspect `log.jsonl` in the printed run dir):
- `hp_all.o1` decreases at some frame N.
- `opponent_struct.0x78` enters the 0xC0 family near frame N.
- The `in` field shows `B` on exactly plan frames 21–23.

- [ ] **Step 4: Determinism check**

Run the same command twice. Then:
```bash
diff <run1>/log.jsonl <run2>/log.jsonl && echo DETERMINISTIC
```
Expected: `DETERMINISTIC`. If not, diff the first divergent line; check README's recorded config (JIT off? frame limiter on?) and record the root cause + fix in README before proceeding.

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/plans/example_walk_and_b.json scripts/emu/README.md
git commit -m "test(emu): M4 acceptance plan passes; determinism verified"
```

---

### Task 11: GDB handoff workflow + first real cards (M5)

**Files:**
- Modify: `scripts/emu/README.md` (Combined Lua+GDB workflow section)

- [ ] **Step 1: Verify plan freeze/resume across a GDB stop**

Start a long plan (e.g. the acceptance plan with `tail_frames: 600`). Mid-plan, connect GDB and `Ctrl+C` — `jusemu status` must report `paused` (not `dead`). `continue` in GDB; the plan must resume and complete with correct total frames (frame counting is emulated-frame-based, so the log must show no gap).

- [ ] **Step 2: Work 2–3 cards from the validation queue**

Use `docs/research/GDB-Validation-Queue.md` Session 1 (cards 2, 3, 9 are self-contained checks at `0x02078488`/`0x020783CC`). Workflow per card: `state load training_goku` → set the card's breakpoint via the existing GDB tooling → run the input plan that lands a hit → when the breakpoint fires, do the card's register/memory checks in GDB → `continue` → record the verdict in the queue doc.

- [ ] **Step 3: Document the combined workflow**

Write the README section with the exact command sequence used, including the S5-derived rule about GDB connections across savestate loads.

- [ ] **Step 4: Commit**

```bash
git add scripts/emu/README.md docs/research/GDB-Validation-Queue.md
git commit -m "docs(emu): combined Lua+GDB workflow; first validation cards done (M5)"
```

---

## Self-review checklist (done at plan-writing time)

- Spec coverage: §2 build+spike → Tasks 5–7; §3 bridge/CLI/IPC → Tasks 3, 4, 9; §4 input contract → Task 8; §5 formats → Tasks 2, 9; §6 failure modes → Tasks 3, 9; §7 determinism → Task 10; §8 testing → every task; GDB sequential handoff → Task 11. Screenshot command (spec §3) → Task 4 (`do_screenshot`).
- No placeholders: every code step has full code; the two "adjust to what you find" points (Task 8 step 2 member names, S3 offset constant) are bounded discovery steps with exact grep commands and fixed shape.
- Type consistency: command ops (`run_plan`, `state_save`, `state_load`, `peek`, `poke`, `dump`, `set_watches`, `status`, `selftest`) match between `jusemu.py` and `agent_bridge.lua`; watch spec fields (`name`, `addr`, `chain`, `offset`, `len`) match across `jus_addresses.py`, `jus_plan.py`, and the bridge; heartbeat states match `jus_ipc.BridgeState`.
