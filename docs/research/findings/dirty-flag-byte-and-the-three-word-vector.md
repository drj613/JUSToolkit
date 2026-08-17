# Findings: `0x02024C3C` is a dirty-flag setter, and `+0x0C` is one component of a three-word vector

Loop-Atlas iteration 129. Static.

> **Conflict flagged in iteration 132.** Below I call the vtable `+0x18` call a *notify*. That was an
> inference from where the call sits, **not** a reading of the target. Iteration 132 diffed the CommonEffect
> vtables `0x0209C30C`/`0x0209E114` and found slot `+0x18` there is **`Clone`** (`0x0206CFC0`, `CloneMain`).
> Either these are different vtables or the label here is wrong. See
> `vtable-diff-names-slot-0x18-as-clone.md` section 5; unresolved.

Read `0x02024C3C` (64 bytes) — the notify fired right after iteration 128's in-place negation — plus its
other caller. Results:

1. `0x02024C3C` is a **dirty-flag OR-setter** on the byte at `+0x24`, notifying through vtable `+0x18`
   **only on a clear→set transition**.
2. The coordinate iteration 128 negated is **one component of a three-word vector** at
   `+0x0C`/`+0x10`/`+0x14`. Bit `0x01` of `+0x24` means "that vector changed."
3. Iteration 128 negated **`+0x0C` alone** — so the mirror flips one axis of three. That is direct
   corroboration for reading the `+0x48` flag as *horizontal* facing.

---

## 1. The whole function

```
0x02024C3C  push {r3, r4, r5, lr}
0x02024C40  mov  r5, r0
0x02024C44  ldrb r2, [r5, #0x24]     ; cur = flags
0x02024C48  mov  r4, r1              ; bits
0x02024C4C  orr  r1, r2, r4          ; new = cur | bits
0x02024C50  cmp  r2, r1
0x02024C54  beq  #0x2024c64          ; nothing newly set -> skip the notify
0x02024C58  ldr  r2, [r0]
0x02024C5C  ldr  r2, [r2, #0x18]
0x02024C60  blx  r2                  ; obj->vtable[+0x18](obj)
0x02024C64  ldrb r0, [r5, #0x24]     ; RE-READ, not reusing r2
0x02024C68  orr  r0, r0, r4
0x02024C6C  orr  r0, r0, #0x30       ; 0x10 | 0x20, always
0x02024C70  strb r0, [r5, #0x24]
0x02024C74  pop  {r3, r4, r5, pc}
0x02024C78  bx   lr                  ; orphan -- see section 4
```

Three details worth naming:

- **Notify on transition only.** The `cmp`/`beq` fires the vtable call just once per clean→dirty edge, not
  on every mark. Repeated marking is cheap.
- **The re-read at `0x02024C64` is deliberate.** It reloads `+0x24` instead of reusing `r2` from before the
  `blx`, which means the vtable `+0x18` handler is allowed to modify the same flag byte.
- **`0x30` is set unconditionally and never triggers the notify.** The transition test looks only at
  `bits`, so `0x10` and `0x20` can go clear→set silently. Two bits are deliberately outside the
  notification scheme.

## 2. Bit `0x01` marks the three-word vector

Both call sites pass `bits = 1`, and both do it immediately after writing that vector:

```
; 0x0206CEAC (iteration 128) -- writes ONE component
0x0206CF1C  str r2, [r0, #0xc]        ; = -value
0x0206CF20  bl  #0x2024c3c            ; r1 = 1

; 0x02024BE4 -- writes ALL THREE
0x02024C24  str r2, [r0, #0xc]
0x02024C28  str r3, [r0, #0x10]
0x02024C2C  str ip, [r0, #0x14]
0x02024C20  mov r1, #1
0x02024C30  bl  #0x2024c3c
```

Two independent functions, both marking bit `0x01` after touching `+0x0C`…`+0x14`. And `0x02024BE4`
handles the three words as a **unit of `0xC` bytes**:

```
0x02024BEC  mov r3, #0
0x02024BFC  str r3, [sp]        ; a 12-byte stack temporary,
0x02024C00  str r3, [sp, #4]    ; all three words zeroed
0x02024C04  str r3, [sp, #8]
0x02024C08  mov r2, #0xc
0x02024C0C  bl  #0x2051890      ; memcpy, 0xC bytes
0x02024C10  ldr r0, [r4, #0x50] ; the same [arg+0x50] object as iteration 128
0x02024C14  ldr ip, [sp, #8]
0x02024C18  ldr r3, [sp, #4]
0x02024C1C  ldr r2, [sp]
```

