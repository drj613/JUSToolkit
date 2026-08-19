# Findings: ColPrm's three "hot fields" are owned sub-objects, not per-frame state

Loop-Atlas iteration 54. Static.

Iteration 53 flagged `ColPrm+0xE0`, `+0xE4` and `+0xE8` as **PLAUSIBLE** per-frame mutable state
because all three had 5–6 reads *and* writes while other fields were written once.

**Refuted.** All three are **owned sub-object pointers** — written once at construction, nulled at
destruction. The high read counts come from the constructor reloading each pointer before four setup calls.

Lesson: **access count alone can't tell "mutated per frame" from "constructed via several calls."**
Both look like read-write traffic. Only reading the code tells them apart.

---

## 1. The uniform lifecycle

All three follow the same five-step pattern. Block 1 in full:

```
0x0207C5C4  bl  #0x20517fc       ; memset the manager to 0
0x0207C5C8  bl  #0x2020d90       ; factory -> a new object
0x0207C5CC  str r0, [r4, #0xe0]  ; store it
0x0207C5D0  mov r0, #0x9e000     ; a resource id
0x0207C5D4  str r0, [sp, #8]
0x0207C5D8  ldr r0, [r4, #0xe0]
0x0207C5E0  bl  #0x2012940       ; init(obj, &id)
0x0207C5E4  ldr r0, [r4, #0xe0]
0x0207C5EC  ldr r0, [r0, #4]
0x0207C5F0  bl  #0x2028384       ; install a handler table
0x0207C5F4  ldr r0, [r4, #0xe0]
0x0207C5F8  mov r1, r4           ; r1 = the owner
0x0207C5FC  ldr r0, [r0, #4]
0x0207C604  ldr r2, [r2, #0x24]
0x0207C608  blx r2               ; register self with the sub-object (vtable slot 0x24)
0x0207C60C  ldr r0, [r4, #0xe0]
0x0207C610  mov r1, #0x1000000
0x0207C61C  ldr r2, [r2, #0x94]
0x0207C620  blx r2               ; vtable slot 0x94
```

All six `+0xE0` accesses: one `str`, five `ldr` reloading the pointer for each call. Nothing is mutated.

Side by side:

| field | factory | resource id | handler table |
|---|---|---|---|
| `+0xE0` | `0x02020D90` | `0x9E000` | `0x0207F480` |
| `+0xE4` | `0x02026F94` | `0xA5000` | `0x0207FB60` |
| `+0xE8` | `0x02026F94` | `0xA0000` | `0x0207FBB0` |

The handler tables are code/data addresses inside arm9, not strings — installed via
`0x02028384(obj->[4], table)`.

## 2. Destruction — and `+0xE8` is missing from it

```
0x0207C93C  ldr r0, [r4, #0xe0]
0x0207C940  cmp r0, #0
0x0207C944  beq #0x207c95c
0x0207C948  ldr r1, [r0]
0x0207C94C  ldr r1, [r1, #8]
0x0207C950  blx r1               ; destructor, vtable slot 0x8
0x0207C954  mov r0, #0
0x0207C958  str r0, [r4, #0xe0]  ; null it
0x0207C95C  ldr r0, [r4, #0xe4]  ; same for +0xE4
0x0207C978  str r0, [r4, #0xe4]
```

`+0xE0` and `+0xE4` are null-checked, destroyed via vtable slot `0x8`, and nulled. **`+0xE8` is not
touched here at all** — its only accesses are one `str` at construction and four `ldr` in setup.
No destruction, no null-out.

Either its teardown lives outside the `0x0207C400`–`0x0207DA00` window, or it leaks.

## 3. A cross-subsystem link

`0x02026F94` — the factory for `+0xE4` and `+0xE8` — is the same function `Battle_NoteTrackCreate`
calls at `0x02155440`, storing its result at `NoteTrack+0x8C` (iteration 49) with resource id `0x86000`.

So `NoteTrack+0x8C`, `ColPrm+0xE4` and `ColPrm+0xE8` all hold the same object type. Iteration 49 showed
NoteTrack doing the same vtable-`0x24` self-registration (`r1 = r4`). One shared component type across
both subsystems.

## 4. The resource-id space

Scanning arm9 for `mov Rd,#imm` feeding `bl 0x02012940` turns up 15 call sites, 12 distinct ids, all
multiples of `0x1000`:

```
0x040000  0x08A000  0x09A000  0x09C000  0x09E000  0x09F000
0x0A0000  0x0A1000  0x0A3000  0x0A5000  0x0A6000  0x0C0000
```

ColPrm's three (`0x9E000`, `0xA0000`, `0xA5000`) fall in the dense `0x8A000`–`0xA6000` cluster.
NoteTrack's `0x86000` is absent — issued from ov6, outside this scan.

## 5. This is not the contact-matrix writer

The open question — what fills the contact array at `ColPrm+0x158` — is **not answered here.** This region
is construction and teardown only. The `+0xE0`/`+0xE4`/`+0xE8` sub-objects are now candidates for hosting
the writer, since the manager delegates to them.

## Predictions status

| Claim | Verdict |
|---|---|
| `+0xE0`/`+0xE4`/`+0xE8` are the per-frame mutable state | **REFUTED** *(my own iteration-53 PLAUSIBLE)* — they are owned sub-object pointers |
| All three follow one construct-init-install-register lifecycle | **CONFIRMED_STATIC** — identical five-step blocks `0x5C` apart |
| Each gets a resource id and a handler table | **CONFIRMED_STATIC** — ids `0x9E000`/`0xA5000`/`0xA0000`, tables `0x0207F480`/`0x0207FB60`/`0x0207FBB0` |
| `+0xE0` and `+0xE4` are destroyed via vtable slot `0x8` | **CONFIRMED_STATIC** — `0x0207C950`, `0x0207C970` |
| `+0xE8` is destroyed in the same teardown | **REFUTED** — untouched there; 5 accesses total, none a teardown |
| `NoteTrack+0x8C` and `ColPrm+0xE4`/`+0xE8` are the same object type | **CONFIRMED_STATIC** — same factory `0x02026F94`, same vtable-`0x24` self-registration |
| The handler-table literals are name strings | **REFUTED** — code/data addresses, not printable |
| This region writes the contact array | **REFUTED** — construction and teardown only |

## Next angles, ranked

1. **Follow `+0xE0`'s handler table at `0x0207F480`.** Function pointers on the object that owns the
   contact array's manager — the most direct route to the collision test.
2. **Find `+0xE8`'s teardown**, or confirm it leaks. Cheap: grep arm9 for a null-store to `+0xE8` off a
   ColPrm base.
3. **Identify `0x02012940`'s id argument.** 12 distinct `0x1000`-aligned ids across arm9 — likely file or
   graphics resource handles, which would name several objects at once.
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84`, `prmData+0x0C/+0x10/+0x14`, the 68-entry table at
   `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe for the walker.
