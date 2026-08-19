## P199 — the accumulator is pipeline stage 5; the earlier null was an empty list

Traced the accumulator's identity by walking upward through its callers. No emulator needed. This also corrects a shared misreading we both relied on.

### `0x020821C4` is stage 5 of an eight-stage pipeline

`0x02080C28` (arm9, 72 bytes) calls eight functions in sequence, all with the same object in `r4`:

```
0x02080C30: bl 0x02080F14
0x02080C38: bl 0x02081B20
0x02080C40: bl 0x02081D68
0x02080C48: bl 0x02081DDC     <- collision resolution (stage 4)
0x02080C50: bl 0x020821C4     <- the accumulator (stage 5)
0x02080C58: bl 0x020826A0
0x02080C60: bl 0x02082780
0x02080C68: bl 0x02082984
```

Its caller is `0x0207F480` (call site `0x0207FA9C`), in the `BattleColPrm` neighbourhood alongside `0x0207C4C0`, `0x0207C988`, and `0x0207CE7C`. This is the **collision/physics pipeline**. The accumulator and the collision function are **adjacent stages sharing one argument**.

### The earlier null was an empty list, not a missing call

Runtime breakpoints at `0x02081ED0` / `0x02081EE0` never fired on a landed hit, and I retracted that card at P188. Now the control flow explains why. Those addresses sit inside a **`while`-loop body**:

```
0x02081EA0: ldr r4, [sl, #0x48]   ; list head
0x02081EA4: b   0x020821AC        ; jump to loop condition
0x02081EA8: ldr r5, [r4, #8]      ; LOOP BODY -- breakpoints are in here
   ...
0x020821A4: str r0, [r1, #0x40]   ; body also writes the +0x40 flag word
0x020821A8: ldr r4, [r4]          ; next
0x020821AC: cmp r4, #0
0x020821B0: bne 0x02081EA8        ; loop
0x020821B4: epilogue
```

Textbook list walk from `[sl+0x48]`. The body runs once per element, so a null means **the list was empty on those frames** — not that `0x02081DDC` never executed.

**The retraction still stands**: `0x02081ED0` and `0x02081EE0` genuinely didn't fire, which is what I retracted. What's new is that the **containing function isn't excluded**. It's stage 4 of a pipeline that almost certainly runs every frame, so it's probably entered constantly. Those are different claims, and the second was never measured.

**Rule 26: a breakpoint on an interior instruction can't distinguish "function not called" from "function called but branch/loop body not entered."** Site an entry breakpoint first, then narrow. Same family as rule 19 (a control sited downstream can't separate "never happened" from "happened and was undone"), but about *position within* a function rather than position in the frame.

### The card, revised

`0x02081DDC` and `0x020821C4` — **function entries**, not interior stores. Confidence `PLAUSIBLE`.

- **Program point:** first instruction of each. Both are **upstream** of `0x02156DE8` if this pipeline is where staging happens.
- **Reachability:** `INFERRED` for live-battle execution; `ESTABLISHED` that both are called unconditionally from `0x02080C28` with the same argument.
- **Test:** break at `0x02081DDC` and `0x020821C4` during a landed hit; keep `0x0215AC08` as the in-session control.
- **Expected:** both fire, and fire *before* `0x0215AC08`.
- **Failure signature:** neither fires — then the whole pipeline is off this path and both the accumulator lead and the collision reading die together, cleanly.
- **If both fire:** read `(r5 - 0xA4)` at `0x020821F8` and compare against `0x0220FDC4` / `0x0220FC3C`. That's still the question that decides whether the accumulator touches the scratch.

### Why the negative result would be worth as much

If neither entry fires, one reading kills two leads I've spent three wakes on — no emulator patch, no trace needed. If both fire, the interior null becomes interpretable for the first time: an empty pair list on the sampled frames, a statement about *when* damage is staged rather than *whether* this code stages it.
