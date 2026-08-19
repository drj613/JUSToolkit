# melonDS agent control layer

Everything in this directory lets an agent play Jump Ultimate Stars hands-free.
A patched melonDS fork runs a Lua bridge script (`agent_bridge.lua`) inside the
emulator; the `jusemu.py` CLI talks to it through files — sending button plans,
reading memory, and driving savestates. The GDB stub is still available for
breakpoints, so Lua and GDB work side by side on the same session.

## Quick start

```bash
bash scripts/emu/launch_emu.sh          # boots ROM + bridge, no clicking needed
cd scripts/emu
python3 jusemu.py status                # state=idle, live framecount
python3 jusemu.py selftest              # read_ok=true
python3 jusemu.py peek 0x021DF1D4 2     # player HP, raw (divide by 64)
python3 jusemu.py run plans/damage_probe.json
bash stop_emu.sh                        # kill every emulator we started
```

`launch_emu.sh` always calls `stop_emu.sh` first. A stale emulator is the
number-one confusing failure: the old bridge keeps writing heartbeats and racing
for the command inbox, so the CLI looks like it's talking to a bridge that
ignores it.

**`pkill` doesn't work from a sandboxed shell here.** It returns 0 and claims a
match, but the signal is silently dropped. `stop_emu.sh` resolves PIDs with
`pgrep`, kills them one by one, and checks they're actually gone.

## Build

```bash
bash scripts/emu/build_melonds_lua.sh
```

The build needs Lua 5.4 from Homebrew. `lua5.4` and `luac5.4` live in
`/opt/homebrew/opt/lua@5.4/bin` and are **not** on `PATH` by default — use the
full path, or add that directory to `PATH` yourself.

Things the build script already handles (listed so nobody rediscovers them):

- The CMake option is `ENABLE_GDBSTUB`, not `ENABLE_GDB_STUB`. The wrong name
  is silently ignored.
- Deps: `enet`, `faad2`, `pkg-config`. `libslirp` is *not* needed.
- `brew install lua` now pulls Lua **5.5** and unlinks 5.4; the fork needs 5.4.
- `qt@6` is only an alias — `brew --prefix qt@6` points nowhere until the real
  `qt` formula is installed.
- Keg-only prefixes must be in `CMAKE_PREFIX_PATH` or `find_package(Lua)` fails.

### Pinned commit

`c26edf0e0d75364823856c9272a103fe39e03999` (see `build_info.json`).

### ROM/BIOS hashes

See `hashes.json`. No external BIOS/firmware dumps are needed — melonDS boots
JUS in DS mode with its built-in FreeBIOS.

| File | SHA-256 |
| --- | --- |
| ROM (`jus.nds`) | `a9c9bf89e6d99548b7c87e822b217c3fb74ef25186535b06193a6fb73d0d6d27` |
| Save (`jus.sav`) | `f2a794a9dcc2f34be76682c2377315d5f45bc8eeb95f725478c5f2cc31edb83b` |
| BIOS9 / BIOS7 / Firmware | not used (direct boot) |

The melonDS config lives at `~/Library/Preferences/melonDS/melonDS.toml` —
**Preferences**, not Application Support. `[JIT] Enable=false` matters: the GDB
stub can't run alongside the JIT recompiler.

## Our patches

`patches/joypad-set.patch` carries four changes to the fork. Regenerate it with
`cd $SRC_DIR && git diff > scripts/emu/patches/joypad-set.patch`.

1. **`joypad.set(table|nil)` / `joypad.get_committed()`** — button injection.
   The fork's `joypad` was read-only. `set(t)` overrides with `t` as the
   complete pressed set (physical input ignored), `set({})` forces neutral,
   `set(nil)` releases the override. `get_committed()` reads back the mask the
   core actually used — that's what you want for timing. The existing
   `joypad.get` reads the *physical* mask and doesn't reflect the override.
2. **`--lua-script <path>`** — the fork had **no** non-GUI way to load a Lua
   script (no CLI flag, no config key, no env var; the console is append-only).
   Without this flag, none of this tooling can run unattended.
