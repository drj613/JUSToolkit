# melonDS Agent Control Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Rev 2** — incorporates Codex review round 2 (input-override isolation, async savestate lifecycle, IPC hardening, bridge-core unit tests, canonical JSON).

**Goal:** Let a Claude session drive melonDS unattended (inputs, savestates, memory watches, screenshots) via a Lua bridge + Python CLI, per `docs/harness/2026-08-14-melonds-agent-control-design.md`.

**Architecture:** A patched build of NPO-197's melonDS-lua fork runs `agent_bridge.lua` (thin emulator bindings) around `bridge_core.lua` (pure logic, unit-tested with the `lua5.4` CLI). A Python CLI (`jusemu.py`) talks to the bridge through rename-published files in `/tmp/jus_emu/`. The existing GDB stub stays as a second, sequential control plane.

**Tech Stack:** Lua 5.4 (inside melonDS + `lua5.4` CLI for tests), Python 3 stdlib only (`unittest`), CMake/clang for the emulator build, `screencapture` for screenshots.

**Key facts verified from fork source (2026-08-14, do not rediscover):**
- `memory.read_u8/read_u16_le/read_u32_le(addr, domain)` and `memory.read_bytes_as_array(addr, len, domain)` exist. Pass domain `"ARM9 System Bus"` to use full CPU-visible addresses like `0x021DF1D5` (routes through BizHawk-derived safe-peek). The default `"Main RAM"` domain is *offset-based*. **Never call `memory.usememorydomain`** — it stores a pointer to a stack local (fork bug); always pass the domain string per call.
- `savestate.save(path)` / `savestate.load(path)` are **asynchronous**: they emit Qt signals; the actual work happens later on another thread. Both are modeled as multi-frame state machines in the bridge (Tasks 7, 9).
- `_Update()` is a global Lua function the fork calls once per frame while the script runs. `emu.framecount()` returns the emulated frame counter.
- `joypad` is read-only (`joypad.get`); injection is added by our patch (Task 8).
- Button name order used by `input.getjoy` (and our canonical order everywhere): `A,B,Select,Start,Right,Left,Up,Down,R,L,X,Y`.

**Input-override semantics (fixed vocabulary, used consistently):**
- `joypad.set(table)` — override active; the table is the complete pressed set; **physical input is ignored**.
- `joypad.set({})` — **force-neutral**: override active, nothing pressed. Used for plan gaps, tail frames, touch-only segments, pre-savestate-load, and error cleanup *during* a plan.
- `joypad.set(nil)` — **release**: override off, physical input returns. Used only when the bridge goes idle (plan finished/aborted and cleanup done) and at script stop.

**Human checkpoints (flag to user when reached):**
- Task 5: ROM/BIOS paths; confirming the emulator boots; recording hashes.
- Task 10: navigating once to a training battle for the bootstrap savestate.

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

    def test_no_duplicate_names_within_preset(self):
        for preset in WATCH_PRESETS:
            names = [s["name"] for s in resolve_watch(preset)]
            self.assertEqual(len(names), len(set(names)), preset)

    def test_unknown_preset_raises(self):
        with self.assertRaises(KeyError):
            resolve_watch("nonsense")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scripts/emu && python3 -m unittest tests.test_jus_addresses -v`
Expected: ERROR with `ModuleNotFoundError: No module named 'jus_addresses'`

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
Expected: all 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/jus_addresses.py scripts/emu/tests/
git commit -m "feat(emu): address book with watch presets and pointer chains"
```

---

### Task 2: Plan + watch validation (`jus_plan.py`)

Validates plans and watch specs per spec §5 and converts plans to the Lua-literal form the bridge consumes. `validate_watches` is the *single* validator used by every CLI path (`run`, `watch set`, `peek`) — Codex finding #10.

**Files:**
- Create: `scripts/emu/jus_plan.py`
- Test: `scripts/emu/tests/test_jus_plan.py`

- [ ] **Step 1: Write the failing test**

```python
# scripts/emu/tests/test_jus_plan.py
import unittest
from jus_plan import (validate_plan, validate_watches, plan_to_lua,
                      lua_literal, PlanError)

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


class TestValidatePlan(unittest.TestCase):
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

    def test_unsorted_segments_rejected(self):
        bad = dict(GOOD, segments=[
            {"from": 21, "to": 23, "buttons": ["B"]},
            {"from": 0, "to": 20, "buttons": ["RIGHT"]},
        ])
        with self.assertRaises(PlanError):
            validate_plan(bad)

    def test_negative_frames_rejected(self):
        for seg in ({"from": -1, "to": 3, "buttons": ["A"]},
                    {"from": 0, "to": -3, "buttons": ["A"]}):
            with self.assertRaises(PlanError):
                validate_plan(dict(GOOD, segments=[seg]))

    def test_negative_tail_rejected(self):
        with self.assertRaises(PlanError):
            validate_plan(dict(GOOD, tail_frames=-5))

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

    def test_touch_out_of_bounds_rejected(self):
        for xy in ({"x": 256, "y": 96}, {"x": -1, "y": 0}, {"x": 0, "y": 192}):
            with self.assertRaises(PlanError):
                validate_plan(dict(GOOD, segments=[
                    {"from": 0, "to": 1, "touch": xy}]))


class TestValidateWatches(unittest.TestCase):
    def test_limit_32_watches(self):
        specs = [{"name": "w%d" % i, "addr": 0x02000000 + i, "len": 1}
                 for i in range(32)]
        validate_watches(specs)  # exactly at limit: ok
        specs.append({"name": "w32", "addr": 0x02000100, "len": 1})
        with self.assertRaises(PlanError):
            validate_watches(specs)

    def test_byte_budget_512(self):
        validate_watches([{"name": "b", "addr": 0x02000000, "len": 512}])
        with self.assertRaises(PlanError):
            validate_watches([{"name": "b", "addr": 0x02000000, "len": 513}])

    def test_read_crossing_ram_boundary_rejected(self):
        with self.assertRaises(PlanError):
            validate_watches([{"name": "x", "addr": 0x023FFFFC, "len": 8}])

    def test_duplicate_names_rejected(self):
        with self.assertRaises(PlanError):
            validate_watches([
                {"name": "a", "addr": 0x02000000, "len": 1},
                {"name": "a", "addr": 0x02000004, "len": 1}])

    def test_chain_depth_limit(self):
        with self.assertRaises(PlanError):
            validate_watches([{"name": "c", "len": 1, "offset": 0,
                               "chain": [0x02000000, 0, 0, 0, 0]}])


class TestLuaEmit(unittest.TestCase):
    def test_emits_loadable_lua_table(self):
        lua = plan_to_lua(validate_plan(GOOD))
        self.assertTrue(lua.startswith("return {"))
        self.assertIn('walk_and_b', lua)
        self.assertIn("Right", lua)  # RIGHT normalized to fork casing

    def test_control_chars_escaped(self):
        self.assertEqual(lua_literal("a\nb"), '"a\\nb"')
        self.assertEqual(lua_literal('q"\\'), '"q\\"\\\\"')
        self.assertEqual(lua_literal("x\r\ty"), '"x\\rty"'.replace("t", "\\t", 1)
                         if False else '"x\\r\\ty"')

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
"""Plan/watch validation and conversion to Lua literals.

Spec: docs/harness/2026-08-14-melonds-agent-control-design.md §5.
Limits: <=32 watches, <=512 watched bytes/frame, chain depth <=3.
validate_watches() is THE watch validator; every CLI path uses it.
"""
from jus_addresses import resolve_watch

BUTTONS = {  # CLI accepts uppercase; values are the fork's exact casing
    "A": "A", "B": "B", "SELECT": "Select", "START": "Start",
    "RIGHT": "Right", "LEFT": "Left", "UP": "Up", "DOWN": "Down",
    "R": "R", "L": "L", "X": "X", "Y": "Y",
}
MAX_WATCHES = 32
MAX_WATCH_BYTES = 512
MAX_CHAIN_DEPTH = 3
MAIN_RAM = (0x02000000, 0x02400000)
TOUCH_W, TOUCH_H = 256, 192


class PlanError(ValueError):
    pass


def validate_watches(specs):
    """Validate a list of concrete watch specs. Raises PlanError."""
    if len(specs) > MAX_WATCHES:
        raise PlanError("too many watches (%d > %d)" % (len(specs), MAX_WATCHES))
    names = set()
    total = 0
    for w in specs:
        name = w.get("name")
        if not name or name in names:
            raise PlanError("missing/duplicate watch name: %r" % name)
        names.add(name)
        ln = w.get("len", 0)
        if not (isinstance(ln, int) and 1 <= ln <= MAX_WATCH_BYTES):
            raise PlanError("bad len for %s" % name)
        total += ln
        if "chain" in w:
            if len(w["chain"]) - 1 > MAX_CHAIN_DEPTH:
                raise PlanError("chain too deep: %s" % name)
            if not isinstance(w.get("offset", 0), int):
                raise PlanError("bad offset: %s" % name)
        elif "addr" in w:
            a = w["addr"]
            if not (MAIN_RAM[0] <= a and a + ln <= MAIN_RAM[1]):
                raise PlanError("read outside main RAM: %s" % name)
        else:
            raise PlanError("watch needs addr or chain: %s" % name)
    if total > MAX_WATCH_BYTES:
        raise PlanError("watch byte budget exceeded (%d > %d)" %
                        (total, MAX_WATCH_BYTES))
    return specs


def _nonneg(v, what):
    v = int(v)
    if v < 0:
        raise PlanError("%s must be >= 0, got %d" % (what, v))
    return v


def validate_plan(plan):
    """Return a normalized copy of the plan, or raise PlanError."""
    out = {"name": str(plan["name"]),
           "load_state": plan.get("load_state"),
           "tail_frames": _nonneg(plan.get("tail_frames", 0), "tail_frames")}

    segs, last_end = [], -1
    raw = plan["segments"]
    if raw != sorted(raw, key=lambda s: int(s["from"])):
        raise PlanError("segments must be sorted by 'from'")
    for seg in raw:
        f = _nonneg(seg["from"], "from")
        t = _nonneg(seg["to"], "to")
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
            x, y = int(seg["touch"]["x"]), int(seg["touch"]["y"])
            if not (0 <= x < TOUCH_W and 0 <= y < TOUCH_H):
                raise PlanError("touch out of bounds: %d,%d" % (x, y))
            norm["touch"] = {"x": x, "y": y}
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
    out["watches"] = validate_watches(watches)
    return out


_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def _quote(s):
    body = "".join(_ESCAPES.get(c, "\\%d" % ord(c) if ord(c) < 32 else c)
                   for c in s)
    return '"%s"' % body


def lua_literal(v):
    if v is None:
        return "nil"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return "0x%X" % v if v > 255 else str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return _quote(v)
    if isinstance(v, list):
        return "{" + ", ".join(lua_literal(x) for x in v) + "}"
    if isinstance(v, dict):
        parts = ["[%s] = %s" % (_quote(str(k)), lua_literal(val))
                 for k, val in sorted(v.items()) if val is not None]
        return "{" + ", ".join(parts) + "}"
    raise TypeError(type(v))


def plan_to_lua(normalized):
    """Emit the validated plan as a Lua literal chunk ('return {...}')."""
    return "return " + lua_literal(normalized)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts/emu && python3 -m unittest tests.test_jus_plan -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/jus_plan.py scripts/emu/tests/test_jus_plan.py
git commit -m "feat(emu): centralized plan/watch validation, escaped Lua emission"
```

