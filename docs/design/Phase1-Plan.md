# Phase 1 Plan — Live GDB Discovery Session (pending Phase 0)

Status: WAITING on the Phase-0 loop (`docs/design/Static-RE-Phase0.md`,
report will land at `scripts/analysis/loop-report-phase0.md`). Do not
write the Phase-1 guide until that report exists — P7 regenerates the GDB
queue and P4/P5 may replace several breakpoint addresses below.

## Context

The static campaign (`scripts/analysis/loop-report.md`,
`docs/research/Battle-Engine-Map.md`) closed everything static search can
reach. The remaining gaps are provably invisible statically (heap-only
pointers, vtable dispatch, register-indexed addressing — failure mode hit
3+ times). One targeted emulator+GDB session converts them into concrete
addresses; those seed a final automated loop (Phase 2).

Human runs GDB + emulator; a live Claude session assists with hex
interpretation in real time.

Existing infra to build on (do NOT rebuild): `scripts/gdb/README.md`
(melonDS + arm-none-eabi-gdb workflow), `scripts/gdb/jus_gdb_watcher.py`
(105KB watcher from the prior GDB campaign), `scripts/gdb/dump_*.gdb`.

## Trigger

When `scripts/analysis/loop-report-phase0.md` exists: tell Claude
"Phase 0 done — generate the Phase-1 guide per docs/design/Phase1-Plan.md".

## Deliverable to generate then: `docs/research/Phase1-GDB-Guide.md`

Start-to-finish guide with these sections:

1. **Setup (~10 min)** — melonDS with GDB stub + `arm-none-eabi-gdb`
   connect recipe, ROM/save prep, loading `jus_gdb_watcher.py`, one
   smoke-test breakpoint to confirm the stub works end-to-end.
2. **Discovery blocks, ordered by value.** Each block: exact copy-pasteable
   `break`/`watch` commands, what to do in-game to trigger, exactly what to
   capture (register set + memory-window dumps), expected-if-true /
   expected-if-false patterns. Current blocks (addresses subject to
   Phase-0 revision):
   - **A — object identity**: break `ov6 0x02158BA8`; compare `r1` against
     the live `0x023D2A74` pointer chain. Unblocks damage-pipeline,
     physics-writers, hitstun-timers, weight-hunt at once.
   - **B — damage-formula writer** (highest single value): watchpoint on
     scratch `[[char+0x1a8]+0x10]+0xE8` during a hit; the writer PC is the
     actual damage-formula site that beat 3 static rounds.
   - **C — velocity/gravity**: dump the `+0x6A–0xBA` window of the
     identified character struct while jumping / getting launched; diff
     frames to classify velocity vs timer fields.
   - **D — hitstun init**: watchpoints on `char+0x98`/`+0xA0` at the moment
     a hit lands; writer PC = the init site (both static candidates were
     refuted).
   - **E — combo-scale flag**: watch `[sl+0xf8]` across a full combo and a
     match reset (piggybacks on block A's session).
3. **Capture convention** — every GDB transcript saved under
   `jus_files/analysis/gdb/session1/` (gitignored), one file per block, so
   findings are machine-checkable evidence and become seed anchors for the
   Phase-2 loop.
4. **Live-helper protocol** — a companion prompt for the open Claude
   session: it has the Battle-Engine-Map + `scripts/analysis/query.py`
   available; user pastes raw GDB output; it decodes hex, decides the next
   command, and logs confirmed addresses/fields as it goes.
5. **Validation card batch** — the surviving cards from
   `docs/research/GDB-Validation-Queue.md` (post-Phase-0 regeneration),
   grouped into whichever discovery block's session they can piggyback on.

## Session capture kit (what makes the live Claude session effective)

Full RAM dumps ARE useful — as files for tooling, never pasted into chat.
NDS main RAM is 4 MiB (`0x02000000`–`0x02400000`); in GDB:
`dump binary memory <file>.bin 0x02000000 0x02400000`.

1. **Churn mask first** (kills the noise problem): two dumps of the SAME
   paused idle state → `scripts/analysis/ramdiff.py baseline idle1.bin
   idle2.bin -o mask.json`. Everything that differs (framecounters, sound
   DMA, RNG) is masked out of all later diffs.
2. **Differential pairs around events**: pre/post a single hit, idle vs
   jumping, pre/mid combo → `ramdiff.py diff pre.bin post.bin --mask
   mask.json` → short, pasteable list of changed addresses with
   u8/u16/u32/s16/Q12 interpretations. This is the primary velocity/HP/
   timer field-finder.
3. **Sidecar context per dump** — each snapshot needs: `info registers`,
   the `0x023D2A74` chain dereferenced (`ramdiff.py chain <dump>
   0x023D2A74 0x0 ...` works offline on the dump), characters on screen,
   visible HP, what just happened. The Phase-1 guide will ship a GDB
   `snap <label>` macro automating dump+sidecar (macro file to be written
   at guide-generation time, once Phase-0 addresses are final).
4. **Planted known values**: use moves with documented `damage1` (Goku
   kit) so expected computed values are searchable:
   `ramdiff.py find post.bin --u16 8 --near <charptr> --radius 0x8000`.
5. **Savestates at key moments** (melonDS): savestate immediately before a
   hit = replayable experiment; rerun the identical frames with different
   watchpoints. Single biggest quality multiplier.
6. **Per-breakpoint capture discipline**: on every stop —
   `info registers` + `x/16wx $sp` + `disas $pc-0x20,$pc+0x20`, appended
   to a per-block transcript file under `jus_files/analysis/gdb/session1/`.
7. **Skip VRAM/OAM** — combat logic lives in main RAM; graphics memory is
   noise for this campaign.

Tooling status: `scripts/analysis/ramdiff.py` exists and self-tests
(baseline/diff/find/chain/selftest). The `snap` GDB macro file and the
live-helper companion prompt are generated with the Phase-1 guide.

## Human prep (independent of Phase 0)

- `brew install melonds arm-none-eabi-gdb` (or per `scripts/gdb/README.md`
  from-source build if the brew melonDS lacks the GDB stub).
- ROM + a save that can boot into a free battle quickly, with
  well-documented characters unlocked (Goku / Ichigo preferred — best
  data coverage).

## After Phase 1

Feed the session transcripts + confirmed addresses into a Phase-2 loop
(round-3 tracers with corrected ground truth: B10/B11/B13/B15/B16 from
`jus_files/analysis/findings/critic.round1.json`, plus guard/SP/throws),
then a final synthesis + remaining validation cards. Estimated total to a
substantially complete map: this GDB session (~60–90 min) + one more
overnight loop.
