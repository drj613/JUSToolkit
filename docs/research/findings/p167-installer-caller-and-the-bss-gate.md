# P167 — One caller, unconditional, gate is a BSS byte in ov6

Iteration 167. Static. Goal: find the gate on the per-mode handler installer `0x0214F91C` (P166), and the writer of `root+0x08`. Found the gate. Didn't find the writer, and I'm not going to pretend otherwise.

The right tool was a hand-rolled Thumb `BL` scanner over `ov06.bin`. `xrefs.json` misses ~89% of Thumb pc-relative literal loads (P160), so its caller lists for Thumb functions can't be trusted. Decoding every `F000–F7FF` / `F800–FFFF` halfword pair and computing the target directly is exhaustive by construction.

## The installer has exactly one caller and the call is unconditional

`CONFIRMED_STATIC`. One `BL` in all of ov6 targets `0x0214F91C`: the one at **`0x0214DA58`**.

```
0x0214DA44: b538  push {r3, r4, r5, lr}     ; function start (ARM code ends at 0x0214DA42 with bx lr)
0x0214DA46: 4815  ldr  r0, [pc, #0x54]      ; pool 0x0214DAA0
0x0214DA48: 2101  mov  r1, #1
0x0214DA4A: 6800  ldr  r0, [r0]
0x0214DA4C: 30f0  add  r0, #0xF0
0x0214DA4E: 6800  ldr  r0, [r0]
0x0214DA50: f01a ed9e  blx <arm>
0x0214DA54: 4811  ldr  r0, [pc, #0x44]      ; pool 0x0214DA9C -> 0x02172960
0x0214DA56: 6800  ldr  r0, [r0]             ; r0 = [0x02172960]
0x0214DA58: f001 ff60  bl  0x0214F91C       ; the installer
```

No branch guards it. The gate lives upstream — this whole function is reached conditionally.

## This settles the runtime question I'd filed

I opened `jus-usf` asking for a breakpoint at the installer, worried that `r0` might not come from `[0x02172960]` — which would mean the battle root isn't what writes these fields.

It is. Pool `0x0214DA9C` holds `0x02172960`; the caller does `ldr r0,[r0]` before the `bl`. The installer's `r0` **is** the global's pointee. `CONFIRMED_STATIC`, no runtime needed.

So `root+0x08` and `root+0xC8` (P166) are fields of the same object the anchor points at — the identity both claims rested on. The caller is `0x0214DA58`, uniquely. I downgraded the runtime request, but it had already run — and it converges with the scan from the opposite direction (below).

## Runtime confirmed it independently, same wake

The runtime loop ran `jus-usf` before my downgrade reached them, and it converges with the scan:

```
mode 2, breakpoint *0x0214F91C:  lr = 0x0214DA5D   r0 = 0x021DEA60   r1 = 0x00000001
[0x02172960] in the same run  =  0x021DEA60
```

`lr` is odd, so Thumb, putting the return address at **`0x0214DA5C`** — which is exactly `0x0214DA58 + 4`, the instruction after the `BL` my scanner found. A live return address and an exhaustive static `BL` scan agreeing on the same call site, from opposite directions. Exactly one hit per battle, so the single-caller claim holds at runtime too.

`CROSS_CONFIRMED`: `r0` at the installer is `[0x02172960]`. The expensive failure did not happen; `root+0x08` and `root+0xC8` keep their labels.

**And mode 12 hits neither the installer nor the return site** — zero hits on both, in the *same* GDB session that had just caught mode 2, so the breakpoints were provably live. Setup demonstrably ran (anchor present, `+0x08` = 12, `+0xC8` = 0, default handler). So the gate is upstream of the call, which is what the BSS byte below is.

Their own caveat is worth carrying: two earlier mode-12 attempts printed the same "0 hits" and were both invalid — one where GDB detached on a `SIGILL`, one where the script hit an unsupported command. **A no-hit result is worthless unless the log also shows the session stayed healthy and a control fired.**

## The gate: a byte at `0x0217296D`

