#!/usr/bin/env bash
# scripts/emu/stop_emu.sh
# Kill every melonDS we started and verify they're really gone.
#
# `pkill` is unreliable here: under a sandboxed shell it reports success
# (rc=0, pattern matched) while the signal is silently dropped. So: resolve
# PIDs with pgrep, kill them individually, and re-check.
set -uo pipefail

PATTERN="${1:-melonDS.app/Contents/MacOS/melonDS}"

pids() { pgrep -f "$PATTERN" 2>/dev/null || true; }

found="$(pids)"
if [ -z "$found" ]; then
  echo "no melonDS running"
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
echo "all melonDS processes stopped"
