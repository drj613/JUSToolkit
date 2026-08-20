---
name: melonds-window-focus-triggers-sigsegv-loop
description: "Clicking/focusing the melonDS-lua window after a savestate load can freeze the emulator permanently (infinite SIGSEGV-handler loop), not a real pause — never click the window; focus it BEFORE loading a state"
metadata: 
  node_type: memory
  type: project
  originSessionId: 329d0fef-b7f8-4c51-a5ce-144e785cd796
  modified: 2026-08-20T02:44:33.601Z
---

Root-caused 2026-08-19 (runtime loop, sampled the hung process instead of killing it — see `data/owner-matches/melonds-activation-hang-sample.txt`, referenced from `docs/orchestration/HANDOFF-Ed-2026-08-19-runtime.md`).

**Mechanism:** focusing/activating the melonDS window makes Qt sync the macOS menu bar, which runs a PCRE2 JIT regex that faults. melonDS's ARMJIT `SigsegvHandler` (installed via `sigaction(SIGSEGV, ...)` at `ARMJIT_Memory.cpp:792`, no guard against double-registration) catches the fault, doesn't recognize the address, and chains to its saved "previous" handler — which a savestate load had already re-registered as itself. Infinite SIGSEGV-handler loop on the main thread. Looks exactly like a beachball/hang, not a crash (no stderr output) and is NOT the same as melonDS's real pause-on-blur behavior, even though the CLI's stale-heartbeat heuristic reports both as "paused."

**Why it matters:** this explained three separate incidents in one session that all looked like different bugs — a human's window click, an agent's `osascript activate` call (which blocked 120s with no error), and a "freeze right after a keypress" that was actually the focus-click before the key, not the key itself. `JIT.Enable` being `false` in config does NOT prevent this — the handler installs regardless.

**How to apply:** never click into or otherwise focus/activate the melonDS window after a savestate load, from a script or by hand. If a human needs to play: focus the window FIRST, then load the savestate over IPC (not the reverse), then play without clicking away and back. If it ever beachballs anyway, run `sample <pid> 5 -file <path>` (or `spindump`) BEFORE `stop_emu.sh` — killing the process destroys the only artifact that can confirm/deny this diagnosis. Related: [[melonds-emulator-is-a-shared-unbrokered-resource]].
