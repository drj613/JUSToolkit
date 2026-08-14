# C3 — Why hitbox-priority Failed Three Rounds

Loop-Atlas iteration 17. Static. New tool: `scripts/decomp/thumb_dis.py`.

The round-2 angle from `Battle-Engine-Map.md` turned out to be a tooling fix, not a new hypothesis. The most-refuted subsystem was searched three times against a disassembly that mis-decodes the relevant code.

## Root cause: the ov6 listing decodes Thumb as garbage ARM

`jus_files/analysis/disasm/ov6.txt` decodes the entire battle overlay as ARM. The Thumb HP-apply callers come out as nonsense:

```
0x02151300: 01688968  stmvs sb, {r0, fp, sp, lr}
0x02151304: 8847201c  stcne p7, c4, [r0], #-0x220
0x02151308: c9f69cef  svc #0x9cf6c9
0x0215130C: 10bd0000  andeq fp, r0, r0, lsl sp
```

`stmvs`, `stcne p7`, `svc #0x9cf6c9` — none of that is real code. ARM decoding steps 4 bytes at a time, so **odd-halfword addresses are missing entirely**: of the five Thumb sites from C0, `0x021513D8` decodes as a bogus `svc`, and `0x021513EE`, `0x021514E6`, `0x021515B2`, `0x02151636` **don't appear in the file at all**.

`functions.json` labels only **18 of ov6's 752 functions** as Thumb, so the disassembler treated nearly everything as ARM.

That listing is what every prior hitbox-priority round searched. It explains two long-standing gaps in `Battle-Engine-Map.md`:

- "the actual damage-formula site, **unfound across 3 rounds**" (campaign item B11)
- "**no two-entity `hitTier`/`hitProperties` comparison** found anywhere in ov0/ov3/ov4/ov5/ov6"

Neither proves the code doesn't exist. Both are consistent with the code being Thumb.

**This doesn't promote any hitbox-priority claim by itself.** It removes a false constraint — a different, smaller thing. Recorded as the round-2 finding the doc requested.

## New tool

`scripts/decomp/thumb_dis.py` — Thumb-16 plus the 32-bit BL/BLX pair. Prints `.hw 0xXXXX` for unrecognized halfwords instead of guessing.

Validated on two known sites before use:

- `0x021540AA` renders `blx 0x02078CB8` then `cmp r0, #0x0` — matches the nature-predicate call from C0.
- `0x02150DD8` renders `blx 0x020783CC` — the auto-heal caller whose return address matches `lr = 0x02150DDD` from a live GDB breakpoint.

## All six Thumb HP-apply callers are heals

Each site's delta argument (`r1`):

| site | delta setup | raw | displayed |
|---|---|---|---|
| `0x02150DD8` | `mov r1,#0x80` | 128 | +2.0 |
| `0x021513D8` | `mov r1,#1` ; `lsl r1,#14` | 16384 | +256.0 |
| `0x021513EE` | `mov r1,#1` ; `lsl r1,#14` | 16384 | +256.0 |
| `0x021514E6` | `mov r1,#0x80` | 128 | +2.0 |
| `0x021515B2` | `mov r1,#0x80` | 128 | +2.0 |
| `0x02151636` | `mov r1,#1` ; `lsl r1,#14` | 16384 | +256.0 |

Every delta is positive. The `+128` sites are per-frame regen; the `16384` sites exceed the `0x4000` max-HP clamp, making them **full heals** (`0x4000` = 16384 exactly — the engine's ceiling).

The `+128` at `0x02150DD6` is a **hardcoded immediate**, triple-confirming the harness session: their GDB `lr`, their observed delta of `+128` across 14,736 hits, and now the literal instruction itself.

### Melee damage doesn't use this function at all

All **14** callers of `0x020783CC` are now accounted for: 6 Thumb heals and 8 ARM sites that take an already-computed delta from script-effect records.

This makes "melee bypasses `0x02078488`" **stronger**, not weaker. I previously suggested melee might hide in the unidentified Thumb sites — wrong. This closes that possibility. Melee HP loss reaches the character struct some other way.

## A failed approach, recorded

I scanned every binary for direct `strh Rd,[Rn,#0x18]` — a write to current HP bypassing the apply function. Result: **226 sites** across arm9 and 12 overlays (22 in ov6 alone).

Useless as-is: `+0x18` is a common offset and nothing constrains the base register to a character struct. Recording it so nobody repeats this search in this form.

To make it useful: constrain by context. A real HP write should sit near a read of `+0x16` (max HP) for clamping, or near the `LDRSH` pair the engine uses elsewhere. Filtering the 226 by "reads `+0x16` within a few instructions" is the version worth running.

## Next angles, ranked

1. **Trace the delta producers at the 8 ARM script-effect sites.** The harness session showed the delta arrives pre-computed; resistance and nature multipliers are upstream. This is campaign item B11 with a corrected search space.
2. **Re-run hitbox-priority searches with Thumb decoding.** Three failed rounds now have a plausible reason for failing — the previously-searched space is worth revisiting for a two-entity comparison.
3. Filter the 226 `+0x18` writers by proximity to a `+0x16` read.

## Prediction status

| ID | Claim | Verdict |
|---|---|---|
| — | Melee damage arrives via one of the 5 unidentified Thumb HP-apply callers | **REFUTED** — all six are heals |
| — | Melee damage bypasses `0x020783CC` entirely | **strengthened** — all 14 callers accounted for, none is damage |
| B11 | The damage-formula site is findable in the existing disassembly | **REFUTED as posed** — the listing mis-decodes the Thumb regions |
