## P191 — the dismissed `+0xE8` hits are 21 real stores, not widget noise

At P181 I retired 30 candidates with "ov12 is the UI overlay … not chasing them." Properly examined, **21 of those 30 are genuine Thumb stores to `+0xE8`.**

The usual Rule 1 approach failed: `query.py func` returns *no containing function* for any of the 30. The control (`0x0215C360`) resolves fine, so the tool works — these addresses just aren't inside any function in `functions.json`. Read as ARM they decode to garbage (`stmdavs`, `rsclo`), which is what Thumb code looks like through an ARM decoder.

I decoded the raw bytes as Thumb by hand — a different representation than the scanner's listing, so agreement between them can't share a bias:

```
ov12 0x021B461C: adds r0, #0xe8 | ldr r1, [r0, #0x0]   <- LOAD
ov10 0x02178E00: adds r0, #0xe8 | str r1, [r0, #0x0]   <- STORE, then b001/bdf0 = add sp,#4 / pop {r4-r7,pc}
```

`0x30E8` is `adds r0,#0xE8`; `0x6001`/`0x6801` are the store/load forms. The ov10 stores are followed by a **function epilogue** — the shape of a small setter: `obj->field = val; return;`. These are code, and they are writers.

### Classification of all 30

| Region | STORE | LOAD | not an `add #0xE8` |
|---|---|---|---|
| ov10 | **10** | 1 | 1 |
| ov12 | **9** | 3 | 0 |
| ov01 | **2** | 0 | 1 |
| ov00 / ov05 / ov07 | 0 | 0 | 3 |

`CONFIRMED_STATIC`: 21 real Thumb stores to `+0xE8` across ov10, ov12, and ov01. The P181 dismissal was wrong about what they are.

### What actually excludes them — overlay residency, not overlay purpose

The real discriminator is **overlay residency during battle**, which I didn't check and can't settle statically.

- **ov01 is the interesting one.** ov0–ov9 all load at `0x0214CD20`, so ov1 and ov6 **can't both be resident**. If ov6 is resident during a fight, ov1's two stores can't execute. That exclusion rests on the aliasing map, not a guess about what the overlay does. (ov1 isn't idle code — the mode classifier lives there, P164.)
- **ov10 and ov12** load at `0x02172A60` and `0x021AC1C0`, distinct from ov6's range, so aliasing excludes nothing. Whether they're resident mid-battle is a one-line runtime check, and until it runs these 21 stores are `UNCHECKED, NOT CLEAR`.

### The card

Type: residency question, not an address. Confidence `PLAUSIBLE` that residency clears all 21.

- **Test:** mid-battle, read a word from `0x02172A60` (ov10's load address) and `0x021AC1C0` (ov12's), and compare against the first word of each overlay file.
- **Expected:** no match — the menu overlays aren't resident during a fight.
- **Failure signature:** a match means that overlay *is* resident, and its `+0xE8` stores are live B11-writer candidates that must be read individually.
- **Reachability:** `INFERRED`. I haven't established which overlays are resident in battle; I'm asking, not asserting.

### Rule 16, and why this failure is different

**A prior is not a check.** The other failures in this run were bad instruments or stale labels. This one was worse: ov12 had already fooled me at P171 with a text-widget field, and I used that burn as *reason to skip ov12*. Evidence that a region is unreliable got read as evidence that it's irrelevant. If a region has fooled me once, that's reason to look harder, not permission to skip — and the skip retired 21 real stores for ten iterations.

Worth recording too: P181 said "the 30 hits split mainly between 12 in ov12 and 12 in ov10." **Six more sat in ov00, ov01, ov05, and ov07**, hidden by the word "mainly" and equally unexamined. Two of those turned out to be stores.
