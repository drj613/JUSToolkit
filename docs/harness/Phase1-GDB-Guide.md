# Phase-1 GDB Guide — Live Discovery Session (start to finish)

Generated 2026-07-02, after the Phase-0 gap-closing loop completed
(`scripts/analysis/loop-report-phase0.md`). Companion documents:
`docs/research/Battle-Engine-Map.md` (the static atlas every claim here
comes from), `docs/research/GDB-Validation-Queue.md` (the full 30-card
queue), `docs/design/Phase1-Plan.md` (the plan this guide fulfills).

**Who does what:** you run melonDS + GDB and play the game. A live Claude
session (Section 4) decodes hex, decides the next command, and logs
confirmed findings. This guide is written so you can follow it top to
bottom; every GDB command is copy-pasteable.

**One hard constraint shapes everything below:** melonDS's GDB stub has
**no hardware watchpoints** and unreliable `stepi` (see
`scripts/gdb/README.md` "Known Limitations"). Every "watch this field"
task in the plan is therefore implemented as a `pollwatch` — a conditional
breakpoint at a hot anchor instruction that stops only when the watched
word changes (~1-frame resolution), followed by breakpoint bisection to
isolate the writer PC. The macro is in `scripts/gdb/phase1_macros.gdb`.

---

## 0. Prep checklist (before the session)

- [ ] `brew install melonds arm-none-eabi-gdb` (or build melonDS with
  `-DENABLE_GDB_STUB=ON` per `scripts/gdb/README.md`).
- [ ] JUS ROM + a save that boots into a free battle quickly, with Goku
  and/or Ichigo decks ready (best-documented kits → known `damage1`
  values for planted-value checks).
- [ ] Terminal `cd`'d to the **worktree root**
  (`.claude/worktrees/battle-engine-atlas`) — all paths in the macros are
  relative to it; `jus_files` is a symlink there and works.
- [ ] A second Claude Code session open in the same worktree, primed with
  the companion prompt from Section 4.
- [ ] Know your melonDS savestate hotkeys (default: Shift+F1 save,
  F1 load). Savestates are the single biggest quality multiplier here —
  savestate before every experiment so it's replayable.

## 1. Setup (~10 min)

1. melonDS → Config → Emu Settings → Devtools: enable GDB stub, ARM9 port
   `3333`. Load the ROM, get to the main menu.
2. Connect and load tooling:

   ```gdb
   arm-none-eabi-gdb -x scripts/gdb/jus_gdb_watcher.py
   (gdb) target remote localhost:3333
   (gdb) source scripts/gdb/phase1_macros.gdb
   (gdb) continue
   ```

3. Start a free battle (1v1, a dummy/CPU opponent you can hit freely).
   Once in-battle, Ctrl+C in GDB, then smoke-test the stub end to end:

   ```gdb
   (gdb) pchain
   (gdb) break *0x020784E4
   (gdb) continue
   ```

   Expected: `pchain` prints valid `0x02xxxxxx` player/opponent struct
   pointers, and the breakpoint hits within a second or two even while
   idle (`0x020784E4` is the 25%-gauge check; its callers run
   continuously in battle). On the stop, `r0` = a character struct and
   `[r0+0x56c]` = its gauge. Run `ctx` and `gauge $r0` to confirm, then
   `delete` and `continue`.

   If the breakpoint never hits: you're not in a battle (ov6 not
   resident), or the stub isn't attached — recheck step 1.

4. Build the churn mask (kills RAM-diff noise for the whole session).
   With both characters standing still, Ctrl+C:

   ```gdb
   (gdb) snap idle1
   (gdb) continue
   ```

   Wait ~2 s, Ctrl+C again, `snap idle2`. Then in a shell:

   ```bash
   scripts/analysis/ramdiff.py baseline \
     jus_files/analysis/gdb/session1/idle1.bin \
     jus_files/analysis/gdb/session1/idle2.bin \
     -o jus_files/analysis/gdb/session1/mask.json
   ```

   Everything that differs between two idle dumps (framecounters, sound
   DMA, RNG) is masked out of all later diffs.

---

## 2. Discovery blocks (ordered by value)

Do them in order — Block A takes two minutes and every later block's
interpretation depends on it. Blocks A, B, D, and G share one battle
setup (attacker landing hits on a defender); C, E, F build on it.

