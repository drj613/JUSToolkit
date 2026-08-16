# Findings: `char+0x1a8` is the pooled entity — and last wake read the setter backwards

Loop-Atlas iteration 74. Static.

Iteration 73 claimed the `0x1F0` battle character "is stored at `X+0x1a8`" by setter
`0x021570EC`, inferring a larger outer object. **Both wrong.** The setter's `arg1` *is*
the battle character; what lands at `+0x1a8` is the **pooled entity** from claim 1's
constructor `0x020834D4`.

The correct trace shows a **bidirectional character↔entity link** set up synchronously
inside `Battle_CharaCreate`, tying the battle character to projectile-entities and
collision in one step.

---

## 1. The setter is a callback, not a call

`0x021570EC` has **zero callers**. Its only ROM reference is a literal load at
`0x02156B9C` inside `Battle_CharaCreate` — it's passed as a **function pointer**:

```
0x02156B9C  ldr r0, [pc, #0x1c8]   ; pool 0x02156D6C -> 0x021570EC, the callback
0x02156BA4  str r2, [sp]           ; r2 = 0
0x02156BA8  add r2, r4, #0x100
0x02156BAC  ldrsb r2, [r2, #0xe0]  ; character+0x1E0, the entity index
0x02156BB0  mov r1, r4             ; r1 = the character
0x02156BB4  lsl r2, r6, r2         ; 1 << index
0x02156BC0  bl  #0x2083624
0x02156BC4  ldr r1, [r4, #0x1a0]
0x02156BC8  ldr r0, [r4, #0x1a8]   ; <- read back immediately
```

`0x02083624` is a thin shim: shuffles `r3` and the stack arg, leaves `r0`–`r2` alone,
and tail-calls **`0x020834D4`** — the pooled-entity constructor (claim 1,
`Battle-Engine-Map.md`).

The `ldr r0,[r4,#0x1a8]` four instructions later is the giveaway: `+0x1a8` is filled
**during** the constructor.

## 2. The constructor calls back with (entity, character)

```
0x020834E0  mov ip, r0             ; ip = the callback (arg0)
0x020834E4  ldr r0, [r4]           ; r0 reloaded from the manager global 0x0214BE14
0x020834EC  ldr r4, [r0, #0x14]    ; r4 = the entity
...
0x02083518  cmp ip, #0             ; guarded: no callback is legal
0x0208351C  mov r0, r4             ;   r0 = the entity
0x02083528  blx ip                 ;   callback(entity, character)
0x0208352C  str r0, [r4, #0x30]    ;   entity+0x30 = the callback's return value
```

`r1` is **never written** between `0x020834D4` and the `blx`, so it still holds
`Battle_CharaCreate`'s `r4` — the character.

The callback closes the loop in both directions:

```
0x021570EC  push {r4, lr}
0x021570F0  mov r4, r1             ; r4 = the character
0x021570F4  str r0, [r4, #0x1a8]   ; character+0x1a8 = the entity
0x02157104  mov r0, r4
0x02157110  pop {r4, pc}           ; returns the character
```

**`character+0x1a8` = the entity**; the return value gives **`entity+0x30` = the
character**.

| direction | field | written at |
|---|---|---|
| character → entity | `character+0x1a8` | `0x021570F4` |
| entity → character | `entity+0x30` | `0x0208352C` |

`mov ip, r0` at `0x020834E0` also resolves iteration 72's puzzle: `ldr r0,[r0,#0]` at
`0x02083550` reads the **manager global**, not `arg0`. `arg0` (the callback) is parked
in `ip` on the first instruction. Iteration 72's ColObj chain is unaffected.

## 3. What the entity carries

Everything earlier wakes hung off `[char+0x1a8]` is actually an **entity** field:

| offset | contents | source |
|---|---|---|
| `+0x10` | the ColObj, from installer `0x0207C988` at `0x02083560` | iteration 72 |
| `+0x10` | the pending-delta struct (`+0x40` bit `0x800` gates delta application) | iteration 47 |
| `+0x18` | the `0xA8`-byte NoteTrack | iterations 47, 49 |
| `+0x30` | back-pointer to the character | this wake |
| `+0x38` | `strb` of `-1` at `0x02083520` | this wake |

Right after the constructor returns, NoteTrack construction reads the entity back out:

