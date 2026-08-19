# Findings: the ov6 collision accessor bank, a 17-entry kind table, and what `ProjectileId` actually does

Loop-Atlas iteration 40. Static. New tool: `scripts/decomp/find_jump_tables.py`.

Goal: find the code that consumes negative `ProjectileId` (surviving hypothesis from
`findings/projectileid-is-a-selector-not-an-index.md`). **No such code exists.** Instead: the collision
field readers, a decoded 17-entry dispatch table, and a direct answer.

**`ProjectileId` is not dispatched on. It is copied verbatim into a spawned object** — only for 2 of 17
spawn kinds.

---

## 1. REFUTED: no ~17-case ARM jump table, and no 18/34 bias

Scanned arm9 plus all 14 overlays for both ARM jump-table idioms
(`add pc,pc,Rm,lsl#2` and `ldr pc,[pc,Rm,lsl#2]`), recovering case counts from guarding `cmp Rm,#N`:

- **129 dispatch sites total. Zero with 17 cases.** ov6 has 15 sites, none with 15–19 cases.
- No `cmp` against `0x11`, `0x12`, `0x22`, 17, 18 or 34 in the ov6 reading window.

**Limit:** Thumb has no LDRSB immediate form; Thumb switch dispatches are not covered. Silence is not
proof of absence. Two earlier wrong conclusions came from ARM-only tools, so the new tool prints this
caveat on every run.

## 2. The narrow scan that worked: `ldrsb Rd,[Rn,#3]`

`ProjectileId` is a signed byte at collision offset `0x03`, so the reading instruction is `LDRSB` with
immediate offset 3. Across every binary: **25 sites** — few enough to read them all. (Four earlier
offset-only scans in this campaign skipped that step and got it wrong.)

Nine are in ov6, eight on base `r4`, clustered in `0x021559C8`–`0x02156754`.

## 3. What that ov6 cluster is — and a correction to my first reading

Within `0x02155900`–`0x02156900`, base `r4` is read at **11 of the 16 named collision fields**:

| offset | field | reads |
|---|---|---|
| `+0x00` | CollisionType | 1 |
| `+0x01` | SubType | 5 |
| `+0x02` | ExtFlags | 23 |
| `+0x03` | ProjectileId | 16 |
| `+0x04` | FrameStart | 11 |
| `+0x05` | DurationMult | 5 |
| `+0x08` | OffsetX | 2 |
| `+0x0A` | PositionFlags | 2 |
| `+0x0C` | Width | 2 |
| `+0x0E` | DamageFlags | 2 |
| `+0x10` | HitTier | 1 |

**My first reading was wrong; recording it rather than quietly fixing it.** I assumed "11 of 16
collision fields off one base register" meant this was the runtime `CollisionEntry` *walker* — the
long-open question in `Battle-Engine-Map.md`. Two checks killed that:

- **No stride arithmetic.** No `add r4,r4,#0x14`, no `mov Rd,#0x14`, no multiply by 20 in the window.
  A record walker must advance by 20 bytes.
- **36 `push` function starts** in a 0x1100-byte window — ~30–50 bytes per function on average.

This is an **accessor / stub bank**, not the walker. The walker is still unfound. The open question is
narrowed, not closed: field-level readers are located, and their callers lead to the walker.

## 4. CONFIRMED_STATIC: 17 spawn stubs, a shared factory, and a decoded table

31 stubs in the window share one shape. Two examples from `jus_files/analysis/disasm/ov6.txt`:

```
0x02155D78: push {r4, lr}
0x02155D7C: mov r4, r1            ; r1 = pointer to a collision record
0x02155D80: ldrsb r2, [r4, #2]    ; ExtFlags
0x02155D84: mov r1, #8            ; <-- the kind constant, unique per stub
0x02155D88: bl #0x21565a4         ; shared factory
0x02155D8C: ldrsb r1, [r4, #3]    ; ProjectileId
0x02155D90: strb r1, [r0, #2]     ; store it into the object at +2
0x02155D94: pop {r4, pc}

0x02155D98: (identical, but mov r1, #0xe)
```

Kind constants across the 31 stubs: **exactly 0..16 — 17 distinct values**.

Shared factory at `0x021565A4` (six instructions):

```
0x021565A4: ldr   r3, [pc, #0x10]      ; r3 = 0x021710A8   (a table)
0x021565A8: ldrsb r3, [r3, r1]         ; slot = table[kind]
0x021565AC: strb  r1, [r0, r3, lsl #4] ; object[slot*16 + 0] = kind
0x021565B0: add   r0, r0, r3, lsl #4
0x021565B4: strb  r2, [r0, #1]         ; object[slot*16 + 1] = ExtFlags
0x021565B8: bx    lr
0x021565BC: .word 0x021710A8
```

