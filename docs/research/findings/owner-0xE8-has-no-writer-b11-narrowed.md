# Findings: `owner+0xE8` has no writer in any offset-encoded store

Loop-Atlas iteration 76. Static.

**B11** — who writes `[[char+0x1a8]+0x10]+0xE8`. Iteration 75 gave us distinctive
companion fields for the base, so this is now a proper exhaustive sweep.

**Result: zero credible writers.** Two direct stores exist ROM-wide; both ruled out.
Zero split-offset stores. Zero stores to `+0xE8` in ov6, where the field is read.

A strong negative, but bounded — three unsearchable instruction forms are quantified
in §3.

---

## 1. The sweep

`scripts/decomp/find_field_writers.py` (new, with selftest) runs three passes: direct
`str rD,[base,#OFF]`; split `add rT,base,#N` … `str rD,[rT,#M]` where `N+M == OFF`;
and a companion check — which *distinctive* offsets does the same base register touch
inside the same function?

Companion list from iteration 75's unified owner struct:
`0x34`, `0x38`, `0x3c`, `0x40`, `0x50`, `0x60`, `0xa4`, `0x174`, `0x175`, `0x182`.
`+0x08` **excluded** — iteration 69 showed it is a conventional list-head offset shared
by design, so it carries no signal.

ROM-wide, all 16 regions:

| pass | sites |
|---|---|
| direct `str …,[base,#0xE8]` | **27** |
| direct, restricted to arm9 + ov6 | **2** |
| direct, with any distinctive companion | **0** |
| split-offset (`add` + `str`) | **0** |
| any store to `+0xE8` in ov6 | **0** |

## 2. Both arm9 candidates are ruled out

```
0x02046908  ldr r0, [pc, #0x100]     ; r0 = a GLOBAL, not a struct pointer
0x0204690C  ldr r1, [r0, #0xe8]
0x02046910  orr r1, r1, #1
0x02046914  str r1, [r0, #0xe8]      ; a bit set in a global block
```

`0x02046914`'s base is pc-relative — a literal load masquerading as a field access (the
same class that cost iteration 47 fourteen false hits). Its function `0x0204641C` has
zero callers and no symbol.

`0x0207C684` is inside **`Battle_ColPrmManCreate`** (`0x0207C4C0`). Its `+0xE8` is the
ColPrm manager's third sub-object, documented at iterations 68–69 — a different struct
that shares the offset by coincidence. This is the third time offset reuse has appeared
in this subsystem.

Two other wide candidates also died: `0x0215D204` (ov5) matched four companions but
belongs to `KomaHelp_Create` from `KomaHelp.cpp`, a menu widget; the seven arm9 sites
that pass `owner+0xA4` to a call are all outside the battle overlays.

## 3. What the sweep cannot see

Printed by the tool every run, so zero is never mistaken for proof:

| blind spot | arm9 | ov6 |
|---|---|---|
| Thumb-mode functions | 313 / 4043 (8%) | **18 / 752 (2%)** |
| `stm` block stores | 4596 | 949 |
| register-offset stores `str rD,[rN,rM]` | 169 | 13 |

Plus one form no counter can bound: a sub-region pointer passed as an argument, so the
callee's offset has no relation to `+0xE8`. The obvious candidate was `owner+0xA4` —
the installer memsets `0xD0` bytes from there, and `0xA4 + 0x44 = 0xE8`. **Tested and
empty: ov6 has zero `add rX,rY,#0xa4` sites.** Recorded as refuted per iteration 38's
lesson.

ov6's numbers are what make the negative meaningful. The field is *read* in ov6 at
`0x02158BA8`, and ov6 has almost no Thumb code and only 13 register-offset stores —
"the ov6 writer is hiding in a blind spot" is a thin story. **If a writer exists, it is
far more likely in arm9**, where the owner struct is installed.

## 4. The vestigial-field hypothesis

The only **confirmed** write to `+0xE8` in the whole ROM is the installer's memset:
`0xD0` bytes from `+0xA4` at `0x0207CA80`, covering `+0xA4`–`+0x173`. Zeroed at
install; after four search rounds, never set.

A sibling field supports this. `+0x140` on the same struct is read by the accumulator
flush at `0x0215A300`–`0x0215A334`, and a **live breakpoint logged `r1 = 0` on every
hit** during a run with two landed hits — already documented, and why the accumulator
was refuted as the melee damage path.

So: `+0x140` observed always-zero at runtime, `+0xE8` with no locatable writer after
four rounds. The simplest reading is that **this group of fields is vestigial in the
retail build** — present in the struct, zeroed at install, written by nothing. PLAUSIBLE,
not confirmed: §3's blind spots are real, and `+0xE8`'s runtime value has never been
read (the Phase-1 guide has the card, unexecuted).

If that is right, **B11 is the wrong question** and the ov6 read at `0x02158BA8` is dead
code — worth knowing before another wake is spent on it.

## Predictions status

| Claim | Verdict |
|---|---|
| Exactly 27 ARM immediate-offset stores target `+0xE8` ROM-wide | **CONFIRMED_STATIC** — full sweep of all 16 regions |
| No store to `+0xE8` exists anywhere in ov6 | **CONFIRMED_STATIC** — 0 of 27 sites are in ov6 |
| No `+0xE8` store shares a distinctive companion offset with the owner | **CONFIRMED_STATIC** — 0 of 27, against a 10-offset list |
| No split-offset store resolves to `+0xE8` | **CONFIRMED_STATIC** — 0 sites, `add`+`str` pass |
| `0x02046914` writes the owner | **REFUTED** — base is a pc-relative global |
| `0x0207C684` writes the owner | **REFUTED** — inside `Battle_ColPrmManCreate`; that `+0xE8` is the ColPrm manager's own sub-object |
| The writer reaches the field via an `owner+0xA4` sub-region pointer | **REFUTED** — 0 `add rX,rY,#0xa4` sites in ov6 |
| `+0xE8` is zeroed at installation | **CONFIRMED_STATIC** — inside the `0xD0` memset from `+0xA4` at `0x0207CA80` |
| A writer exists and is hidden in a blind spot | **not claimed** — possible; ov6's 2% Thumb and 13 reg-offset stores make it unlikely *there* |
| `+0xE8`/`+0x140` are vestigial in the retail build | **PLAUSIBLE** — `+0x140` observed 0 at runtime; `+0xE8` has no writer after 4 rounds |

## Next angles, ranked

1. **Stop searching for the writer; test whether `+0xE8` is ever nonzero.** One harness
   read of `[[char+0x1a8]+0x10]+0xE8` on a landed hit settles B11 either way. The
   Phase-1 guide already has the card. Blocked by the static-only constraint, but now
   the *cheapest* remaining route.
2. **Sweep the arm9 `stm` blocks** covering `+0xE8`. 4596 instructions is too many by
   hand, but only those whose base carries a companion offset matter — a bounded
   extension of the new tool.
3. **Re-audit the map's `char+0xNN` offsets** across the three objects (carried).
4. **Name the owner** by tracing the pool at `[[0x0214BE14]+0x8C]+0x8` (carried).
