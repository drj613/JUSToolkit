## P205 — a truncation control caught itself, and no `+0x48` list insert exists at an immediate offset

### The control failed first

I searched for stores to `+0x48` and found nothing in `0x02081xxx`. Before reporting that, I ran the control: does the search find the two reads I already know — `0x02081DEC` and `0x02081EA0` (`ldr [sl,#0x48]`)?

**It did not.** The tool caps output at 200 lines by default. The real total is **644**. My "no stores" result was a truncation artifact — a cap producing a finding. With `--all`, the control passes (both known reads appear) and everything below is trustworthy.

### The three word stores to `+0x48` in the collision range

| Address | Containing function | What it is |
|---|---|---|
| `0x0207F87C` | `0x0207F480` — the pipeline's caller | `mov r1,#0` / `str r1,[r4,#0x4c]` / `str r1,[r4,#0x48]` — **clears a pair to zero** |
| `0x020812F4` | `0x02080F14` — pipeline **stage 1** | `ldr r2,[r1,#0x48]` / `add r0, r2, r0, lsl #8` / `str r0,[r1,#0x48]` — an **accumulator** on a numeric field |
| `0x02076164` | `0x02075FBC` (0 callers, another callback) | `ldr r1,[pc]` / `ldr r1,[r1]` / `str r0,[r1,#0x48]` — a **global-derived** object |

`0x020812F4` is `+= r0 << 8` on `r1`, not a list head — a different struct at a coinciding offset. That's rule 20's fifth collision this investigation. `0x02076164` writes through a global, a third object. Neither touches the list.

### What I am not claiming

`0x0207F87C` clears `+0x48` and `+0x4C` together, which looks like resetting a head/tail pair — and it sits in the pipeline's own caller. Tidy explanation for the list being empty every frame. **But `r4`'s identity is not established.** `r4` gets reassigned at least three times before that store — `0x0207F490` (`mov r4,r5`, zero), `0x0207F4E0` (`mov r4,fp`), `0x0207F568` (`ldr r4,[r6]`) — so naming the object requires tracing control flow to that store. I won't assert an identity I haven't pinned.

Also: `0x0207F480`'s prologue is `ldr r0,[r0,#4]` then `ldr r6,[r0,#0x10]`. It doesn't use its argument directly — it works on `[[arg+4]+0x10]`, the same double-deref shape `0x02156DDC` uses. The pipeline caller's working object is not its argument, one more reason `r4` cannot be assumed.

### Result

`CONFIRMED_STATIC`, scope stated: **no list insert into `+0x48` exists as an immediate-offset word store anywhere in arm9 or the overlays** (644 hits examined, control passing). Since `+0x48` and `+0x4C` are cleared together and elements chain through their own first word (`0x02081DF8`: `ldr r6,[r5]`), a head/tail pair is the natural reading, and insertion would write the tail's link plus `+0x4C`. That insertion isn't visible at an immediate offset — same blind-spot class as the `+0xA4` term writer, same answer: it's reached through a computed or register offset.

`UNCHECKED, NOT CLEAR`: `+0x4C` stores (not swept) and register/computed-offset shapes.