---

### Task 3: IPC layer (`jus_ipc.py`)

Hardened per Codex round 2: lazy heartbeat (status works when the bridge is dead), persistent id counter, pending-command record surviving inbox consumption, epoch-validated acks, stale-epoch cleanup, rename-only atomic writes.

**Files:**
- Create: `scripts/emu/jus_ipc.py`
- Test: `scripts/emu/tests/test_jus_ipc.py`

- [ ] **Step 1: Write the failing test**

```python
# scripts/emu/tests/test_jus_ipc.py
import json, os, tempfile, time, unittest
from jus_ipc import IpcClient, BridgeState, interpret_heartbeat


def write_hb(d, epoch="epoch1", state="idle", age=0.0):
    tmp = os.path.join(d, "hb.tmp")
    with open(tmp, "w") as f:
        json.dump({"session": epoch, "framecount": 100,
                   "wallclock": time.time() - age, "state": state}, f)
    os.replace(tmp, os.path.join(d, "heartbeat.json"))


class TestHeartbeat(unittest.TestCase):
    def hb(self, age_s, state="idle", alive=True):
        return interpret_heartbeat(
            {"session": "abc", "framecount": 100,
             "wallclock": time.time() - age_s, "state": state},
            emulator_alive=alive)

    def test_fresh_states(self):
        self.assertEqual(self.hb(0.5), BridgeState.IDLE)
        self.assertEqual(self.hb(0.5, "plan_running"), BridgeState.PLAN_RUNNING)
        self.assertEqual(self.hb(0.5, "loading_state"), BridgeState.LOADING_STATE)
        self.assertEqual(self.hb(0.5, "saving_state"), BridgeState.SAVING_STATE)

    def test_stale_alive_is_paused(self):
        self.assertEqual(self.hb(30, alive=True), BridgeState.PAUSED)

    def test_stale_dead_is_dead(self):
        self.assertEqual(self.hb(30, alive=False), BridgeState.DEAD)

    def test_unknown_state_is_dead(self):
        self.assertEqual(self.hb(0.5, "wat"), BridgeState.DEAD)


class TestClientNoBridge(unittest.TestCase):
    def test_status_without_heartbeat_is_dead(self):
        c = IpcClient(tempfile.mkdtemp())
        state, hb = c.state()
        self.assertEqual(state, BridgeState.DEAD)
        self.assertIsNone(hb)

    def test_publish_without_heartbeat_raises(self):
        c = IpcClient(tempfile.mkdtemp())
        with self.assertRaises(RuntimeError):
            c.publish_command("status", {})


class TestClient(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        write_hb(self.dir)
        self.c = IpcClient(self.dir)

    def ack(self, cid, epoch="epoch1", ok=True):
        tmp = os.path.join(self.dir, "ack", "t")
        with open(tmp, "w") as f:
            json.dump({"id": cid, "epoch": epoch, "ok": ok,
                       "result": {"state": "idle"}}, f)
        os.replace(tmp, os.path.join(self.dir, "ack", "%d.json" % cid))

    def test_ids_monotonic_across_instances(self):
        a = self.c.publish_command("status", {})
        self.ack(a)
        self.c.wait_ack(a, timeout=1)
        c2 = IpcClient(self.dir)
        b = c2.publish_command("status", {})
        self.assertGreater(b, a)

    def test_publish_writes_inbox_and_pending(self):
        cid = self.c.publish_command("status", {})
        self.assertTrue(os.path.exists(
            os.path.join(self.dir, "cmd", "inbox.lua")))
        self.assertTrue(os.path.exists(
            os.path.join(self.dir, "cmd", "pending.json")))
        content = open(os.path.join(self.dir, "cmd", "inbox.lua")).read()
        self.assertIn('"status"', content)
        self.assertIn("epoch1", content)
        self.assertIn(str(cid), content)

    def test_pending_blocks_even_after_inbox_consumed(self):
        self.c.publish_command("status", {})
        os.remove(os.path.join(self.dir, "cmd", "inbox.lua"))  # bridge ate it
        with self.assertRaises(RuntimeError):
            self.c.publish_command("status", {})

    def test_wait_ack_clears_pending(self):
        cid = self.c.publish_command("status", {})
        self.ack(cid)
        ack = self.c.wait_ack(cid, timeout=1)
        self.assertTrue(ack["ok"])
        self.assertFalse(os.path.exists(
            os.path.join(self.dir, "cmd", "pending.json")))

    def test_ack_with_wrong_epoch_rejected(self):
        cid = self.c.publish_command("status", {})
        self.ack(cid, epoch="old-epoch")
        with self.assertRaises(TimeoutError):
            self.c.wait_ack(cid, timeout=0.3)

    def test_stale_epoch_files_cleaned_on_new_epoch(self):
        cid = self.c.publish_command("status", {})
        # bridge restarts with a new session:
        write_hb(self.dir, epoch="epoch2")
        c2 = IpcClient(self.dir)
        c2.publish_command("status", {})  # must not raise: stale cleaned
        self.assertEqual(c2.epoch, "epoch2")

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
"""File-based IPC with agent_bridge.lua running inside melonDS.

Layout under the IPC dir (default /tmp/jus_emu):
  heartbeat.json      bridge-owned; {session, framecount, wallclock, state}
  cmd/inbox.lua       client-owned; one pending command as a Lua literal
  cmd/pending.json    client-owned; {id, epoch} survives inbox consumption
  cmd/next_id         client-owned; persistent id counter
  ack/<id>.json       bridge-owned; {id, epoch, ok, result|error}
  stop.flag           client-owned sentinel; bridge aborts active plan
  runs/, states/      run artifacts and savestates

Commands are Lua literals (bridge needs no JSON parser); acks and
heartbeats are JSON from the bridge's canonical encoder. Delivery is
at-most-once: on timeout a command's fate is unknown; check status
before reissuing (spec §3). Single client per IPC dir by design.
"""
import enum, json, os, subprocess, time

from jus_plan import lua_literal

HEARTBEAT_STALE_S = 5.0
DEFAULT_DIR = os.environ.get("JUS_EMU_DIR", "/tmp/jus_emu")


class BridgeState(enum.Enum):
    IDLE = "idle"
    PLAN_RUNNING = "plan_running"
    LOADING_STATE = "loading_state"
    SAVING_STATE = "saving_state"
    FLUSHING = "flushing"
    PAUSED = "paused"   # heartbeat stale, emulator process alive (GDB stop?)
    DEAD = "dead"

_LIVE = {s.value: s for s in (BridgeState.IDLE, BridgeState.PLAN_RUNNING,
                              BridgeState.LOADING_STATE,
                              BridgeState.SAVING_STATE, BridgeState.FLUSHING)}


def emulator_process_alive():
    out = subprocess.run(["pgrep", "-if", "melonDS"],
                         capture_output=True, text=True)
    return out.returncode == 0


def interpret_heartbeat(hb, emulator_alive):
    if time.time() - hb["wallclock"] > HEARTBEAT_STALE_S:
        return BridgeState.PAUSED if emulator_alive else BridgeState.DEAD
    return _LIVE.get(hb["state"], BridgeState.DEAD)


def _write_atomic(path, content):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        f.write(content)
    os.replace(tmp, path)


class IpcClient:
    def __init__(self, ipc_dir=DEFAULT_DIR):
        self.dir = ipc_dir
        for sub in ("cmd", "ack", "runs", "states"):
            os.makedirs(os.path.join(self.dir, sub), exist_ok=True)
        self.epoch = None
        hb = self._read_heartbeat()
        if hb is not None:
            self.epoch = hb["session"]
            self._clean_stale_epoch_files()

    # -- heartbeat / status --------------------------------------------
    def _read_heartbeat(self):
        try:
            with open(os.path.join(self.dir, "heartbeat.json")) as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def state(self):
        hb = self._read_heartbeat()
        if hb is None:
            return BridgeState.DEAD, None
        return interpret_heartbeat(hb, emulator_process_alive()), hb

    # -- epoch hygiene --------------------------------------------------
    def _clean_stale_epoch_files(self):
        pend = os.path.join(self.dir, "cmd", "pending.json")
        try:
            with open(pend) as f:
                if json.load(f).get("epoch") != self.epoch:
                    os.remove(pend)
                    inbox = os.path.join(self.dir, "cmd", "inbox.lua")
                    if os.path.exists(inbox):
                        os.remove(inbox)
        except (OSError, ValueError):
            pass
        ackdir = os.path.join(self.dir, "ack")
        for name in os.listdir(ackdir):
            try:
                with open(os.path.join(ackdir, name)) as f:
                    if json.load(f).get("epoch") != self.epoch:
                        os.remove(os.path.join(ackdir, name))
            except (OSError, ValueError):
                os.remove(os.path.join(ackdir, name))

    # -- command ids ------------------------------------------------------
    def next_id(self):
        path = os.path.join(self.dir, "cmd", "next_id")
        try:
            with open(path) as f:
                n = int(f.read().strip())
        except (OSError, ValueError):
            n = 0
        n += 1
        _write_atomic(path, str(n))
        return n

    # -- publish / wait ---------------------------------------------------
    def publish_command(self, op, args, cmd_id=None):
        if self.epoch is None:
            raise RuntimeError("no bridge heartbeat — is agent_bridge.lua "
                               "loaded? (`jusemu status` for details)")
        pend = os.path.join(self.dir, "cmd", "pending.json")
        if os.path.exists(pend):
            raise RuntimeError(
                "a command is pending (unacked); check `jusemu status`, "
                "then remove %s if it is stale" % pend)
        cid = cmd_id if cmd_id is not None else self.next_id()
        body = "return " + lua_literal(
            {"epoch": self.epoch, "id": cid, "op": op, "args": args})
        _write_atomic(pend, json.dumps({"id": cid, "epoch": self.epoch}))
        _write_atomic(os.path.join(self.dir, "cmd", "inbox.lua"), body)
        return cid

    def wait_ack(self, cid, timeout=10.0):
        ack_path = os.path.join(self.dir, "ack", "%d.json" % cid)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(ack_path):
                with open(ack_path) as f:
                    ack = json.load(f)
                if ack.get("epoch") == self.epoch and ack.get("id") == cid:
                    os.remove(ack_path)
                    pend = os.path.join(self.dir, "cmd", "pending.json")
                    if os.path.exists(pend):
                        os.remove(pend)
                    return ack
                os.remove(ack_path)  # stale/foreign ack: discard, keep waiting
            time.sleep(0.05)
        raise TimeoutError(
            "no ack for command %d after %.1fs — INDETERMINATE: the bridge "
            "may or may not have executed it. Check `jusemu status`." %
            (cid, timeout))

    def request_stop(self):
        _write_atomic(os.path.join(self.dir, "stop.flag"), "stop")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scripts/emu && python3 -m unittest tests.test_jus_ipc -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/jus_ipc.py scripts/emu/tests/test_jus_ipc.py
git commit -m "feat(emu): hardened file IPC — pending records, epoch cleanup, id persistence"
```

