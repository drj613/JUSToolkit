# JUS Deck State Dump Script
#
# Usage:
#   1. Get game to desired state (e.g., deck builder with Eve as leader)
#   2. Connect GDB: target remote localhost:3333
#   3. Run: source scripts/gdb/dump_deck_state.gdb
#   4. Share the output file: jus_files/analysis/deck_dump.txt

set pagination off
set logging file jus_files/analysis/deck_dump.txt
set logging overwrite on
set logging on

echo === JUS DECK STATE DUMP ===\n
echo Timestamp:
shell date

echo \n\n=== DECK REGION 0x020a0c00 - 0x020a1000 (1KB) ===\n
x/256xw 0x020a0c00

echo \n\n=== DECK REGION 0x020a1000 - 0x020a2000 (4KB) ===\n
x/1024xw 0x020a1000

echo \n\n=== DECK REGION 0x020a2000 - 0x020a3000 (4KB) ===\n
x/1024xw 0x020a2000

echo \n\n=== SAVE/UNLOCK REGION 0x020b0000 - 0x020b1000 (4KB) ===\n
x/1024xw 0x020b0000

echo \n\n=== KOMA HOLDER REGION 0x0228aa00 - 0x0228ac00 (512B) ===\n
x/128xw 0x0228aa00

echo \n\n=== SEARCH FOR 0xD4 (Eve low byte) in 0x020a0000-0x020b0000 ===\n
# Can't do custom scan in plain GDB, but we have the hex dump above

echo \n\n=== KNOWN ADDRESSES ===\n
echo 0x020a0c98 (deck state flag):\n
x/16xb 0x020a0c90

echo \n0x020a20f6 (leader marker area):\n
x/16xb 0x020a20f0

echo \n0x020a2240 (counter area):\n
x/16xb 0x020a2238

echo \n0x020AFEB4 (active deck index):\n
x/4xb 0x020AFEB4

echo \n\n=== DUMP COMPLETE ===\n

set logging off
echo Results saved to: jus_files/analysis/deck_dump.txt\n
