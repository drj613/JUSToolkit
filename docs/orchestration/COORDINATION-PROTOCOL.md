# Cross-Session Coordination Protocol

Shared canon for the JUS reverse-engineering loops. Every self-paced session re-reads
its own charter each wake; each charter points here for the rules they all share. If a
rule here conflicts with a charter, this file wins.

## Why this exists (read once, then it's muscle memory)

Two sessions — a **runtime** loop and a **static** loop — depend on each other, and
coordination collapsed until the owner hand-prompted it back. Four failures, one root
cause: **coordination was a social act, not a protocol step.** A heads-down agent never
*chooses* to stop and talk. So every rule below turns a judgment call into a checklist
step that gates something the agent already wants to do.

The four failures this protocol is built to prevent:

1. **The barbell.** The runtime loop went silent for a whole session — contact only at
   the start and end — because comms competed with work instead of bracketing it.
2. **The parked anchor.** A static-derived address handed over for runtime testing sat
   behind other work all session. Dereferencing it takes minutes and would have shown it
   was garbage (a literal-pool word, not a global). The static side caught its own error
   four wakes later instead.
3. **Gimmick contamination.** Two sessions of damage numbers were measured with a stage
   gimmick silently ON, while the boot harness reported "OFF" by comparing against a
   reference it captured in the same broken state — a check that agreed with itself. The
   *owner* caught it, not either agent.
4. **Context-free artifacts.** Numbers travelled without their match conditions;
   addresses travelled without their reachability basis. Each side inherited the other's
   hidden assumptions.

## Roles (key off roles, not names — names drift across restarts)

| Role | Job | Current instance |
|---|---|---|
| **runtime** | Drives the melonDS harness, boots battles, measures damage/status, scans RAM. Produces magnitudes. | `justoolkit-09` — started 2026-08-19, **continuous** through several name changes (was `justoolkit-e2`); confirmed directly, with commits 918ec18, d878084, 95209f4, 0941b71 |
| **static** | Works the disassembly, maps structs/formulas, produces addresses. Labels claims. | **alive** — the static loop is continuous through iteration 218; commits `f84f644`, `d1fb4c6`, `56f2783`. Name unknown to itself (a session cannot see its own name), so identify this seat by its `loop-atlas:` commits, not by a name |
| **ledger** | Reads the beads ledger + git, keeps the human catch-up summary, flags inconsistencies, nudges idle loops. Does **not** write findings. | `justoolkit-3e` — started 2026-08-19, confirmed the seat directly; never touches the emulator |

**Other sessions active in this project (not loops, no assigned role):**

| session | what it is doing | emulator |
|---|---|---|
| `justoolkit-8f` | investigating why in-battle touch (dream-attack / support-call taps) does not work; came in cold via a user request | **drove it 2026-08-19**, sent live in-battle touch at DS (140,90); released and stopped melonDS |

**Exclusive access to the emulator is not covered by anything below, and that is the biggest
gap in this protocol.** On 2026-08-19 a session outside the role table drove melonDS
concurrently with the runtime loop's damage measurements, sending live in-battle touch. Three
sessions of results came into question and several nulls had been charged to design error.
Reads and screenshots are harmless; **input during a live battle contaminates**. Until this is
settled properly: say so before you drive it, say so when you stop, and record both on `br`
bead `jus-emulator-access-not-exclusive-tum`. The measurement provenance schema below needs a
mandatory line — *was exclusive access held, and how was that established* — because without
it a conditions block reads clean while being contaminated. That is the gimmick lesson with
another agent as the contaminant.

**`ListAgents` is not a liveness oracle for this table.** On 2026-08-19 this failed three
times in one hour. I read a roster that omitted the runtime and ledger sessions and concluded
both seats were vacant. The ledger independently reached the same conclusion and wrote "ended;
unassigned" into the runtime row — and into the **static** row, while the static loop was
actively committing to this branch. All three seats were occupied throughout.

A session missing from `ListAgents` is *not* evidence it has stopped. Ask it, or check for
recent commits, before writing a seat off. Better: identify a seat by its commit prefix
(`loop-atlas:`, `loop-ed:`) rather than by a session name, because names drift, rosters lie,
and a session cannot even see its own name. Durable content belongs in beads addressed to the
**role**, because that survives both a dead session and a misread roster.

**On every restart, update this table.** Names drift across restarts; this table is the
authoritative mapping. Always resolve the role via `ListAgents` as a backup, but keep this
table current so cold-start readers and cross-session messages can resolve roles without guessing.

All three loops were shut down on 2026-08-19 for the branch consolidation, each
leaving a handoff doc. Whoever restarts a role fills its row back in.

## The wake bracket (the core mechanism)

Communication is not a task that competes with work — it is a **bracket around every
wake**, at the boundary where flow is already broken. Every wake, in order:

1. **Kill switch.** Check it first (each loop's charter names its own).
2. **INGEST.** Read the beads ledger (`br ready` + a sweep of coord beads owned by /
   assigned to your role). Process retractions and taint notices *before* extending
   anything that depends on them.
3. **TRIAGE / FAST LANE.** Any partner artifact awaiting your cheap validation jumps the
   queue — see "Fast lane" below.
4. **WORK.** Exactly **one task** this wake. Capture evidence as terse structured notes
   *while* working (seconds, no prose), so the flush at step 6 is cheap. If the task
   touches a function already quoted in the record, **re-read that function whole before
   searching for a new one** — see "Re-read before you search" below.
5. **RECORD.** Write/update the coord beads for anything you produced.
6. **FLUSH.** Publish everything outbound: retractions, results bearing on the partner's
   open questions, new artifacts — all of it, unprompted. Then `br sync --flush-only`.
7. **SCHEDULE.** Only now may you call `ScheduleWakeup`. **You may not schedule the next
   wake with an unflushed outbox or an unreported urgent item.**

**One task per wake** is load-bearing: smaller wakes mean more boundaries, which means
more comm windows — with zero mid-flow interruptions. The runtime loop especially must
adopt this; unbounded wakes are what produced the barbell.

## Re-read before you search

When a question touches a function already in the record, the first move is to re-read
**that whole function**, not to search for a new one.

We re-read *documents* at wake time — it is step 2 of the bracket and it has paid
repeatedly. We do not re-read *disassembly* we have already pulled, because having
extracted a listing once feels like having read it. It is not the same thing. Extraction
is bounded by the question you had at the time; the listing usually answers questions you
had not thought to ask yet.

Three times in one week the answer was inside something one seat had already quoted. The
sharpest case: the `kshape.bin` record base had been open for a full wake, and
`ldr r0, [r0, #0x14]` — which yields the base by subtraction from any known bitmap — was
sitting in `0x02076D30`, a function already quoted verbatim in the finding doc that posed
the question.

**The corollary, which is where this actually goes wrong.** Do not filter or truncate a
listing you are about to reason from. Two failures landed within an hour of each other,
in different costumes:

```
query.py disasm 0x02076D30 --count 26 | grep -iE "0x1f|lsl|cmp|tst|and|bic|add"
                                        # no `ldr` in the pattern -> hides the answer
git remote -v | head -2                 # -> "the only remote is fork", which is false
```

Both narrow the output using a guess about what the answer looks like, and **neither
prints a warning when the answer is not in the set.** This is the circular-constraint
failure one level down: not a search space over addresses, but the pipe used to read the
search's output. A modular constraint on candidate bases and a grep alternation on a
listing are the same move — deciding in advance which shapes the answer may take.

Rule: **if the output is short enough to read whole, read it whole.** A 34-line function
has no business going through a filter. When you must narrow, say so in the finding, and
treat any residue you have to explain away as a signal that the bound excluded something.

## Push, don't pull

Retractions and ground truth get **pushed, not pulled.** If you retract or relabel
anything you ever sent the partner, or get a result bearing on their open question, it
goes out that same wake — you don't wait to be asked. Urgent items (retractions,
contamination, failed anchors, invalidated assumptions) are sent **immediately**, not
held for the boundary flush.

## Fast lane: cheap validation of the partner's work is P0

Any address the static loop sends gets runtime-tested within **one wake** of receipt,
budget **≤10 minutes**. If it can't be tested that cheaply, *that fact* goes back the
same wake ("can't test cheaply because X" is also a message). This is the rule that would
have caught the parked anchor four wakes early.

**Falsification before expansion.** The first runtime action on a new anchor is the
cheapest test likely to *disprove* it (mapped? readable? plausible shape? stable/variable
where expected?). Garbage ends the test immediately and produces a rejection artifact.
The first action on a measurement harness is a control capable of proving its own state
report *wrong*.

## Provenance is a schema, not a norm

An artifact missing its provenance block is **malformed** — the receiver bounces it back
rather than building on it. That bounce-back is what makes the schema self-enforcing.

**Measurement (runtime → static) must carry:** build/version · character & loadout ·
stage · **stage-gimmick state and how it was independently verified** · rules/mode ·
relevant status/setup · harness commit · raw observations + repetitions · derived value
(if any) · positive-control result for the batch · confidence + caveats.

**Address (static → runtime) must carry:** address + type (ROM/RAM/pointer/offset/
instruction) · build applicability · **reachability basis** (caller / xref / pointer
chain / signature / surrounding logic; is live-battle reachability established or only
inferred?) · expected runtime shape or invariant · a concrete **one-line runtime test and
its recognizable failure signature** · confidence label.

## Claim lifecycle + taint

Every claim carries an explicit state. "Confirmed" must never ambiguously mean "confirmed
by one method."

```
PROPOSED → STATIC_CONFIRMED | RUNTIME_CONFIRMED → CROSS_CONFIRMED
                     ↘ RETRACTED / SUPERSEDED
```

