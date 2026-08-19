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
FORCE=0
for a in "$@"; do
  case "$a" in
    --keep-ipc) KEEP_IPC=1 ;;
    --force)    FORCE=1 ;;
  esac
done

[ -x "$MELONDS" ] || { echo "no melonDS binary at $MELONDS (run build_melonds_lua.sh)"; exit 1; }
[ -f "$ROM" ] || { echo "no ROM at $ROM"; exit 1; }

# ---- exclusive-access check -------------------------------------------------
# This script kills EVERY melonDS process and then wipes the shared IPC dir, so
# launching while another session is driving the emulator silently destroys its
# run. That happened: three wakes of runtime measurements were confounded by it
# (bead jus-emulator-access-not-exclusive-tum) and the symptoms all looked like
# game behaviour or bad experiment design -- attacks that never landed, a core
# frozen mid-run, a stale pending.json, and damage-formula stops that appeared
# to fire with no input.
#
# So: refuse if someone else demonstrably holds a live emulator. Set
# JUS_EMU_HOLDER to identify yourself; --force restores the old behaviour.
HOLDER_FILE="$IPC_DIR/HOLDER"
ME="${JUS_EMU_HOLDER:-unlabelled-$PPID}"
if [ "$FORCE" = 0 ] && [ -f "$HOLDER_FILE" ]; then
  OTHER="$(sed -n '1p' "$HOLDER_FILE" 2>/dev/null || true)"
  OTHER_PID="$(sed -n '2p' "$HOLDER_FILE" 2>/dev/null || true)"
  if [ -n "$OTHER_PID" ] && kill -0 "$OTHER_PID" 2>/dev/null && [ "$OTHER" != "$ME" ]; then
    echo "REFUSING TO LAUNCH: '$OTHER' holds the emulator (melonDS pid $OTHER_PID, still alive)." >&2
    echo "  since $(sed -n '3p' "$HOLDER_FILE" 2>/dev/null)" >&2
    echo "Launching would kill their emulator and wipe the shared IPC dir." >&2
    echo "Coordinate first, or pass --force if you know they are done." >&2
    exit 3
  fi
fi

# Always start from a clean slate: a leftover emulator keeps writing
# heartbeats and racing for the command inbox, which looks like a bridge bug.
bash "$SCRIPT_DIR/stop_emu.sh" --force || exit 1

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
# Claim it, so another session's launch refuses instead of killing this one.
printf '%s\n%s\n%s\n' "$ME" "$EMU_PID" "$(date '+%Y-%m-%d %H:%M:%S')" > "$HOLDER_FILE"
echo "emulator claimed by '$ME' (pid $EMU_PID)"

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