`lsl #4` gives a **16-byte stride**, so the object is an array of 16-byte slots.

The table at **`0x021710A8`** (ov6 file offset `0x24388`) decodes as 17 signed bytes:

```
06 05 00 00 00 01 02 02 02 02 02 03 04 00 02 02 01
```

| kind | slot | | kind | slot | | kind | slot |
|---|---|---|---|---|---|---|---|
| 0 | 6 | | 6 | 2 | | 12 | 4 |
| 1 | 5 | | 7 | 2 | | 13 | 0 |
| 2 | 0 | | 8 | 2 | | 14 | 2 |
| 3 | 0 | | 9 | 2 | | 15 | 2 |
| 4 | 0 | | 10 | 2 | | 16 | 1 |
| 5 | 1 | | 11 | 3 | | | |

17 kinds map onto **7 distinct slots (0..6)**, many-to-one — slot 2 alone collects kinds 6, 7, 8, 9,
10, 14 and 15. Max slot 6 means the object is at least **112 bytes** (7 × 16).

Partial slot layout from the writes: `+0x00` kind, `+0x01` ExtFlags, `+0x02` ProjectileId.

## 5. CONFIRMED_STATIC: `ProjectileId` is copied, not dispatched on

Of 31 stubs, exactly **two** copy `ProjectileId` into the created object: `0x02155D84` (kind 8) and
`0x02155DA4` (kind 14). Both do `strb r1,[r0,#2]` — stored **verbatim as a signed byte**, no bias, no
negation, no bounds check, no table lookup.

This settles the question from the last two iterations:

- Not an index — no 17-entry data table exists (iteration 39).
- Not a switch selector — no 17-case jump table exists (§1).
- A **tag carried into the spawned entity**. Whatever interprets it reads `slot+0x02` downstream.

This also explains the §4 field cross-tab: `ExtFlags` (23 reads) and `ProjectileId` (16 reads) are
read as a pair to seed the new object.

## 6. The tempting 17-vs-17 coincidence, which I am NOT claiming

17 spawn kinds (§4), 17 distinct negative `ProjectileId` values (−18..−34). Tempting to call them the
same enum with a −18 bias.

**The evidence says no.** If `ProjectileId` were the kind selector, all 17 stubs would read it. Only 2
do, and those two get their kind from a **hardcoded immediate** (`#8`, `#0xE`) unrelated to
`ProjectileId`. The two are independent 17-valued things.

Recorded explicitly because arity coincidences have caused over-fits before (the `chr_b +0x30`
four-sequential-IDs episode, the type-correlation suspicion at iteration 37).

## Predictions status

| Claim | Verdict |
|---|---|
| A ~17-case ARM jump table dispatches on `ProjectileId` | **REFUTED** — 0 of 129 dispatch sites have 17 cases |
| Code applies an 18 or 34 bias to `ProjectileId` | **REFUTED** — no such `cmp`/`add` in the reading window |
| `ProjectileId` is copied verbatim into a spawned object at slot`+0x02` | **CONFIRMED_STATIC** — `0x02155D90`, `0x02155DB0` |
| Only 2 of the 17 spawn kinds carry `ProjectileId` | **CONFIRMED_STATIC** — kinds 8 and 14 |
| 17 spawn stubs exist with kind constants 0..16 | **CONFIRMED_STATIC** — 31 stubs, 17 distinct kinds |
| A 17-entry kind→slot table lives at `0x021710A8` | **CONFIRMED_STATIC** — decoded, 7 distinct slots, 16-byte stride |
| The ov6 `0x02155900`–`0x02156900` bank is the runtime CollisionEntry **walker** | **REFUTED** — my own first reading; no stride arithmetic, 36 tiny functions |
| The ov6 bank is a field **accessor/stub** layer over CollisionEntry | **CONFIRMED_STATIC** — 11 of 16 named fields read off one base |
| The 17 spawn kinds are the same enum as the 17 `ProjectileId` values | **not claimed** — only 2 of 17 stubs touch the field; kinds are hardcoded immediates |

## Next angles, ranked

1. **Find callers of the 31 stubs.** They pass a collision-record pointer in `r1`, so a caller is the
   walker itself or one step from it — the most direct route to the "runtime CollisionEntry parser"
   question.
2. **Find what reads slot`+0x02`.** That is the actual consumer of `ProjectileId` and would give the
   field a meaning. Object base = whatever `r0` holds at `0x021565AC`.
3. **Name the 7 slots and 17 kinds.** Slot 2 (7 kinds) is worth attention first.
4. Explain the 24 positive `ProjectileId` values and 17 negatives on non-projectile collision types
   (open from iteration 39).
