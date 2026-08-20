# Handoff — static loop (atlas), clean shutdown 2026-08-19

> **SUPERSEDED by `HANDOFF-Atlas-P232-2026-08-19.md`** (iteration 232). This doc is still
> accurate on the damage formula derivation, but the branch and worktree it names no longer
> exist and the partner session names have drifted. Read the P232 handoff first.

Written at shutdown request relayed from DJ. Final state of the STATIC loop
(`loop/battle-engine-atlas`), iteration 212. Assume the reader has **zero context**.

## Role

Static reverse engineering of JUS battle mechanics: disassembly, struct and formula mapping,
addresses. Partner is the RUNTIME loop (emulator measurements, `justoolkit-fa`); a LEDGER loop
(`justoolkit-dc`) audits coordination. Standing rules live in `docs/research/Loop-Charter-Atlas.md`,
`docs/orchestration/Charter-Atlas-additions.md`, and `docs/orchestration/COORDINATION-PROTOCOL.md`
(which wins on conflict). Never use an emulator or GDB from this role; never modify anything under
`jus_files/ripped_jus_files/`.

## What I was mid-way through, and the exact next action

**The damage formula is SOLVED** (see `docs/research/Research-Status.md`, dated section 201–212, and
`docs/research/findings/p211-damage-formula-end-to-end.md`).

```
base = ldrsb [elem+0x10 + 4]            ; the move's damage in whole displayed HP
r3   = base << 8                        ; to 8.8 fixed point
    x= [attacker_scratch+0x184] / 256
    x= [attacker_scratch+0x186] / 256
    x= nature_table[defence][attack]
r5   = that result
r0   = -(r5 / 4) per resistance gate passed     ; 0, 1 or 2 gates
out  = (r5 + r0) >> 2                   ; 8.8 -> raw/64 HP scale, stored at 0x02082684 str r1,[fp]
```
Function is arm9 `0x020823E4`, called from `0x02081280`, result accumulated into `scratch+0xA4` at
`0x020812DC`. `CROSS_CONFIRMED` at two bases with controls firing: B base `2048` → `384` (6.000);
DOWN+B base `1792` → `336` (5.250).

**EXACT NEXT ACTION: find whatever sets bit 5 of `[r8+0x40]`.** That is the class-2 resistance gate.
Gate 1 (`0x02082634`) fires on class 1 unconditionally; gate 2 (`0x02082650`) needs that bit. Both read
byte table `0x02092E68` (`[0]=1 [1]=1 [2..7]=2`). In all measured conditions `[r8+0x40] = 0x00000008`,
bit 5 clear. Runtime was taking the `JUS_WATCH` half; the static half is to find writers of `+0x40`
that set bit 5 — **and remember a mask passed to a helper sits next to a CALL, not a store** (this is
how the whole campaign lost fourteen iterations).

This matters because runtime refuted ability `0x09` from both the cached bitset (`battleObj+0x128`) and
the live list (`char_struct+0x1A` count, `+0x1B` bytes), in both directions. The reduction reads a flag
bit and a class table, never the abilities — so **an ability must feed those flags at LOAD time.** That
is the last open link in the damage model.

## Load-bearing but UNCONFIRMED right now

- **`r1` at `0x02082634`** — the class-table index. Its width is unpinned. I assumed the 2-bit nature
  category, but `r1` is reused between the nature lookup and the gates. If it is wider, the table's
  entries `[4..7]` matter and my "0%, 25% or 50%" reading may be incomplete.
- **Which side owns `+0x184`/`+0x186`.** Measured on the attacker's scratch (`0x0220FC3C`), both `1.0`.
  Nothing is known about what writes them or when they are not `1.0`.
- **The nature-category source.** 2-bit fields extracted from `scratch+0x175` via `lsl`/`lsr #0x1E`,
  with bits 0–1 / 2–3 / 4–5 selected by flags. No writer identified.
- **`0x02081F5C`** (`subne sb, sb, r2, lsl #7`) is **LIVE-BUT-UNREACHED, not refuted.** Runtime's
  unconditional counter showed 0 fires because the containing loop body never runs (the list at
  `ColPrmMan+0x48` is empty on a landed hit), so its gate and `r2` were never tested. Do not record it
  as refuted on the merits.
- **`ColPrmMan+0x48`'s list insert.** No immediate-offset word store exists anywhere (644-hit sweep,
  control passing). Insertion must use a computed or register offset. `+0x4C` was never swept.

## Retractions partners may not have fully processed

