# P164 — Mode classifier lives in ov1; reads a 16-byte-per-mode descriptor table

**Iteration 164. Static only.** Goal: read `0x0216446C`, the function whose return value decides which じかん conversion the time limit uses.

First thing it produced was a correction to my own work.

## The address belongs to ov1, not arm9 or ov6

P163 queued this as "arm9 `0x0216446C`" because arm9 `0x020753F4` calls it. Wrong. `0x0216446C` sits in the shared `0x0214CD20` overlay window — the aliasing hazard the queue keeps warning about, now hitting a real claim for the first time.

`overlays.json` says five overlays cover that address: ov1, ov5, ov6, ov7, ov8. Disassembling the same bytes under each:

| overlay | what `0x0216446C` decodes to |
|---|---|
| **ov1** | **clean 4-instruction leaf ending in `bx lr`** |
| ov5 | mid-function fragment (`cmp r4,#0` / `beq`), no entry point |
| ov6 | mid-function fragment (`ldr r0,[r7]` then a `pop` four instructions later) |
| ov7 | garbage (`mrshs r6, apsr` — Thumb or data decoded as ARM) |
| ov8 | garbage (`ldcllt p0, c11...`) |

`CONFIRMED_STATIC`: **ov1.** Three independent supports. **Boundaries** are right — `0x02164468` is `bx lr`, `0x0216447C` is `push {r3, r4, r5, r6, r7, r8, sb, lr}`, so `0x0216446C`–`0x02164478` is a complete function between two others. **Decode is coherent**, unlike the garbage overlays. **Semantics fit**: ov1 is the menu overlay, and ルールセレクト is a menu screen.

`functions.json` bins it inside `0x02164254` and reports "0 callers" — the known function-binning blind spot. It is its own leaf function.

## What it does

```
0x0216446C: 040090e5  ldr r0, [r0, #4]
0x02164470: 010280e0  add r0, r0, r1, lsl #4
0x02164474: 0c0090e5  ldr r0, [r0, #0xc]
0x02164478: 1eff2fe1  bx lr
```

`CONFIRMED_STATIC`: `mode_field(ctx, mode) = [[ctx+4] + mode*0x10 + 0xC]` — **a table of 16-byte per-mode descriptor records, returning the 32-bit field at record offset `+0xC`.**

Codex got those four words as raw hex — no addresses, no hypothesis — before this was written. It returned the same expression, stated the element size as 16 bytes and the field offset as 12 independently.

The time-limit branch from P163 isn't a hardcoded mode test. It's **data-driven**: `+0xC == 1` means じかん is seconds (`value * 60`), anything else gives `(value+1)*144 - 1`. Whatever `144` means, it's a property of a mode *record*, not of the conversion code.

`ctx` comes from ov1 `0x021643A4`, called at arm9 `0x020753A4`. `not claimed`: what that object actually is. Finding it would expose the table and all three modes' `+0xC` values — the remaining step to explaining `144`.

## Menu-side settings record is 164 bytes

Tracing the source object to the top of `0x0207538C`:

```
0x02075390: 0050a0e1  mov r5, r0          ; arg0 = a container
0x02075394: 042095e5  ldr r2, [r5, #4]    ; array base
0x02075398: 0140a0e1  mov r4, r1          ; arg1 = a slot index
0x0207539C: a400a0e3  mov r0, #0xa4
0x020753A0: 942027e0  mla r7, r4, r0, r2  ; r7 = base + slot * 0xA4
```

`CONFIRMED_STATIC`: **the menu-side settings object is an array element with stride `0xA4` = 164 bytes**, indexed by slot. Every `[r7+0x70]`…`[r7+0x7C]` field in P163's map is an offset inside that record.

## Two P163 loose ends closed

`CONFIRMED_STATIC`: destination base is `0x020AFE90`. P163 read the stores as `str r2, [r1, #0xc]` etc. without proving what `r1` held; `r1` loads at `0x020753CC` from pool `0x02075590`, whose `.word` is `0x020AFE90`. Last unverified link in the field map.

`CONFIRMED_STATIC`: new settings field. `0x020AFEDC` = **settings `+0x4C`**, a byte:

```
0x020753A8: ldrb   r1, [r5, #0xc]
0x020753B0: cmp    r1, #0
0x020753B8: mvnne  r1, #0
0x020753BC: strbeq r4, [r0]      ; [0x020AFEDC] = slot index
0x020753C4: strbne r1, [r0]      ; [0x020AFEDC] = -1
```

Holds **the slot index, or `-1`**, chosen by `[container+0xC]`. ov6 references `0x020AFEDC` directly too (pool `0x02150AFC`), so battle code reads it.

> **Caution — I nearly conflated these myself.** This is **settings `+0x4C`** on the static struct at `0x020AFE90`. It is *not* `root+0x4C`, the per-character word array on the heap-allocated battle root at `[0x02172960]` from P160–P161. Two different structs, both with a `+0x4C`. Any future "+0x4C" claim needs to name its base.

## Queued by this wake

1. **Read ov1 `0x021643A4`** — returns the `ctx` holding the mode table at `[ctx+4]`. Gives up the table, all three modes' `+0xC` values, and finally explains `144`.
2. Dump the 16-byte mode records once the table base is known. Three modes × 16 bytes — small, fully documentable.
3. **Five-way disassembly sweep of every claimed address in the `0x0214CD20` window**, with boundary and coherence checks. This wake found a cited, load-bearing address attributed to the wrong overlay in a doc I wrote last iteration. The sweep is overdue and now proven to catch real errors.
4. Still open: the **Thumb** writer of `[0x020AFE90+0x28]`.
