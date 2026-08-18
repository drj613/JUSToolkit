# The 47-caller predicate is a network-session test

Iteration 153. Static only.

Iteration 152 left `[0x0214CCF4 + 4]` as the highest-leverage unknown: a single global
object pointer whose nullness gates **47** call sites, including the chara setup loop's
decision about where to pull character descriptor data from. This pass pins it down.

## The answer

**`[0x0214CCF4 + 4]` is the address `0x0214CCF8`, and exactly two overlays reference it:
`ov10` (202 references) and `ov7` (43 references). Nothing else in the ROM touches it —
zero references in `arm9`, zero in every other overlay.**

From `Overlay-Map.md`'s asset-name attribution, those two overlays are:

| overlay | identity | asset evidence |
|---|---|---|
| `ov07` | Local wireless multiplayer | `Commu`×94, `Common`×14, `deckselect`×11 |
| `ov10` | Nintendo WFC (online) | `dwc`×15, `result`×9, `info`×4 |

`dwc` is Nintendo's Wi-Fi Connection library; `Commu` is the communication module. A global
touched 245 times, exclusively from the local-wireless and online overlays, is a **networking
session object pointer**. That makes `0x0208C51C` the game's "is a network session active?"
test.

This explains the shape that prompted the question. `0x0208C51C` is 24 bytes with **47
callers** because "am I in a networked match?" gets asked everywhere. It lives in `arm9` and
tests a fixed RAM slot, so `arm9` can check without linking against either networking
overlay. Only the overlays write the object; `arm9` only reads the pointer.

Confidence: the reference counts and their exclusive concentration are
**CONFIRMED_STATIC** — measured by exhaustive word-aligned scan of `arm9` plus all 15
overlays. The *interpretation* as a networking session object is **PLAUSIBLE**, resting on
the overlay identities (themselves derived from asset-name counts in earlier work) rather
than on a naming string or allocation tag for the object itself.

## The accessor cluster around `0x0214CCF4`

`0x0214CCF4` is a small struct: two byte flags at `+0`/`+1`, and the session pointer at
`+4`. Eight leaf accessors sit in `0x0208C51C`–`0x0208C5E0`:

| address | behaviour |
|---|---|
| `0x0208C51C` | `return [g+4] != 0` — the session test, **47 callers** |
| `0x0208C538` | `memset(g, 0, 2)` then `g[1] = 1` — init |
| `0x0208C564` | if `g[0] != 0` then `g[0] = 0`, `return 1`; else `return 0` — **test-and-clear** |
| `0x0208C588` | `return g[0]` |
| `0x0208C598` | `g[0] = 1` |
| `0x0208C5AC` | `return g[1]` |
| `0x0208C5BC` | `g[1] = 1` |
| `0x0208C5D0` | `g[1] = 0` |

`g[0]` has a test-and-clear accessor but no plain clear — the signature of a **one-shot
pending-event flag**: set by a producer, consumed once by whoever tests it. `g[1]` has plain
get/set/clear and is initialised to `1`, reading as a persistent enable rather than an event.

**No accessor writes `+4`.** The init `memset` covers only 2 bytes, and `0x0208C51C` merely
reads the pointer. The actual writer lives in `ov7` or `ov10`, somewhere among those 245
references, and was not traced this pass.

## What this settles about the descriptor paths

Iteration 152 found the chara setup loop selects between three sources for descriptor words
`+0x08`/`+0x0C`, gated by `0x02086BD4` = `([0x020AFE90 + 0x28] != 0) OR 0x0208C51C()`.

Now that `0x0208C51C` is identified, the selection reads as **networked versus not**:

- **Path C** — predicate false, no session active: reads two static word tables at
  `0x020A1EFC` and `0x020A1EBC`, indexed by slot. Purely local data.
- **Path B** — predicate true: routes into `ov10` at `0x0219B9CC` / `0x0219BA00` (the
  online overlay — unambiguously `ov10`, since both addresses lie past `ov11`'s end at
  `0x02181A60`), then falls back to Thumb helpers `0x0208C10C` / `0x0208C114` when the
  session test fails on the second consultation.
- **Path A** — targets `0x02173004` / `0x02173014` remain **unattributable** between `ov10`
  and `ov11`, which share load address `0x02172A60`.

So the loop pulls character descriptor data from the network when a session exists and from
static tables when it does not. The three-way mapping onto specific modes — local wireless
versus online versus offline — is **not claimed**: Path A is unattributed, and the local
wireless overlay `ov7` does not appear in any of the six descriptor functions.

## A neighbouring cluster of networking globals

Scanning for literal words that point into `0x0214CC00`–`0x0214CD20` — the region
immediately below `ov6`'s load base `0x0214CD20` — turns up a cluster:

| address | references |
|---|---|
| `0x0214CCE0` | 38 |
| `0x0214CCF0` | 2 |
| `0x0214CCF4` | 9 |
| `0x0214CCF8` | 245 |
| `0x0214CCFC` | 6 |
| `0x0214CD00` | 5 |

`0x0214CCFC` and `0x0214CD00` are also referenced from `ov7` and `ov10`, so the whole band
looks like the networking subsystem's fixed globals — parked just under the overlay load
region where `arm9` and every overlay can reach them at a constant address.

## Two index gaps re-confirmed on a live case

**Literal loads.** `xrefs.json` records **4** loads of `0x0214CCF4`; the exhaustive raw scan
finds **9** pool words holding that value. Five loads missing on the one global this finding
is about — an independent confirmation of iteration 152's measured `9.4%` gap, and the
reason the raw scan was run alongside the database query rather than instead of it.

**Function binning.** `functions.json` records only four functions in
`0x0208C500`–`0x0208C640` (`0x0208C51C`, `0x0208C538`, `0x0208C5AC`, `0x0208C5E4`), but the
table above lists **eight** leaf accessors. The record for `0x0208C5AC` claims `52` bytes
and actually spans three functions: `0x0208C5AC`, `0x0208C5BC`, `0x0208C5D0`. A sixth
module affected by the known binning hazard.

## Not claimed

That the object at `0x0214CCF8` is any specific networking structure — no allocation tag or
string names it, and its writer in `ov7`/`ov10` was not traced. What `[0x020AFE90 + 0x28]`
means, the other term of the path predicate. What `g[0]`'s one-shot event signifies or who
sets it. And the mapping of the three descriptor paths onto named multiplayer modes.
