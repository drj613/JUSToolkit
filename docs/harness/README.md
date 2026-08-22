# Harness docs

How to measure — the agentic melonDS harness, the melonDS-lua fork, and GDB session
tooling. Game findings do not live here (trust rule: see `../README.md`); the code
itself is in `scripts/emu/` (see `scripts/emu/README.md`).

| Doc | What it covers |
|---|---|
| `Menu-Nav-Verified-From-Pixels.md` | Screen-verified boot-to-battle navigation; the framebuffer `screendump` path |
| `RE-Session-Playbook.md` | Strategies for human+LLM RE sessions (GDB diffing, experiment design) |
| `Phase1-GDB-Guide.md` (+ `.html`) | Running melonDS + GDB live-discovery sessions end to end |
| `2026-08-14-melonds-agent-control.md` | Plan for agent control of melonDS |
| `2026-08-14-melonds-agent-control-design.md` | Design spec for the same |

## Operational rules (folded from project memory, 2026-08-21)

- **Never click/focus the melonDS-lua window after a savestate load** — it can freeze
  the emulator in a permanent SIGSEGV-handler loop that looks like a pause. Focus it
  BEFORE loading a state; sample the process before killing a beachball.
- **Savestates in `/tmp/jus_emu/states` DO survive a stop/relaunch cycle** — relaunch
  is cheap recovery.
- **Pressing Start skips the opening intro** — needed by scripted boot-to-battle.
- **The emulator is a single shared, unbrokered resource.** Input during a live battle
  from any session contaminates every other session's measurements — announce before
  driving it and when you stop (see `../orchestration/COORDINATION-PROTOCOL.md`).
