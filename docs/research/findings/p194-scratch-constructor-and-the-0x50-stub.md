## P194 — scratch constructor identified from a live value; `+0x50` is a no-op stub

Runtime read four fields off the confirmed scratch `0x0220FDC4` in battle. One of them — `+0x50 = 0x0207D9A0` — turned out to be a static handle, so I chased it instead of the queued shifted-register scan.

### `0x0207D9A0` is an empty stub, and I found what installs it

`0x0207D9A0`, `0x0207D9A4`, and `0x0207D9A8` are each a single `bx lr` — no-op virtual methods. The installer:

```
0x0207CB24: ldr r0, [r4, #0x40]
0x0207CB28: ldr r1, [pc, #0x24]     ; r1 = 0x0207D9A0, the stub
0x0207CB2C: bic r0, r0, #0x200      ; clear bit 9 of the flag word
0x0207CB30: str r0, [r4, #0x40]
0x0207CB38: str r1, [r4, #0x50]     ; install the no-op at +0x50
```

`CROSS_CONFIRMED`. This is the convergence the standing rule asks for: runtime read `scratch+0x50 = 0x0207D9A0` from **live RAM**, and I found the **static instruction** that writes exactly that value to exactly that offset, on an object whose `+0x40` flag word it also maintains. Exact value, exact offset, two representations sharing no machinery.

So `0x0207C988` (arm9, 444 bytes, 6 callees, 1 caller) **operates on the scratch**, with `r4` as the scratch. Its caller is `0x020834D4` — the pooled-entity constructor already named in the charter — so this is entity construction. The `+0x40`/`+0x50` pair is a *detach*: clear a flag bit, point the handler slot at a do-nothing.

### What it initialises, and what it doesn't

Stores on `r4`: `+0x30`, `+0x34`, `+0x38`, `+0x3C`, `+0x40`, `+0x50`, `+0x5C`, `+0x60`, and bytes at `+0x174`, `+0x175`, `+0x182`.

**Nothing at `+0xE8`, `+0x130`, or `+0x134`.** `CONFIRMED_STATIC`. The scratch's constructor skips the damage fields, consistent with them being per-event scratch written by whatever stages a hit.

### Upgrade to a P187 dismissal

At P187 I retired `0x0207C744` (`str r1,[r4,#0x134]`) as "a bulk initialiser" — a characterisation. The pool word it stores is `0x0207DE80`, a **code address**. So in that object `+0x134` is a **function-pointer slot**, and `0x0207C4C0` installs a handler table inline at `+0x11C`, `+0x120`, `+0x124`, `+0x128`, `+0x12C`, `+0x134`, `+0x138`, `+0x148`. That's a different struct from the scratch, whose `+0x134` holds `384`. Same offset, different meaning — rule 6. The dismissal was right; it now rests on a property of the candidate, not on my description of it.

### The card

`scratch+0x50` — pointer slot, `PLAUSIBLE`.

- **Reachability:** `ESTABLISHED`. Runtime already read this offset live off `0x0220FDC4`.
- **Basis:** while idle it holds `0x0207D9A0`, a `bx lr` no-op, installed by a detach path that also clears bit 9 of `+0x40`.
- **Test:** read `[scratch+0x50]` during a landed hit and compare against `0x0207D9A0`.
- **Expected:** if damage staging attaches a real handler, `+0x50` holds a **different** arm9 address on the damage frame — and that address is the handler to break on.
- **Failure signature:** it stays `0x0207D9A0` throughout, meaning the slot isn't part of the damage path and this dies cleanly.
- **Why it's worth a read:** `+0x40` bit 11 is the damage-pending flag and `+0x40` bit 9 is cleared by the same instruction pair that installs this stub, so the flag word and this slot are maintained together.

### Accepted correction from the runtime loop

My P193 "convergence" — a constructor writing a literal zero to `+0xE8` matching the bracket measuring `+0xE8 = 0` — was **a coincidence of value, not evidence of identity**. A different struct's constructor zeroing its own field says nothing about our field reading zero. They caught it before writing it up as mutual support; I'd already written it up. "Both say zero" is seductive precisely because the numbers match while the objects don't.

Their two measured reasons for the struct difference beat my inferred one: the scratch's `+0x0` is a **pair link** (player scratch `0x0220FC3C` holds `+0x0 = 0x0220FDC4`, the opponent's, whose own `+0x0` is null), not a vtable slot; and my ov12 constructor **zeroes `+0x50`**, which on the live scratch holds an arm9 pointer that zeroing would destroy.

Worth keeping: the pair-link shape matches exactly what I attributed to `0x02081DDC` — "walks a pair and stages damage on both sides." That function is refuted as executing on a landed hit, but **the shape it assumed is real**. That's a different failure from the one recorded, and it slightly raises confidence that whatever does stage damage walks a pair the same way.