---

### Task 4: CLI (`jusemu.py`)

Wires Tasks 1–3. Fixes from Codex round 2: single command id per run, `selftest` subcommand, non-interactive screenshot failure, validated poke/dump inputs, `main()` covered by tests with a mocked client, reproducibility metadata required.

**Files:**
- Create: `scripts/emu/jusemu.py`
- Test: `scripts/emu/tests/test_jusemu.py`

- [ ] **Step 1: Write the failing test**

```python
# scripts/emu/tests/test_jusemu.py
import json, os, tempfile, time, unittest
from unittest import mock
import jusemu


class TestArgBuilding(unittest.TestCase):
    def test_parser_has_all_subcommands(self):
        p = jusemu.build_parser()
        for cmd in ["run", "peek", "poke", "state", "dump", "watch",
                    "screenshot", "status", "stop", "selftest"]:
            args = p.parse_args([cmd] + jusemu.SMOKE_ARGS[cmd])
            self.assertEqual(args.command, cmd)

    def test_peek_with_chain(self):
        op, args = jusemu.build_peek(addr="0x78", length=2, chain="player")
        self.assertEqual(args["chain"], [0x023D2A74, 0x10])
        self.assertEqual(args["offset"], 0x78)

    def test_poke_rejects_odd_hex(self):
        with self.assertRaises(SystemExit):
            jusemu.parse_hexbytes("fff")

    def test_dump_range_validated(self):
        with self.assertRaises(SystemExit):
            jusemu.validate_dump_range(0x02000010, 0x02000000)  # reversed
        with self.assertRaises(SystemExit):
            jusemu.validate_dump_range(0x02000000, 0x02000000 + 0x500000)  # too big

    def test_run_timeout_scales(self):
        self.assertGreater(jusemu.run_timeout(3600), jusemu.run_timeout(60))


class TestMain(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.dir, "runs"))
        self.client = mock.Mock()
        self.client.epoch = "e1"
        self.client.next_id.return_value = 42
        self.client.publish_command.return_value = 42
        self.client.wait_ack.return_value = {"id": 42, "epoch": "e1",
                                             "ok": True, "result": {}}
        patcher = mock.patch("jusemu.IpcClient", return_value=self.client)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_run_uses_one_id_everywhere(self):
        plan_path = os.path.join(self.dir, "p.json")
        with open(plan_path, "w") as f:
            json.dump({"name": "t", "segments":
                       [{"from": 0, "to": 1, "buttons": ["A"]}]}, f)
        jusemu.main(["--ipc-dir", self.dir, "run", plan_path])
        # publish_command called with the pre-reserved id
        _, kwargs = self.client.publish_command.call_args
        self.assertEqual(kwargs.get("cmd_id"), 42)
        rd = os.path.join(self.dir, "runs", "t-42")
        self.assertTrue(os.path.isdir(rd))
        meta = json.load(open(os.path.join(rd, "meta.json")))
        self.assertEqual(meta["cmd_id"], 42)

    def test_run_meta_marks_missing_hashes(self):
        plan_path = os.path.join(self.dir, "p.json")
        with open(plan_path, "w") as f:
            json.dump({"name": "t", "segments":
                       [{"from": 0, "to": 1, "buttons": ["A"]}]}, f)
        jusemu.main(["--ipc-dir", self.dir, "run", plan_path])
        meta = json.load(open(os.path.join(self.dir, "runs", "t-42",
                                           "meta.json")))
        self.assertIn("reproducible", meta)  # False when hashes.json absent

    def test_selftest_invokes_bridge(self):
        jusemu.main(["--ipc-dir", self.dir, "selftest"])
        args, kwargs = self.client.publish_command.call_args
        self.assertEqual(args[0], "selftest")

    def test_paused_run_reports_frozen_not_failed(self):
        self.client.wait_ack.side_effect = TimeoutError("x")
        self.client.state.return_value = (jusemu.BridgeState.PAUSED, {})
        plan_path = os.path.join(self.dir, "p.json")
        with open(plan_path, "w") as f:
            json.dump({"name": "t", "segments":
                       [{"from": 0, "to": 1, "buttons": ["A"]}]}, f)
        jusemu.main(["--ipc-dir", self.dir, "run", plan_path])  # must not raise


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
  python3 jusemu.py selftest
  python3 jusemu.py peek 0x021DF1D5 1
  python3 jusemu.py peek 0x78 2 --chain player
  python3 jusemu.py state save training
  python3 jusemu.py run plans/example_walk_and_b.json
  python3 jusemu.py screenshot /tmp/shot.png
"""
import argparse, hashlib, json, os, subprocess, sys, time

from jus_addresses import CHAINS
from jus_ipc import IpcClient, BridgeState, DEFAULT_DIR
from jus_plan import validate_plan, validate_watches, plan_to_lua

MAX_DUMP_BYTES = 0x400000  # 4 MB (all of main RAM)

SMOKE_ARGS = {  # minimal valid argv per subcommand, used by tests
    "run": ["p.json"], "peek": ["0x02000000", "1"],
    "poke": ["0x02000000", "ff"], "state": ["save", "s"],
    "dump": ["0x02000000", "0x02000010", "out.bin"],
    "watch": ["set", "w.json"], "screenshot": ["out.png"],
    "status": [], "stop": [], "selftest": [],
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
    sc = sub.add_parser("screenshot")
    sc.add_argument("outfile")
    sc.add_argument("--interactive", action="store_true",
                    help="fall back to manual window selection")
    for name in ("status", "stop", "selftest"):
        sub.add_parser(name)
    return p


def die(msg):
    print("error: %s" % msg, file=sys.stderr)
    raise SystemExit(2)


def parse_hexbytes(s):
    if len(s) == 0 or len(s) % 2 != 0 or not all(
            c in "0123456789abcdefABCDEF" for c in s):
        die("hexbytes must be even-length hex, got %r" % s)
    return [int(s[i:i+2], 16) for i in range(0, len(s), 2)]


def validate_dump_range(start, end):
    if end <= start:
        die("dump end must be > start")
    if end - start > MAX_DUMP_BYTES:
        die("dump larger than %d bytes" % MAX_DUMP_BYTES)
    return start, end


def build_peek(addr, length, chain):
    a = int(addr, 0)
    validate_watches([{"name": "peek", "len": length}
                      | ({"chain": CHAINS[chain], "offset": a} if chain
                         else {"addr": a})])
    if chain:
        return "peek", {"chain": CHAINS[chain], "offset": a, "len": length}
    return "peek", {"addr": a, "len": length}


def run_timeout(total_frames):
    return total_frames / 30.0 + 15.0  # emulated speed >=30fps + slack


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def make_run_dir(ipc_dir, plan, cmd_id, epoch):
    rd = os.path.join(ipc_dir, "runs", "%s-%d" % (plan["name"], cmd_id))
    os.makedirs(rd, exist_ok=True)
    with open(os.path.join(rd, "plan.json"), "w") as f:
        json.dump(plan, f, indent=1)
    meta = {"epoch": epoch, "cmd_id": cmd_id, "created": time.time(),
            "plan_sha256": hashlib.sha256(
                json.dumps(plan, sort_keys=True).encode()).hexdigest(),
            "reproducible": False}
    here = os.path.dirname(os.path.abspath(__file__))
    build_info = os.path.join(here, "build_info.json")
    hashes = os.path.join(here, "hashes.json")  # rom/bios/fw/save/config
    if os.path.exists(build_info) and os.path.exists(hashes):
        meta["build"] = json.load(open(build_info))
        meta["hashes"] = json.load(open(hashes))
        cfg = meta["hashes"].get("melonds_config_path")
        if cfg and os.path.exists(os.path.expanduser(cfg)):
            meta["config_sha256"] = _sha(os.path.expanduser(cfg))
        meta["reproducible"] = True
    if plan.get("load_state"):
        sidecar = os.path.join(ipc_dir, "states",
                               plan["load_state"] + ".meta.json")
        if os.path.exists(sidecar):
            meta["state"] = json.load(open(sidecar))
    with open(os.path.join(rd, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return rd


def do_screenshot(outfile, interactive):
    script = ('tell application "System Events" to tell (first process '
              'whose name contains "melonDS") to get id of first window')
    win = subprocess.run(["osascript", "-e", script],
                         capture_output=True, text=True)
    if win.returncode != 0:
        if interactive:
            return subprocess.run(["screencapture", "-w", outfile]).returncode
        print("error: melonDS window not found (permissions? running?); "
              "use --interactive to pick a window manually", file=sys.stderr)
        return 1
    return subprocess.run(
        ["screencapture", "-l", win.stdout.strip(), outfile]).returncode


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "screenshot":
        raise SystemExit(do_screenshot(args.outfile, args.interactive))

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
        cid = client.next_id()
        rd = make_run_dir(args.ipc_dir, plan, cid, client.epoch)
        lua_path = os.path.join(rd, "plan.lua")
        with open(lua_path, "w") as f:
            f.write(plan_to_lua(plan))
        client.publish_command(
            "run_plan", {"plan_path": lua_path, "run_dir": rd}, cmd_id=cid)
        try:
            ack = client.wait_ack(cid, timeout=run_timeout(plan["total_frames"]))
        except TimeoutError:
            state, _ = client.state()
            if state == BridgeState.PAUSED:
                print("emulator paused (GDB?) — plan frozen, not failed. "
                      "Resume the emulator, then `jusemu status`.")
                return
            raise
        print(json.dumps(ack, indent=1))
        print("log: %s" % os.path.join(rd, "log.jsonl"))
        return

    if args.command == "peek":
        op, a = build_peek(args.addr, args.length, args.chain)
        timeout = 10.0
    elif args.command == "poke":
        op, a = "poke", {"addr": int(args.addr, 0),
                         "bytes": parse_hexbytes(args.hexbytes)}
        timeout = 10.0
    elif args.command == "state":
        op, a = "state_" + args.action, {"slot": args.slot}
        timeout = 30.0  # save/load are multi-frame state machines
    elif args.command == "dump":
        s, e = validate_dump_range(int(args.start, 0), int(args.end, 0))
        op, a = "dump", {"start": s, "end": e,
                         "outfile": os.path.abspath(args.outfile)}
        timeout = 60.0
    elif args.command == "watch":
        specs = validate_watches(json.load(open(args.spec)))
        op, a = "set_watches", {"specs": specs}
        timeout = 10.0
    elif args.command == "selftest":
        op, a = "selftest", {}
        timeout = 30.0
    cid = client.publish_command(op, a)
    print(json.dumps(client.wait_ack(cid, timeout=timeout), indent=1))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests**

Run: `cd scripts/emu && python3 -m unittest discover tests -v`
Expected: all tests from Tasks 1–4 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/jusemu.py scripts/emu/tests/test_jusemu.py
git commit -m "feat(emu): jusemu CLI — single-id runs, selftest, validated inputs"
```

