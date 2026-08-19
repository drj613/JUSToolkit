# Phase-1 GDB macros — Battle Engine Atlas live discovery session.
# Source from the repo root (worktree) AFTER connecting to melonDS:
#   (gdb) source scripts/gdb/phase1_macros.gdb
#
# All captures land in jus_files/analysis/gdb/session1/ (gitignored).
# Uses `set logging enabled on` (GDB >= 12). On older GDB, replace with
# `set logging on` / `set logging off`.

shell mkdir -p jus_files/analysis/gdb/session1

# ---------------------------------------------------------------------------
# pchain — resolve the offline-mode character-struct pointer chain
# (see scripts/gdb/README.md "Wifi Pointers Don't Work"):
#   player:   *(*(0x023D2A74) + 0x10)
#   opponent: *(*(*(0x023D2A74) + 0x00) + 0x10)
# ---------------------------------------------------------------------------
define pchain
  set $inter = *(unsigned int*)0x023D2A74
  printf "chain: intermediate = 0x%08X\n", $inter
  if ($inter >= 0x02000000 && $inter < 0x02400000)
    set $player = *(unsigned int*)($inter + 0x10)
    printf "chain: player struct   = 0x%08X\n", $player
    set $oq = *(unsigned int*)($inter + 0x00)
    if ($oq >= 0x02000000 && $oq < 0x02400000)
      set $opponent = *(unsigned int*)($oq + 0x10)
      printf "chain: opponent struct = 0x%08X\n", $opponent
    else
      printf "chain: opponent intermediate invalid (0x%08X)\n", $oq
    end
  else
    echo chain: invalid — not in battle yet?\n
  end
end
document pchain
Resolve player/opponent character-struct pointers from 0x023D2A74.
Sets $player and $opponent convenience variables.
end

# ---------------------------------------------------------------------------
# ctx — per-breakpoint capture discipline (run at every interesting stop)
# ---------------------------------------------------------------------------
define ctx
  info registers
  x/16wx $sp
  disassemble $pc-0x20, $pc+0x30
end
document ctx
Standard stop capture: registers + 16 stack words + disasm around $pc.
end

# ---------------------------------------------------------------------------
# gauge <charPtr> — dump the +0x56c Meter struct {ptr, max, cur}
# ---------------------------------------------------------------------------
define gauge
  set $g = *(unsigned int*)($arg0 + 0x56c)
  if ($g >= 0x02000000 && $g < 0x02400000)
    printf "gauge[char 0x%08X]: ptr=0x%08X max=%u cur=%u\n", (unsigned int)$arg0, $g, *(unsigned short*)($g + 0x16), *(unsigned short*)($g + 0x18)
  else
    printf "gauge[char 0x%08X]: +0x56c holds 0x%08X (not a main-RAM ptr)\n", (unsigned int)$arg0, $g
  end
end
document gauge
gauge <charPtr>: print the +0x56c gauge pointer and its max(+0x16)/cur(+0x18).
end

# ---------------------------------------------------------------------------
# walk558 <charPtr> — census the +0x558 Meter-node linked list
# (walker semantics per Battle-Engine-Map.md guard-sp-gauges claim 11:
#  next=+0x00, max=+0x16, cur=+0x18, skip-flags +0x3c bit0 / +0x40 byte)
# ---------------------------------------------------------------------------
define walk558
  set $wn = *(unsigned int*)($arg0 + 0x558)
  set $wi = 0
  while ($wn >= 0x02000000 && $wn < 0x02400000 && $wi < 32)
    printf "node[%d] @0x%08X next=0x%08X max=%u cur=%u f3c=0x%02X f40=0x%02X\n", $wi, $wn, *(unsigned int*)$wn, *(unsigned short*)($wn + 0x16), *(unsigned short*)($wn + 0x18), *(unsigned char*)($wn + 0x3c), *(unsigned char*)($wn + 0x40)
    set $wn = *(unsigned int*)$wn
    set $wi = $wi + 1
  end
  printf "walk558: %d node(s)\n", $wi
end
document walk558
walk558 <charPtr>: walk and print the char+0x558 Meter-node list (max 32).
end

# ---------------------------------------------------------------------------
# snap <label> — full-RAM dump + sidecar (registers + pointer chain).
# Dump:    jus_files/analysis/gdb/session1/<label>.bin  (4 MiB main RAM)
# Sidecar: jus_files/analysis/gdb/session1/<label>.sidecar.txt
# NOTE: snap redirects GDB logging to the sidecar; if you had a block
# transcript open (startlog), re-run `startlog <block>` after snap.
# Analyze offline: scripts/analysis/ramdiff.py {baseline,diff,find,chain}
# ---------------------------------------------------------------------------
define snap
  dump binary memory jus_files/analysis/gdb/session1/$arg0.bin 0x02000000 0x02400000
  set logging file jus_files/analysis/gdb/session1/$arg0.sidecar.txt
  set logging overwrite on
  set logging enabled on
  echo === snap $arg0 ===\n
  info registers
  pchain
  set logging enabled off
  set logging overwrite off
  shell date >> jus_files/analysis/gdb/session1/$arg0.sidecar.txt
  printf "snap: wrote %s.bin + %s.sidecar.txt\n", "$arg0", "$arg0"
end
document snap
snap <label>: dump 0x02000000-0x02400000 to <label>.bin plus a sidecar with
registers and the resolved 0x023D2A74 pointer chain. Label = no spaces.
end

# ---------------------------------------------------------------------------
# startlog <block> / stoplog — per-block transcript files
# ---------------------------------------------------------------------------
define startlog
  set logging file jus_files/analysis/gdb/session1/$arg0.transcript.txt
  set logging enabled on
  echo === transcript $arg0 ===\n
end
document startlog
startlog <block>: append all GDB output to <block>.transcript.txt.
end

define stoplog
  set logging enabled off
end
document stoplog
Stop the current transcript.
end

# ---------------------------------------------------------------------------
# pollwatch <watchAddr> <anchorAddr> — watchpoint substitute.
# melonDS's GDB stub has NO hardware watchpoints and software watchpoints
# are unusably slow (single-step based). Instead: snapshot *watchAddr now,
# then set a conditional breakpoint at a hot "anchor" instruction that runs
# every frame; it only stops when the watched u32 changed. Resolution:
# one anchor interval (~1 frame). Emulation slows while armed — arm it
# right before the event, disarm (delete the breakpoint) after.
# Only ONE pollwatch at a time (re-arming overwrites $pw_addr/$pw_val).
# Suggested anchor: 0x020784E4 (gauge %-check — runs continuously in battle).
# ---------------------------------------------------------------------------
define pollwatch
  set $pw_addr = (unsigned int*)$arg0
  set $pw_val = *$pw_addr
  break *$arg1 if (*$pw_addr != $pw_val)
  printf "pollwatch: armed on *0x%08X (now 0x%08X), anchor 0x%08X\n", (unsigned int)$pw_addr, $pw_val, (unsigned int)$arg1
  echo pollwatch: when it stops, the write happened within the last anchor interval\n
end
document pollwatch
pollwatch <watchAddr> <anchorAddr>: stop at anchor when u32 at watchAddr
changes. Watchpoint substitute for melonDS (no hardware watchpoints).
end