```
0x02156CCC  ldr r6, [r4, #0x1a8]   ; r6 = the entity
0x02156CD8  ldr r1, [r6, #8]
0x02156CDC  add r0, r6, #0x18      ; build the NoteTrack at entity+0x18
0x02156CE0  mov r2, r6
0x02156CD4  str r4, [sp]           ; the character, on the stack
0x02156CE4  bl  #0x21553e0         ; Battle_NoteTrackCreate
0x02156CE8  ldr r6, [r6, #0x18]
```

**Two `+0x10` readings collide** — iteration 72 says ColObj, iteration 47 says
pending-delta struct. One is wrong; this wake doesn't settle which. Flagged, not
resolved.

## 4. There is no outer object

Iteration 73 inferred an outer struct ≥ `0x570` bytes because the map has a gauge at
`char+0x56c` while `Battle_CharaCreate` allocates only `0x1F0`. With the setter read
correctly, the ov6 battle character is just `0x1F0` bytes and every observed ov6 offset
(`+0x1a0`, `+0x1a8`, `+0x1b4`, `+0x1bc`, `+0x1c0`, `+0x1c4`, `+0x1c8`, `+0x1cc`,
`+0x1e0`, `+0x1ea`, `+0x1eb`) fits.

The `+0x56c` object is a **different struct**. Its GDB anchor `0x020784E4` lives in
arm9, does `ldr r4,[r0,#0x56c]`, and arm9 has its own character constructor at
`0x02053528`. Two character-like structs in two binaries, not one wrapped struct.
**Which one the map's `sl`/`charPtr` claims refer to is still open** — the campaign's
oldest unresolved question, now stated more sharply.

## 5. Why the last two wakes both missed

Iteration 73 read `mov r4,r1 / str r0,[r4,#0x1a8]` and guessed the roles instead of
tracing the one call site. `xrefs-to` returns exactly one reference — cheap to check,
and it settles the direction outright.

**Rule:** `str r0,[r1,#N]` says nothing about which argument is the container. Never
assign roles from the store alone; find a caller. If there are no callers, the function
is a callback and the *invoker* supplies the roles.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x021570EC` is a callback, not a regular function | **CONFIRMED_STATIC** — 0 callers; literal load at `0x02156B9C`; `blx ip` at `0x02083528` |
| `character+0x1a8` holds the pooled entity | **CONFIRMED_STATIC** — `str r0,[r4,#0x1a8]` at `0x021570F4`, `r0` = entity from `0x0208351C` |
| `entity+0x30` holds the character | **CONFIRMED_STATIC** — `str r0,[r4,#0x30]` at `0x0208352C`; setter returns `r1` |
| `r1` reaches the callback unmodified | **CONFIRMED_STATIC** — no write to `r1` in `0x020834D4`–`0x02083528` |
| `0x02083624` is a shim onto `0x020834D4` | **CONFIRMED_STATIC** — `bl #0x20834d4` at `0x0208363C`; `r0`–`r2` untouched |
| NoteTrack is built at `entity+0x18` | **CONFIRMED_STATIC** — `add r0,r6,#0x18` at `0x02156CDC`; `r6` = `[char+0x1a8]` |
| The `0x1F0` object is stored at an outer `X+0x1a8` | **REFUTED** *(iteration 73, mine)* — direction is reversed |
| An outer object ≥ `0x570` holds the battle character | **REFUTED** — `+0x56c` struct is a separate arm9 object |
| The battle character is `0x1F0` bytes | **CONFIRMED_STATIC** — allocation tag at `0x02156A58`; all eleven observed offsets fit |
| `entity+0x10` is the ColObj **and** the pending-delta struct | **not claimed** — two wakes disagree; unresolved |

## Next angles, ranked

1. **Settle `entity+0x10`.** ColObj (iter 72) or pending-delta struct (iter 47)? Both
   matter for the damage pipeline. One store site each — cheap.
2. **Re-audit map's `char+0xNN` offsets** against three objects: ov6 `0x1F0` character,
   entity, and arm9 `+0x56c` struct.
3. **Name the arm9 struct** behind `0x02053528` / `+0x56c` via the allocation census —
   not in battle allocations, so check arm9 tags.
4. **Read `ColObj+0x24`'s method** `0x0207D94C` (carried).
