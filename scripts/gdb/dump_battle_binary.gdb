# JUS Battle State Binary Dump Script
#
# Dumps memory regions relevant to in-match battle state
#
# Usage:
#   1. Get into a battle in-game
#   2. Connect GDB: target remote localhost:3333
#   3. Pause with Ctrl+C at desired moment
#   4. Run: source /Users/djdjo/Documents/mine/JUSToolkit/scripts/gdb/dump_battle_binary.gdb

set pagination off

shell mkdir -p /tmp/jus_battle

echo Dumping battle memory to binary files...\n

# Battle state region (timer, scores, match state)
dump binary memory /tmp/jus_battle/battle_1d0000.bin 0x021d0000 0x021e0000
echo Saved: battle_1d0000.bin (0x021d0000 - 0x021e0000) - Battle state\n

# Character data region (HP, position, status)
dump binary memory /tmp/jus_battle/char_1df000.bin 0x021df000 0x021e0000
echo Saved: char_1df000.bin (0x021df000 - 0x021e0000) - Character data\n

# Extended battle region
dump binary memory /tmp/jus_battle/battle_1e0000.bin 0x021e0000 0x02200000
echo Saved: battle_1e0000.bin (0x021e0000 - 0x02200000) - Extended battle\n

echo \nDone! Files saved to /tmp/jus_battle/\n
shell ls -la /tmp/jus_battle/

# Quick dump commands for state comparison
define battle-state1
  shell mkdir -p /tmp/jus_battle/state1
  dump binary memory /tmp/jus_battle/state1/battle_1d0000.bin 0x021d0000 0x021e0000
  dump binary memory /tmp/jus_battle/state1/char_1df000.bin 0x021df000 0x021e0000
  dump binary memory /tmp/jus_battle/state1/battle_1e0000.bin 0x021e0000 0x02200000
  echo Saved battle state1\n
end

define battle-state2
  shell mkdir -p /tmp/jus_battle/state2
  dump binary memory /tmp/jus_battle/state2/battle_1d0000.bin 0x021d0000 0x021e0000
  dump binary memory /tmp/jus_battle/state2/char_1df000.bin 0x021df000 0x021e0000
  dump binary memory /tmp/jus_battle/state2/battle_1e0000.bin 0x021e0000 0x02200000
  echo Saved battle state2\n
end

echo \nBattle comparison commands loaded:\n
echo   battle-state1  - Save current battle state as state1\n
echo   battle-state2  - Save current battle state as state2\n
