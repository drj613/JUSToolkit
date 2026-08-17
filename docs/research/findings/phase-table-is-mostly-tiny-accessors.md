# Findings: the phase table is an interface of mostly-trivial accessors

Loop-Atlas iteration 124. Static.

Iteration 123 called the table's 17 unique targets "15 real handlers". **Wrong.** Seven
are **interior entry points inside one 540-byte function**, and several more are one- or
two-instruction predicates. Only **two** targets are substantial — the table is a vtable
of small accessors, not a pipeline of phase handlers.

---

## 1. What the 17 targets actually are

| target | status |
|---|---|
| `0x0207D9A4`, `0x0207D9A8` | uncatalogued — each a single `bx lr` |
| `0x0207D9AC` | function start, **916** bytes |
| `0x0207DD40` | function start, **540** bytes |
| `0x0207DDD4`, `0x0207DE08`, `0x0207DE3C`, `0x0207DE44`, `0x0207DE4C`, `0x0207DE80`, `0x0207DE88` | **inside `0x0207DD40`** |
| `0x0207DF60`, `0x0207DFC0`, `0x0207DFC8` | in an uncatalogued gap, `0x0207DF5C`–`0x0207DFD7` |
| `0x0207DFD8` | function start, 28 bytes |
| `0x0207DFF4` | function start, 36 bytes |
| `0x0207E010` | **inside `0x0207DFF4`** |

`0x0207DD40 + 540 = 0x0207DF5C`, so seven slots land inside it. `functions.json` lists no
size for them — they are not functions.

## 2. The interior entries are tiny

```
0x0207DE08  cmp r2, #0
0x0207DE0C  movlt r0, #3
0x0207DE10  bxlt lr                  ; a predicate returning 3

0x0207DE44  mov r0, #0
0x0207DE48  bx lr                    ; a constant-return stub

0x0207DF60  cmp r2, #6
0x0207DF64  addls pc, pc, r2, lsl #2 ; a 7-case jump table
```

`0x0207DE44` is a third do-nothing entry alongside the two `bx lr` stubs — returns `0`
instead of void.

## 3. The two substantial targets

| target | size | arg0 offsets touched | callees |
|---|---|---|---|
| `0x0207D9AC` | 916 | `+0x0`, `+0x2`, `+0x4`, `+0x6`, `+0x28`, `+0x50` | `0x02051890`, `0x020517FC`, `0x0201899C` |
| `0x0207DD40` | 540 | `+0xC`, `+0x2C`, `+0x30`, `+0xB0` | `0x0206CF28` |

`0x0207DFD8` (28 bytes) and `0x0207DFF4` (36 bytes) each call only `memset`.

## 4. Why the earlier framing misled

Counting unique addresses and calling them handlers assumes one address = one function.
Here two addresses share a body, eight more are entry points into two bodies, and three
are one-instruction stubs. The table exposes 17 entry points across roughly **six**
distinct code bodies, two of which carry nearly all the work.

## Predictions status

| Claim | Verdict |
|---|---|
| The table's 17 unique targets are 15 real handlers | **REFUTED** *(iteration 123, mine)* — most are interior entry points or stubs |
| Seven targets lie inside `0x0207DD40` | **CONFIRMED_STATIC** — `0x0207DD40 + 540 = 0x0207DF5C`, all seven below it |
| `0x0207E010` lies inside `0x0207DFF4` | **CONFIRMED_STATIC** — `0x0207DFF4 + 36 = 0x0207E018` |
| `0x0207DE44` is a constant-return stub | **CONFIRMED_STATIC** — `mov r0,#0`; `bx lr` |
| `0x0207DE08` is a predicate | **CONFIRMED_STATIC** — `cmp r2,#0`; `movlt r0,#3`; `bxlt lr` |
| `0x0207DF60` contains a jump table | **CONFIRMED_STATIC** — `cmp r2,#6`; `addls pc,pc,r2,lsl #2` |
| Only two targets are substantial | **CONFIRMED_STATIC** — 916 and 540 bytes; the rest are 28, 36, or uncatalogued fragments |
| `0x0207DF60`, `0x0207DFC0`, `0x0207DFC8` are catalogued functions | **REFUTED** — they sit in an uncatalogued gap `0x0207DF5C`–`0x0207DFD7` |
| The table is a phase pipeline | **not claimed** — the shape now looks like an interface of accessors, but nothing here shows how the index is chosen |

## Next angles, ranked

1. **Read `0x0207DD40` whole.** It backs eight of the 17 slots — its structure *is* most of
   the table's meaning.
2. **Read `0x0207D9AC`** — 916 bytes, the largest; calls `memcpy`, `memset`, `0x0201899C`.
3. **Resolve the uncatalogued gap** `0x0207DF5C`–`0x0207DFD7` — three slots and a 7-case
   jump table.
4. **Enumerate the other `record+0x40` bits** (carried).
