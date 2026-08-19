## P188 — RETRACTION of `0x02081ED0`, and the seven sites resolved

### RETRACTED: `0x02081ED0` / `0x02081EE0` (was `PLAUSIBLE`, P187)

Runtime tested it. **Neither breakpoint fires during a landed hit.** Both were confirmed set ("Breakpoint 2 at 0x2081ed0", "Breakpoint 3 at 0x2081ee0"); counts: `ED0=0`, `EE0=0` against `CTRL=2` on `0x0215AC08`, with two hits of exactly `-6.000` (146 → 140 → 134). `0x02081DDC` does not execute on this path.

**It failed in a way I didn't predict, and that matters.** My card said the kill condition was `r2` never matching `0x0220FDC4`. That question never came up — there's no `r2` to compare because the code never runs. So `[[participant+0x1C]+0xC]` versus `entity+0x10` is **UNTESTED, not answered**. If a site turns up that does execute, that comparison is still open.

Nothing depended on this card. `scratch+0x40` bit 11 as the damage-pending flag is **unaffected** — the flush reads it live at `0x02158B9C`/`0x02158BA0` and that path is measured. Only the *setter* claim is retracted.

I trust the null because of runtime's own control: `0x0215AC08` is independently proven to fire on damage, so a live detector and two real hits exist in the *same session* as the null. Their first attempt was void for exactly the reason the control exists — the presses missed, giving `ED0=0` with no stimulus — and they reported it inconclusive and re-ran instead of sending a false refutation.

### The seven unchecked sites, now checked

I'd flagged 7 of 12 `orr #0x800` sites as *unchecked, not clear* (no `--overlay` passed). All seven resolved. **None sets bit 11 of `+0x40`.**

| Site | Region | What it actually is |
|---|---|---|
| `0x02161228` | ov6 | `orrne r2, r2, #0x800` → `strne r2, [r4, #0x50]` — stores to **`+0x50`**, not `+0x40` |
| `0x0216D1EC` | ov6 | composite mask: paired with `orr r3, r3, #0x1000`, no `+0x40` store |
| `0x0216D8D8` | ov6 | composite mask, same shape |
| `0x02170064` | ov6 | composite mask, same shape |
| `0x02170520` | ov6 | composite mask, same shape |
| `0x02170C60` | ov6 | composite mask, `0x800 | 0x1000 | 0x8400000` |
| `0x02175708` | ov10 | **data, not code** — decodes as `.word 0x56084310` followed by nonsense; false positive from scanning a data region as ARM |

Search control: `orr 0x40000000` returns the known setter at `0x02159200`, confirming the instrument reaches the listings.

### Why both are invisible, and what it suggests

`CONFIRMED_STATIC`: bit 11 of `scratch+0x40` is not set by any immediate-form `orr` in the covered listings. This is the **same structural blind spot** as `+0x134` (the amount), for a related reason — Thumb can't encode `0x800` as a single data-processing immediate, so a Thumb setter would load the mask from a literal pool, which `search-op-imm` can't see. Same way `+0x134` exceeds Thumb's word-store offset range and hides from `search-imm`.

`SPECULATIVE`: the amount and its pending flag being invisible *the same way* is a weak convergent signal that **one writer stages both** — which you'd expect, since the flush reads the flag and the amount together. It's not evidence of where that writer is.

For `B11`: the static route to the *flag* closes by the same mechanism as the route to the *amount*. This strengthens the tooling case rather than replacing it — the Z2 gap (the stub acks the packet and the write path never checks the address) is still the cheapest real fix.

### Instruments, not reasoning

Runtime's read is worth recording: my three fake nulls this wake all came from **tooling** — wrong subcommand syntax, `2>/dev/null` eating the usage error, an omitted `--overlay` — and theirs came from a literal `%%08X` detaching gdb. Same family. The reasoning has been holding; the instruments keep lying, and only controls catch them.
