# melonDS Agent Control Layer — Design

**Date:** 2026-08-14
**Status:** Draft, pending review
**Goal:** Let a Claude session drive melonDS unattended — inject inputs,
step through combat, read memory, manage savestates, capture screens — so
it can work through the GDB Validation Queue (~30 cards, est. 230
human-minutes) and the Human-Testing-Queue (89 pending tests) without a
human at the controls.

---

## 1. Problem

The repo already has a working *observation* layer: melonDS's GDB stub +
`scripts/gdb/jus_gdb_watcher.py` (snapshots, diffs, traces, known
addresses, working offline pointer chains). What's missing is *actuation*:
every documented workflow says "human provides controller input." The
melonDS GDB stub can never close this gap alone — it has no input control,
no hardware watchpoints, and unreliable `stepi`.

Required capabilities (all four confirmed as goals):

1. Damage/mechanics probes — trigger a move, read HP/struct diffs.
2. Frame data & hitboxes — startup/active/recovery, hitstun counts
   (needs frame accuracy).
3. Menu/deck automation — navigate menus, set up matchups.
4. Long exploratory sessions — savestate branching (try, rewind, vary).

## 2. Chosen approach

Build on **NPO-197's melonDS-lua fork** (the open melonDS PR #1671
branch), pinned to a specific commit, built on macOS with
`-DENABLE_GDB_STUB=ON` so the Lua and GDB planes run simultaneously.

Source inspection (2026-08-14, `NPO-197/melonDS-lua` master) confirms the
fork already provides:

| Capability | Lua API | Status |
| --- | --- | --- |
| Memory read/write | `memory.read_bytes_as_array`, `write_bytes_as_array`, typed reads, memory domains | ✅ present |
| Savestates | `savestate.save(f)`, `savestate.load(f)` | ✅ present |
| Touch input | `input.NDSTapDown(x,y)`, `input.NDSTapUp()` | ✅ present |
| Per-frame hook | `_Update()` called once per emulated frame | ✅ present |
| Frame counter | `emu.framecount()` | ✅ present |
| **Button injection** | `joypad` is **read-only** (`joypad.get`) | ❌ **must patch** |
| Pause / frame-step from Lua | absent (console button pauses the *script* only) | ❌ not needed (see §3) |

**The one required emulator patch:** add `joypad.set(table)` — inject a
12-button mask (A, B, X, Y, L, R, Start, Select, D-pad) into the
EmuInstance input path each frame, overriding (or OR-ing with) host
input while a script plan is active. Small change centred on
`src/frontend/qt_sdl/lua/libs/LuaInput.cpp` plus the input plumbing.
Offer it upstream to the PR branch after it's proven.

### Rejected alternatives

- **macOS keystroke automation** (AppleScript/cliclick on the melonDS
  window): zero emulator changes, but cannot hold a button for exactly N
  frames or land an input on a specific frame. Kept as *fallback bridge*
  if the fork won't build on macOS.
- **Full AgentServer fork** (JSON-RPC inside melonDS): best long-term
  ceiling, far more work. Revisit only if the Lua layer's ceiling is hit.
- **DeSmuME Lua / BizHawk:** Windows-centric; repo already standardized
  on melonDS for Mac (see `scripts/archive/jus_watcher-lua-README.md`).

## 3. Architecture: plan-executor, not interactive stepper

Instead of the agent interactively stepping frames (slow, chatty, and
unsupported), the Lua script is a **frame-accurate executor**. The agent
submits a *plan*; the bridge runs it deterministically at full speed and
returns a per-frame log. Frame data falls out of the log ("hitstun timer
0→18 on frame 24, 0 again on frame 42") with exact frame accuracy and no
stepping.

```text
Claude session
    |  CLI calls
    v
scripts/emu/jusemu.py          (Python, Claude-facing)
    |  command/response files (JSON), log tailing
    v
scripts/emu/agent_bridge.lua   (runs inside melonDS Lua console)
    |  direct Lua API calls, once per frame
    v
melonDS-lua core  <—— in parallel ——>  GDB stub :3333 (unchanged)
```

**IPC = files, not sockets.** The bridge polls a command file each frame
and appends JSON-lines to a response/log file. Rationale: no Lua socket
dependency in the fork, trivially debuggable, atomic-rename semantics are
enough at 60 Hz. Directory: `/tmp/jus_emu/` (gitignored; configurable).

### Component 1: `scripts/emu/agent_bridge.lua`

Loaded once via melonDS's Lua console. Every `_Update()` (i.e. every
emulated frame) it:

1. **Applies the active input plan** — a list of
   `{frame_start, frame_end, buttons=[...], touch={x,y}}` segments,
   executed relative to plan start frame.
2. **Evaluates watch specs** — absolute addresses and pointer chains
   (e.g. `[0x023D2A74] + 0x10` → player struct; `+0x00 → +0x10` →
   opponent struct, per `scripts/gdb/README.md`), reading declared
   fields/regions.
3. **Appends one JSON line** per frame to the run log: framecount,
   watched values, input applied.
4. **Checks the command file** for new instructions:
   `run_plan`, `state_save <slot>`, `state_load <slot>`,
   `peek <addr> <len>`, `poke <addr> <bytes>`, `dump <start> <end>`,
   `set_watches <spec>`, `status`, `stop`.
5. **Writes an ack/result file** per command id so the Python side can
   block until completion.

Plan completion (last segment's `frame_end` + optional tail frames)
finalizes the log and writes a `done` marker.

### Component 2: `scripts/emu/jusemu.py`

Claude-facing CLI (argparse subcommands; no daemon):

```text
jusemu run <plan.json> [--tail-frames N]   # execute plan, wait, print log path + summary
jusemu peek <addr> <len> [--chain player|opponent]
jusemu poke <addr> <hexbytes>
jusemu state save|load <slot>
jusemu dump <start> <end> <outfile>
jusemu watch set <watchspec.json>          # persistent per-frame watches
jusemu screenshot <outfile>                # macOS `screencapture -l <windowid>` first pass
jusemu status                              # bridge alive? framecount? active plan?
```

It writes command files, waits (with timeout) for the bridge's ack, and
prints structured results. Reuses address constants by importing/porting
the known-address table from `jus_gdb_watcher.py` into a shared
`scripts/emu/jus_addresses.py` (single source of truth; the GDB watcher
migrates to import it in a follow-up, not in this project).

### Component 3: emulator build

- Clone `NPO-197/melonDS-lua`, pin commit hash in
  `scripts/emu/README.md` and a `build_melonds_lua.sh` helper.
- Build with `-DENABLE_GDB_STUB=ON`; document Lua 5.4 dependency
  (`brew install lua@5.4`).
- Apply the `joypad.set` patch, kept as a `.patch` file in
  `scripts/emu/patches/` so the pinned upstream commit + patch is
  reproducible.
- Verify the Lua sandbox opens `io`/`os` (needed for file IPC); if the
  fork restricts them, extend the patch to expose a minimal
  `client.read_file`/`write_file` instead.

### Component 4: GDB plane (unchanged)

`jus_gdb_watcher.py` + `phase1_macros.gdb` continue to own breakpoints,
backtraces, and writer-PC bisection for the validation queue. Typical
combined session: Lua sets up the scenario (savestate load + input plan),
GDB catches the breakpoint when the code path fires.

## 4. Data formats

**Input plan** (`plan.json`):

```json
{
  "name": "goku_5b_on_raoh",
  "load_state": "slot_training_goku_raoh",
  "segments": [
    {"from": 0,  "to": 20, "buttons": ["RIGHT"]},
    {"from": 21, "to": 23, "buttons": ["B"]}
  ],
  "tail_frames": 120,
  "watches": ["player_struct", "opponent_struct", "hp_all"]
}
```

**Watch spec names** resolve via `jus_addresses.py` to either absolute
addresses or pointer chains. Custom specs allowed inline:
`{"name": "x", "chain": ["0x023D2A74", "+0x10"], "offset": "0x78", "len": 2}`.

**Per-frame log** (JSON lines):

```json
{"f": 1843, "in": ["B"], "w": {"player_struct.0x78": 34, "hp_all.p1": 40}}
```

Logs land in `/tmp/jus_emu/runs/<name>-<timestamp>/`, with the plan
copied alongside for replayability. Analysis scripts (frame-data
extraction, diffing) read these logs; first pass reuses the existing
diff mindset from `analyze_deck_dump.py`.

## 5. Error handling

- **Bridge dead / melonDS not running:** every `jusemu` command has a
  timeout (default 10 s) and reports "bridge not responding" with a
  checklist (emulator open? script loaded? paths match?).
- **Plan under/overrun:** bridge logs actual frames executed; `jusemu run`
  compares against expectation and flags mismatch.
- **Savestate slot missing:** bridge acks with an error payload; CLI
  surfaces it verbatim.
- **Pointer chain reads null/garbage** (e.g. not in battle): watch value
  logged as `null`, never crashes the frame loop; every bridge frame
  handler wrapped in `pcall`.
- **Log growth:** per-frame logs are bounded by plan length; long
  free-running watch mode rotates files at 100k lines.

## 6. Determinism & reproducibility

- Pin: melonDS-lua commit, patch set, ROM hash, BIOS/firmware hashes,
  save file. Record all of them in each run directory's `meta.json`.
- Prefer the **interpreter** (JIT off) for research runs.
- Savestate before every experiment; plans reference states by slot name
  so any run replays from its `meta.json` + plan.

## 7. Testing

- **Bridge unit-ish tests:** a `selftest` command — bridge echoes a
  counter, reads a known-constant ROM/RAM value, saves+loads a scratch
  savestate, reports framecount monotonicity.
- **End-to-end acceptance test (the "hello world"):** from a training
  savestate, run a plan that walks Goku right for 20 frames and presses
  B; assert the log shows opponent HP decreasing and the hitstun field
  (`+0x78` → `0xC0` family) toggling. This exercises input injection,
  watches, savestates, and logging in one shot.
- **Determinism check:** run the same plan twice from the same state;
  logs must be byte-identical (excluding timestamps).
- **CLI tests:** pure-Python unit tests for plan validation, address
  resolution, and IPC framing (no emulator needed).

## 8. Deliverables & placement

On `master` as shared infrastructure (usable by this session and the
battle-engine-atlas agent):

```text
scripts/emu/
  README.md              # build, setup, usage, pinned commit
  build_melonds_lua.sh
  patches/joypad-set.patch
  agent_bridge.lua
  jusemu.py
  jus_addresses.py
  plans/                 # example + reusable plans
docs/superpowers/specs/2026-08-14-melonds-agent-control-design.md  # this doc
```

## 9. Milestones

1. **M1 — Build:** melonDS-lua compiles and runs JUS on macOS with GDB
   stub enabled; Lua console loads a trivial script. (Fallback decision
   point: if blocked >1 day, stand up the keystroke bridge instead.)
2. **M2 — Patch:** `joypad.set` works — a Lua one-liner makes the
   character walk.
3. **M3 — Bridge + CLI:** command loop, watches, savestates, logging;
   selftest passes.
4. **M4 — Acceptance:** the Goku hello-world plan passes; determinism
   check passes.
5. **M5 — First real work:** knock out 2–3 cards from the GDB Validation
   Queue end-to-end using Lua setup + GDB breakpoints, and document the
   combined workflow in `scripts/emu/README.md`.

## 10. Out of scope (YAGNI)

- Sockets/JSON-RPC server, gRPC.
- Full AgentServer fork of melonDS.
- Taint tracking, write provenance, structured trace aggregation.
- Framebuffer pixel export from Lua (macOS `screencapture` is enough for
  now; revisit if menu automation needs pixel-diffing).
- Migrating `jus_gdb_watcher.py` onto `jus_addresses.py` (follow-up).
- Windows/Linux support for the bridge (Mac-first; nothing precludes it).

## 11. Risks

| Risk | Mitigation |
| --- | --- |
| Fork doesn't build on macOS / is stale vs. master | M1 timebox + keystroke-automation fallback |
| Lua sandbox lacks `io`/`os` for file IPC | Extend patch with minimal file read/write bindings |
| Input injection races host input | Plan-active flag overrides host input entirely during runs |
| Savestates incompatible across builds | Pin commit; states named per build in `meta.json` |
| GDB stub + Lua interact badly (pause states) | M5 explicitly tests combined use; if conflicted, run planes in separate sessions |
| `_Update()` timing ≠ exactly once per emulated frame | Verify against `emu.framecount()` in selftest; adjust hook point if needed |
