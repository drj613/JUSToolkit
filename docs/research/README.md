# JUS research documentation — start here

Rewritten 2026-08-19, after the three loop branches were consolidated onto one branch.
The previous version of this file told every new session to run `bd ready` (the project
moved to `br`), cited uppercase bead ids that `br` rejects, and named a "Current Focus"
that was months stale. If you read that version, discard it.

## The one rule

**Beads is the system of record. Documents explain; they do not decide.**

A document must not assert status in prose. No bare `CONFIRMED`, no `VERIFIED`, no
`Status: Draft`. A load-bearing claim is written as the claim plus the bead that holds its
state:

```
damage reduction is x0.75 per gate [jus-reduction-is-quarter-multiplier-xk1]
```

The bead carries the lifecycle label; the document carries the evidence and the reasoning.
Check a claim with `br show <id>`, not by reading how confident the prose sounds.

Lifecycle labels, from `docs/orchestration/COORDINATION-PROTOCOL.md`:

`state:proposed` → `state:plausible` → `state:runtime-confirmed` / `state:static-confirmed`
→ `state:cross-confirmed`, or out to `state:retracted` / `state:tainted`.

`state:cross-confirmed` means a runtime number and a static address agreed **through
different representations**. It never means "one method, twice".

## Three layers, and only one of them is current

| layer | where | authority |
|---|---|---|
| **Claims** | beads (`br list --label coord`) | the record. Has a lifecycle label. |
| **Canon** | `docs/research/*.md` (40 files) | current explanation, should cite bead ids |
| **Journal** | `docs/research/findings/` (193 files) | **history only.** Never current. |

`findings/` is an append-only research journal — one file per static-loop iteration,
titled "Loop-Atlas iteration N". An entry was true when written and was never revised
afterwards. **Do not cite a `findings/` file as the current answer.** See
`findings/README.md`.

`docs/confirmed-facts/characters/` now holds two verified maps (Goku, Ichigo) plus
`character-index.md`, the identity fields for all 71 characters. The other 69 map files
were placeholders and were deleted. See `docs/confirmed-facts/characters/README.md`.

## Current state (2026-08-19)

All three loops — runtime, static, ledger — were shut down for the consolidation, each
leaving a handoff. Read the one for your role first:

- runtime → `docs/HANDOFF-2026-08-19-runtime-shutdown.md`
- static → `docs/orchestration/HANDOFF-Atlas-Shutdown-2026-08-19.md`
- ledger → `HANDOFF-LEDGER-2026-08-19.md`

**The damage arithmetic is measured; the gate structure is not.** A landed hit loses 25% of
its base per gate — not a flat −2.0 [`jus-reduction-is-quarter-multiplier-xk1`]. The formula
routine is `0x020823E4` and each adjustment is the same quarter-step, `(base<<6)>>8`.

**The gate word is `[r8+0x44]`, not `[r8+0x40]`** [`jus-gate-word-is-r8-0x44-fnz`], with
`r8 = *(arg0+0x0C)`. Six gates hang off it — bits 4, 5 and 6 subtract a quarter, bits 12, 13
and 14 add one — and **none of them is unconditional**. Bits 4, 5, 12 and 13 also require a
category from the sixteen-byte table at `0x02092E68`, whose entries are three distinct values
(`0`, `1`, `2`), not two.

**The scope caveat matters more than the result, and it got worse.** The earlier note that "the
flag word read `0x00000008` with bit 5 clear, so only the class-1 path has been exercised" was
a read of the wrong word — `0x08` is bit 3 of `[r8+0x40]`, which gates none of the six
adjustments. The gate word has therefore never been read at all, and which gate produced the
measured −25% is open: bit 4, bit 5, and the class-free bit 6 are all candidates. "Total
reduction is 0%, 25% or 50%" is not the shape of the code either — the code sums up to three
quarter-steps in either direction.

**The next action** is a breakpoint at `0x0208257C` on a landed hit, reading `r2`, `r8`, `r4`,
`r1`, `r5` and `r0` in one capture. That gives the enabled gates, both object addresses, the
category index and the pre-adjustment base together. It replaces the older plan of watching
`[r8+0x40]` for a bit-5 write, which was aimed one word low.

**Nature does affect damage, and the January 1.5× was right all along**
[`jus-nature-is-read-in-damage-path-hbt`]. The tables the damage routine reads, at
`0x0209FEF4` and `0x0209FF14`, hold `0x0180` — 1.5 in 8.8 — and the arithmetic turns a base
of 8 into 12.000, which is the owner's own live-play number. The August claim that nature is
not consulted is `state:tainted` [`jus-nature-does-not-affect-damage-0c6`]; what it actually
established is that poking the byte *it* poked, mid-battle, changed nothing. The refutation
banners that were briefly added to `archive/Combat-Mechanics.md` and `archive/Combat-Mechanics-Reference.md`
were themselves wrong and have been corrected.

Nature and the resistance gates land in the **same accumulator** and are **additive**.
Advantage plus one resist gate is 1.25× the base, not 1.5 × 0.75.

## Documents currently marked refuted or superseded

| document | why |
|---|---|
| `archive/Damage-Reduction-Is-Flat.md` | central claim refuted; its DOWN+B row of 5.000 is wrong |
| `archive/Combat-Mechanics.md` | asserts the 1.5× nature multiplier as CONFIRMED |
| `archive/Combat-Mechanics-Reference.md` | same |
| `archive/Menu-Nav-Oracle-Attempt-1.md` | superseded by `../harness/Menu-Nav-Verified-From-Pixels.md` |
| `archive/findings/defence-candidates-ruled-out.md` | attributes the reduction to ability `0x09` |

Kept, not deleted — a failed experiment records why an approach doesn't work, which is
worth having. They carry banners so a reader can't land on them unaware.

## Checking your own work

```bash
python3 scripts/check_docs.py        # doc/bead consistency linter
br list --label coord                # the coordination record
br show <bead-id>                    # a claim's real state and provenance
```

The linter fails on a document citing a retracted or tainted bead, on a bead id that
doesn't exist, and on `CONFIRMED`-style prose with no bead id near it. Run it before
committing docs.

## Two failure modes this project has actually suffered

1. **A check that agrees with itself.** A pixel oracle reported "gimmicks OFF" for weeks
   while they were ON, because its reference was captured in the same broken state. Verify
   contamination-capable state through an independent representation — a RAM flag, not a
   screenshot compared against its own past.
2. **Clean evidence skipping the check.** Tidy listings and neat correlations suppress
   verification. A long document is not a verified one; see `docs/confirmed-facts/characters/README.md`.

## Orientation, by topic

| document | use it for |
|---|---|
| `../harness/RE-Session-Playbook.md` | how to approach a research session |
| `HP-And-Damage-Runtime-Findings.md` | HP encoding, measured damage, harness traps |
| `Nature-System-Consolidated.md` | the nature system (current) |
| `Character-State-Struct.md` | in-battle character RAM layout |
| `chr_b-Complete-Mapping.md` | `chr_b.bin` file format |
| `jpower-Mapping.md` | damage/move data format |
| `Overlay-Residency-By-Mode.md` | which overlays are resident when |
| `scripts/emu/README.md` | the melonDS agent harness (not in this directory) |

Harness how-to docs moved to `../harness/` in the 2026-08-21 restructure (see
`../README.md` for the split and the trust rule). `Deck-Editor-Automated.md` stays here
deliberately: it mixes deck-editor game findings (geometry, legality) with harness usage
and is cited by `confirmed-facts/`, so it was not split.

`archive/Research-Status.md` is historical progress tracking and is not maintained. Use beads.