`CONFIRMED_STATIC`. Two `BL`s target the containing function `0x0214DA44` — `0x0214DB40` and `0x0214DBA4` — both gated.

The first:

```
0x0214DB24: 480b  ldr  r0, [pc, #0x2C]      ; pool 0x0214DB54 -> 0x0217296D
0x0214DB26: 7800  ldrb r0, [r0]             ; one byte at 0x0217296D
0x0214DB28: 2800  cmp  r0, #0
0x0214DB2A: d00f  beq  0x0214DB4C           ; zero -> skip the whole install path
...
0x0214DB40: f7ff ff80  bl 0x0214DA44
```

**`0x0217296D` is a single byte in ov6's BSS**, thirteen bytes past the root pointer global `0x02172960` (BSS runs `0x02172960`–`0x02172A60`). When it reads zero, the install path is skipped — exactly what the runtime loop saw for mode 12: `root+0x08` written, `root+0xC8` never `1`, default handler left in place.

Codex got the four halfwords with no addresses, only the fact that a word `0x0217296D` sits at `L+0x30`. It returned the same literal-address arithmetic (`Align(L+4,4) + 0x2C = L+0x30`), the same one-byte access at `0x0217296D`, the same branch target, and stated the fall-through condition as "the loaded byte is nonzero" — while noting the supplied facts don't determine that byte's value. Independent, no disagreement.

The second caller gates differently: `0x0214DB94` saves `r0`, calls out via `blx`, `cmp r0,#0` / `beq`, then calls `0x0214DBA0` and `0x0214DA44`. So there are **two** gated entry paths — one on a BSS byte, one on a call result. `not claimed`: which path a real battle takes.

## The handler is a tick that reports completion

`CONFIRMED_STATIC`, found on the way. At `0x0214DD32`:

```
0x0214DD2E: 481d  ldr  r0, [pc, #0x74]
0x0214DD30: 6800  ldr  r0, [r0]             ; the root
0x0214DD32: f001 fe09  bl 0x0214F948        ; = { ldr r1,[r0,#0]; blx r1 } -- invoke root+0x000
0x0214DD36: 2800  cmp  r0, #0
0x0214DD38: d00d  beq  +0x1a                ; zero -> nothing more
0x0214DD3A: 481a  ldr  r0, [pc, #0x68]
0x0214DD3C: 6800  ldr  r0, [r0]
0x0214DD3E: f001 fdfb  bl 0x0214F938        ; install the DEFAULT and clear +0xC8
```

The per-mode handler at `root+0x000` is called through the trampoline `0x0214F948`. **A non-zero return means the rule is over** — default handler restored, `root+0xC8` cleared. That's a real `1 → 0` transition on the flag, but not the one I wrongly proposed for mode 12: it fires on rule completion, not on a failed install.

This also explains the runtime loop's frame timeline. `memset` → default (flag `0`) → per-mode (flag `1`) is the install order; the reverse edge exists and belongs to the end of a match.

## What I did not find

`not claimed`: **the writer of `root+0x08`.** The mode is read as a word at `[root+8]` by the installer, and the runtime loop has it holding the poked settings byte across ten modes, so a writer exists. It isn't a `ldrb [x,#0x10]` from the settings struct followed by a `str [y,#8]` — that pattern appears **zero** times in ov6, and I checked all 34 ov6 pool references to `0x020AFE90`. Either the copy uses a register-offset store (invisible to immediate-based search), or it happens in arm9 before ov6's setup runs.

## Queued by this wake

1. **Runtime, cheap and sharp:** read the byte at `0x0217296D` in a mode-2 battle and a mode-12 battle. Non-zero for 2 and zero for 12 confirms the gate. Same value in both refutes it as *the* discriminator and means the second (call-result) path is what differs.
2. **Static:** the `root+0x08` writer, searching arm9 and register-offset stores.
3. Unchanged: the writer of `root+0x118`/`+0x11C` (the runtime loop's top ask), and the writer of `root+0x4C` (term `V`).
