# Findings: the installer's three-word buffer is entirely dead, and four record fields get names

Loop-Atlas iteration 140. Static.

Iteration 139 left a question: the raw x/y/z saved at `sp+8`…`sp+0x10` are never passed to `0x02082C34`, so
"a later call consumes them." **Wrong.** Scanning all 111 instructions of `0x0207C988` shows those three
words are **written and never read**.

Reading the rest of the installer also names four fields on the ColPrm record from the *caller's* side,
including the destination of the element allocated last wake.

---

## 1. The buffer is dead — every store, and the call that fills it

Every stack reference in the whole function:

```
0x0207C994  add r0, sp, #8      ; the buffer's address, passed to 0x0201899C
0x0207C9D8  add r2, sp, #0      ; a DIFFERENT two-word struct -- this one IS used
0x0207C9E0  str r0, [sp, #8]    ; raw x
0x0207C9EC  str r0, [sp, #0xc]  ; raw y
0x0207C9F8  str ip, [sp, #0x10] ; raw z
0x0207C9FC  str r3, [sp]        ; x >> 4   -> used, via r2
```

There is **no load** from `sp+8`, `sp+0xC` or `sp+0x10` anywhere. So:

- `0x0201899C(sp+8, …)` fills the buffer, and its work is **overwritten** three instructions later.
- The raw x/y/z that overwrite it are **never read**.
- `0x0201899C`'s return value is discarded too — `r0` is clobbered at `0x0207C9AC` by `ldr r4, [sb, #8]`.

The whole three-word buffer, and the call that initialises it, are **dead**. That is the seventh vestigial
finding in this project, and the first where a *function call*'s only purpose is discarded output.

Only `sp+0`/`sp+4` — the shifted pair from iteration 139 — actually reach anything.

## 2. Where last wake's element goes

```
0x0207CA08  bl  #0x2082c34      ; allocate the element
0x0207CA0C  str r0, [r4, #0x5c] ; record+0x5C = the element
```

`r4` is `[sb+8]`, the ColPrm record (iteration 72). So **`record+0x5C` holds the BattleMove element**, sitting
immediately below `record+0x60`, the ColObj — two subsystem handles side by side.

## 3. Two container fields resolved

```
0x0207CA04  ldr r0, [sb, #0xf0] ; -> 0x02082C34, the element allocator
0x0207CA10  ldr r0, [sb, #0xec] ; -> 0x0207AEDC, Battle_ColObjCreate
```

The queue has carried "trace `+0x0EC` and `+0x0F0`'s objects" for many wakes. Both now have roles:
**`+0xEC` is the ColObj factory's container, `+0xF0` is the element container.** Still on `sb` (the
installer's `arg0`), which is **not** established to be the ColPrm manager — same caveat as iteration 138.

## 4. Record fields named from the caller's side

Iteration 72 found the pool allocator *reading* `record+0x34`/`+0x38` but could not say where the values came
from. The installer supplies them directly:

```
0x0207CA64  str r7, [r4, #0x34]   ; record+0x34 = the installer's arg2
0x0207CA6C  str r6, [r4, #0x38]   ; record+0x38 = the installer's arg3
```

And `record+0x3C` is a flags word assembled from a **stack argument**:

```
0x0207C9A4  ldr r5, [sp, #0x30]      ; arg5, a stack argument
0x0207CA3C  orr r5, r5, #0x20c000    ; always
0x0207CA44  ldr r0, [pc, #0x104]     ; = 0x00FCFFFF
0x0207CA4C  tst r7, r0
0x0207CA54  orrne r5, r5, #0x30000   ; if arg2 & 0x00FCFFFF
0x0207CA58  ands r0, r7, #0xf
0x0207CA5C  lslne r0, r0, #4
0x0207CA60  orrne r0, r0, #0x400000
0x0207CA68  orrne r5, r5, r0         ; if arg2's low nibble is set
0x0207CA7C  str r5, [r4, #0x3c]
```

