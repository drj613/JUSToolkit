## P185 — per-character update has no caller chain (CONFIRMED_STATIC)

Runtime's four-point bracket confirmed the prediction: `+0x134` already holds the reduced `384` at `0x02156DE8`, the first instruction after `r4` loads. Two fires per point, matching two landed hits of `-6.000` each. The validity check passed in strong form — two fighters resolved to two *different* scratches (`0x02244020` → `0x0220FDC4`, `0x02228A00` → `0x0220FC3C`). A constant would look identical across both; two distinct plausible values is what makes it real.

The reduction happens before `0x02156DDC` is entered. The plan was to walk its caller chain back into collision/hit detection. **That walk doesn't exist.**

`0x02156DDC` has **zero callers**. It's installed as a callback:

```
0x02156AB4: ldr r0, [r4, #0x1c0]     ; r4 = battleObj
0x02156AB8: ldr r1, [pc, #0x2a4]     ; r1 = 0x02156DDC
0x02156ABC: ldr r0, [r0, #4]         ; r0 = [[battleObj+0x1C0]+4]
0x02156AC0: bl  0x02028384           ; the install
0x02156AC8: mov r1, r4               ; then battleObj is set as its argument, vtable +0x24
```

Its two pool neighbours `0x021574CC` and `0x021570EC` are loaded into `r0` at `0x02156AFC` and `0x02156B9C` and passed onward — the same constructor installs a set of callbacks, not just this one.

**What `0x02028384` actually is.** I nearly called it the per-frame battle scheduler. It isn't. It's a generic setter:

```
0x02028388: ldrb r3, [r0, #0x28]     ; test bit 3 of the flag byte
0x020283D8: str  r2, [r0, #0x40]     ; store the pointer at +0x40
0x02028418: strb r1, [r0, #0x28]     ; set/clear bit 2 from (pointer != 0)
0x0202841C: bl   0x02027EDC          ; notify
```

`0x02028384` has **690 caller references** across arm9, ov10, and ov12 — menu and text-widget overlays. It's an engine-wide "store pointer at `+0x40`, flip the enabled/dirty bit, notify" utility. Calling it a battle scheduler would've been the ov12 text-widget mistake in a new costume: an offset hit inside a function I hadn't named.

The honest statement is narrower than the queue assumed: `0x02156DDC` is registered at `[[battleObj+0x1C0]+0x40`-of-`+4]` through a generic mechanism, and **whatever invokes it each frame is engine-generic, not reachable by walking ov6 call edges.** No static caller chain connects the damage sequence to collision detection — the link is a stored function pointer in a system with 690 unrelated users.

**Third independent static route to the `+0x134` writer. All three are closed:**

| Route | Result |
|---|---|
| Immediate-offset stores to `+0xE8` / `+0x130` / `+0x134` | none in ov6 (iteration-76 sweep) |
| Split / register-offset stores, positive control proving the scanner reaches ov6 | none in ov6 (`regoff_store_scan.py`, P181) |
| Caller chain upstream of `0x02156DDC` | **no chain — callback install, generic invoker** |

`B11` isn't static-solvable with the tools this loop has. That's a result, not a stuck note: a watchpoint on `scratch+0x134` names the writer in one stop, and `jus-fun` (melonDS watchpoints) moves from *useful* to *the only remaining route*. The field is invisible to peek polling — lifetime under one frame, zero except on a damage frame — so polling can't substitute.

**Instrument rule (from runtime's harness note).** A literal `%%08X` left in a generated GDB script made GDB error on the argument count and **detach**, producing zero fires for the whole run. Zero fires looks exactly like a wrong breakpoint address. Added to rule 11: before believing a null result, ask what a broken instrument would have produced — *a tool that quit early looks the same as a tool that ran and found nothing.* The fix (hand-written heredoc instead of generated formatting) removes the class of error, not just the instance.

**Still open, unchanged.** Seven of `0x0215C360`'s 10 callees that never receive the scratch remain unexamined; the bracket says where the value already is and rules nothing out. Runtime's parameter-matched `384`-vs-`800` arm didn't run: at tail 40 in `heal_on_range`, a full sweep produced zero damage events because that tail appears to block rightward movement (`x 649 -> 654` over 24 steps, versus `654 -> 454` leftward), so the seek never closed distance. Zero hits says nothing about the value. A 10-frame tail change flipping 22 connections to zero is *consistent* with a different tail selecting a different attack, but equally explained by the seek never arriving.