3. **Fixed `Lua_ReadData` in `lua/libs/LuaMemory.cpp`.** Upstream reads bytes
   into the *high* end of an `s64`, so on a little-endian host `read_u8`
   returned `byte << 56` — e.g. 0xEE came back as `-1297036692682702848`. Now
   it shifts back down, arithmetically for signed types. The adjacent `isSigned`
   trait was also inverted (`((T)0-1 > 0)` is false for every 8/16-bit type
   after integer promotion, and true for `u32`), so `u32` reads sign-extended
   and `s8`/`s16` never did. Both fixed. `read_bytes_as_array` was always
   correct, which is why the selftest passed while `peek` returned garbage.
4. **Reset `flagStop`** in `createLuaState()`. Upstream never cleared it, so
   after one Stop-button press every later script was killed instantly — fatal
   for repeated unattended runs.

Don't call `memory.usememorydomain`: it stores a pointer to a stack local. Pass
the domain string (`"ARM9 System Bus"`) per call instead.

## Verified behavior (spike findings)

**Lua runs on the GUI thread, not the emu thread, via a queued Qt connection**
(`EmuThread.cpp` emits `signalLuaUpdate`; `LuaConsoleDialog` lives on the GUI
thread with a default `AutoConnection`). Two consequences:

- One `_Update()` call is **not** one emulated frame. `agent_bridge.lua` drives
  plan progress off `emu.framecount()` deltas and logs the delta as `d` in every
  row so skipped frames are visible. In practice `d` has always been 1, but the
  design must not assume it.
- `joypad.set()` writes and the core's mask commit happen concurrently — that's
  why the patch uses `std::atomic`.

`_Update()` also fires while the emulator is paused and during ROM boot, so any
logic gated on "a frame passed" must check `framecount`, not callback count.

**Savestates work and are portable across launches.** `state save` acks only
after the file size stabilizes and the sidecar is written; `state load` settles
by waiting for `framecount` to match the sidecar's `framecount_at_save`. A state
saved in one process loaded correctly into a fresh launch, restoring framecount
exactly.

**Menu input granularity:** a **1-frame** press is exactly one menu step. A
4-frame hold triggers auto-repeat and moves two steps. Hold length is the
difference between reliable and unreliable navigation.

**Boot-to-battle input path** (all via `jusemu.py run`, no hand input):
`START` (skips the intro) → `LEFT` to Jアリーナ → `A` → three `DOWN` to
トレーニング → `A` → `A` (deck select) → `A` (stage select) → `START`
(rule screen, "バトルスタート").

**Screenshots:** `jusemu.py screenshot` uses AppleScript System Events, which
needs Accessibility permission and currently fails. The working approach is
`CGWindowListCopyWindowInfo` via `pyobjc-framework-Quartz` to get the window
id, then `screencapture -l <id>`. Pick the **largest** melonDS window — the Lua
console and other small windows share the owner name. Plain `screencapture`
works without extra setup, so Screen Recording permission is already granted.

### Reading HP correctly

HP is a **16-bit little-endian value in 1/64 units**. The "1/4 scale" byte from
older notes is just its high byte. Read 2 bytes **at the address**, not at
`addr-1` — that older instruction is wrong and it silently returns the high byte
alone (38 rather than 9728, i.e. 0.594 rather than 152.000).

| slot | player | opponent |
|---|---|---|
| active (CURRENT HP) | `0x021DF1D4` | `0x021DF7F0` |
| deck 1/2/3 | `+0x50` each | `+0x50` each |

**These are CURRENT HP. Two bytes earlier is MAX HP and it is not what you
want** [`jus-reading-max-hp-not-current-2jo`]. The pair sits in the character
struct as `+0x16` max / `+0x18` current, so the addresses above are `+0x18`:

| field | player | opponent |
|---|---|---|
| max HP (`char+0x16`) | `0x021DF1D2` | `0x021DF7EE` |
| **current HP** (`char+0x18`) | `0x021DF1D4` | `0x021DF7F0` |

The two read **identically at full health**, so a max-HP read looks exactly like
a working measurement and stays perfectly stable while damage lands. That cost
four sessions of "no hits landing" which were charged to game behaviour, to
experiment design, and to another session's interference before anyone checked
the field. If HP is not moving, verify which of the two you are reading before
concluding anything about the game.

