# The ov05 conflict was a labelling error; the resolver-aliasing hypothesis is true but not load-bearing

Iteration 156. Static analysis, plus one peer runtime measurement.

## The conflict is closed

`ov05_mode_UNIDENTIFIED` had been open for dozens of iterations. The nature resolver at `0x0214E480` only appears in `ov05`, but a residency run measured `ov01` at **99.8%** "on the deck-editor screen" while `ov05` showed **6.5%**. Both couldn't be the deck editor.

Iteration 150 proposed the problem was **measurement attribution, not code**: the old boot path navigated to the wrong screen, so the measurement itself was correct but the label was wrong. `justoolkit-ed` re-measured on pixel-verified screens:

| screen | ov05 | ov01 |
|---|---|---|
| Deck-make **editor** (KomaEdit) | **99.5%** | 4.8% |
| Deck-make **list** (DeckSelect) | 8.0% | **99.6%** |

The prediction, stated before the measurement: ov05 above 90% on the verified editor, ov01 dropping. That's exactly what came back. Static symbols in `modules.json` back this up — `ov1` = DeckSelect/StageSelect/RuleSelect, `ov5` = DeckMake/KomaList/KomaEdit/KomaState/KomaHelp/KomaIBook/Database/JPower.

`Overlay-Map.md` was right all along; the old `6.5%` reading was taken on the deck *list* screen. There was never a code-level fact that needed explaining.

## The overlay-aliasing hypothesis — CONFIRMED_STATIC

`justoolkit` flagged a consequence: `0x0214E480` sits inside the shared `0x0214CD20` overlay window, so during battle — when `ov06` is resident instead of `ov05` — that address holds `ov06` code. Disassembling the same address under both overlays confirms this:

```
ov05 0x0214E480:  ldrb r1, [r0, #6]        ov06 0x0214E480:  ldr  r2, [r0, #4]
     0x0214E484:  cmp  r1, #0                   0x0214E484:  ldr  r0, [pc, #0x378]
     0x0214E488:  bne  #0x214e4c4               0x0214E488:  str  r2, [r1]
     0x0214E48C:  ldrb r1, [r0, #0xb]           0x0214E48C:  mov  r1, #0
     0x0214E490:  asr  r1, r1, #4               0x0214E490:  blx  #0x20101f4
```

Raw bytes, `32` each:

```
ov05: 0610d0e5000051e30d00001a0b10d0e54112a0e10f1001e2030051e30600001a
ov06: 042090e578039fe5002081e50010a0e35707fbfa88008ae5d919dae164239fe5
```

Not equal. **`0x0214E480` is `ov05`-only code and is unreachable during a battle.**

## But it doesn't explain the damage result

The proposed consequence was that "the resolver everyone has been reasoning about belongs to the editor, and battle code may never consult it" — which would explain why nature doesn't affect battle damage (twice confirmed). The premise is true; but the explanation isn't needed, because **the campaign's battle-side conclusion never depended on `0x0214E480`.**

The battle path uses an `arm9` predicate at `0x02078CB8`, which is always resident and not overlay-aliased:

```
0x02078CB8: ldrb  r0, [r0, #0xb]
0x02078CBC: asr   r0, r0, #4
0x02078CC0: and   r0, r0, #0xf
0x02078CC4: cmp   r0, #3
0x02078CC8: movne r0, #1
0x02078CCC: moveq r0, #0
```

`findings/c0-nature-in-battle.md` already showed that the **only** use of this predicate in `ov06` is at `0x021540AA`, where it selects an *asset filename* — `_b.aar` with VRAM allowance `0x005F2000` when true, plain `.aar` with `0x005F1000` when false — with no damage arithmetic at the call site. The damage result was already explained by the resident predicate's single battle use.

The aliasing hazard is real and worth documenting. It's just not the reason nature doesn't scale damage.

## Audit: the campaign never made this error

Every reference to `0x0214E480` in `docs/` labels it `ov5` explicitly — "the deck-editor accessor", "a family of ov5 (menu) special-form dispatch getters". Grepping all mentions for an `ov6`-or-battle attribution returns **0**. Four files cite it: `Overlay-Map.md`, `GDB-Validation-Queue.md`, `Battle-Engine-Map.md`, `findings/nature-SOLVED.md`.

That's a near-miss, not a save. The labelling was correct by habit; no campaign rule required checking whether an address in the `0x0214CD20` window was overlay-aliased before reasoning about it in a battle context.

## Independent cold validation of the nibble logic

Three byte sequences — `arm9 0x02078CB8`, `arm9 0x02076F70`, `ov05 0x0214E480` — were handed to an independent decoder as raw hex with **no hypothesis, no symbol names, and no suggestion of what the code was for**, and asked what they compute. Its unprompted findings:

| finding | matches the campaign record? |
|---|---|
| Byte `+0xB` packs two 4-bit sub-fields, bits `7:4` and bits `3:0`, each holding `0`–`15` | yes |
| `0x02078CB8` and `0x0214E480` extract bits `7:4` with *identical* arithmetic and compare against `3` | yes |
| They differ only in consumption — one returns a Boolean, the other branches | yes |
| `0x0214E480` reaches that comparison only when the byte at `+6` is zero | yes, matches the recorded condition gating |
| `0x02076F70` extracts the **lower** nibble, bits `3:0`, performs no comparison, and stores it at `+0x12` of another structure | yes — `nature-SOLVED.md` records the low nibble mapping to runtime `+0x12` |
| Marked as speculation: two packed categorical fields, with upper value `3` a distinguished category | yes — the recorded "`3` is a no-override sentinel" |

**It found nothing new.** Every point matches `findings/nature-SOLVED.md`, including the `+0x12` destination of the low nibble and the sentinel role of `3`. That's the useful outcome: an independent decoder, given only bytes, reconstructed the two-nibble layout and the sentinel from scratch. The nature finding now has a cold-start corroboration that shares no reasoning with the original.

## One wording correction

`findings/nature-SOLVED.md` line 9 describes the accessor as being at `ov5 0x0214E480` with a "copy in `arm9.txt` at `0x02076F70` / `0x02078CB8`". The cold decode shows those two arm9 sites are **not** both copies: `0x02078CB8` reads the **high** nibble and compares it against `3`, while `0x02076F70` reads the **low** nibble and stores it without comparing. Only `0x02078CB8` is a copy of the resolver's logic. Calling them jointly a "copy" is imprecise and should read "the high-nibble predicate `0x02078CB8` and the low-nibble reader `0x02076F70`".

## Declined measurement

A koma-browser residency number was offered, noting that KomaList and KomaIBook are both `ov5`. Correct — it can't tell them apart, so it would spend a run for no information. Declined.

## Not claimed

What `ov06 0x0214E480` actually is; its bytes were read only to prove non-identity. Whether any *other* address the campaign cites inside the `0x0214CD20` window has been reasoned about in the wrong overlay's context — the audit here covered `0x0214E480` specifically, and the general sweep is queued. And what the low nibble of `+0xB` means remains unknown, unchanged.