---

### Task 5: Build the fork (`build_melonds_lua.sh`) — human checkpoint

**Files:**
- Create: `scripts/emu/build_melonds_lua.sh`
- Create: `scripts/emu/README.md` (skeleton; grows in later tasks)
- Create: `scripts/emu/hashes.json` (after human checkpoint)

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
Expected: `Built: .../melonDS.app`. If CMake/compile errors: this is the spec's M1 timebox — spend up to a day, document each fix in `scripts/emu/README.md`. If truly blocked, STOP and consult the user about the keystroke-automation fallback.

- [ ] **Step 3: Pin the commit**

Edit `build_melonds_lua.sh`: replace `master` in the `PINNED_COMMIT` default with the hash the build printed.

- [ ] **Step 4: Human checkpoint — boot the game and record hashes**

Ask the user to: open the built app, point it at BIOS/firmware/ROM, enable the GDB stub (ARM9 port 3333), load the JUS ROM, confirm the Lua console exists (Tools menu). Then create `scripts/emu/hashes.json`:

```json
{
  "rom_sha256": "<shasum -a 256 of the ROM>",
  "bios9_sha256": "<...>", "bios7_sha256": "<...>",
  "firmware_sha256": "<...>", "save_sha256": "<...>",
  "melonds_config_path": "~/Library/Application Support/melonDS/melonDS.toml"
}
```
(Verify the actual config path/format for this build and correct the value.)

- [ ] **Step 5: Write README skeleton and commit**

`scripts/emu/README.md` must contain: purpose (one paragraph), build instructions, the pinned commit, the hash table, an empty "Verified behavior (spike findings)" section, and an empty "Combined Lua+GDB workflow" section.

```bash
git add scripts/emu/build_melonds_lua.sh scripts/emu/README.md scripts/emu/build_info.json scripts/emu/hashes.json
git commit -m "feat(emu): pinned melonDS-lua build script + hashes + README skeleton"
```

---

### Task 6: Spike S1–S2 (callback thread + I/O safety)

