---
name: jus-savestates-survive-relaunch
description: JUS melonDS savestates in /tmp/jus_emu/states DO survive a stop/launch cycle — the handoff's "none survive a reboot" is wrong
metadata:
  type: project
---

Verified 2026-08-19: after a full `stop_emu.sh` / `launch_emu.sh` cycle, `fight_base` reloaded
with the battle anchor resolving to 0x021DEA60, rule bytes 0/0/0, HP 160.000/152.000 and
auto-heal still off. `docs/HANDOFF-2026-08-18-runtime-2.md` s6 claims "none survive a reboot".
That claim is wrong.

**Why it matters:** it inverts the cost model. A relaunch is CHEAP RECOVERY rather than the
loss of a session's working set, which makes the one-GDB-connection-per-launch hazard
survivable — a dead stub halts the CPU with no way back except relaunch, and that's now an
acceptable price rather than a disaster. It also means a missing savestate is a REAL absence
(never created, or deleted), not an expiry, which is how `pos_base` was misdiagnosed.

**How to apply:** treat the states directory as durable and check it before believing a doc
that names a savestate. Before any GDB work, remember the stub allows ONE connection per
launch; if it's already spent, expect a half-attach that freezes the emulator, and just
relaunch. Related: [[record-check-spans-branches]] — a stale hazard note outlives the
condition that produced it.
