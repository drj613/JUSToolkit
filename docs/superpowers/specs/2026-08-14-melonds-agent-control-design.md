# melonDS Agent Control Layer — Design

**Date:** 2026-08-14 (rev 2, after Codex review)
**Status:** Draft, pending user review
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
`-DENABLE_GDB_STUB=ON` so the Lua and GDB planes coexist.

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

**The one required emulator patch:** add `joypad.set(mask)` per the
contract in §4. Kept as a `.patch` file in `scripts/emu/patches/` against
the pinned commit; offer it upstream once proven.

### Rejected alternatives

- **macOS keystroke automation** (AppleScript/cliclick on the melonDS
  window): zero emulator changes, but cannot hold a button for exactly N
  frames or land an input on a specific frame. Kept as *fallback bridge*
  if the fork won't build on macOS.
- **Full AgentServer fork** (JSON-RPC inside melonDS): best long-term
  ceiling, far more work. Revisit only if the Lua layer's ceiling is hit.
- **DeSmuME Lua / BizHawk:** Windows-centric; repo already standardized
  on melonDS for Mac (see `scripts/archive/jus_watcher-lua-README.md`).

### Validation spike gates the design (M1)

The Codex review correctly flagged that several primitives this design
leans on are *assumed*, not verified. M1 is therefore an explicit spike
that must answer, empirically, before the bridge is built:

- **S1:** Which thread calls `_Update()`, and does it keep firing when
  the frontend is paused / GDB is connected / a breakpoint has stopped
  ARM9? (Read the fork's source; confirm with a logging script.)
- **S2:** Are synchronous `io` open/read/append/rename and
  `savestate.save/load` safe from that callback? Measure worst-case
  callback time with a representative watch set (target: comfortably
  under one frame at 60 fps, ~16 ms).
- **S3:** Where in the frame does the DS core sample input, relative to
  `_Update()`? (Determines whether an injected mask takes effect on
  frame N or N+1 — the plan executor must know which.)
- **S4:** What does `savestate.load()` do to the currently executing
  callback, the frame counter, and Lua VM state?
- **S5:** Does a savestate load preserve a live GDB connection and
  installed breakpoints?

Spike findings get written into `scripts/emu/README.md` ("verified
behavior" section) and any design deltas come back to this spec before
M3. If S1/S2 fail (e.g. `_Update()` can't do file I/O safely), the
fallback inside the same architecture is: command polling moves to a
Qt-side timer patch, or IPC frequency drops further — the plan-executor
model survives either way.

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
    |  command/response files (JSON), heartbeat, logs
    v
scripts/emu/agent_bridge.lua   (runs inside melonDS Lua console)
    |  direct Lua API calls, per-frame hot path kept minimal
    v
melonDS-lua core  <—— sequential handoff ——>  GDB stub :3333 (unchanged)
```

**IPC = files, not sockets** — no Lua socket dependency, trivially
debuggable. Directory: `/tmp/jus_emu/` (configurable). But the hot path
is protected (Codex finding #1):

- **Per-frame work is in-memory only** while a plan runs: apply input
  mask, read watches, append the frame record to a Lua table.
- **Log flush** happens at plan completion (and every 600 frames for
  long runs), not per frame.
- **Command-file polling** happens every 10 frames when idle and is
  *suspended* while a plan is executing (plans are uninterruptible except
  by the `stop` sentinel file, checked every 10 frames).
- **Heartbeat:** every poll tick, the bridge rewrites
  `heartbeat.json` = `{session, framecount, wallclock, state}` where
  `state ∈ {idle, plan_running, flushing}`. The CLI uses wallclock
  staleness + process liveness to distinguish *dead bridge* from
  *emulator paused* (e.g. by GDB) — a stale heartbeat with a live
  melonDS process reports `paused`, not `dead`.

### Component 1: `scripts/emu/agent_bridge.lua`

Loaded once via melonDS's Lua console. Behavior:

- **Idle loop** (every 10th `_Update()`): read command file if its
  rename-published name changed; execute one command; write ack file;
  update heartbeat.
- **Plan execution:** on `run_plan`, (1) if the plan names a savestate,
  issue `savestate.load()` as the *only* action that frame; (2) plan
  frame 0 is defined as the first `_Update()` after the load completes
  (adjusted per S3/S4 findings); (3) each frame: apply the input mask
  for the current segment, read watches, buffer the record; (4) after
  the last segment + `tail_frames`, write the neutral mask, flush the
  log, write `done-<cmdid>.json`, return to idle.
- **Commands:** `run_plan`, `state_save <slot>`, `state_load <slot>`,
  `peek`, `poke`, `dump`, `set_watches`, `status`, `stop`, `selftest`.
- **Cleanup invariant:** the neutral input mask is written on *every*
  exit path — plan completion, per-frame `pcall` error, `stop`, script
  unload (finalizer), and before any `savestate.load`. Input release is
  ordered *before* log flush and ack writes so a failure later in the
  sequence can't leave a button held.
- **Error handling:** each frame's work runs in a `pcall`; on error the
  plan aborts, mask goes neutral, partial log is flushed with an
  `aborted: <reason>` marker, and an error ack is written. Watch reads
  additionally validate pointers before dereference: value must be in
  main-RAM range (`0x02000000–0x02400000`) and aligned; otherwise the
  watch logs `null` for that frame.

### Component 2: `scripts/emu/jusemu.py`

Claude-facing CLI (argparse subcommands; no daemon):

```text
jusemu run <plan.json>            # execute plan, wait, print log path + summary
jusemu peek <addr> <len> [--chain player|opponent]
jusemu poke <addr> <hexbytes>
jusemu state save|load <slot>
jusemu dump <start> <end> <outfile>
jusemu watch set <watchspec.json>
jusemu screenshot <outfile>       # macOS `screencapture -l <windowid>` first pass
jusemu status                     # idle/plan_running/paused/dead + framecount
jusemu stop                       # abort active plan (sentinel file)
```

**Protocol rules** (Codex findings #5, failure modes 4/6/7):

- **Session epoch:** the bridge generates a session id at script load and
  publishes it in `heartbeat.json`. Every command file embeds the epoch;
  the bridge rejects mismatches. On startup the CLI reads the heartbeat,
  adopts the epoch, and clears any stale command/ack files from previous
  epochs.
- **Command ids:** monotonically increasing per epoch, generated by the
  CLI. One ack file per id. Publication of command, ack, `done`, and
  `meta` files all uses write-temp-then-rename.
- **No automatic retries.** On timeout the CLI reports the command as
  *indeterminate* (it may or may not have executed) and tells the caller
  to check `status` before reissuing. `peek`/`dump`/`status` are safe to
  reissue; `poke`/`state`/`run_plan` are not auto-reissued.
- **Single client.** One emulator instance, one bridge, one CLI at a
  time is an explicit assumption; the CLI refuses to start a command if
  an unacked command file from the current epoch already exists.
- **Timeouts:** default 10 s for idle commands; for `run_plan`,
  timeout = expected frames ÷ 30 fps + 15 s slack (plans legitimately
  take a while). A `paused` status suppresses the timeout error and
  reports "emulator paused (GDB?), plan frozen at frame N" instead.

Address constants live in `scripts/emu/jus_addresses.py` (single source
of truth, ported from `jus_gdb_watcher.py`; the GDB watcher migrates to
import it in a follow-up, not in this project).

### Component 3: emulator build

- Clone `NPO-197/melonDS-lua`, pin the commit hash in
  `scripts/emu/README.md` and `build_melonds_lua.sh`.
- Build with `-DENABLE_GDB_STUB=ON`; document the Lua 5.4 dependency
  (`brew install lua@5.4`).
- Apply `patches/joypad-set.patch` (§4).
- Verify the Lua sandbox opens `io`/`os` (needed for file IPC); if
  restricted, extend the patch with minimal `client.read_file` /
  `client.write_file` bindings instead.

### Component 4: GDB plane — sequential handoff, not concurrent plans

v1 scope (Codex finding #3): **plans do not run across GDB stops.** The
combined workflow is sequential:

1. Lua plane: load savestate, run the input plan that produces the
   scenario, plan completes, bridge goes idle (inputs neutral).
2. GDB plane: connect (or already connected but `continue`d), set the
   card's breakpoint, then either the scenario's *next* plan triggers the
   code path or the agent replays the plan.
3. When the breakpoint fires, the emulator stops; the bridge heartbeat
   goes stale and `jusemu status` reports `paused`. The agent does its
   GDB work (registers, backtrace, memory) through the existing
   `jus_gdb_watcher.py`, then issues `continue`.
4. If a plan *was* running when the stop hit, it freezes mid-flight and
   resumes on `continue` (frame counting is emulated-frame based, so the
   plan stays frame-accurate across the stop — verified in M5).

GDB `continue` ownership: the agent (or human) driving the GDB session
owns it; the bridge never touches the GDB connection. Whether a
`savestate.load` survives a live GDB connection is spike item S5; until
verified, the documented procedure is: disconnect GDB before loading
states, reconnect after.

## 4. Input injection contract (`joypad.set`)

Semantics (Codex finding #2):

- `joypad.set(mask)` sets a **persistent latch** in the frontend: the
  12-button mask replaces host input entirely, every frame, until
  `joypad.set(nil)` clears it. (Latch, not one-shot, so a dropped
  callback can't cause an unintended release; the bridge still calls it
  each frame for clarity.)
- The patch applies the latch at the point where the frontend commits
  key state to the core, *before* core input sampling for that frame.
  S3 verifies the effective-frame offset; the plan executor compensates
  so "press B on plan frame 21" means the core sees B on frame 21.
- While the latch is active, physical keyboard/controller input is
  ignored (no OR-ing — deterministic runs need exactly one input
  source). Emergency human override = the Lua console's Stop button,
  which unloads the script and fires the neutral-mask finalizer.
- Contradictory inputs (Left+Right, Up+Down) are rejected at plan
  validation time in the CLI, not silently passed through.
- Acceptance for M2 is edge-accurate, not "the character walks": a
  scripted 3-frame B press must show exactly 3 frames of B in a
  `joypad.get` readback log, at the expected frame numbers.

## 5. Data formats

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

- `from`/`to` are **inclusive** plan-frame numbers (plan frame 0 defined
  in §3). Segments must be non-overlapping and sorted; gaps between
  segments are neutral input. The CLI validates all of this plus button
  names before submission.
- Touch segments: `{"from": n, "to": m, "touch": {"x": 128, "y": 96}}`;
  `NDSTapUp()` is issued automatically at segment end and plan end.

**Watch specs** resolve via `jus_addresses.py` to absolute addresses or
pointer chains. Custom inline specs:
`{"name": "x", "chain": ["0x023D2A74", "+0x10"], "offset": "0x78", "len": 2}`.
Limits: ≤32 watches, ≤512 bytes read per frame, chain depth ≤3
(validated by the CLI; keeps the frame budget bounded per S2).

**Per-frame log** (JSON lines, buffered, flushed per §3). Values are
memory state sampled in `_Update()` — whether that is pre- or
post-frame-N game logic is pinned down by S3 and documented; what matters
is that it's the *same* point every frame:

```json
{"f": 1843, "in": ["B"], "w": {"player_struct.0x78": 34, "hp_all.p1": 40}}
```

Runs land in `/tmp/jus_emu/runs/<name>-<cmdid>/` with the plan and
`meta.json` copied alongside. `meta.json` records: fork commit + patch
hashes, ROM/BIOS/firmware/save hashes, **melonDS config hash**
(`melonDS.ini`), savestate slot + its build tag, plan hash, session
epoch. Long free-running watch mode rotates logs at 100k lines.

**Savestate slots:** `slot name → /tmp/jus_emu/states/<name>.mln` plus a
sidecar `<name>.meta.json` (build tag, ROM hash, created-at frame). Load
refuses on build/ROM mismatch. Saves are write-temp-then-rename.

## 6. Error handling & failure modes

Covered in §3/§4 invariants, plus:

- **Bridge dead vs paused vs busy:** heartbeat protocol (§3). `dead` →
  CLI prints a checklist (emulator open? script loaded? epoch match?).
- **Emulator crash mid-plan:** heartbeat goes stale with no live
  process; CLI reports last-known frame; the run directory keeps the
  last flushed log segment; the plan + savestate make the run
  repeatable after restart.
- **Savestate corrupt/missing/mismatched:** bridge acks with a typed
  error; sidecar metadata catches build/ROM mismatch before load.
- **Disk full / permission errors:** bridge catches write failures,
  aborts the plan with neutral input, error ack states the OS error.
- **Screenshot failures:** window not found / permissions / occlusion →
  CLI reports; screenshots are best-effort observability, never
  load-bearing for pass/fail.

## 7. Determinism & reproducibility

- Pin and record (in `meta.json`): fork commit, patches, ROM/BIOS/
  firmware/save hashes, melonDS config hash, savestate identity.
- Interpreter (JIT off) for research runs; frame limiter on; host input
  latched out during plans (§4).
- Savestate before every experiment; plans reference states by slot so
  any run replays from `meta.json` + plan + state file.
- **Determinism acceptance** (M4): same plan + state, two runs,
  byte-identical logs. If they diverge, the recorded config surface is
  the diagnostic checklist; known suspects (RTC, audio sync mode) get
  pinned as spike follow-ups rather than guessed at now.

## 8. Testing

- **Spike (M1):** S1–S5 experiments, findings documented.
- **Bridge selftest command:** echo counter, read a known-constant ROM
  value, save+load a scratch savestate, framecount monotonicity check,
  measured callback duration under the max watch load.
- **M2 input acceptance:** edge-accurate 3-frame press readback (§4).
- **End-to-end acceptance (M4):** from a training savestate, a plan
  walks Goku right 20 frames and presses B; assert the log shows
  opponent HP decreasing and `+0x78` entering the `0xC0` family.
- **Determinism check (M4):** byte-identical replay (§7).
- **CLI unit tests:** plan validation, address resolution, IPC framing,
  epoch/stale-file handling — pure Python, no emulator.

## 9. Deliverables & placement

On `master` as shared infrastructure (usable by this session and the
battle-engine-atlas agent):

```text
scripts/emu/
  README.md              # build, setup, verified-behavior notes, pinned commit
  build_melonds_lua.sh
  patches/joypad-set.patch
  agent_bridge.lua
  jusemu.py
  jus_addresses.py
  plans/                 # example + reusable plans
docs/superpowers/specs/2026-08-14-melonds-agent-control-design.md  # this doc
```

## 10. Milestones

1. **M1 — Build + validation spike:** fork compiles and runs JUS on
   macOS with GDB stub enabled; S1–S5 answered and documented. Timebox:
   if blocked >1 day on the build, stand up the keystroke-automation
   fallback while continuing.
2. **M2 — Input patch:** `joypad.set` passes the edge-accurate readback
   test.
3. **M3 — Bridge + CLI:** command loop, heartbeat/epoch protocol,
   watches, savestates, buffered logging; selftest passes.
4. **M4 — Acceptance:** Goku hello-world plan + determinism check pass.
5. **M5 — First real work:** knock out 2–3 GDB Validation Queue cards
   using the sequential Lua→GDB handoff; verify plan freeze/resume
   across a breakpoint stop; document the combined workflow.

## 11. Out of scope (YAGNI)

- Sockets/JSON-RPC server, gRPC; full AgentServer fork.
- Concurrent plan execution across GDB stops (sequential handoff only).
- Taint tracking, write provenance, trace aggregation.
- Framebuffer pixel export from Lua (macOS `screencapture` suffices;
  revisit if menu automation needs pixel-diffing).
- Migrating `jus_gdb_watcher.py` onto `jus_addresses.py` (follow-up).
- Multi-client, multi-instance support; Windows/Linux bridges.

## 12. Risks

| Risk | Mitigation |
| --- | --- |
| Fork doesn't build on macOS / is stale vs. master | M1 timebox + keystroke-automation fallback |
| `_Update()` can't safely do file I/O or savestates (S1/S2/S4 fail) | Fallback: Qt-timer-side command polling patch; plan-executor model survives |
| Lua sandbox lacks `io`/`os` | Extend patch with minimal file bindings |
| Input latch races host input path | Latch applied at frontend commit point, host input ignored while active; S3 verifies ordering |
| GDB stop freezes bridge mid-plan | Heartbeat `paused` state; sequential-handoff scope; freeze/resume verified in M5 |
| Savestate load breaks GDB connection (S5) | Documented procedure: disconnect before load until verified otherwise |
| Savestates incompatible across builds | Sidecar metadata with build tag; refuse mismatched loads |
| Frame-budget overrun from heavy watches | CLI-enforced watch limits; callback duration measured in selftest |
