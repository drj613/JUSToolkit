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

`docs/characters/` now holds two verified maps (Goku, Ichigo) plus
`character-index.md`, the identity fields for all 71 characters. The other 69 map files
were placeholders and were deleted. See `docs/characters/README.md`.

## Current state (2026-08-19)

All three loops — runtime, static, ledger — were shut down for the consolidation, each
leaving a handoff. Read the one for your role first:

- runtime → `docs/HANDOFF-2026-08-19-runtime-shutdown.md`
- static → `docs/orchestration/HANDOFF-Atlas-Shutdown-2026-08-19.md`
- ledger → `HANDOFF-LEDGER-2026-08-19.md`

**The damage chain is solved end to end.** Reduction is a **×0.75 multiplier, 25% of base
per gate** — not a flat −2.0 [`jus-reduction-is-quarter-multiplier-xk1`]. Two gates read
the class table at `0x02092E68`; the formula routine is `0x020823E4`.

**The scope caveat matters more than the result.** In every measurement ever taken the flag
word read `0x00000008` with bit 5 clear, so only the class-1 path has been exercised.
"Total reduction is 0%, 25% or 50%" is a three-point model with **one point sampled**. It
is not characterised.

**The exact next action** is to find what sets bit 5 of `[r8+0x40]`. It is the last unknown
in the chain, and it is where abilities are expected to feed in at load time.

**Nature does not affect damage** [`jus-nature-does-not-affect-damage-0c6`]. The 1.5×
advantage multiplier in `Combat-Mechanics.md` and `Combat-Mechanics-Reference.md` is wrong;
both now carry a refutation banner.

## Documents currently marked refuted or superseded

| document | why |
|---|---|
| `Damage-Reduction-Is-Flat.md` | central claim refuted; its DOWN+B row of 5.000 is wrong |
| `Combat-Mechanics.md` | asserts the 1.5× nature multiplier as CONFIRMED |
| `Combat-Mechanics-Reference.md` | same |
| `Menu-Nav-Oracle-Attempt-1.md` | superseded by `Menu-Nav-Verified-From-Pixels.md` |
| `findings/defence-candidates-ruled-out.md` | attributes the reduction to ability `0x09` |

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
   verification. A long document is not a verified one; see `docs/characters/README.md`.

## Orientation, by topic

| document | use it for |
|---|---|
| `RE-Session-Playbook.md` | how to approach a research session |
| `HP-And-Damage-Runtime-Findings.md` | HP encoding, measured damage, harness traps |
| `Nature-System-Consolidated.md` | the nature system (current) |
| `Character-State-Struct.md` | in-battle character RAM layout |
| `chr_b-Complete-Mapping.md` | `chr_b.bin` file format |
| `jpower-Mapping.md` | damage/move data format |
| `Overlay-Residency-By-Mode.md` | which overlays are resident when |
| `scripts/emu/README.md` | the melonDS agent harness (not in this directory) |

`Research-Status.md` is historical progress tracking and is not maintained. Use beads.
