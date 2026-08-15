# Findings: `prmData` lives at `character+0x84`, and why offset scans structurally cannot find the walker

Loop-Atlas iteration 44. Static.

Iteration 43 found `Battle_PrmDataInit` stores the collision record array at `prmData+0x00`. This
wake traced where `prmData` itself lives, then failed to find its consumer — which finally explains
why the collision walker has resisted every scan in this campaign.

**`prmData` is at `character+0x84`.** None of the 10 sites that read `+0x84` chain into a load of
`+0x00`, because the pointer is handed out through **accessor functions**. Offset-chain scans are
blind past the accessor boundary.

Retraction from earlier this wake: the ov11 "collision-array reader" was an artifact of the scanner
stepping over a `bx lr`.

---

## 1. CONFIRMED_STATIC: `prmData` is stored at `character+0x84`

`Battle_PrmDataInit` (`0x021702BC`) has **3 callers**, all in ov6:

| caller | module |
|---|---|
| `0x0215F6A4` | `BattleCharaDataLoad.cpp` — the character path |
| `0x021632F8` | `BattleMapGimmick.cpp` |
| `0x0216474C` | `BattleMapItem.cpp` |

The character path is a per-character loop:

```
0x0215F698: ldrb r0, [r6, #0x15]      ; kind
0x0215F69C: ldrh r1, [r6, #0x16]      ; index
0x0215F6A0: ldr  r0, [r4, r0, lsl #2] ; kind remapped through a word table
0x0215F6A4: bl   #0x21702bc           ; Battle_PrmDataInit(kind, index)
0x0215F6A8: str  r0, [r6, #0xc]       ; cached in the loop descriptor
0x0215F6AC: ldr  r1, [r6]             ; the character object
0x0215F6B0: str  r0, [r1, #0x84]      ; <-- prmData stored at character+0x84
0x0215F6B4: sub  r7, r7, #1
0x0215F6B8: add  r6, r6, #0x1c        ; descriptor stride 0x1C
0x0215F6C0: bne  #0x215f5a8
```

Full path to a collision record:

```
character+0x84  ->  prmData  ->  prmData+0x00  ->  chr/col/<name>.bin array  ->  +index*20
```

The loop uses a **per-character load descriptor of stride `0x1C`**: `kind` at `+0x15` (byte),
`index` at `+0x16` (halfword), `prmData` cached at `+0x0C`. The `kind` passed to
`Battle_PrmDataInit` is not the raw `+0x15` value — it goes through a word table first.

## 2. REFUTED, mine, same wake: the ov11 "collision-array reader"

The scan looked for `ldr Rd,[Rn,#0x84]` followed within 4 instructions by a load off `Rd`, and
reported one hit reaching `+0x00`:

```
0x0217B0B4  ldrne r0,[r0,#0x84]
0x0217B0B8  moveq r0,#0x0
0x0217B0BC  .word 0xE12FFF1E     <-- this is `bx lr`
0x0217B0C0  ldr   r0,[r0,#0x0]   <-- START OF THE NEXT FUNCTION
```

`0xE12FFF1E` is `bx lr`. The two loads are in **different functions**. The scanner had no
function-boundary check, so it walked through a return into the next function.

Re-run with boundary checking (stop at `bx lr`, `pop {..,pc}`, or any branch):

| | result |
|---|---|
| `ldr [Rn,#0x84]` sites ROM-wide | 10 |
| chains into a load off the loaded register | **0** |

**Nothing loads `prmData+0x00` in a straight line from `character+0x84`.** Fifth false positive from
an under-constrained scan this campaign. The specific defect — not stopping at function
boundaries — is now fixed.

## 3. Also refuted as a strategy: scanning for ×20 stride arithmetic

The walker must multiply an index by 20. Both idioms (`mov Rd,#0x14` + `mul`/`mla`, and
`×5` then `<<2`) give **70 hits** across arm9 and overlays — 14 in arm9, 30 in ov5, 9 in ov6, 3 in
ov11.