Timing is measured **externally** (Python watches the spike file's update rate) because Lua's `os.clock()` is CPU time, not wall time, and can hide blocking I/O (Codex finding #34).

**Files:**
- Create: `scripts/emu/spike/s1_s2_update_probe.lua`
- Create: `scripts/emu/spike/s2_timing_monitor.py`
- Modify: `scripts/emu/README.md`

- [ ] **Step 1: Write the probe script**

```lua
-- scripts/emu/spike/s1_s2_update_probe.lua
-- S1: does _Update() fire per frame? during pause? during GDB stop?
-- S2: is synchronous file I/O safe from the callback? (timing judged
--     externally by s2_timing_monitor.py; os.clock() is CPU-time only)
local count = 0

function _Update()
    count = count + 1
    -- representative I/O: heartbeat-like rename publication every frame
    local f = io.open("/tmp/jus_emu_spike.tmp", "w")
    f:write(string.format('{"count":%d,"frame":%d}', count, emu.framecount()))
    f:close()
    os.rename("/tmp/jus_emu_spike.tmp", "/tmp/jus_emu_spike.json")
    -- representative memory load: 512 bytes over the ARM9 bus
    memory.read_bytes_as_array(0x021DF000, 512, "ARM9 System Bus")
    if count % 600 == 0 then
        print("frames=" .. count .. " framecount=" .. emu.framecount())
    end
end
```

```python
# scripts/emu/spike/s2_timing_monitor.py
"""Externally measure the spike callback rate and stalls.

Run while s1_s2_update_probe.lua is active. Reports effective callback
frequency and the largest inter-update gap over 30 seconds. If the
emulator's video output is smooth AND rate ~= 60/s with max gap < 100ms,
per-frame file I/O is acceptable.
"""
import json, time

SPIKE = "/tmp/jus_emu_spike.json"
seen, gaps, last_t, last_c = 0, [], None, None
t_end = time.time() + 30
while time.time() < t_end:
    try:
        with open(SPIKE) as f:
            c = json.load(f)["count"]
    except (OSError, ValueError):
        time.sleep(0.005)
        continue
    now = time.time()
    if last_c is not None and c != last_c:
        gaps.append(now - last_t)
        seen += c - last_c
    if c != last_c:
        last_t, last_c = now, c
    time.sleep(0.002)
print("updates seen: %d (%.1f/s), max gap %.1f ms" %
      (seen, seen / 30.0, max(gaps) * 1000 if gaps else -1))
```

- [ ] **Step 2: Run the experiments**

With the game running, load the Lua probe, then `python3 scripts/emu/spike/s2_timing_monitor.py`. Record:
1. Rate ≈ 60/s with small max gap, and the game visibly smooth → per-frame I/O acceptable.
2. Pause the emulator from the frontend menu: does the spike file keep updating? Record yes/no.
3. Connect GDB (`target remote localhost:3333` — halts the core): does it keep updating? Record. `continue`, `Ctrl+C`, record again. Disconnect.

- [ ] **Step 3: Document findings**

Write results into README "Verified behavior": callback behavior during pause/GDB stop, measured rate and max gap, framecount-per-callback relation. If `_Update()` does NOT fire during GDB stops: the heartbeat `paused` inference is correct as designed. If the rate is meaningfully below the emulator's fps or the game stutters: STOP and consult the user — the bridge needs the Qt-timer fallback (spec §12) before Task 9.

- [ ] **Step 4: Commit**

```bash
git add scripts/emu/spike/ scripts/emu/README.md
git commit -m "spike(emu): S1/S2 callback + externally-measured I/O timing findings"
```

---

### Task 7: Spike S4–S5 (savestate settling, GDB survival)

**Files:**
- Create: `scripts/emu/spike/s4_savestate_probe.lua`
- Modify: `scripts/emu/README.md`

- [ ] **Step 1: Write the savestate probe**

The authoritative settle signal (Codex #26/#28): at save time record `emu.framecount()`; a load has settled when `emu.framecount()` **equals a value at-or-near the recorded one** (states restore the counter) — not merely any discontinuity. The probe verifies that assumption:

```lua
-- scripts/emu/spike/s4_savestate_probe.lua
-- S4: async savestate semantics. Run with MODE="save" in a battle at a
-- memorable moment, then MODE="load" after playing further.
local MODE = "load"  -- "save" | "load"
local issued_at, saved_fc = nil, nil
local marker = math.random(1, 1e9)  -- Lua VM state: should survive load

function _Update()
    local fc = emu.framecount()
    if issued_at == nil then
        issued_at = fc
        if MODE == "save" then
            savestate.save("/tmp/jus_emu_spike_state.mln")
            print("save issued at frame " .. fc .. " marker=" .. marker)
        else
            savestate.load("/tmp/jus_emu_spike_state.mln")
            print("load issued at frame " .. fc .. " marker=" .. marker)
        end
        return
    end
    -- log every callback for 120 callbacks so the settle profile is visible
    if fc ~= issued_at then
        print(string.format("cb: framecount=%d (issued_at=%d) marker=%d",
                            fc, issued_at, marker))
        issued_at = fc
    end
end
```

- [ ] **Step 2: Run S4 and record**

Run save-mode, note the frame number printed. Play ~10 seconds. Run load-mode. Record in README: (a) how many callbacks until framecount jumps, (b) whether it jumps **to the frame recorded at save time** (this is the settle signal the bridge uses), (c) whether `marker` survived (Lua VM outside savestate), (d) whether a save's file appears immediately or frames later (`ls -la /tmp/jus_emu_spike_state.mln` timestamps). If framecount is NOT restored to the saved value, STOP: the bridge's settle detection (Task 9) must switch to the fallback — extend the C++ patch with a `client.state_op_done()` completion flag set by the Qt save/load handlers — and this plan's Task 8/9 code must be adjusted accordingly before proceeding.

- [ ] **Step 3: Run S5 (GDB vs savestate)**

With GDB connected and a breakpoint set (`break *0x020784FC`), issue a `savestate.load` from the Lua console. Record: does GDB stay connected? Does the breakpoint still fire after load? Write the resulting rule into README (expected: "disconnect GDB before state loads" until proven otherwise).

- [ ] **Step 4: Commit**

```bash
git add scripts/emu/spike/s4_savestate_probe.lua scripts/emu/README.md
git commit -m "spike(emu): S4/S5 savestate settle signal and GDB-survival findings"
```

---

### Task 8: `joypad.set` patch (M2)

Patch scope (Codex #29–#33): atomic fields, lifecycle cleanup on script stop and ROM reset, a `joypad.get_committed()` readback of the mask actually committed to the core (so S3 measures core-visible timing, not Lua-side latch state).

**Files:**
- Create: `scripts/emu/patches/joypad-set.patch`
- Create: `scripts/emu/spike/s3_input_readback.lua`

- [ ] **Step 1: Locate the input commit point and its thread**

In the fork checkout:
```bash
grep -rn "SetKeyMask\|keyMask\|inputMask" src/frontend/qt_sdl/ src/NDS.h | head -30
grep -rn "onStop\|luaState = nullptr\|deleteLater" src/frontend/qt_sdl/lua/ | head
```
Identify: (a) the single authoritative call site passing the key mask to the core (trace *all* writers — hotkeys, turbo, focus handling — and confirm nothing overwrites after it); (b) which thread runs it vs. which thread runs Lua (cross-check the S1 finding); (c) the Lua console's stop/unload path for cleanup hooks.

- [ ] **Step 2: Implement the patch**

Shape (adjust names to what Step 1 found):

`EmuInstance.h`:
```cpp
#include <atomic>
// Lua input override (agent bridge). Active-low 12-bit mask, order:
// A,B,Select,Start,Right,Left,Up,Down,R,L,X,Y. Atomics because Lua and
// the input commit point may run on different threads (spike S1).
std::atomic<bool>     luaInputOverride {false};
std::atomic<uint32_t> luaInputMask {0xFFF};
std::atomic<uint32_t> lastCommittedMask {0xFFF}; // readback for joypad.get_committed
```

At the located commit point:
```cpp
uint32_t mask = inputMask;                     // existing host-derived mask
if (luaInputOverride.load(std::memory_order_relaxed))
    mask = luaInputMask.load(std::memory_order_relaxed);
lastCommittedMask.store(mask, std::memory_order_relaxed);
nds->SetKeyMask(mask);
```

In the Lua console's stop/unload path (found in Step 1c) and in the emulator's ROM-reset/close path:
```cpp
emuInstance->luaInputOverride = false;
emuInstance->luaInputMask = 0xFFF;
```

`LuaInput.cpp`:
```cpp
static const char* joyOrder[12] = {
    "A","B","Select","Start","Right","Left","Up","Down","R","L","X","Y"};

int Lua_setJoy(lua_State* L)  // joypad.set(table|nil)
{
    LuaBundle* bundle = get_bundle(L);
    EmuInstance* inst = bundle->getEmuInstance();
    if (lua_isnoneornil(L,1))   // release: physical input returns
    {
        inst->luaInputOverride = false;
        inst->luaInputMask = 0xFFF;
        return 0;
    }
    luaL_checktype(L,1,LUA_TTABLE);  // {} = force-neutral override
    uint32_t mask = 0xFFF;           // all released (active low)
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

int Lua_getCommitted(lua_State* L)  // joypad.get_committed() -> table
{
    LuaBundle* bundle = get_bundle(L);
    uint32_t mask = bundle->getEmuInstance()->lastCommittedMask.load();
    lua_createtable(L,0,12);
    for (int i = 0; i < 12; i++)
    {
        lua_pushboolean(L, !(mask & (1u << i)));   // active low -> pressed
        lua_setfield(L,-2,joyOrder[i]);
    }
    return 1;
}
AddJoypadFunction(Lua_getCommitted,get_committed);
```

Generate: `cd $SRC_DIR && git diff > <repo>/scripts/emu/patches/joypad-set.patch`, rebuild via `build_melonds_lua.sh`.

- [ ] **Step 3: Write the edge-accuracy readback test (settles S3)**

```lua
-- scripts/emu/spike/s3_input_readback.lua
-- Latch B on rel frames 60-62; read back the CORE-COMMITTED mask.
local start, log = nil, {}
function _Update()
    local fc = emu.framecount()
    if start == nil then start = fc; joypad.set({}) end
    local rel = fc - start
    if rel >= 60 and rel <= 62 then joypad.set({B = true})
    elseif rel == 63 then joypad.set({}) end
    if rel >= 55 and rel <= 70 then
        local c = joypad.get_committed()
        log[#log+1] = string.format("rel=%d committed_B=%s", rel,
                                    tostring(c.B))
    end
    if rel == 71 then
        joypad.set(nil)
        for _, line in ipairs(log) do print(line) end
    end
end
```

- [ ] **Step 4: Run and evaluate**

In a battle: load the script. PASS: `committed_B=true` on exactly 3 consecutive `rel` values. Record the offset between latch frame (60) and first committed frame in README as **`INPUT_APPLY_OFFSET`** (0 if same frame). Additional checks: hold Right 20 frames → character walks; hold a keyboard key during the latch → `get_committed` must NOT show it (override isolation); stop the script mid-press via the console Stop button → character stops acting (lifecycle cleanup works).

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/patches/joypad-set.patch scripts/emu/spike/s3_input_readback.lua scripts/emu/README.md
git commit -m "feat(emu): joypad.set/get_committed patch — atomic, lifecycle-safe (M2)"
```

---

### Task 9: Bridge core (`bridge_core.lua`) with unit tests, then bindings (`agent_bridge.lua`) — M3

Split per Codex #36: `bridge_core.lua` is pure logic (canonical JSON, segment masks, plan/settle state machines) unit-tested with the `lua5.4` CLI; `agent_bridge.lua` binds it to emulator + filesystem.

**Files:**
- Create: `scripts/emu/bridge_core.lua`
- Create: `scripts/emu/tests/test_bridge_core.lua`
- Create: `scripts/emu/agent_bridge.lua`

- [ ] **Step 1: Write the failing core tests**

```lua
-- scripts/emu/tests/test_bridge_core.lua
-- Run: lua5.4 scripts/emu/tests/test_bridge_core.lua  (from repo root)
package.path = "scripts/emu/?.lua;" .. package.path
local core = require("bridge_core")
local passed, failed = 0, 0
local function eq(a, b, msg)
    if a == b then passed = passed + 1
    else failed = failed + 1; print("FAIL: " .. msg ..
         " expected=" .. tostring(b) .. " got=" .. tostring(a)) end
end

-- jenc: canonical (sorted keys), NULL sentinel, empty-object support
eq(core.jenc({b = 1, a = 2}), '{"a":2,"b":1}', "sorted keys")
eq(core.jenc({1, 2, 3}), "[1,2,3]", "array")
eq(core.jenc(core.NULL), "null", "null sentinel")
eq(core.jenc(core.obj({})), "{}", "empty object not array")
eq(core.jenc({x = core.NULL}), '{"x":null}', "null value kept")
eq(core.jenc('a"\n'), '"a\\"\\n"', "string escaping")

-- segment lookup: gaps are force-neutral, not release
local plan = { segments = {
    { ["from"] = 0, ["to"] = 2, buttons = {"Right"} },
    { ["from"] = 5, ["to"] = 6, buttons = {"B"}, touch = nil },
  }, total_frames = 10 }
local m = core.mask_for_frame(plan, 1)
eq(m.buttons.Right, true, "in-segment button")
m = core.mask_for_frame(plan, 3)
eq(next(m.buttons), nil, "gap = empty pressed set")
eq(m.neutral_override, true, "gap keeps override active")
m = core.mask_for_frame(plan, 9)
eq(m.neutral_override, true, "tail keeps override active")

-- pressed list in fixed canonical order
local pl = core.pressed_list({ B = true, A = true, Right = true })
eq(table.concat(pl, ","), "A,B,Right", "canonical button order")

-- plan machine: init -> running -> done, with per-frame records
local pm = core.new_plan_machine(plan, { }, 0)
local rec
for i = 1, 10 do rec = pm:step(function() return {} end) end
eq(pm.state, "done", "plan machine completes")
eq(rec.f, 9, "last frame index")

-- settle machine: settles when framecount hits the sidecar target
local sm = core.new_settle_machine(1000, 60)   -- target fc, max wait
eq(sm:step(1500), "waiting", "not settled at other fc")
eq(sm:step(1000), "settled", "settled at target fc")
local sm2 = core.new_settle_machine(1000, 2)
sm2:step(1500); sm2:step(1501)
eq(sm2:step(1502), "timeout", "settle timeout")

print(string.format("passed=%d failed=%d", passed, failed))
os.exit(failed == 0 and 0 or 1)
```

- [ ] **Step 2: Run to verify failure**

Run: `lua5.4 scripts/emu/tests/test_bridge_core.lua`
Expected: error, `module 'bridge_core' not found` (install via `brew install lua@5.4` if the binary is missing; it landed with Task 5's build deps).

- [ ] **Step 3: Write `bridge_core.lua`**

```lua
-- scripts/emu/bridge_core.lua
-- Pure logic for the agent bridge: canonical JSON, plan/settle machines.
-- No emulator or filesystem access; unit-tested with lua5.4 CLI.
local M = {}

M.NULL = setmetatable({}, { __tostring = function() return "null" end })
local OBJ = {}
function M.obj(t) return setmetatable(t, OBJ) end  -- force object encoding

M.BUTTON_ORDER = { "A","B","Select","Start","Right","Left","Up","Down",
                   "R","L","X","Y" }

local function esc(s)
    return (s:gsub('[%c"\\]', function(c)
        if c == '"' then return '\\"' end
        if c == "\\" then return "\\\\" end
        if c == "\n" then return "\\n" end
        if c == "\r" then return "\\r" end
        if c == "\t" then return "\\t" end
        return string.format("\\u%04x", c:byte())
    end))
end

function M.jenc(v)
    if v == M.NULL or v == nil then return "null" end
    local t = type(v)
    if t == "number" then return string.format("%.17g", v) end
    if t == "boolean" then return tostring(v) end
    if t == "string" then return '"' .. esc(v) .. '"' end
    if t == "table" then
        local is_obj = getmetatable(v) == OBJ
        if not is_obj and (#v > 0 or next(v) == nil) then
            local parts = {}
            for _, x in ipairs(v) do parts[#parts+1] = M.jenc(x) end
            return "[" .. table.concat(parts, ",") .. "]"
        end
        local keys = {}
        for k in pairs(v) do keys[#keys+1] = tostring(k) end
        table.sort(keys)
        local parts = {}
        for _, k in ipairs(keys) do
            parts[#parts+1] = '"' .. esc(k) .. '":' .. M.jenc(v[k])
        end
        return "{" .. table.concat(parts, ",") .. "}"
    end
    error("unencodable type: " .. t)
end

-- Which buttons/touch are active on a logical plan frame.
-- Gaps and tail return an empty pressed set with neutral_override=true:
-- the override stays on for the whole plan (physical input stays locked out).
function M.mask_for_frame(plan, frame)
    for _, seg in ipairs(plan.segments) do
        if frame >= seg["from"] and frame <= seg["to"] then
            local buttons = {}
            if seg.buttons then
                for _, b in ipairs(seg.buttons) do buttons[b] = true end
            end
            return { buttons = buttons, touch = seg.touch,
                     neutral_override = true }
        end
    end
    return { buttons = {}, touch = nil, neutral_override = true }
end

function M.pressed_list(buttons)
    local out = {}
    for _, b in ipairs(M.BUTTON_ORDER) do
        if buttons[b] then out[#out+1] = b end
    end
    return out
end

-- Plan machine: one step per _Update(); read_watches is injected.
function M.new_plan_machine(plan, watches, input_apply_offset)
    local pm = { plan = plan, watches = watches, frame = 0,
                 offset = input_apply_offset or 0, state = "running" }
    function pm:step(read_watch_fn)
        local eff = self.frame + self.offset
        local mask = M.mask_for_frame(self.plan, eff)
        local w = M.obj({})
        for _, spec in ipairs(self.watches) do
            local v = read_watch_fn(spec)
            w[spec.name] = (v == nil) and M.NULL or v
        end
        local rec = { f = self.frame, latch = M.pressed_list(mask.buttons),
                      w = w }
        self.frame = self.frame + 1
        if self.frame >= self.plan.total_frames then self.state = "done" end
        return rec, mask
    end
    return pm
end

-- Settle machine: load has settled when framecount == target (sidecar's
-- framecount_at_save; spike S4 verified states restore the counter).
function M.new_settle_machine(target_fc, max_waits)
    local sm = { target = target_fc, waited = 0, max = max_waits }
    function sm:step(fc)
        if fc == self.target then return "settled" end
        self.waited = self.waited + 1
        if self.waited >= self.max then return "timeout" end
        return "waiting"
    end
    return sm
end

return M
```

- [ ] **Step 4: Run core tests to verify pass**

Run: `lua5.4 scripts/emu/tests/test_bridge_core.lua`
Expected: `passed=N failed=0`, exit 0.

- [ ] **Step 5: Commit the core**

```bash
git add scripts/emu/bridge_core.lua scripts/emu/tests/test_bridge_core.lua
git commit -m "feat(emu): bridge core — canonical JSON, plan/settle machines, unit-tested"
```

- [ ] **Step 6: Write `agent_bridge.lua` (bindings)**

```lua
-- scripts/emu/agent_bridge.lua
-- Agent control bridge. Load once in melonDS's Lua console.
-- Protocol: scripts/emu/jus_ipc.py docstring + spec §3.
package.path = (os.getenv("JUS_EMU_SRC") or "scripts/emu") .. "/?.lua;"
    .. package.path
local core = require("bridge_core")

local IPC_DIR = os.getenv("JUS_EMU_DIR") or "/tmp/jus_emu"
local BUS = "ARM9 System Bus"
local POLL_INTERVAL = 10
local SETTLE_MAX = 120            -- callbacks; S4-informed
local SAVE_STABLE_POLLS = 3       -- save done = file size stable this long
local FLUSH_EVERY = 600
local MAIN_RAM_LO, MAIN_RAM_HI = 0x02000000, 0x02400000
local INPUT_APPLY_OFFSET = 0      -- set from S3 finding in README

local session = tostring(os.time()) .. "-" .. tostring(math.random(1e6))
local state = "idle"  -- idle|plan_running|loading_state|saving_state|flushing
local tick = 0
local pm, run_dir, cmd_id, log_buf = nil, nil, nil, {}
local settle, pending_plan = nil, nil
local saving = nil                -- {slot, path, last_size, stable, id}
local default_watches = {}

-- ---------- io ------------------------------------------------------------
local function write_atomic(path, content)
    local f = assert(io.open(path .. ".tmp", "w"))
    f:write(content); f:close()
    assert(os.rename(path .. ".tmp", path))  -- POSIX rename clobbers
end

local function heartbeat()
    write_atomic(IPC_DIR .. "/heartbeat.json", core.jenc(core.obj({
        session = session, framecount = emu.framecount(),
        wallclock = os.time(), state = state })))
end

local function ack(id, ok, payload)
    local body = core.obj({ id = id, epoch = session, ok = ok })
    if ok then body.result = payload else body.error = tostring(payload) end
    write_atomic(IPC_DIR .. "/ack/" .. id .. ".json", core.jenc(body))
end

-- ---------- input (see plan header for set({})/set(nil) semantics) --------
local function force_neutral() joypad.set({}); input.NDSTapUp() end
local function release_override() joypad.set(nil); input.NDSTapUp() end

-- ---------- memory ----------------------------------------------------------
local function valid_ptr(p)
    return p >= MAIN_RAM_LO and p < MAIN_RAM_HI and p % 4 == 0
end

local function resolve_chain(chain)
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

-- ---------- logging ----------------------------------------------------------
local function flush_log()
    if run_dir == nil or #log_buf == 0 then return end
    local f = assert(io.open(run_dir .. "/log.jsonl", "a"))
    f:write(table.concat(log_buf, "\n")); f:write("\n"); f:close()
    log_buf = {}
end

-- ---------- savestate sidecars ----------------------------------------------
local function state_path(slot) return IPC_DIR .. "/states/" .. slot end

local function write_sidecar(slot)
    write_atomic(state_path(slot) .. ".meta.json", core.jenc(core.obj({
        slot = slot, framecount_at_save = emu.framecount(),
        session = session, saved_at = os.time() })))
end

local function read_sidecar(slot)
    local f = io.open(state_path(slot) .. ".meta.json", "r")
    if f == nil then return nil end
    local body = f:read("a"); f:close()
    -- minimal parse: extract framecount_at_save integer
    local fc = body:match('"framecount_at_save":(%d+)')
    return fc and tonumber(fc) or nil
end

-- ---------- plan lifecycle ----------------------------------------------------
local function abort_plan(reason)
    force_neutral()
    if run_dir then
        log_buf[#log_buf+1] = core.jenc(core.obj({ aborted = tostring(reason),
                                                   f = pm and pm.frame or 0 }))
        flush_log()
    end
    if cmd_id then ack(cmd_id, false, reason) end
    release_override()
    pm, run_dir, cmd_id, pending_plan, settle, state = nil, nil, nil, nil, nil, "idle"
end

local function finish_plan()
    force_neutral()
    flush_log()
    write_atomic(run_dir .. "/done-" .. cmd_id .. ".json",
                 core.jenc(core.obj({ frames = pm.frame, ok = true,
                                      epoch = session })))
    ack(cmd_id, true, core.obj({ frames = pm.frame,
                                 log = run_dir .. "/log.jsonl" }))
    release_override()
    pm, run_dir, cmd_id, state = nil, nil, nil, "idle"
end

local function start_plan(p)
    pm = core.new_plan_machine(p, p.watches or default_watches,
                               INPUT_APPLY_OFFSET)
    log_buf = {}
    state = "plan_running"
end

local function plan_step()
    local rec, mask = pm:step(read_watch)
    if next(mask.buttons) then joypad.set(mask.buttons) else force_neutral() end
    if mask.touch then input.NDSTapDown(mask.touch.x, mask.touch.y)
    else input.NDSTapUp() end
    log_buf[#log_buf+1] = core.jenc(rec)
    if #log_buf >= FLUSH_EVERY then flush_log() end
    if pm.state == "done" then finish_plan() end
end

-- ---------- state machines: load / save ----------------------------------------
local function begin_state_load(id, slot, then_plan)
    local target = read_sidecar(slot)
    if target == nil then
        ack(id, false, "no sidecar for state '" .. slot ..
            "' (unknown or pre-protocol savestate)")
        return
    end
    force_neutral()                          -- spec: neutral before load
    cmd_id, pending_plan = id, then_plan
    savestate.load(state_path(slot) .. ".mln")
    settle = core.new_settle_machine(target, SETTLE_MAX)
    state = "loading_state"
end

local function settle_step()
    local r = settle:step(emu.framecount())
    if r == "settled" then
        settle = nil
        if pending_plan then
            local p = pending_plan; pending_plan = nil
            start_plan(p)
        else
            ack(cmd_id, true, core.obj({ loaded = true,
                                         framecount = emu.framecount() }))
            cmd_id, state = nil, "idle"
            release_override()
        end
    elseif r == "timeout" then
        abort_plan("state load did not settle (framecount never hit target)")
    end
end

local function begin_state_save(id, slot)
    saving = { slot = slot, path = state_path(slot) .. ".mln",
               last_size = -1, stable = 0, id = id }
    os.remove(saving.path)
    savestate.save(saving.path)
    state = "saving_state"
end

local function saving_step()
    local f = io.open(saving.path, "rb")
    local size = -1
    if f then size = f:seek("end"); f:close() end
    if size > 0 and size == saving.last_size then
        saving.stable = saving.stable + 1
        if saving.stable >= SAVE_STABLE_POLLS then
            write_sidecar(saving.slot)
            ack(saving.id, true, core.obj({ slot = saving.slot,
                                            bytes = size }))
            saving, state = nil, "idle"
            return
        end
    else
        saving.stable = 0
    end
    saving.last_size = size
    saving.waited = (saving.waited or 0) + 1
    if saving.waited > SETTLE_MAX then
        ack(saving.id, false, "savestate.save produced no stable file")
        saving, state = nil, "idle"
    end
end

-- ---------- selftest (multi-frame; spec §8) --------------------------------------
local selftest = nil
local function begin_selftest(id)
    -- phase 1: heavy watch read + timing; phase 2: save; phase 3: load+settle
    local t0 = os.time()
    local bytes = memory.read_bytes_as_array(0x021DF000, 512, BUS)
    selftest = { id = id, read_ok = #bytes == 512, t0 = t0,
                 fc0 = emu.framecount() }
    begin_state_save(id, "_selftest")
    -- saving_step acks the save; we intercept by wrapping: simplest is to
    -- let save ack, then CLI runs `state load _selftest` as step 2 of the
    -- selftest procedure (documented in README).
    selftest = nil
    -- report the synchronous half immediately in the save ack via sidecar
end

-- ---------- commands --------------------------------------------------------------
local handlers = {}

function handlers.status(args)
    return core.obj({ state = state, framecount = emu.framecount(),
                      session = session,
                      plan = pm and pm.plan.name or core.NULL })
end

function handlers.peek(args)
    local v = read_watch({ chain = args.chain, offset = args.offset,
                           addr = args.addr, len = args.len })
    if v == nil then error("pointer chain invalid (not in battle?)") end
    return core.obj({ value = v })
end

function handlers.poke(args)
    memory.write_bytes_as_array(args.addr, args.bytes, BUS)
    return core.obj({ written = #args.bytes })
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
    return core.obj({ bytes = args["end"] - args.start,
                      outfile = args.outfile })
end

function handlers.set_watches(args)
    if #args.specs > 32 then error("too many watches") end
    local total = 0
    for _, s in ipairs(args.specs) do total = total + (s.len or 0) end
    if total > 512 then error("watch byte budget exceeded") end
    default_watches = args.specs
    return core.obj({ count = #args.specs,
                      note = "applies to subsequent plans without watches" })
end

function handlers.selftest(args)
    -- synchronous half; async half = `state save _selftest` then
    -- `state load _selftest` driven by the CLI selftest procedure
    local bytes = memory.read_bytes_as_array(0x021DF000, 512, BUS)
    local fc1 = emu.framecount()
    return core.obj({ framecount = fc1, read_ok = #bytes == 512,
                      session = session })
end

local function poll_commands()
    local inbox = IPC_DIR .. "/cmd/inbox.lua"
    local f = io.open(inbox, "r")
    if f == nil then return end
    local content = f:read("a"); f:close()
    os.remove(inbox)
    local chunk = load(content, "cmd", "t", {})
    if chunk == nil then return end
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
        local pok, p = pchunk and pcall(pchunk) or false, nil
        if type(pok) == "boolean" and not pok then
            ack(cmd.id, false, "plan parse error"); return
        end
        if type(pok) == "table" then p = pok end  -- lua quirk guard
        if p == nil then
            local ok2, p2 = pcall(pchunk); if ok2 then p = p2 end
        end
        if type(p) ~= "table" then ack(cmd.id, false, "plan not a table"); return end
        run_dir, cmd_id = cmd.args.run_dir, cmd.id
        if p.load_state then
            begin_state_load(cmd.id, p.load_state, p)
        else
            start_plan(p)
        end
        return
    end
    if cmd.op == "state_load" then
        begin_state_load(cmd.id, cmd.args.slot, nil); return
    end
    if cmd.op == "state_save" then
        begin_state_save(cmd.id, cmd.args.slot); return
    end
    local h = handlers[cmd.op]
    if h == nil then ack(cmd.id, false, "unknown op " .. tostring(cmd.op)); return end
    local hok, result = pcall(h, cmd.args)
    ack(cmd.id, hok, result)
end

local function check_stop()
    local f = io.open(IPC_DIR .. "/stop.flag", "r")
    if f then
        f:close(); os.remove(IPC_DIR .. "/stop.flag")
        if state == "plan_running" or state == "loading_state" then
            abort_plan("stopped by client")
        end
    end
end

-- ---------- main loop -----------------------------------------------------------
os.execute("mkdir -p " .. IPC_DIR .. "/cmd " .. IPC_DIR .. "/ack " ..
           IPC_DIR .. "/runs " .. IPC_DIR .. "/states")
release_override()
heartbeat()
print("agent_bridge up, session " .. session)

function _Update()
    tick = tick + 1
    local ok, err = pcall(function()
        if state == "plan_running" then plan_step() end
        if state == "loading_state" then settle_step() end
        if state == "saving_state" then saving_step() end
        if tick % POLL_INTERVAL == 0 then
            heartbeat()
            check_stop()
            if state == "idle" then poll_commands() end
        end
    end)
    if not ok then
        pcall(force_neutral)
        pcall(abort_plan, "lua error: " .. tostring(err))
        pcall(release_override)
    end
end
```

Implementation note: the `run_plan` chunk-loading block above has a deliberately defensive double-`pcall`; simplify it during implementation to a single `local ok, p = pcall(pchunk)` followed by a `type(p) == "table"` check — the shown shape is the specification of behavior (reject unparseable/non-table plans with an error ack), not sacred code.

- [ ] **Step 7: Live smoke test**

With the game at any screen, load `agent_bridge.lua` in the Lua console (set `JUS_EMU_SRC` env or edit `package.path` to the repo's `scripts/emu`). Then:

```bash
cd scripts/emu
python3 jusemu.py status                 # state=idle, live framecount
python3 jusemu.py selftest               # read_ok=true
python3 jusemu.py peek 0x021DEA71 1      # battle timer address readable
```
Start a battle, then:
```bash
python3 jusemu.py peek 0x78 1 --chain player    # 0x22 on ground
python3 jusemu.py state save smoketest          # ack only after file stable + sidecar
ls /tmp/jus_emu/states/smoketest.*              # .mln and .meta.json both exist
python3 jusemu.py state load smoketest          # settles via sidecar framecount
python3 jusemu.py stop                          # no-op ok when idle
```
Error paths to exercise deliberately: `state load nosuchslot` (typed error ack), `peek 0x78 1 --chain player` while at the main menu (pointer-invalid error), a second CLI command while one is pending (refused).

- [ ] **Step 8: Commit**

```bash
git add scripts/emu/agent_bridge.lua
git commit -m "feat(emu): agent bridge bindings — command loop, save/load machines (M3)"
```

---

### Task 10: Bootstrap savestate + acceptance test (M4) — human checkpoint

**Files:**
- Create: `scripts/emu/plans/example_walk_and_b.json`

- [ ] **Step 1: Human checkpoint — create the training savestate**

Ask the user to boot into a free battle / training scenario (ideally Goku vs an idle CPU dummy, per the Phase1 guide), then:
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
    {"from": 25, "to": 27, "buttons": ["B"]}
  ],
  "tail_frames": 120,
  "watches": ["hp_all", "player_struct", "opponent_struct"]
}
```
Save as `scripts/emu/plans/example_walk_and_b.json`. Note the deliberate gap (frames 21–24) — it exercises force-neutral. Iterate segment frames until the B press connects; that iteration must be doable *without touching the emulator by hand*.

- [ ] **Step 3: Run acceptance**

```bash
python3 jusemu.py run plans/example_walk_and_b.json
```
PASS criteria (inspect `log.jsonl` in the printed run dir):
- `hp_all.o1` decreases at some frame N.
- `opponent_struct.0x78` enters the 0xC0 family near N.
- `latch` shows `["B"]` on exactly plan frames 25–27, `[]` on 21–24 and the tail.
- **Physical-input exclusion:** re-run while holding a keyboard arrow key the whole time; log must be unaffected (same latch values, same movement).
- **Mid-plan stop:** start the run, `python3 jusemu.py stop` mid-flight from a second shell; ack is an error, character stops (no stuck buttons), bridge returns to idle.

- [ ] **Step 4: Determinism check**

Run the plan twice (no keyboard input). Logs are canonical JSON (sorted keys, fixed button order), so:
```bash
diff <run1>/log.jsonl <run2>/log.jsonl && echo DETERMINISTIC
```
Expected: `DETERMINISTIC`. If not: find the first divergent line, classify it (game nondeterminism vs. watch-read timing), check recorded config (JIT off? frame limiter on?), record root cause + fix in README before proceeding.

- [ ] **Step 5: Commit**

```bash
git add scripts/emu/plans/example_walk_and_b.json scripts/emu/README.md
git commit -m "test(emu): M4 acceptance — gaps, stop, input exclusion, determinism"
```

---

### Task 11: GDB handoff workflow + first real cards (M5)

**Files:**
- Modify: `scripts/emu/README.md` (Combined Lua+GDB workflow section)

- [ ] **Step 1: Verify plan freeze/resume across a GDB stop**

Start a long plan (acceptance plan with `tail_frames: 600`). Mid-plan, connect GDB and `Ctrl+C` — `jusemu status` must report `paused` (not `dead`). `continue`; the plan must resume and complete with the correct total frames and no gap in `f` values in the log.

- [ ] **Step 2: Work 2–3 cards from the validation queue**

Use `docs/research/GDB-Validation-Queue.md` Session 1 (cards 2, 3, 9 are self-contained checks at `0x02078488`/`0x020783CC`). Per card: `state load training_goku` → set the card's breakpoint via existing GDB tooling → run the input plan that lands a hit → at the breakpoint, do the card's register/memory checks in GDB → `continue` → record the verdict in the queue doc. Respect the S5 rule about GDB connections across state loads.

- [ ] **Step 3: Document the combined workflow**

Write the README section with the exact command sequence used, including the S5 rule and the `paused` status behavior.

- [ ] **Step 4: Commit**

```bash
git add scripts/emu/README.md docs/research/GDB-Validation-Queue.md
git commit -m "docs(emu): combined Lua+GDB workflow; first validation cards done (M5)"
```

---

## Deferred (explicitly out of this plan, matching spec §11)

- Free-running watch logging + 100k-line rotation: `set_watches` only sets defaults for subsequent plans. Add a follow-up task if idle-time watching is ever needed.
- Migrating `jus_gdb_watcher.py` onto `jus_addresses.py`.
- Multi-client IPC, Windows/Linux bridges, framebuffer export from Lua.

## Self-review checklist (done at plan-writing time)

- Spec coverage: build+spike §2 → Tasks 5–7; bridge/CLI/IPC §3 → Tasks 3, 4, 9; input contract §4 → Task 8 (incl. lifecycle cleanup + `get_committed`); formats §5 → Tasks 2, 9 (sidecars, `done-<cmdid>.json`); failure modes §6 → Tasks 3, 9, 10 (stop/error paths exercised); determinism §7 → Task 10 (canonical JSON + config hash in meta); testing §8 → every task, plus `lua5.4` bridge-core tests and mocked `main()` tests; sequential GDB handoff → Task 11; screenshots → Task 4 (non-interactive failure).
- Codex round-2 findings: #1/#27/#29/#32 force-neutral vs release + C++ lifecycle (header vocabulary, Task 8, Task 9); #2/#17/#26/#28/#39 async savestate machines + sidecars + settle-by-saved-framecount (Tasks 7, 9); #3 `loading_state`/`saving_state` in both enums; #4/#19 lazy heartbeat + epoch cleanup; #5 rename-only atomics; #6/#11 persistent ids, epoch-validated acks, single id per run; #7 pending record; #8/#9 NULL sentinel + canonical ordering; #10/#12/#13/#16/#40 centralized validation everywhere; #14 log field renamed `latch` + offset in README; #15 control-char escaping (both emitters, tested); #21/#24 selftest as CLI command with documented async half; #22 `done-<cmdid>.json`; #23 non-interactive screenshot; #25 free-running watches explicitly deferred; #30 atomics; #31/#37 `get_committed` readback; #33 all-writers trace in Task 8 step 1; #34 external timing monitor; #35 interop exercised in live smoke + protocol edge tests in Task 3; #36 bridge-core unit tests; #38 `main()` tests; #41 canonical JSON fixes diffability; #42 gap/tail/stop/input-exclusion acceptance criteria.
- Type consistency: ops (`run_plan`, `state_save`, `state_load`, `peek`, `poke`, `dump`, `set_watches`, `status`, `selftest`) match CLI↔bridge; watch fields (`name`, `addr`, `chain`, `offset`, `len`) match across all three modules; heartbeat states match `BridgeState`; log field is `latch` everywhere.