`0xC` bytes, three consecutive word stores, one dirty bit covering all of them: a **three-component
vector**. `+0x0C` is its first component.

## 3. Why this strengthens iteration 128

Iteration 128 read `[[P+0x50]+0x0C]`, negated it in place, and marked bit `0x01`. It now turns out `+0x0C`
is **one axis of three**, and the negation touched *only* that axis — `+0x10` and `+0x14` were left alone.

Flipping exactly one axis of a three-axis vector is a **single-axis mirror**. That is what "facing" means
geometrically, and it is a sharper piece of evidence than iteration 128 had: at the time, the negated field
could have been a scalar.

The reading of the `+0x48` byte as a facing / horizontal-flip bit stays **PLAUSIBLE** — still nothing names
it — but the supporting evidence is now one step tighter.

## 4. Recorded, not smoothed over

**An orphan `bx lr` inside the record.** `0x02024C3C + 64 = 0x02024C7C`, so the record includes
`0x02024C78`, one instruction past the `pop` that ends the real function. It has **0 references** and is not
a known function start. Most likely a do-nothing virtual default, reachable only through a vtable — and this
database indexes literal loads and branches, **not vtable contents**, so a vtable reference would be
invisible to it. Same merged-record shape as iterations 125 and 126, at the smallest scale yet: one
instruction.

**`0x02024BE4` is a reset-to-zero.** It zeroes a 12-byte stack temporary, `memcpy`s it to `arg2`, then
stores those (still zero) words into the vector. This reading needed `0x02051890` to be
`memcpy(dst, src, n)`, so I checked: at `0x020518A0` it loads via `ldrh ip, [r1, #-1]` while `r0` is the
side being read *and* written with alignment fixups (`0x020518AC`–`0x020518B4`). So **`r0` = destination,
`r1` = source** — the standard order, now verified rather than assumed. Also note `arg0` (`r0`) of
`0x02024BE4` is **never read** — it is overwritten at `0x02024BF4` before any use.

**`+0x24` is another conventional offset.** 1838 hits, 86 of them `strb`. No field-writer hunt is viable;
it joins `+0x08`, `+0x10`, `+0x18`, `+0x20`, `+0x48` on that list.

## Predictions status

| Claim | Verdict |
|---|---|
| `0x02024C3C` is a dirty-flag OR-setter on the byte `+0x24` | **CONFIRMED_STATIC** — `ldrb`/`orr`/`strb` at `0x02024C44`–`0x02024C70` |
| The vtable `+0x18` notify fires only on a clear→set transition | **CONFIRMED_STATIC** — `cmp r2, r1`; `beq #0x2024c64` |
| The `+0x18` handler may modify `+0x24` | **CONFIRMED_STATIC** — the byte is re-read at `0x02024C64` rather than reusing `r2` |
| `0x10` and `0x20` are set without ever notifying | **CONFIRMED_STATIC** — `orr r0, r0, #0x30` sits after the transition test |
| Bit `0x01` marks the `+0x0C`/`+0x10`/`+0x14` vector | **CONFIRMED_STATIC** — two independent sites pass `1` right after writing it |
| `+0x0C`…`+0x14` is a single three-word vector | **CONFIRMED_STATIC** — `mov r2, #0xc` at `0x02024C08`, three consecutive stores, one dirty bit |
| Iteration 128's negation flipped one axis of three | **CONFIRMED_STATIC** — it wrote `+0x0C` only |
| The `+0x48` byte is a facing / horizontal-flip bit | **PLAUSIBLE** *(strengthened)* — a single-axis mirror, not a scalar negation |
| `0x02024BE4` resets the vector to zero | **CONFIRMED_STATIC** — `0x02051890` verified as `memcpy(dst=r0, src=r1, n=r2)` at `0x020518A0`–`0x020518B4` |
| `0x02024C78` is part of `0x02024C3C` | **REFUTED** — unreachable past the `pop`; an orphan inside the record |
| `0x02024C78` has no callers at all | **not claimed** — vtable references are not indexed by this database |

## Next angles, ranked

1. **Name the other bits of `+0x24`.** `0x01` is the vector; `0x10`/`0x20` are the silent pair. The other
   five are open, and the two callers here only ever pass `1`.
2. **Name `Q`** (carried) — setter at vtable `+0x5C`, boolean at `+0x48`, lazy child at `+0x18`.
3. **Read `0x0206CA8C`** (carried, 1004 bytes) — installs the iteration-128 callback and eleven others.