Nearby fields on the same struct, for orientation: `char+0x13..0x15` are the
three packed nature slots, `char+0x1A` the live ability count, `char+0x1B` the
ability ids, `char+0x41` the chr_b index, `char+0x49` the regen rate (poke to 0
to stop healing).

`displayed_HP = raw / 64`. Full write-up and measured damage values in
`docs/research/HP-And-Damage-Runtime-Findings.md`.

Two traps when measuring damage: **training mode heals to full within a few
frames**, so never diff before/after — log every frame and take the minimum of
the dip. And **facing decides whether an attack connects**; walking past the
opponent leaves you facing away, and every button whiffs.

## The in-battle training menu (press START) — read this before measuring damage

> **This menu belongs to DECK-MAKER TEST PLAY ONLY, and none of the current
> savestates are in that mode** [`jus-nature-menu-not-in-these-modes-43m`].
> Verified: on `fight_base` (J Arena training) a START press opens **no menu at
> all** and the follow-up presses go to the battle; on `dm_battle` START opens
> the **J Arena pause menu** — バトル再開 / リトライ / デッキセレクト /
> Jアリーナメニューにもどる — which shares none of the rows below. So `自動回復`,
> `COM設定` and `相手の属性` are **not reachable** from the battles we have, and
> an experiment built on them will fail in ways that look like the game
> misbehaving. Auto-heal must instead be stopped by poking `char+0x49` to 0.
> Reaching the mode below needs a scripted boot through デッキメイク.

Pressing **START** during a deck-maker test battle opens an options menu that
controls the three things that were previously fighting every damage measurement.
Rows, top to bottom:

| row | option | values seen | why it matters |
|---|---|---|---|
| 0 | テストプレイ再開 | — | resume (START also resumes) |
| 1 | COM設定 | なにもしない / 戦う | **"do nothing" is the default** — the CPU never approaches or attacks |
| 2 | 自動回復 | ON / OFF | **the auto-heal.** OFF makes damage cumulative |
| 3 | 相手の属性 | 力 / 知 / 笑 | sets the **opponent's nature** — a direct lever for nature-triangle damage |
| 4 | デッキメイク | — | back to the editor |
| 5 | リトライ | — | restart the battle |

Navigation: `DOWN`/`UP` to move, **`A` to cycle a value** (not LEFT/RIGHT — those
do nothing), `START` to resume.

Three consequences worth knowing:

1. **`自動回復 OFF` is the fix for the auto-heal**, and it is cleaner than poking
   memory. Verified: player HP went 10240 → 8704 from two hits and **stayed
   there** for the rest of the run. Damage becomes cumulative and directly
   readable. With it ON, HP is restored ~2.0 displayed per character per frame,
   which pins HP at max and makes damage invisible to a per-frame watch.
2. **`COM設定` defaults to なにもしない**, so an idle-and-wait measurement records
   nothing through no fault of the harness. Set it to 戦う to get incoming hits.
3. **If the menu is open, all bridge input goes to the menu, not the battle.**
   This is a silent failure: plans complete with `ok: true` and every attack
   reads as a miss. If several attack runs in a row report zero hits, screenshot
   before debugging anything else.

A first clean measurement with the heal off: the CPU landed **768 raw = 12.000
displayed** twice, identical both times.

The memory equivalent of the auto-heal is the regen rate at **`struct + 0x49`**
(i.e. `hp_addr + 0x31`). Poking it to `0` also stops the healing — verified, HP
held steady for 5 seconds. Note the menu toggle and that byte are not the same
thing: turning 自動回復 OFF left the byte reading `1`, so the setting appears to
gate whether the regen routine runs rather than zeroing the rate.

## Known issues

- **A plan with `load_state` set stops the bridge.** Running a plan whose JSON
  has `load_state` kills the `_Update()` callback: the heartbeat freezes while
  the emulator keeps running at full speed, and nothing prints to the Lua
  console (so it's not a Lua error, and not the force-stop hook — that only
  fires when `flagStop` is set). Isolated by elimination: the same plan with the
  same 32-byte block watches runs fine once `load_state` is removed, and a
  standalone `state load` works repeatedly. **Workaround:** issue
  `jusemu.py state load <slot>` as its own command first, then run the plan.
  Root cause not yet found; this is what plan Task 7 (spike S4/S5) is for.
