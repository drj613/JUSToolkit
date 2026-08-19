# P181 — Register-offset store scanner finds no `scratch+0xE8` writer in ov6

> **SCOPE NOTE added 2026-08-19 (P190).** This doc's title and control section are framed around
> ov6, but **the scanner scans arm9 first and then every overlay** — see `regions()` in
> `scripts/analysis/regoff_store_scan.py`. The commit that added it (`7d4b6a4`) says "in ov6" and
> understates what the code does. That mismatch caused a wrong correction at P187 that took two
> wakes to unwind. Global results, re-run with an arm9 positive control (`+0x40` → 4 arm9 hits):
> `+0x130` and `+0x134` return **0 candidates anywhere**. Two limits below are still open and are
> *not* covered by that: the 24 dismissed `+0xE8` hits in ov12/ov10, and the shifted-register
> store class.

**Iteration 181. Static, new tooling.** `query.py search-imm` only catches stores with an immediate offset in the instruction. Three store shapes dodge it, and for large offsets one is unavoidable: a Thumb word store's immediate caps at 124, so **any Thumb writer of `+0xE8` must use a split offset or a register offset.** Iteration 76 already swept the ARM immediate space and found nothing in ov6. That leaves split/register-offset stores as the last static hiding place for the B11 writer.

New tool: `scripts/analysis/regoff_store_scan.py`. Read-only. Takes an offset, reports candidates with context.

## The mode filter, and why rule 1 demanded it

First run flagged arm9 `0x020509C8` — `Thumb add r0, #0xe8`. Disassembling it (rule 1: name the containing function before trusting an offset hit) revealed the region is **ARM**, and the real instruction is `ldr r3, [pc, #0xe8]`. **ARM instruction bytes happen to match Thumb patterns.**

The scanner now checks each candidate's containing function in `functions.json` and drops mismatched modes. That killed the false positive. It also flags candidates in unbinned code (`22` of `30` for `+0xE8`) as mode-unverified instead of silently trusting them — the function-binning blind spot is real and the tool shouldn't paper over it.

## Control: the tool reaches ov6

A negative means nothing without showing the tool *could* have found a positive where it matters.

| offset | candidates | in **ov6** | note |
|---|---|---|---|
| `+0x40` | 17 (11 mode-dropped) | **3** | control — scanner does reach ov6 Thumb code |
| `+0xE8` | 30 (1 mode-dropped) | **0** | target |
| `+0x130` | 0 anywhere | 0 | sibling field read at the same flush |

`+0x40` producing three ov6 hits proves that zero ov6 hits at `+0xE8` comes from the **code**, not the tool's coverage. `+0x130` — the second pending amount the same flush reads at `0x02158BAC` — has no split-offset writer anywhere either, which is consistent.

## The static search space for the B11 writer is exhausted

`CONFIRMED_STATIC`, with limits named:

- **Immediate-offset stores:** swept at iteration 76. 27 ARM hits ROM-wide, none in ov6, zero split-offset, both arm9 candidates individually refuted.
- **Split-offset stores** (`add rN,#0xE8` then `str [rN]`), ARM and Thumb: swept here. **None in ov6.** The 30 hits elsewhere split mainly between 12 in ov12 and 12 in ov10 — and ov12 is the UI overlay whose `+0x172` field burned me at P171, so `+0xE8` there is almost certainly an unrelated widget field. Not chasing them.

**What this tool cannot detect, named precisely:**

1. A register-offset store where the offset register is **loaded or computed**, not `mov rM,#0xE8`.
2. A **shifted**-register store — `str rX,[rBase, rIdx, lsl #2]` with `rIdx` = 58 writes `+0xE8`. The scanner doesn't look for this. Genuine gap, not theoretical.
3. A store through a **cached pointer** to the field, so no offset appears at the store at all.
4. Code outside the binaries I scan.

## The watchpoint is the only remaining route, now backed by evidence

`jus-fun` was already raised to "blocks the campaign's oldest question." It's now the sole route left, and the case for it is a **demonstrated negative with a positive control** — not an assumption that static had been tried. A write-watchpoint on `scratch+0xE8` names the writer in one capture; the runtime loop has offered to breakpoint whatever I name and read its inputs live.

Worth noting: this scan is unaffected by the doc's unverified `+2.0` regen correction, because it never looks at the stored value. Had I built the version my queue originally called for — hunting a `sub #0x80` — the result would have depended on a magnitude nobody has measured.

## Queued by this wake

1. **Extend the scanner to shifted-register stores** (gap 2 above). `str rX,[rY,rZ,lsl #2]` with `rZ` = 58 is a real way to write `+0xE8` and the one remaining shape a static tool can reach.
2. The polled-KO discriminator; the `{kind,id}` table; the extra-ability writer; auto-heal.
