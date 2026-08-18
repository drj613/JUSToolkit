# Which "vestigial" claims the Thumb blind spot can actually touch

Iteration 149. Static only.

Iteration 148 widened the Thumb *caller* sweep, but a bigger question remained open.
`find_field_writers.py` warns "Thumb code -- this walks ARM-mode functions only," which
means every **no-writer** claim in the campaign was built on an ARM-only store scan. This
pass sorts the seven vestigial claims by whether that blind spot can reach them, and
resolves what it can through arithmetic instead of guesswork.

## The triage

Not all seven are exposed. Grouped by what each claim actually rests on:

| Claim | Kind of claim | Thumb-exposed? |
|---|---|---|
| View handler table is dead | reachability of `0x0215FC20` / `0x0215FB64` | **No — already cleared.** Both were among the nine re-verified in iteration 148 with the widened window; still no Thumb caller. |
| `owner+0xE8` has no writer (B11) | no store to `+0xE8` | **No — armoured by encoding.** See below. |
| `record+0x68` is never set | no store to `+0x68` | **Yes.** `0x68` is expressible. Swept below. |
| Deck add-entry never succeeds | no store to `deck+0x30` / `+0x18EC` | **Partly.** `+0x30` is expressible; `+0x18EC` is not. Swept below. |
| Installer's three-word buffer is dead | written-and-never-read inside one ARM function | **No.** Self-contained in `0x0207C988`'s 111 instructions. |
| Half of `MovMan`'s constructor is dead | overwritten by `memset(obj,0,0x2648)` | **No.** Dead by data flow, not by reachability. |
| Shared decoders / zeroed deck | explicitly *not yet a claim* | **N/A.** |

Three of the seven are not reachability-or-writer claims at all, one was already cleared,
and only two-and-a-bit are genuinely in scope. Worth saying plainly: the blind spot is
narrower than "every vestigial claim is in doubt."

## The encoding ceiling closes B11 by itself

ARMv4T immediate-offset stores scale a 5-bit immediate:

| form | encoding | scaling | max byte offset |
|---|---|---|---|
| `STR Rd,[Rn,#imm]` | `0110 0 iiiii nnn ddd` | `imm5 << 2` | `31 << 2` = **`0x7C`** |
| `STRB Rd,[Rn,#imm]` | `0111 0 iiiii nnn ddd` | `imm5` | `31` = **`0x1F`** |
| `STRH Rd,[Rn,#imm]` | `1000 0 iiiii nnn ddd` | `imm5 << 1` | `31 << 1` = **`0x3E`** |

This checks out empirically too: sweeping all 16 regions for these three patterns produces
**46390** matches, and the largest offset actually observed for each form is exactly
`0x7C`, `0x1F`, `0x3E` — the theoretical maxima, hit but never exceeded.

So:

- **`0xE8` (232) is not expressible.** `232 >> 2` = `58` > `31`. No direct Thumb
  immediate store can write `owner+0xE8`, in any encoding, anywhere in the ROM. The B11
  no-writer result is **strengthened** by the Thumb question, not threatened by it. The
  only remaining Thumb routes are a computed base (`add` then `str`) or a register-offset
  store — the same two residuals the ARM scan already declares.
- **`0x18EC` is not expressible** either, by the same argument, so half the deck claim is
  armoured the same way.
- **`0x68` (104) is expressible.** `104 >> 2` = `26` <= `31`. Genuine gap; swept below.
- **`0x30` (48) is expressible.** `48 >> 2` = `12`. Genuine gap; swept below.

## The sweeps

Raw halfword patterns across the full ROM, filtered to addresses inside a known
`functions.json` Thumb-mode function:

| offset | raw patterns | inside a known Thumb function |
|---|---|---|
| `0x68` | **101** | **2** — `ov12 0x021C3BB4`, `ov12 0x021C47BC` |
| `0x30` | **375** | **12** |

**`record+0x68`:** both surviving candidates sit in **`ov12`** (base `0x021AC1C0`), which
is not a battle overlay and not where ColPrm lives. Zero candidates survive in `arm9`
game code or `ov6`. The claim holds.

