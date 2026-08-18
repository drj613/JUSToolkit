# Handoff — Loop-Atlas, iterations 147–156

Branch `loop/battle-engine-atlas`, HEAD **`510f46d`**, tree clean, **24** commits ahead of
`origin/loop/battle-engine-atlas` (nothing pushed this session — pushing was never
authorised, so don't).

Canonical state lives in `scripts/analysis/loop-state-atlas.json` — iteration **156**, **75** queue
entries, **388** confirmed constants, **427** lessons. The canon doc is
`docs/research/Battle-Engine-Map.md`. Per-wake findings go in `docs/research/findings/*.md`,
now **147** files. The map's inline parentheticals cross-reference finding filenames; don't
rename findings without fixing the map.

**I can only vouch for iterations 147–156.** For phases 0–1, the koma sprint,
and anything before P147, read `docs/research/Research-Status.md` and the charter instead of
trusting any summary. Prior handoffs said the same thing, and it still applies.

---

## 1. Where you are

**Top of queue** — first item is the highest-value lead in the campaign right now:

1. **Hunt the dream-attack chain counter.** Owner-supplied live-play ground truth (P156):
   tapping the active character triggers a *dream attack*; tapping a different deck character
   switches to them and they dream-attack too; returning to the original character fires a
   **special attack** (up-special if you hold up while tapping), and **that special's damage
   scales with how many characters were tapped in between.** Every damage effect this campaign
   has found so far is *flat* — flat resistance, nature not scaling, the ability bitset null
   in both directions. **Chain length is the first concrete multiplier lead.** Find the counter
   field and the site that consumes it; start from the damage core `0x02078488` / public entry
   `0x020783CC`.
2. **Find the per-move variant selector.** A dream attack is a quicker version of an existing
   move, so a variant selector must exist. Check the `BattleObjShot` kind byte (`element+0x1A`, 27
   kinds) and `MoveMan` element flags first.
3. **Sweep every cited address inside the `0x0214CD20` overlay window** and confirm each is
   attributed to the overlay it was actually reasoned about in. P156 audited only
   `0x0214E480`.

Also queued and worth knowing: identify `[0x020AFE90 + 0x28]` (the unknown second term of
path predicate `0x02086BD4`, 149 literal loads); read `0x021671E4` (called right after the
network session teardown); trace `0x0206BB44`'s base register; support-summon effect dispatch
(the owner's ground truth says attack/heal/displacement/status — the existing
`ALL_6_THUMB_SITES_ARE_HEALS` finding may be one arm of it).

Three items the relay had listed as "queued" — damage-core nature field, mode-ID globals,
`record+0x3C` writers — are all still queued and unblocked, but they sit **below** the
dream-attack hunt now. The multiplier lead is worth more than any of them.

---

## 2. Key findings, iterations 147–156

**BattleObjShot (the projectile subsystem).** `Battle_ObjShotManCreate` = **`0x0216A7BC`**
(not `0x0216A7D4`, the `bl` site), confirmed by its own allocator `__FILE__`/`__FUNCTION__`
args rather than module proximity. Manager is **`0x3FD4`** bytes, singleton at **`0x021729EC`**:
`+0x00` active list, `+0x10` free list, `+0x18` a resource object (id `0x88000`), `+0x1C` an
array of **72 elements of `0x6C`** ending at `+0x1E7C`. Per-frame entry is **`0x0216AF04`**.
Shot behaviour dispatches through a **27-entry table at `0x02172864`** indexed by a kind byte
at `element+0x1A` — arity pinned by the `"BattleObjShot.cpp"` string starting at `0x021728D0`,
leaving exactly `0x6C` bytes. Six kinds (`0x01`, `0x05`, `0x0E`, `0x17`, `0x18`, `0x19`) carry
no entity. Eleven element fields mapped incl. a `0x1E`-frame default lifetime.
**`0x2158` bytes of the manager remain unaccounted** — elements end at `+0x1E7C`, manager is
`0x3FD4`, and `search-imm 0x1E7C` returns zero ROM-wide.

**Reachability and the battle root.** ObjShot/ObjCtrl constructors are called from **Thumb**
in ov6 (`0x0214D826`, `0x0214D818`), storing their managers into the battle root via global
**`0x0214D928`** — ObjShot at `root+0x110`, ObjCtrl at `root+0x10C`. P151 independently hit
the same global from the other direction (the chara setup loop's bound is `[root+0x158]`, the
character count).

**Chara setup loop descriptors.** Descriptor words `+0x08`/`+0x0C` come from **three**
alternative function pairs, not one: `0x02173004`/`0x02173014`, or `0x020875B0`/`0x020875D8`,
or `0x02028920`/`0x020208EC`. Selection is two byte guards then predicate `0x02086BD4` =
`([0x020AFE90+0x28] != 0) OR 0x0208C51C()`. `sp+0x28` is a per-slot enable byte array
(`[0]=0`, `[1]=1`; what fills `>=2` is unknown). This **corrected a `CONFIRMED_STATIC` row**
in `findings/thumb-disassembler-and-the-chara-setup-loop.md`, which had named one pair as the
source.

**The network session object.** `0x0208C51C` (24 bytes, **47 callers**) returns
`[0x0214CCF4+4] != 0`. That slot is `0x0214CCF8`, referenced **only** by `ov10` (Nintendo WFC
online) and `ov7` (local wireless) — **zero** references in arm9 or anywhere else. So it is a
network-session liveness pointer, and `arm9` tests it from a fixed RAM slot without linking
either overlay. Lifecycle: ov7 init at `0x021661C0` sets it to **`0x021AA0D8`** then
`memset(0x021AA0D8, 0, 0x1CB4)` (**7348** bytes); ov7 teardown at `0x02166372` nulls it.
Liveness-tracked scanning shows the slot is accessed **only at `+0x00`** — 547 reads, 2 writes.

**ov05 conflict closed.** A contradiction that had lingered for dozens of iterations turned out
to be a **measurement-labelling error**, not a code fact, exactly as predicted: the peer's old
run measured the deck *list* screen while calling it the editor. Re-measured on pixel-verified
screens — editor ov05 **99.5%** / ov01 **4.8%**; list ov01 **99.6%** / ov05 **8.0%**.
`Overlay-Map.md` was right all along.

**The vtable correction.** A peer reported "objects with vtable `0x0215D3B4`". That address is
a **300-byte ARM function** with 12 callees and a `push {r4, lr}` prologue — a code entry
point, not a vtable. Their damage *measurement* was unaffected; the *localization narrative*
built on the label was not. Lesson: separate a peer's measurement from its labelling.

**A real convergence worth reusing.** `entity+0x128` (their ability bitset) fits an 8-byte
hole my static work left open: `char+0x120` is an 8-byte sub-object ending *at* `+0x128`, and
`char+0x130` starts a separate one. Static gap and runtime find agreeing from opposite
directions — cite that instead of the vtable claim.

**The encoding ceiling (closes B11 by arithmetic).** ARMv4T immediate stores scale a 5-bit
field: `STR` maxes at `31 << 2` = **`0x7C`**, `STRB` at **`0x1F`**, `STRH` at **`0x3E`** —
verified empirically against **46390** pattern matches, observed maxima exactly those values,
never exceeded. `owner+0xE8` is 232, and `232 >> 2` = 58 > 31, so **no direct Thumb immediate
store can write it anywhere in the ROM.** The Thumb question *strengthens* the B11 no-writer
result. Same argument armours `deck+0x18EC`. `deck+0x30`'s last game-code candidate
`0x0206BB44` stores **zero**, so the add-entry-is-dead claim holds regardless of its base.

---

## 3. Tool changes

All in `scripts/decomp/`. Every one has a `--selftest`; run it as a gate.

**`find_thumb_callers.py` — two fixes.** (a) `plausible()`'s adjacent-call window was `±2`
halfwords while its own marker scan was `±8`, so two *real* `blx` sites 14 bytes apart could
not see each other and both scored `NONE`. Widened to `±8`. (b) `--audit` gated on
`plausible()` and **silently dropped** everything else, so its output looked like a census when
it was actually a floor. It now keeps impossible-edge rejection but reports heuristic failures
in a separate bucket with an explicit floor/ceiling. Corrected figures: **187 → 340** confirmed
ROM-wide (ceiling **377**), and **15 → 31** in ov6. `findings/thumb-caller-audit.md` is
amended and its "187 of 3691" prediction row flipped to REFUTED.

**`thumb_disasm.py` — `cmp` was decoding as `mov`.** The format-3 `mov` case matched on bits
12 alone (`top == 0b0010`), covering `0x2000`–`0x2FFF`, so **every `cmp Rd,#imm` decoded as
`mov Rd,#imm`**. Silent, and it specifically corrupts control-flow reasoning: a `cmp`+`beq`
read as `mov`+`beq` looks like a branch on a stale flag. Two later `cmp` branches were
unreachable dead code. Fixed; six format-3 encodings now asserted in `--selftest`. This is
what exposed the three-path descriptor selection above.

**`base_offset_scan.py` — new.** Maps which offsets are accessed through a known base
*address*, **with register liveness tracking**. Conservative by construction: stops the walk
on any write to the base, any branch/call/return, any `ldm`/`pop`, on calls when the base is
in `r0`-`r3`/`r12` (AAPCS), and on any encoding it cannot prove safe. Under-reports rather
than misattributes — a missing offset is not evidence of absence, a reported one is evidence
of presence. **It refuted my own claim** that `0x0214CCF8` was a struct base.

> **Read this before trusting any scan you write.** `base_offset_scan.py`'s first version
> reported **zero** hits for a base whose accessors I had hand-read the wake before — a
> clean-looking negative, entirely false. Cause: the arm9 image was picked with
> `sorted(glob(...))[0]`, and sorting puts **`arm7.bin`** ahead of `arm9.bin`. It was scanning
> the wrong CPU's binary. My earlier ad-hoc scans got the right file only by luck of unsorted
> directory order. **Name the file, and give any scan whose interesting answer is "nothing
> survived" a positive control** — otherwise a broken scan is indistinguishable from a clean
> negative.

---

## 4. Confirmed vs open

**Confirmed this session:** the ObjShot manager layout and 27-kind table; Thumb reachability
of both ov6 manager constructors and their battle-root slots; the three-path descriptor
selection and its predicate; `0x0214CCF8` as a networking-only slot with a two-write
lifecycle; the ARMv4T encoding ceilings; that `0x0214E480` is ov05-only and aliased by ov6
during battle; that the ov05 residency contradiction was a labelling error.

**Open, and honestly open:**

- **The per-move attack nature field.** A community guide (relayed, *not* code-verified)
  claims each move has its own Attack Nature. `ColPrm record+0x34`'s low byte does hold **two**
  4-bit fields compared attacker-against-target — the right *shape* — but the semantics
  **skip the target** when they match, which reads as a team/side filter, not damage scaling.
  Marked `PLAUSIBLE` team filter, attack-nature `not claimed`. If a per-move nature exists,
  look at a damage-scaling site, not a spawn filter.
- **The nature-resolver aliasing hypothesis** is `CONFIRMED_STATIC` but **not load-bearing** —
  true, and it does not explain the damage result, because the battle path uses arm9
  `0x02078CB8` (always resident) whose only ov6 use selects a sprite filename.
- The networking identification of `0x021AA0D8` is capped at **`PLAUSIBLE`** and cannot rise
  on static evidence: it is static RAM, never allocated, so no allocation tag or symbol will
  ever name it. Say so rather than implying more digging would promote it.
- `record+0x17C`, `record+0x3C`'s low nibble, `[0x020AFE90+0x28]`, the low nibble of koma
  `+0xB`, `sp+0x28` indices `>= 2`, the `0x2158` unaccounted manager bytes, and the identity
  of all six descriptor functions.

---

## 5. Standing rules

- **One task per wake**, small and committable, prefix `loop-atlas:`.
- **Static only.** No emulator, no GDB. Never modify `jus_files/ripped_jus_files/`.
- **Every claim gets a label** — `CONFIRMED_STATIC` / `PLAUSIBLE` / `SPECULATIVE` / `REFUTED`
  / `not claimed` — plus an address. **Refuted hypotheses are recorded, not deleted.** I
  retracted three of my own claims this session in exactly that style; keep doing it.
- **Doc voice pass.** Every created or substantially edited doc goes through
  `claude -p --model claude-opus-4-6`, then a **numeric-token diff** proving no hex or count
  was dropped. Allow ~420s. Verify the file is unchanged before retrying a timeout.
- **Convergent verification** (charter hard rule, owner-elevated). For load-bearing decodes or
  address claims, seek a second method in a **different representation** — relative
  displacement vs absolute address, encoding arithmetic vs empirical sweep. Agreement across
  representations cannot be shared bias; disagreement identifies which side is wrong.
- **Ask the independent checker BEFORE forming your own conclusion**, not after. Owner
  instruction, and it has paid off twice: once catching a halfword I mis-transcribed
  (`0x6668` for `0x66bc`), once producing a cold-start corroboration of the nature nibble
  layout that shared no reasoning with the original. Hand Codex **raw instruction hex, no
  addresses beyond a start, and no hypothesis.**
- **Escalation** for blocking questions: PR in the `jus_files` repo, `@drj613`.
- **Don't push.** 24 commits are local and that was never authorised.

---

## 6. Tool blind spots, with measured bounds

Four indexes silently under-report. Treat every count as a floor.

| blind spot | measured bound | status |
|---|---|---|
| `xrefs.json` misses Thumb `BLX(1)` → ARM callers | "0 references" means no *ARM* caller | known since it.95–96; `find_thumb_callers.py --to` clears a specific address, `--audit` alone cannot |
| `find_thumb_callers.py --audit` under-reported | **187 → 340** confirmed, ceiling **377**; ov6 **15 → 31** | **fixed** P148 |
| `thumb_disasm.py` decoded `cmp` as `mov` | all of `0x2800`–`0x2FFF` | **fixed** P150 |
| `xrefs.json` literal-load index incomplete | **465 of 4941** arm9 ARM pc-relative loads unrecorded = **9.4%**; 71% have their pool at/past the enclosing function's end | open — `pool-values` counts are floors |
| `find_field_writers.py` is ARM-only | declared in its own docstring | open; encoding ceiling closes it for offsets `> 0x7C` |
| `functions.json` function binning | **six** modules now affected; latest `0x0208C500`–`0x0208C640` has 4 records for 8 leaf accessors | open |
| `callers` double-counts | "2 caller references" often means one caller | long-standing |

Live example of why this matters: `xrefs.json` recorded **4** literal loads of `0x0214CCF4`;
the raw scan found **9** — on the one global that whole finding rested on. **Run the raw scan
alongside the database query, not instead of it.**

---

## 7. Coordination with justoolkit

`justoolkit-47` is a session tracker/relay; `justoolkit-ed` runs the agentic melonDS harness
and is the designated runtime validator — the only route to dynamic evidence without breaking
static-only.

**Delivered to us:** the `0x40` ObjShot element stride confirmed at runtime; the ability
bitset at `entity+0x128` proven **live but null for damage in both directions** (setting bit 9
on a non-resistor and clearing it on a real resistor both do nothing — per-character defence
value is now their leading hypothesis); headless screen capture (`screen.dump`, commit
`be007f1`); menu navigation fixed with absolute taps and per-screen pixel verification; the
ov05 residency re-measurement that closed our contradiction (`9f836c2`, tool at
`scripts/emu/overlay_residency.py`).

**Sent to them:** the ObjShot manager address, element layout, and the better anchor —
`[0x0214D928]` → root → `[root+0x110]` → manager, rather than the singleton. The
`0x0215D3B4`-is-a-function correction. The `entity+0x128`-fills-a-static-gap convergence. Two
boot-trace cautions (Start skips the intro; the in-battle training menu swallows all bridge
input so plans report `ok:true` while nothing happens).

**Pending on their side:** the ObjShot active-list walk logging each element's `+0x1A` kind
byte — queued behind their owner work order (resistance attribution, menu nav, deck creation,
full playthrough). Not blocked, just sequenced. They also flagged that `DOWN+B` was the second
move in `Damage-Reduction-Is-Flat.md` and may be "Forced Change", a special mechanic — the
flat conclusion reportedly holds but the move *labelling* needs review.

**Their standing caveat, which they volunteered:** four attempts "succeeded while measuring
nothing." Treat a negative as real only when they confirm reachability was verified. **Reciprocate
— verify an address is on the path before asking for a sweep.** Doing that in P147b turned up a
bigger result than the sweep would have. A koma-browser residency number was offered and
**declined**: KomaList and KomaIBook are both ov5, so it cannot discriminate.

---

## 8. Charter and PROJECT-GOAL

`docs/research/Loop-Charter-Atlas.md` governs the loop — mission, hard rules (incl. the
convergent-verification rule added this session), delegation, pacing, stop conditions. The
north star is `docs/PROJECT-GOAL.md` (on `master`, `f47d63d`, **not in this worktree**):
reimplementation-grade documentation — field-level structs, control flow, formulas, edge
cases.

The relationship in practice: the charter's evidence discipline is what makes the goal
reachable. "Reimplementation-grade" means a reader can rebuild the behaviour, which requires
knowing not just what a field is but how confident we are and what was ruled out. That is why
refutations are recorded rather than deleted, why every claim carries a label and an address,
and why three of my own claims were retracted in the record this session instead of quietly
edited away.

Pacing: self-paced `/loop`, ~1500s between wakes (owner overrode the charter's 3600s; the
memory note says ~1800s — I used 1500s while actively working a deep queue). Each wake: check
`scripts/analysis/LOOP_STOP` (never present), re-read charter + state, do one task, commit,
update state, **re-arm the wakeup**.

> **The one operational mistake worth inheriting:** I once wrote out that I would schedule the
> next wakeup and then ended the turn without calling the tool. The loop silently died for
> ~16 hours until the peer session noticed. **`ScheduleWakeup` must be the last action of the
> turn, and stating you will call it is not calling it.**