Per-block discipline: `startlog blockX` before you start, `ctx` at every
stop, `stoplog` when done. Paste stop output into the live Claude session
as you go; it decides verdicts and next commands.

### Block A — object identity (~5 min) — unblocks 4 subsystems

**Question:** is the `sl` object in ov6's hit-resolution code the
GDB-verified character struct (chain `0x023D2A74`), or a wrapper one
indirection away? (Map: Cross-Cutting §1; critic recommendation #2.)

```gdb
(gdb) startlog blockA
(gdb) break *0x02158BA8
(gdb) continue
```

Land one hit. On the stop (`0x02158BA8` = right after
`ldr r0,[r1,#0xe8]`):

```gdb
(gdb) ctx
(gdb) pchain
(gdb) print/x $r10
(gdb) set $mi = *(unsigned int*)($r10 + 0x1a8)
(gdb) set $scr = *(unsigned int*)($mi + 0x10)
(gdb) print/x $mi
(gdb) print/x $scr
(gdb) print/x $r1
```

- **Expected if TRUE:** `$r10` (`sl`) equals `$player` or `$opponent`
  from `pchain` (note *which* — that tells you whether hit-resolution
  runs on the attacker or the defender), and `$scr == $r1` (confirms the
  static `[[char+0x1a8]+0x10]` scratch chain live).
- **Expected if FALSE:** `$r10` matches neither → it's a wrapper. Have
  the live helper walk candidate indirections (`*(sl+0x10)`, `*(sl+4)`,
  …) until one equals a chain pointer; record the indirection.

Also record `$r1 + 0xE8` — that exact address is Block C's poll target
— and read the pre-computed damage now: `print *(int*)($r1 + 0xE8)`
(card 5: compare to `floor(damage1/5)+(tier-2)` for the move used).

Keep this breakpoint's findings; `delete` when done. Covers queue
cards 5 (partially) and settles the identity premise of cards 7, 11, 21.

### Block B — the `+0x558`/`+0x56c` gauge-identity dispute (~15 min) — queue card 1, TOP priority

**Question:** is the per-technique node cached via `char+0x558` the same
object that lands in the `char+0x56c` gauge pointer? Phase-0's two
adversarial lenses split on this; one breakpoint settles 3 claims
(chrb-catalog 3/11/16).

```gdb
(gdb) startlog blockB
(gdb) break *0x02077FDC
(gdb) break *0x020783DC
(gdb) continue
```

Trigger technique/move activity (use different attacks, switch
characters). At the `0x02077FDC` stop (`str r5,[r6,#0x56c]` — a pointer
being installed into the gauge slot):

```gdb
(gdb) ctx
(gdb) print/x $r5
(gdb) print/x $r6
(gdb) walk558 $r6
(gdb) gauge $r6
```

At any `0x020783DC` stop (the `+0x558` list walker): `print/x $r0`
(char), then `walk558 $r0` and `gauge $r0`.

- **Expected if TRUE (aliasing lens):** the pointer in `char+0x56c`
  appears among `walk558`'s node addresses — the technique cache DOES
  feed ov6 hit-resolution.
- **Expected if FALSE (disasm lens):** `+0x56c` holds a fixed gauge
  object that never appears in any `walk558` output across the session —
  the two mechanisms are separate.

**Stretch (card 30, same sitting):** catch the never-found-statically
node-insertion write. Pick a character struct (`pchain`), then:

```gdb
(gdb) pollwatch ($player + 0x558) 0x020784E4
(gdb) continue
```

If the head was already populated before you armed it, do this instead
at battle start: break the zero-init site `*0x02075FF8` during
character construction, and on that stop arm
`pollwatch ($r?+0x558) 0x02077310` (live helper reads the register
holding the struct from `ctx`). When it trips, `ctx` — but note the
writer executed within the last anchor interval, so bisect: reload
savestate, break the technique-setup functions (`0x020772E4`,
`0x02077C0C`, `0x02077E70`), check `*(char+0x558)` at each stop; the
first stop where it's nonzero brackets the writer. Also census node
kinds across a match with `walk558` (guard? SP? shared across the
3-character deck? — the SP deck-shared question).

### Block C — the damage-formula writer (~30–45 min) — highest single value

**Question:** who writes scratch `[[char+0x1a8]+0x10]+0xE8`? The actual
damage-formula site; beat 3 static rounds (Map: damage-pipeline claim 8,
spec B11).

No hardware watchpoints, so the protocol is: compute the target address
at move start → arm `pollwatch` → land the hit → bisect.

1. **Get the target address T.** Break move-start:

   ```gdb
   (gdb) startlog blockC
   (gdb) break *0x021570F4
   (gdb) continue
   ```

   Press an attack. On the stop (MoveInfo just installed into
   `char+0x1a8`), run `ctx` — the live helper reads which register holds
   the MoveInfo pointer (expected `r0` per queue card 13, which this
   stop also answers: size `0x1F0`, pointer round-trips). Then:

   ```gdb
   (gdb) set $mi = $r0
   (gdb) print/x *(unsigned int*)($mi + 0x10)
   ```

   If `+0x10` already holds a `0x02xxxxxx` pointer, set
   `$T = *(unsigned int*)($mi+0x10) + 0xE8`. If it's still 0, first
   `pollwatch ($mi + 0x10) 0x020784E4` to catch the sub-object install,
   then recompute `$T`.

2. **Arm and trigger:**

   ```gdb
   (gdb) delete
   (gdb) pollwatch $T 0x020784E4
   (gdb) continue
   ```

   Land the hit. Emulation is slow while armed (GDB evaluates the
   condition every anchor hit) — that's expected. When it stops, the
   write happened within the last frame: `ctx`, and
   `print *(int*)$pw_addr` — the value should be
   `floor(damage1/5)+(tier-2)` for the move.

3. **Bisect to the writer PC.** The stop is at the *anchor*, not the
   writer. Reload the savestate (take one at step 1's stop next run) or
   just redo the move, and set breakpoints at the hit-pipeline entries
   the live helper supplies from the static map — first pass:

   ```gdb
   (gdb) break *0x02157A44
   (gdb) break *0x0215807C
   (gdb) break *0x02158B20
   ```

   At each stop check `*(int*)$T`: the first stop where the value has
   already changed brackets the writer between the previous stop and
   this one. The live helper then pulls that interval's callees from
   `query.py callees` and narrows with 2–3 more breakpoints until the
   exact `str` instruction is caught. **Record the writer PC + `ctx`
   output — this is the single most valuable capture of the session.**

   Repeat once for `+0x130` (`$T2 = scratch + 0x130`) — same runs,
   second pollwatch pass. Covers queue cards 5, 7, 13.

### Block D — trampoline deltas + the drain sibling (~10 min) — cards 2, 3, 4

Same hit-landing setup. Confirms the HP gauge mechanics and the
Phase-0-discovered drain trampoline.

```gdb
(gdb) startlog blockD
(gdb) break *0x020783CC
(gdb) break *0x020783B8
(gdb) continue
```

Land hits; also just idle a while (regen/DoT paths use the same
trampolines). At each stop:

```gdb
(gdb) ctx
(gdb) print/x $r0
(gdb) print $r1
(gdb) gauge $r0
(gdb) print/x $lr
```

- Card 3 TRUE: at `0x020783CC`, `r0` = defender struct, `r1` negative
  with magnitude `floor(damage1/5)+(tier-2)`; `gauge` `cur` drops by
  exactly that after `finish`/next stop.
- Drain sibling: hits arriving via `0x020783B8` (caller `0x0215AC70` in
  `$lr`) carry a *positive* `r1` that the trampoline negates (`rsb`) —
  log which in-game events route through which trampoline.
- Card 2/9: `gauge` max/cur track the visible HP bar (HP displays at 4×
  stored value per `scripts/gdb/README.md`).

### Block E — velocity/gravity field classification (~20 min)

**Question:** which fields in `char +0x6A–0xBA` are velocity vs. timers?
(Map: physics-writers open questions.) Pure snapshot work — no
breakpoints, savestate-friendly.

With the mask from Setup step 4 already built:

1. Standing still: `snap pre_jump`. Jump; Ctrl+C while ascending:
   `snap ascending`. Continue; Ctrl+C while falling: `snap falling`.
2. Get knocked back (savestate just before the hit): `snap pre_kb`,
   then Ctrl+C 2–3 times during the launch arc: `snap kb1`, `snap kb2`.
3. Shell, for each pair:

   ```bash
   scripts/analysis/ramdiff.py diff \
     jus_files/analysis/gdb/session1/pre_jump.bin \
     jus_files/analysis/gdb/session1/ascending.bin \
     --mask jus_files/analysis/gdb/session1/mask.json --limit 100
   ```

   Paste the output into the live session. It focuses the char-struct
   window (`charPtr+0x6A..0xBA` — struct pointer is in each snap's
   sidecar via `pchain`) and classifies per field: **velocity** = signed,
   flips sign between ascending/falling, scales with launch strength
   (Q12: `1.0 = 0x1000`); **timer** = monotonic countdown, same slope
   regardless of motion; **position** = large monotonic drift matching
   screen movement.

Covers the plan's Block C and feeds queue cards 8, 10, 21.

### Block F — hitstun-timer init (~15–30 min) — card 11 + the real writer

**Question:** what writes the hitstun countdown into `char+0x98`/`+0xA0`
when a hit lands? Both static candidates were lens-refuted; card 11
tests the stronger one anyway, then the pollwatch finds the real site.

1. **Card 11 first** (cheap):

   ```gdb
   (gdb) startlog blockF
   (gdb) break *0x0207D16C
   (gdb) continue
   ```

   Land a hit. If it stops: `ctx`, `pchain`, `print/x $r0`, `print $r1`.
   TRUE = `r0` equals the defender struct and `r1` matches the move's
   hitstun; FALSE (lens prediction) = `r0` is a per-hitbox record.
   `delete` after.

2. **Find the real init writer** (the actual prize). Defender =
   whichever chain pointer you're hitting (from Block A):

   ```gdb
   (gdb) pollwatch ($opponent + 0x98) 0x020784E4
   (gdb) continue
   ```

   Land one hit; when it trips, bisect exactly as in Block C step 3
   (same pipeline entries; the init is likely inside the
   `0x02158B20` call graph or the status-effect manager `0x02158ED0`).
   Repeat for `+0xA0` — this also settles the `+0xA0`
   timer-vs-status-vs-position conflict (card 21's premise) if the
   writer turns out to be shared or distinct.

### Block G — combo-scale flag + ×1.20 (~10 min) — card 6

```gdb
(gdb) startlog blockG
(gdb) break *0x02158DC4
(gdb) continue
```

Run three scenarios, logging at every stop
(`ctx`, `print/x $r4`, `x/1ub $r10+0xf8`, `gauge $player` on the
**attacker**):

1. A full multi-hit combo at high attacker gauge.
2. The same combo with the attacker's own gauge ≤ 25% of max.
3. A single first hit after a match reset.

TRUE (desperation `attack_boost`): the ×1.20 path (`r4` scaled, flag
`[sl+0xf8]` set) triggers exactly when the attacker's gauge ≤ 25% max,
independent of combo position. FALSE: it correlates with
first-hit-in-combo or nature advantage instead. Watch when `[sl+0xf8]`
*clears* (match reset? combo end?) — that write site is spec B16's
missing half.

---

## 3. Capture convention

Everything lands in `jus_files/analysis/gdb/session1/` (gitignored —
raw dumps and ROM-derived bytes never get committed):

| Artifact | Produced by | Naming |
|---|---|---|
| Block transcript | `startlog blockX` … `stoplog` | `blockX.transcript.txt` |
| RAM dump (4 MiB) | `snap <label>` | `<label>.bin` |
| Dump sidecar (registers + pointer chain + timestamp) | `snap <label>` | `<label>.sidecar.txt` |
| Churn mask | `ramdiff.py baseline` | `mask.json` |
| Confirmed-findings log | the live Claude session, continuously | `confirmed-log.md` |

Rules of thumb:

- `ctx` at **every** stop before anything else — transcripts are the
  machine-checkable evidence Phase 2's tracers will cite as seed
  anchors.
- `snap` before/after every event you care about; dumps are cheap,
  re-running scenarios isn't. Full dumps are *files for tooling* — never
  paste one into chat; paste `ramdiff.py diff` output instead.
- Savestate before every experiment. Replayable > clever.
- Skip VRAM/OAM — combat logic lives in main RAM (`0x02000000` +
  4 MiB); the `snap` range already covers exactly that.
- One caveat: `snap` redirects GDB logging to its sidecar — re-run
  `startlog <block>` after snapping mid-block.

## 4. Live-helper protocol (companion Claude session)

Open a Claude Code session in the worktree
(`.claude/worktrees/battle-engine-atlas`) and paste this prompt:

```text
You are the live hex-decoding assistant for the Phase-1 GDB discovery
session against Jump Ultimate Stars (NDS). I am running melonDS +
arm-none-eabi-gdb myself and will paste raw GDB output at you; the
session script is docs/harness/Phase1-GDB-Guide.md (read it first,
then skim docs/research/Battle-Engine-Map.md and
docs/research/GDB-Validation-Queue.md for the claims being tested).

Your tools:
- scripts/analysis/query.py (venv at scripts/analysis/.venv) — the
  static disassembly index: func/callers/callees/xrefs-to/search-imm/
  search-op-imm/disasm [--overlay ovN]/strings/pool-values. Use it to
  supply bisection breakpoints (callees of a bracketing interval) and
  to check any address I hit against the static map.
- scripts/analysis/ramdiff.py — analyze RAM dumps I place under
  jus_files/analysis/gdb/session1/ (baseline/diff/find/chain). Never
  ask me to paste a dump; run ramdiff on the files directly.

Your job, every time I paste GDB output:
1. Decode it (registers, hex fields, Q12 fixed-point where 1.0=0x1000,
   s16/u16, HP displayed = 4x stored) against the current block's
   expected-if-true/expected-if-false from the guide.
2. State a verdict for the card being tested: CONFIRMED_LIVE /
   REFUTED_LIVE / UNRESOLVED (never guess — UNRESOLVED is a fine
   answer).
3. Tell me the exact next GDB command(s), copy-pasteable.
4. Append every verdict to
   jus_files/analysis/gdb/session1/confirmed-log.md as you go, format:
   `- [BLOCK/card N] VERDICT — claim — key evidence (addresses,
   values, writer PCs) — transcript file`.
   Writer PCs and struct identities are the crown jewels; record them
   the moment they're confirmed.

Key constants (verify against the Map, don't trust memory): character
pointer chain 0x023D2A74 (player *(i)+0x10, opponent *(*(i))+0x10);
gauge char+0x56c {+0x16 max,+0x18 cur}; damage magnitude =
floor(damage1/5)+(tier-2); trampolines 0x020783CC (fill) / 0x020783B8
(drain, negates); +0x558 Meter-node list (next+0x00, flags +0x3c/+0x40);
MoveInfo char+0x1a8, scratch = *(MoveInfo+0x10), deltas +0xE8/+0x130;
hitstun formula newDuration = floor(duration/10)*[table+0x4c]*2 +
duration. melonDS has NO hardware watchpoints — never suggest `watch`;
use the pollwatch macro (scripts/gdb/phase1_macros.gdb) instead.

Do not edit src/, lib/, or the canon docs during the session; the only
file you write is confirmed-log.md. At session end, produce a summary
table (block → verdicts → new addresses) I can hand to the Phase-2
loop.
```

## 5. Validation card batch (the other 18 cards)

The blocks above cover Session 1 of `GDB-Validation-Queue.md` plus the
highest-value pollwatch work (cards 1–13 and 30, minus a few Session-1
extras). If time and focus remain, extend the same sitting:

| Piggyback on | Cards | What |
|---|---|---|
| Block A/D stops (same breakpoints) | 7, 8, 9, 10, 12 | scratch-delta dispatch, `+0x5C8` meter behavior, `+0x6A` hit-counter, clash dispatcher — all read from stops you're already making |
| Block B setup | 25, 26, 27, 28 | Session 8 guard/SP dispatch opcodes (`break *0x02157A44` / `*0x0215807C`, log `r2`/`r3` per event type) — needs a practice-mode mix of guard blocks, SP spends, status ticks |
| New scenario, same battle | 22, 23, 24 | Session 7 projectile lifecycle — use a known projectile move (`bb_b_01`/`db_b_01`), break the entity-pool alloc `*0x020834D4` |

The remaining cards need different game states — run them as separate
short sittings straight from the queue doc: Session 2 (card 13 — already
covered by Block C step 1), Session 3 (cards 14–15, ending/credits),
Session 4 (cards 16–19, character-select screen), Session 5 (card 20),
Session 6 (card 21), Session 8 (card 29, passive-equip respawn).

## After the session

Hand `confirmed-log.md` + the transcripts back to the main session:
Phase 2 is one more automated loop seeded with the writer PCs and
resolved identities (round-3 tracers B10/B11/B13/B15/B16 with corrected
ground truth, then final synthesis). Estimated: this session (~90 min
core blocks) + one overnight loop to a substantially complete map.