**`deck+0x30`:** of the 12, seven are in `arm9` and five in overlays. Six of the seven
`arm9` hits — `0x0200AD80`, `0x0200ADC2`, `0x020623E2`, `0x0206456C`, `0x020645AA`,
`0x02064628` — fall **below the library/game boundary `0x0206ADB8`**, making them library
code that cannot be the battle deck. That leaves exactly **one** `arm9` game-code
candidate: **`0x0206BB44`**, inside Thumb function **`0x0206BAC8`**. The overlay hits land
in `ov7`, `ov8`, and three in `ov12` — none in `ov6`.

The deck claim now has exactly one named residual instead of an open-ended blind spot.
`0x0206BB44` needs its base register traced before it means anything; `+0x30` is a
common offset, and an offset match alone proves nothing here.

## The filter's own blind spot

"Inside a `functions.json` Thumb function" is only as complete as the database, and this
campaign has now hit the same gap twice: `functions.json` starts `ov6`'s Thumb code at
`0x0214DF14`, while confirmed real Thumb callers sit **below** that (`0x0214D65E`,
`0x0214D818`, `0x0214D826`). Any Thumb store in that uncatalogued region is invisible to
this filter.

For `0x68` that matters concretely: `ov6` had two raw candidates, `0x02152318` and
`0x0217202C`. `0x0217202C` lies past the end of `ov6`'s code in the data region holding
the kind dispatch table and string pool. `0x02152318` lies in the under-catalogued Thumb
range. Both were handed to an independent decoder as raw bytes, with no hint of the
expected answer, rather than judged here — see the next section.

## The two ov6 candidates, decoded independently — both false positives

Rather than judge these myself, I handed both byte windows to an independent decoder as
raw little-endian hex, with no hint of the expected answer. That order caught a mistake
I had made: I transcribed Window A's halfword of interest as `0x6668` when the bytes
actually give **`0x66bc`**. The decoder flagged the inconsistency instead of decoding
around it, which is the whole value of asking first and concluding second.

With the correct halfword, both candidates fall:

**`0x02152318` is not a Thumb store.** It is the low halfword of a coherent ARM
instruction. The surrounding stream decodes cleanly as ARM:

```
0x02152300: 850088e0  add  r0, r8, r5, lsl #1
0x02152304: 022c80e2  add  r2, r0, #0x200
0x02152308: 051081e2  add  r1, r1, #5
0x0215230C: bc16c2e1  strh r1, [r2, #0x6c]
0x02152310: 681098e5  ldr  r1, [r8, #0x68]
0x02152314: 0b00a0e1  mov  r0, fp
0x02152318: bc66d2e1  ldrh r6, [r2, #0x6c]
0x0215231C: 4e0300eb  bl   #0x215305c
```

`0x02152318` is `ldrh r6, [r2, #0x6c]`. The bytes `bc 66` that looked like
`str rD,[rN,#0x68]` in Thumb are the immediate-and-register field of an ARM halfword
load. Worth noting what the real code does with `+0x68` here: `0x02152310` **reads** it
(`ldr r1, [r8, #0x68]`) and never writes it — consistent with the never-set claim rather
than against it.

**`0x0217202C` is data.** Window B decodes as a run of little-endian words
`0x021568C8`, `0x021569AC`, `0x02156A18`, `0x021565C0`, `0x021565F4`, … — all pointers
into `ov6`'s `0x0215xxxx` code range. It is a pointer table, which is what its position
past the end of `ov6`'s code already suggested.

So `ov6` contributes **zero** surviving Thumb-store candidates for `+0x68`, and the
`record+0x68` claim survives the Thumb question in every region.

## Not claimed

That the `0x68` and `0x30` claims are now closed. They are *narrowed*, and by different
amounts, so the two deserve separate wording:

- **`+0x68`:** the raw byte scan is exhaustive over every byte of all 16 regions, and each
  of `ov6`'s candidates was decoded individually, so the uncatalogued-Thumb-range caveat
  does **not** weaken this one. What remains is only the encoding forms no sweep here
  covers.
- **`+0x30`:** narrowed to one game-code candidate, `0x0206BB44`, but I did not decode all
  **375** raw hits individually the way I did `ov6`'s two. The database-completeness caveat
  therefore still bites here, because the reduction from 375 to 12 leaned on the
  known-Thumb-function filter.

Register-offset stores (`str rD,[rN,rM]`) and split `add`+`str` bases remain outside every
sweep in this document, for Thumb exactly as the ARM tool already declares for ARM. And
`0x0206BB44`'s base register is untraced, so it is a candidate and nothing more.