- Pointer chains through `0x023D2A74` resolve, but `+0x78` reads 0 in training
  mode where the notes expect `0x22` on the ground. Absolute addresses are
  reliable; treat chain-based watch specs as unverified.
- The `jusemu.py screenshot` subcommand doesn't work (see above).

## Combined Lua+GDB workflow

Partially exercised. Two findings, one good and one limiting.

**The `paused` design works exactly as intended.** With `arm-none-eabi-gdb`
attached and the core halted, `jusemu.py status` reported:

```
"state": "paused",  heartbeat.state: "plan_running",  framecount frozen
```

That is the designed behavior: the heartbeat goes stale while the emulator
process stays alive, so the client infers `paused` rather than `dead`, and an
in-flight plan reads as frozen rather than failed. A running plan survived the
halt in exactly that state.

**The GDB stub does not survive a disconnect.** The first `target remote
localhost:3333` connects cleanly and `break *0x02078488` sets fine. After that
session ends (or is killed), every later connection fails during the handshake:

```
Ignoring packet error, continuing...
warning: unrecognized item "timeout" in "qSupported" response
Remote replied unexpectedly to 'vMustReplyEmpty': timeout
```

and the emulator stays halted, so the bridge is stuck at `paused` forever. The
only recovery found is relaunching the emulator.

Practical rules:

- **One GDB session per emulator launch.** Plan the whole debugging session
  before attaching; you don't get a second attempt.
- Attach *after* loading a savestate, not before.
- **A savestate load WITH GDB attached works.** This was listed below as an
  expected-but-unproven rule ("disconnect GDB before any savestate load"); it
  has now been tested and the load is fine. That matters, because it lets one
  GDB session cover several battles, which is the only way to get an in-run
  positive control: catch a case you know hits, then load the case you expect
  to miss, with the same breakpoints proven live. A "0 hits" result from a
  separate launch is not evidence.
- **`handle SIGILL ... pass` fails on this stub** ("Can't send signals to this
  remote system") and aborts the whole batch script. Use `nopass`.
- **A no-hit result is worthless unless the log shows the session stayed
  healthy.** Two of three attempts at one negative were invalid -- one where GDB
  detached on SIGILL, one where the script errored -- and both printed exactly
  the same "0 hits" as the valid run.

## Frame counting: the emulator free-runs

`nav.advance(N)` is accurate -- 2300 requested measured 2301 observed against the
emulator's own framecount, and it now RETURNS that observed delta.

The thing to watch is that **the emulator keeps running at ~60fps whenever no plan
is executing.** Three seconds of caller sleep costs 180 emulated frames. So any
framecount delta measured across your own dumps, screenshots or conversions
includes that free-run time. A reported 2300 -> 5310 "overshoot" was this: ~50
seconds of caller work between two reads, not plan error.

Use `nav.advance()`'s return value to attribute frames to a plan. Use a difference
of two emulator-reported framecounts to measure in-game duration -- that counts
free-run frames too, which is correct, since the game does not care where its
frames came from.
- Because the halt freezes `_Update()`, the bridge cannot drive input while the
  core is stopped. Breakpoint commands must end in `continue` so the core keeps
  running and the bridge stays alive; a blocking prompt deadlocks the pair.
- Relaunch with `launch_emu.sh --keep-ipc` to recover without losing savestates.

The unfinished experiment this was for: break at `0x02078488` (the HP-delta apply
function), land a melee hit, and read `r1` (the delta) and `lr` (the caller) to
identify which of the eight dispatcher sites melee damage uses. That would locate
the resistance math, which static reading has not.

Not yet exercised. The config already has the ARM9 stub on port 3333 with
`BreakOnStartup=false` and the JIT off, so `target remote localhost:3333`
should attach to a running bridge session. The expected rule until proven
otherwise: **disconnect GDB before any savestate load**. When GDB halts the
emulator, `_Update()` stops and the heartbeat goes stale; `jusemu.py status`
reports `paused` (not `dead`) because the process is still alive, and a running
plan should freeze rather than fail.