So `record+0x3C` = `arg5 | 0x20C000`, plus `0x30000` when `arg2 & 0x00FCFFFF`, plus
`((arg2 & 0xF) << 4) | 0x400000` when the low nibble is non-zero. **`arg2` is doing double duty** — stored
whole at `+0x34`, and its low nibble re-encoded into bits 4–7 of `+0x3C` with `0x400000` as a marker.

The installer therefore takes **at least six arguments**: `r0`–`r3` plus `[sp+0x30]` and `[sp+0x34]`.

## 5. Two more record fields

```
0x0207CA8C  mov r2, #0x100
0x0207CA94  add r0, r4, #0x100
0x0207CA98  strh r2, [r0, #0x86]   ; record+0x186 = 0x100
0x0207CA9C  strh r2, [r0, #0x84]   ; record+0x184 = 0x100
```

Both were listed as existing in earlier wakes; their initial value is `0x100`. Note the split-immediate form
(`add #0x100` then offset `+0x86`) — `0x186` is not an encodable ARM immediate, the same reason `+0x648` was
invisible in iteration 137.

The tail (`0x0207CAA0`–`0x0207CAF8`) packs 2-bit fields from `[sp+0x34]` into `record+0x175`, writing it
twice — `strb r7` then `strb r2` at `0x0207CAF4`/`0x0207CAF8`, so the first store is immediately
superseded. Another dead store, recorded but not chased.

## Predictions status

| Claim | Verdict |
|---|---|
| A later call consumes the raw x/y/z at `sp+8`…`sp+0x10` | **REFUTED** *(iteration 139, my own)* — no load from those slots in all 111 instructions |
| `0x0201899C`'s output is used | **REFUTED** — overwritten at `0x0207C9E0`, and its return value clobbered at `0x0207C9AC` |
| The three-word buffer is dead | **CONFIRMED_STATIC** — written at three sites, read nowhere |
| `record+0x5C` holds the BattleMove element | **CONFIRMED_STATIC** — `str r0,[r4,#0x5c]` right after `bl #0x2082c34` |
| `+0xEC` is the ColObj factory's container and `+0xF0` the element container | **CONFIRMED_STATIC** — `0x0207CA10` into `0x0207AEDC`, `0x0207CA04` into `0x02082C34` |
| `sb` is the ColPrm manager | **not claimed** — carried caveat; `sb` is the installer's `arg0` |
| `record+0x34`/`+0x38` are the installer's `arg2`/`arg3` | **CONFIRMED_STATIC** — `0x0207CA64`, `0x0207CA6C` |
| `record+0x3C` is a flags word built from `arg5` and `arg2` | **CONFIRMED_STATIC** — `0x0207C9A4` through `0x0207CA7C` |
| `arg2`'s low nibble is re-encoded into `+0x3C` bits 4–7 | **CONFIRMED_STATIC** — `ands #0xf`; `lslne #4`; `orrne #0x400000` |
| The installer takes six or more arguments | **CONFIRMED_STATIC** — `[sp+0x30]` and `[sp+0x34]` are both read |
| `record+0x184`/`+0x186` initialise to `0x100` | **CONFIRMED_STATIC** — `0x0207CA98`, `0x0207CA9C` |
| The first `strb` to `record+0x175` is dead | **CONFIRMED_STATIC** — `0x0207CAF4` then `0x0207CAF8`, same offset |
| What `0x0201899C` actually does | **not claimed** — never read; only that its output here is discarded |

## Next angles, ranked

1. **Read `0x0201899C`.** It is called with a buffer whose contents are thrown away, which makes it either a
   constructor for a three-word type or genuinely dead. Naming it would settle whether section 1 is leftover
   code or a compiler artefact.
2. **Find the installer's caller and read its six arguments.** `arg2` feeds both `record+0x34` and the
   `+0x3C` flags, so naming `arg2` names two fields at once.
3. **Search for `orr .., #0x100`** with companions `0x0C`/`0x14`/`0x34` (carried) — the snapshot suppressor.
4. **Decode `record+0x175`'s 2-bit fields** from `[sp+0x34]` — the tail packs at least three of them.
