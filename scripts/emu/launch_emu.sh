#!/usr/bin/env bash
# scripts/emu/launch_emu.sh
# Start melonDS with the JUS ROM and the agent bridge already running, then
# wait until the bridge publishes its first heartbeat. No clicking required
# (needs the --lua-script patch from scripts/emu/patches/joypad-set.patch).
#
# Usage: bash scripts/emu/launch_emu.sh [--keep-ipc]
#   --keep-ipc   don't wipe /tmp/jus_emu first (keeps savestates and runs)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MELONDS="${MELONDS:-$HOME/src/melonDS-lua/build/melonDS.app/Contents/MacOS/melonDS}"
ROM="${ROM:-$HOME/Documents/mine/rom/jus.nds}"
IPC_DIR="${JUS_EMU_DIR:-/tmp/jus_emu}"
KEEP_IPC=0
[ "${1:-}" = "--keep-ipc" ] && KEEP_IPC=1

[ -x "$MELONDS" ] || { echo "no melonDS binary at $MELONDS (run build_melonds_lua.sh)"; exit 1; }
[ -f "$ROM" ] || { echo "no ROM at $ROM"; exit 1; }

# Always start from a clean slate: a leftover emulator keeps writing
# heartbeats and racing for the command inbox, which looks like a bridge bug.
bash "$SCRIPT_DIR/stop_emu.sh" || exit 1

# Clear transient IPC state, but NEVER states/ -- savestates are expensive to
# recreate (a full scripted boot-to-battle) and are the whole point of being
# able to resume an experiment. `--keep-ipc` additionally preserves runs/.
if [ "$KEEP_IPC" = 0 ]; then
  rm -rf "$IPC_DIR/cmd" "$IPC_DIR/ack" "$IPC_DIR/runs"
fi
mkdir -p "$IPC_DIR"/{cmd,ack,runs,states}
rm -f "$IPC_DIR"/heartbeat.json "$IPC_DIR"/cmd/inbox.lua \
      "$IPC_DIR"/cmd/pending.json "$IPC_DIR"/stop.flag
rm -f "$IPC_DIR"/ack/*.json 2>/dev/null || true

export JUS_EMU_SRC="$SCRIPT_DIR"
export JUS_EMU_DIR="$IPC_DIR"

echo "launching: $MELONDS $ROM --lua-script $SCRIPT_DIR/agent_bridge.lua"
"$MELONDS" "$ROM" --lua-script "$SCRIPT_DIR/agent_bridge.lua" \
  >"$IPC_DIR/emu.stdout" 2>"$IPC_DIR/emu.stderr" &
EMU_PID=$!
echo "$EMU_PID" > "$IPC_DIR/emu.pid"

# Wait for the bridge to come up. The ROM boot itself takes a few seconds.
for i in $(seq 1 60); do
  if [ -f "$IPC_DIR/heartbeat.json" ]; then
    echo "bridge up after ${i}s:"
    cat "$IPC_DIR/heartbeat.json"; echo
    exit 0
  fi
  if ! kill -0 "$EMU_PID" 2>/dev/null; then
    echo "melonDS exited early. stderr:"; cat "$IPC_DIR/emu.stderr"; exit 1
  fi
  sleep 1
done

echo "no heartbeat after 60s. emulator still running (pid $EMU_PID)."
echo "--- stdout ---"; tail -20 "$IPC_DIR/emu.stdout" || true
echo "--- stderr ---"; tail -20 "$IPC_DIR/emu.stderr" || true
exit 1
