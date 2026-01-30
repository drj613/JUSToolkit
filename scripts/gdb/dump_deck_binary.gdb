# JUS Deck Binary Dump Script
#
# Dumps raw binary files for analysis
#
# Usage:
#   1. Get game to desired state
#   2. Connect GDB: target remote localhost:3333
#   3. Run: source /Users/djdjo/Documents/mine/JUSToolkit/scripts/gdb/dump_deck_binary.gdb
#   4. Files saved to /tmp/jus_dumps/

set pagination off

shell mkdir -p /tmp/jus_dumps

echo Dumping deck memory to binary files...\n

# Main deck region
dump binary memory /tmp/jus_dumps/deck_0a0c00.bin 0x020a0c00 0x020a1000
echo Saved: deck_0a0c00.bin (0x020a0c00 - 0x020a1000)\n

dump binary memory /tmp/jus_dumps/deck_0a1000.bin 0x020a1000 0x020a3000
echo Saved: deck_0a1000.bin (0x020a1000 - 0x020a3000)\n

dump binary memory /tmp/jus_dumps/deck_0a3000.bin 0x020a3000 0x020a8000
echo Saved: deck_0a3000.bin (0x020a3000 - 0x020a8000)\n

# Deck index region (contains active deck index at 0x020AFEB4)
dump binary memory /tmp/jus_dumps/deck_0a8000.bin 0x020a8000 0x020b0000
echo Saved: deck_0a8000.bin (0x020a8000 - 0x020b0000)\n

# Save/unlock region
dump binary memory /tmp/jus_dumps/save_0b0000.bin 0x020b0000 0x020c0000
echo Saved: save_0b0000.bin (0x020b0000 - 0x020c0000)\n

# Koma holder
dump binary memory /tmp/jus_dumps/koma_228a00.bin 0x0228aa00 0x0228b000
echo Saved: koma_228a00.bin (0x0228aa00 - 0x0228b000)\n

echo \nDone! Files saved to /tmp/jus_dumps/\n
shell ls -la /tmp/jus_dumps/
