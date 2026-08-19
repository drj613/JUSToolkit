#!/usr/bin/env bash
# scripts/emu/stop_emu.sh
# Kill every melonDS we started and verify they're really gone.
#
# `pkill` is unreliable here: under a sandboxed shell it reports success
# (rc=0, pattern matched) while the signal is silently dropped. So: resolve
# PIDs with pgrep, kill them individually, and re-check.
set -uo pipefail

# This kills EVERY melonDS, so it can take out another session's emulator. It
# warns when the HOLDER file names someone else; --force skips the warning.
# See bead jus-emulator-access-not-exclusive-tum.
FORCE=0
PATTERN="melonDS.app/Contents/MacOS/melonDS"
for a in "$@"; do
  case "$a" in
    --force) FORCE=1 ;;
    *)       [ -n "$a" ] && PATTERN="$a" ;;
  esac
done

IPC_DIR="${JUS_EMU_DIR:-/tmp/jus_emu}"
HOLDER_FILE="$IPC_DIR/HOLDER"
ME="${JUS_EMU_HOLDER:-unlabelled-$PPID}"
if [ "$FORCE" = 0 ] && [ -f "$HOLDER_FILE" ]; then
  OTHER="$(sed -n '1p' "$HOLDER_FILE" 2>/dev/null || true)"
  OTHER_PID="$(sed -n '2p' "$HOLDER_FILE" 2>/dev/null || true)"
  if [ -n "$OTHER_PID" ] && kill -0 "$OTHER_PID" 2>/dev/null && [ "$OTHER" != "$ME" ]; then
    echo "WARNING: '$OTHER' holds this emulator (pid $OTHER_PID). Stopping it anyway." >&2
    echo "  If that was not intended, they will see a dead bridge with no explanation." >&2
  fi
fi

pids() { pgrep -f "$PATTERN" 2>/dev/null || true; }

found="$(pids)"
if [ -z "$found" ]; then
  echo "no melonDS running"
  rm -f "$HOLDER_FILE"
  exit 0
fi

echo "killing: $(echo "$found" | tr '\n' ' ')"
for sig in TERM KILL; do
  remaining="$(pids)"
  [ -z "$remaining" ] && break
  for p in $remaining; do kill "-$sig" "$p" 2>/dev/null || true; done
  for _ in 1 2 3 4 5 6; do
    [ -z "$(pids)" ] && break
    sleep 0.5
  done
done

left="$(pids)"
if [ -n "$left" ]; then
  echo "FAILED to kill: $(echo "$left" | tr '\n' ' ')" >&2
  echo "(a sandboxed shell may not be allowed to signal them)" >&2
  exit 1
fi
rm -f "$HOLDER_FILE"
echo "all melonDS processes stopped"