- `CROSS_CONFIRMED` requires a runtime number and a static address agreeing through
  **different representations** (convergent verification — the owner's standing rule).
- A **retraction** names the invalid claim, why it failed, and every downstream artifact
  that may depend on it. Consumers mark dependent work `TAINTED` until revalidated. Use
  beads dependency links so taint propagates transitively.
- **TTL / trust decay.** Any cross-session claim unverified within **3 wakes**
  auto-downgrades to `SPECULATIVE`. Trust decays by default rather than persisting.
- **Aging blocker.** A `kind:request` / blocker may not survive more than **one completed
  wake** without completion, rejection, or a status update. This alone surfaces a parked
  task immediately.

## Instrument discipline (the gimmick lesson, generalized)

- **A check whose reference was produced by the system under test is no check at all.**
  Verify contamination-capable state (gimmicks, items, mode) through an **independent
  representation** — a RAM flag, not a framebuffer compared to its own past capture. The
  runtime loop already has the pattern: deck state at `0x020A0C00` is the RAM oracle "the
  screen cannot" match.
- **Every measurement batch opens with a positive control** — a known-nonzero-effect
  action proving the instrument is live. The bit-4 Auto-Guard flip that drives damage
  6.0 → 0.0 is the canonical one. A batch of nulls with no positive control is
  uninterpretable.

## Leverage `/codex` — both loops, hardest for runtime

An independent second opinion is cheap and catches what a single perspective can't. Use
the `codex:rescue` skill (or the `codex:codex-rescue` agent) whenever:

- a load-bearing decode, address, or formula is about to land in a canon doc,
- you're stuck two wakes running on the same question,
- you want a claim confirmed or refuted from a fresh angle.

**Ask the independent checker BEFORE forming your own conclusion, not after** — Codex
confirming your conclusion is worth far less than Codex finding the inconsistency (it
caught a mis-transcribed halfword this way). The static loop already uses this well; the
runtime loop should use it deliberately, especially before publishing any address
interpretation or accepting a surprising measurement.

**Frame it neutrally — never lead Codex to your answer.** Give it the context and the
question, but not your hypothesis or the answer you expect. "Confirm `0x02172960` is the
battle root" invites agreement; "here are the reads / xrefs / disassembly — what is this
address?" lets it reach an *independent* conclusion. Then reconcile the two:

- Two conclusions reached independently that agree is the strong signal (the same logic as
  convergent verification — independence is what makes agreement mean something).
- Disagreement is not a failure — it means one side is wrong, and the gap almost always
  shows which. Chase it; don't paper over it.

Leading Codex to your answer throws away the exact independence that made the call worth
making. This applies to both loops.

## Subagents: bounded evidence collectors, never voices

Both advisors and the owner agree: **never delegate outbound communication.** Knowing
which observation invalidates the partner's work needs the main loop's full context, and
a comms subagent forks the audit trail the owner relies on to course-correct.

Subagents are fine for **narrow, read-only evidence collection** (run address X in three
controlled battles and return raw reads; sweep these files; diff this dump). When used:

- the assignment, scope, expected output, and stop conditions go in a coord bead so the
  owner can see them,
- the subagent may gather evidence but **may not publish conclusions** to the partner,
- the main loop inspects the raw output and accepts/rejects it before anything is
  published,
- one narrow task, a fixed experiment budget, no authority to expand scope.

## The ledger (system of record)

**beads (`br`) is the system of record.** It's git-synced, dependency-aware, survives
context clears, and gives the owner `br list` visibility without reading any transcript.
SendMessage is demoted to a **doorbell** — an urgent nudge that points at a bead. A missed
message can no longer corrupt weeks of work, because the ledger is swept every wake
regardless. Push (immediate) + persistent pull (the sweep) = the redundancy you want
between two loops that both demonstrably lapse.

### beads write convention (prefix `JUS-`, all coord artifacts labelled `coord`)

- **kind:** `kind:anchor` · `kind:measurement` · `kind:request` · `kind:retraction`
- **owner (role, not name):** `owner:runtime` · `owner:static`
- **lifecycle:** `state:proposed` · `state:plausible` · `state:static-confirmed` ·
  `state:runtime-confirmed` · `state:cross-confirmed` · `state:retracted` · `state:tainted`
- **provenance block** goes in the bead description (the schema above).
- **taint / dependency:** `br dep add <downstream> <upstream>` so a retraction on the
  upstream flags the downstream.

Representative commands (confirm exact flags with `br --help`; this repo is on `br`
0.2.19 — see the `br JSONL format` note in project memory for the lowercase-id / metadata
quirk):

```
br create --type task --title "anchor: [root+0x4C] multiplier V" \
  --label coord --label kind:anchor --label owner:static --label state:plausible \
  --description "<provenance block>"
br update JUS-xxx --label +state:retracted --label -state:plausible
br dep add JUS-downstream JUS-upstream
br list --label coord            # the shared coordination state
br sync --flush-only             # at every FLUSH step
```

The ledger session consumes this; it does not write findings into it. See
`Charter-Ledger.md`.