Unusable: **20 bytes is too common a struct size** to discriminate. Recording this rather than
grinding through 70 sites — the mistake four earlier offset scans made. The `×5`-then-`<<2` form
returned zero hits; the compiler used `mul`/`mla` throughout.

## 4. Why the walker has resisted the whole campaign

The 10 read sites by module:

| binary | address | module |
|---|---|---|
| arm9 | `0x02049388`, `0x0204939C` | (below first named module) |
| arm9 | `0x02083B98` | `BattleObj.cpp` — the generic object pool |
| **ov6** | **`0x02157DD8`, `0x02157DF0`, `0x02157E14`, `0x02157EA4`, `0x02157F50`** | **`BattleChara.cpp`** |
| ov11 | `0x0217B0B4` | `BattleAI_State.cpp` |
| ov12 | `0x021B6F68` | `ALWidgetBase.cpp` (unrelated — `+0x84` collision of offsets) |

The ov11 site is one of three five-instruction accessors, each ending `bx lr`, each returning a
different per-character pointer:

| accessor | returns |
|---|---|
| `0x0217B0B4` | `character+0x84` (prmData) |
| `0x0217B0CC` | `character+0x90` |
| `0x0217B0E4` | `character+0x9C` |

The five clustered ov6 sites at `0x02157DD8`–`0x02157F50` are the same shape: ov6's own accessor bank.

**This is the structural answer.** The engine never inlines `char+0x84` → `prmData+0x00` → `×20`.
It calls an accessor; the consumer gets the pointer in a register with no trace of its origin. Every
offset-based search this campaign was looking for a chain that does not exist in the instruction
stream.

Same class of failure as the C3 finding, where three hitbox-priority rounds searched an ARM-decoded
listing of Thumb code. In both cases the target was not hidden — the search method could not express
it.

## Predictions status

| Claim | Verdict |
|---|---|
| `prmData` is stored at `character+0x84` | **CONFIRMED_STATIC** — `str r0,[r1,#0x84]` at `0x0215F6B0` |
| `Battle_PrmDataInit` has 3 callers, one per data owner | **CONFIRMED_STATIC** — `0x0215F6A4`, `0x021632F8`, `0x0216474C` |
| A per-character load descriptor of stride `0x1C` drives the loading loop | **CONFIRMED_STATIC** — `kind` at `+0x15`, `index` at `+0x16`, prmData cached at `+0x0C` |
| ov11 `0x0217B0B4` reads the collision array | **REFUTED** — my own artifact; `bx lr` at `0x0217B0BC` separates the two loads |
| Some site chains `character+0x84` directly into `prmData+0x00` | **REFUTED** — 0 of 10 sites, with boundary checking |
| ×20 stride arithmetic identifies the walker | **REFUTED** — 70 hits; 20 is too common a struct size |
| The pointer is handed out by accessor functions, defeating offset-chain scans | **CONFIRMED_STATIC** — ov11 bank of 3 at `0x0217B0B4`/`0x0217B0CC`/`0x0217B0E4`; 5 clustered ov6 sites |
| ov6 `0x02157DD8`–`0x02157F50` is ov6's prmData accessor bank | **PLAUSIBLE** — 5 sites in one `0x180` window in `BattleChara.cpp`, same shape as ov11's |

## Next angles, ranked

1. **Find callers of the five ov6 accessors at `0x02157DD8`–`0x02157F50`.** This is now the precise
   walker question: identify each accessor's function start, run the ARM+Thumb caller scan. The
   consumer is among them. Replaces every offset-based approach.
2. **Check whether those five accessors are dispatch-table entries** rather than directly called —
   iteration 41 found exactly that for the collision stub bank (28 of 36 had zero direct callers).
   Search for their addresses as 32-bit words if the direct scan comes up short.
3. Still open: `prmData+0x0C/+0x10/+0x14` prefixes, what indexes the 68-entry table at `0x02171FEC`,
   what reads spawn-slot`+0x02`, and the 24 positive `ProjectileId` values.
