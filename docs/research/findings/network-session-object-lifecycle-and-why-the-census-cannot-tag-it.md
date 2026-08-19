# The network session object: address, size, lifecycle — and why the census can never tag it

Iteration 154. Static only.

Iteration 153 flagged `0x0214CCF8` as a networking global and left one open task: trace its
writer in `ov7`, then look for an allocation-census tag that could promote the networking
identification from `PLAUSIBLE` to `CONFIRMED`. The writer has now been found, and the
lifecycle is fully traced. The census hypothesis is **dead — for a structural reason worth
recording.**

## The lifecycle — CONFIRMED_STATIC

Two Thumb sites in `ov7` write field `+0x00` of `0x0214CCF8`. They are init and teardown.

**Init, `0x021661BA`–`0x021661C4`:**

```
0x021661ba: ldr r0, [pc, #0x118]   ; = 0x021AA0D8
0x021661bc: ldr r1, [pc, #0x10c]   ; = 0x0214CCF8
0x021661be: ldr r2, [pc, #0x118]   ; = 0x00001CB4
0x021661c0: str r0, [r1, #0x0]     ; [0x0214CCF8] = 0x021AA0D8
0x021661c2: mov r1, #0x0
0x021661c4: blx #0x020517fc        ; memset(0x021AA0D8, 0, 0x1CB4)
```

**Teardown, `0x0216636E`–`0x02166374`:**

```
0x0216636e: ldr r0, [pc, #0xc]     ; = 0x0214CCF8
0x02166370: mov r1, #0x0
0x02166372: str r1, [r0, #0x0]     ; [0x0214CCF8] = 0
0x02166374: bl  #0x021671e4
```

The session object lives at **`0x021AA0D8`**, spans **`0x1CB4` = 7348 bytes**, and is zeroed
on creation. Its address gets published into `[0x0214CCF8 + 0x00]`, then that slot is nulled
on teardown. Over in `arm9`, `0x0208C51C` tests exactly that slot.

This is a liveness pointer with a matched set/clear pair inside the local-wireless overlay —
precisely the shape predicted by the "is a network session active?" reading. That prediction
was made in iteration 153, before this code was examined.

## Why the allocation census can never tag it

`0x021AA0D8` is **not a heap allocation.** It sits between `ov10`'s end (`0x021A7340`) and
`ov12`'s base (`0x021AC1C0`) — static RAM above the overlay images, untouched by the
allocator at `0x0201A228`. The census works by attributing allocator *call sites* through
their `__FILE__`/`__FUNCTION__` arguments, so an object that was never allocated has no call
site to attribute and no tag to find.

The queued hypothesis "the alloc census may tag the allocation" was therefore not just
unproductive but **unfalsifiable by construction**. Worth recording, because the same reflex
will come up again: before reaching for the census, first check whether the object is heap or
static. Only `0x1CB4` bytes of fixed RAM needed reserving, so the designers had no reason to
heap-allocate it.

Consequence for iteration 153's confidence label: the networking identification stays
**PLAUSIBLE**. It is now far better supported — address, size, memset-on-init,
null-on-teardown, all inside the local-wireless overlay — but no string or tag names the
object, and static allocation means none ever will. `PLAUSIBLE` is the ceiling this evidence
can reach under static-only rules; upgrading it would require a runtime read or a symbol
source.

## Refinement to iteration 153

That finding described `0x0214CCF8` as a global "referenced 245 times." Two corrections:

1. **`245` counted pool *words*, not accesses.** Scanning for actual load instructions —
   ARM `ldr Rd,[pc,#imm]` and Thumb `ldr Rd,[pc,#imm8]` — gives **117** loads in `ov7` and
   **381** in `ov10`, **498** total. Several loads can share one pool word, which is why the
   pool count is lower. Both numbers are valid measurements of different things; the earlier
   wording conflated them.
2. **`0x0214CCF8` is a struct base, not a bare pointer slot.** Field `+0x00` is the session
   pointer; other offsets are accessed through the same base.

Field `+0x00` is read overwhelmingly and written almost never — `148` accesses with `2`
stores in `ov7`, and `436` accesses with **`0`** stores in `ov10`. The online overlay only
ever *reads* the session pointer; both writers live in the local-wireless overlay. That
asymmetry is real and worth noting, though a caveat below limits how far it can be pushed.

## A limitation of the offset histogram, stated up front

The scan that produced the offset counts walks forward up to 8 instructions from each base
load and matches any load/store using that register. **It does not track register
liveness.** If the base register is reassigned within that window, a later access to an
unrelated struct gets misattributed.

This matters in practice. `0x0214CCF8` sits only `0x28` bytes below `ov6`'s load base
`0x0214CD20`, so any offset `≥ 0x28` from this base lands *inside `ov6`'s overlay region*.
The histogram reports offsets as large as `+0xC40` in `ov10`. Two explanations are possible —
the networking overlays reusing `ov6`'s RAM as scratch while battle is not resident, or
register reuse inside the scan window — and **this pass cannot distinguish them**, so
nothing is claimed about any offset beyond the first few words.

The `+0x00` result is robust regardless: it rests on `148` and `436` hits, on the two writer
sites read instruction-by-instruction above, and on `arm9`'s independent accessor cluster
testing that same slot. Small-offset reads (`+0x04`, `+0x08`, `+0x14`) are plausible but
carry the same caveat at lower volume.

## Not claimed

Any offset of the `0x0214CCF8` struct beyond `+0x00`, pending a liveness-tracking scan. The
identity of the `7348`-byte object at `0x021AA0D8` beyond its lifecycle. Whether the
networking overlays deliberately reuse `ov6`'s overlay RAM. What `0x021671E4`, called
immediately after teardown, does. And the `PLAUSIBLE` networking reading remains inferred
from overlay provenance plus lifecycle shape, not from a symbol.