- **`0x0220DDE0` was named three times.** It is the **`Battle_ColPrmMan`** (`0xFB54`,
  `BattleColPrm.cpp` / `Battle_ColPrmManCreate` line `0x132`, allocated by `0x0207C4C0`). I first called
  it `Battle_ObjMan` (P202) then `Battle_ColMan` (P203). **Anything dated P202 or P203 using those names
  for that address is superseded.** For reference: `Battle_ObjMan` is `0x42D8` (`BattleObj.cpp`, alloc
  `0x0208321C`); `Battle_ColMan` is `0x219C` (alloc `0x0207AD3C`).
- **`Damage-Reduction-Is-Flat.md`** (branch `re/ability-bitset-not-resistance`) is **REFUTED** at its
  central claim. The reduction is a 25% multiplier, not a flat `-2.0`. Its DOWN+B row (`5.000`) is a bad
  measurement — certified value `5.250`. **Mark this at the head of the file**; it cost the campaign
  ~30 iterations.
- **`defence-candidates-ruled-out.md`** (this worktree) still attributes the flat `-2` to ability `0x09`.
  Refuted by runtime in both directions. Correct it — a stale conclusion where the next reader finds it
  first is the highest-cost record error there is.
- **My P209 prediction failed on all four specifics**, and I discarded unpublished a follow-up claiming a
  fixed base of `512` with resistance subtracting `0x40` from the multiplier. Anything asserting a base of
  `512` or a `0xC0` factor is wrong.
- **`jus-f0v`'s premise is moot.** An ability-free opponent cannot be built (`chr_b` records 70–73 are the
  Debug series, unselectable), but the `8.000` unresisted base is now read directly from the formula, so
  no such opponent is needed.

## Open questions parked for DJ

In `br` bead `jus-law` (owner questions) and `jus-5bg` (the deck build). Live items:
- The three custom decks (Edajima `chr_b[67]` `[9,10,56]`, Eve `chr_b[38]` `[25,2]`, Robin `chr_b[18]`)
  are **still useful**, now for testing what sets bit 5 rather than for the `8.000` baseline. Edajima is
  the discriminating arm — he shares **only** id 9 with Luffy. **Robin is the arm to drop**: she has a
  passive auto-guard, and identical `chr_b` records do **not** imply identical live ability sets (Luffy's
  live list appends id `14`, which appears nowhere in his record; nobody has identified what appends it).
- Whether an HP-delta measurement anywhere in the record used a move with a side effect (see gotcha 4).

## Harness and tooling gotchas — the ones not already written down

1. **`query.py search-imm` and `search-op-imm` silently cap output at 200 lines.** Always pass `--all`.
   A `+0x48` sweep showed 200 of **644** and I nearly reported the missing 444 as absence. I audited all
   eight load-bearing sweeps with `--all` afterwards; none was truncated, but the cap is live.
2. **The `JUS_WATCH` write-watchpoint reports `pc` = the storing instruction **+ 8**** (ARM prefetch).
   Verified twice. It still lands on a real instruction, so it reads as valid and nothing complains.
3. **zsh does not word-split unquoted variables.** `$CMD` with arguments becomes a single command name and
   the tool silently produces zero lines. This caused two fake nulls. Also `set --`/`shift` inside a `for`
   loop misbehaves here.
4. **An HP-delta oracle is invalid for any move with a side effect.** DOWN+B forces an opponent character
   switch, so the post-hit HP word belongs to a *different character* — runtime measured the delta going
   **up** by `+0.578`. This is what produced the bad row that misled the campaign for ~30 iterations.
5. **The unit is part of the search term.** The damage reduction hid because every scan looked for `128`
   (2.0 at the raw/64 HP scale) while the formula works in 8.8, where 2.0 is `512`. Three independent
   exhaustion sweeps were all sound and all blind.
6. **`2>/dev/null` eats usage errors**, so a wrong subcommand looks exactly like a null result.
7. **The opus-4-6 doc edit pass has twice compressed a load-bearing convergence sentence** and dropped the
   very hex tokens that made it convergent. Diff hex tokens every time and **restore** dropped ones rather
   than accepting a near-clean diff.

## The `.beads/issues.jsonl` question — answered

**It is empty on this branch by design, and the live shared db is authoritative.** Commit **`369e15f`**
("chore(beads): stop tracking stale worktree .beads; fall through to main db-backed .beads"), authored by
DJ on 2026-08-18, deleted the whole tracked `.beads/` directory from this worktree — including a stale
50-line `issues.jsonl` — precisely so `br` walks up and finds the main repo's db. This worktree has no
`.beads` directory at all, and `br list --label coord` here returns live beads from the shared db. So:

- **Do not line-merge that file.** Resolving from the live db is correct.
- The `.gitattributes` merge driver shelling out to `bd merge` is a **known-broken path** — `bd` is now
  `br` 0.2.19, which has no `merge` subcommand. Dropping the driver (or taking either side and reconciling
  from the db) is the right call.
- All three loops were writing to the same db throughout, so no bead content is lost by discarding the
  tracked copies.

## The second session on my name

`ListAgents` from here shows five peers — `test-suite-guardrails-2e`, `justoolkit-dc`, `justoolkit-fa`,
`justoolkit-ba`, `trainer-5b` — and **no atlas session at all**, mine included. So I cannot see or identify
`battle-engine-atlas-5f`, and I do not know what it is. What I can say: **I am not a restart.** I have run
continuously through iteration 212 with a coherent history, and I did not spawn another session on this
name. I have committed everything and am stopping, so from this moment nothing should be writing to
`loop/battle-engine-atlas` from my side.

## State files a fresh session needs

- `scripts/analysis/loop-state-atlas.json` — iteration, queue, and `coord_state_2026_08_18` holding every
  retraction pushed, instrument rule adopted, and prepared card.
- `docs/research/Battle-Engine-Map.md` — the canon doc, appended nearly every wake.
- `docs/research/Research-Status.md` — dated handoffs; newest covers 201–212.
- `docs/research/findings/p1*.md`, `p2*.md` — per-iteration findings.
- New tools this run: `scripts/analysis/regoff_store_scan.py` (extended with a shifted-register class),
  `scripts/analysis/poolload_scan.py`, `scripts/analysis/split_sum_scan.py`. Each carries a matcher
  self-test with rejection cases; `poolload_scan.py` has a built-in known-answer scan control that aborts
  the tool if it fails.

**Record checks must span branches.** Five key damage documents exist only on `re/ability-bitset-not-resistance`
and `ledger/session-tracker`: `Damage-Reduction-Is-Flat.md`, `Ability-Bitset-Is-Not-Resistance.md`,
`Damage-Path-Codex-Findings.md`, `Move-Damage-Table-Goku.md`, `HP-And-Damage-Runtime-Findings.md`. My
check-the-record habit grepped one worktree — a fraction of the record — for the whole campaign. The
consolidation onto one branch fixes this, which is the single biggest process win available here.

## Addendum — items received from the runtime loop after this doc was written

The runtime loop shut down shortly after I did. Its handoff is
`docs/HANDOFF-2026-08-19-runtime-shutdown.md` on branch `re/ability-bitset-not-resistance`, final sha
`ad02a407c7114423ef9301f85edb4f1131bcde38`. Read it alongside this one — between them they cover both
halves of the damage work.

Three things it records that are **not** above, all `UNCONFIRMED`:

- **Whether the base byte varies per target.** Untested. `base = ldrsb [elem+0x10 + 4]` was measured as `8`
  for B and `7` for DOWN+B — i.e. it varies per **move** — but nobody has checked whether the same move
  against a different target yields a different byte. **This is what the owner's three decks are still
  genuinely good for**, and it is a cleaner use of them than the baseline question they were requested for.
- **`0x02390A60`** — an element pointer (`elem+0x08`) that lies outside every memory range we have named.
  Unidentified.
- **`attacker_scratch+0x184`/`+0x186`** — confirmed as the attacker's factors, both measured `1.0`, with
  **nothing known about what writes them**. (Also listed above, repeated here because the runtime loop
  flagged it independently.)

And one scoping note worth keeping in front of whoever resumes: in **every** measurement taken,
`[r8+0x40] = 0x00000008` with **bit 5 clear**. So only the class-1 path has ever been exercised. The
"0%, 25% or 50%" reduction range is a three-point model of which **one point has been sampled** — do not
present it as characterised.

## The part of this run worth keeping, in the runtime loop's framing

Four derivations in the final thread reproduced the observed values from wrong premises: two of mine, one I
drafted and binned unpublished, and one of the runtime loop's. Theirs was the worst of the four and they
said so themselves — they computed `1792 − 512` by assuming flatness, the very thing in question, then
offered agreement with the doc as independent confirmation.

Two habits made all four visible instead of canonical, and both are worth carrying through the
consolidation:

1. **Pre-register predictions before the measurement.** Every one of those four was caught because someone
   had written down what would falsify it first. A clean arithmetic fit is a reason for *more* suspicion,
   not less.
2. **Refuse to guess an object's identity.** Twice I declined to name which side a register pointed at
   (`r4` in the formula, and the base's source). Both mattered: `r4` turned out to be the **attacker**,
   which changed what the nature factors meant entirely. The same discipline is now owed to `r1`, the
   class-table index, whose width and owning side are both unread.
