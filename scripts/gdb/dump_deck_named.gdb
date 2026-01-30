# JUS Deck Binary Dump Script (Named Version)
#
# Usage:
#   1. In GDB, set the dump name first:
#      (gdb) set $dump_name = "eve_leader"
#   2. Run this script:
#      (gdb) source /Users/djdjo/Documents/mine/JUSToolkit/scripts/gdb/dump_deck_named.gdb
#
# Or use the quick commands below directly:

# Quick dump as "state1":
define dump-state1
  shell mkdir -p /tmp/jus_dumps/state1
  dump binary memory /tmp/jus_dumps/state1/deck_0a0c00.bin 0x020a0c00 0x020a1000
  dump binary memory /tmp/jus_dumps/state1/deck_0a1000.bin 0x020a1000 0x020a3000
  dump binary memory /tmp/jus_dumps/state1/deck_0a3000.bin 0x020a3000 0x020a8000
  dump binary memory /tmp/jus_dumps/state1/deck_0a8000.bin 0x020a8000 0x020b0000
  dump binary memory /tmp/jus_dumps/state1/save_0b0000.bin 0x020b0000 0x020c0000
  dump binary memory /tmp/jus_dumps/state1/koma_228a00.bin 0x0228aa00 0x0228b000
  echo Saved state1 to /tmp/jus_dumps/state1/\n
  shell ls -la /tmp/jus_dumps/state1/
end

# Quick dump as "state2":
define dump-state2
  shell mkdir -p /tmp/jus_dumps/state2
  dump binary memory /tmp/jus_dumps/state2/deck_0a0c00.bin 0x020a0c00 0x020a1000
  dump binary memory /tmp/jus_dumps/state2/deck_0a1000.bin 0x020a1000 0x020a3000
  dump binary memory /tmp/jus_dumps/state2/deck_0a3000.bin 0x020a3000 0x020a8000
  dump binary memory /tmp/jus_dumps/state2/deck_0a8000.bin 0x020a8000 0x020b0000
  dump binary memory /tmp/jus_dumps/state2/save_0b0000.bin 0x020b0000 0x020c0000
  dump binary memory /tmp/jus_dumps/state2/koma_228a00.bin 0x0228aa00 0x0228b000
  echo Saved state2 to /tmp/jus_dumps/state2/\n
  shell ls -la /tmp/jus_dumps/state2/
end

echo Loaded dump commands. Use:\n
echo   dump-state1   - Save current state as state1\n
echo   dump-state2   - Save current state as state2\n
