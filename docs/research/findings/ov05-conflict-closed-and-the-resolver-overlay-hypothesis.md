# The ov05 conflict was a labelling error, and the resolver-overlay hypothesis is true but not load-bearing

Iteration 156. Static, plus one peer runtime measurement.

## The conflict is closed

`ov05_mode_UNIDENTIFIED` sat open for many iterations: the nature resolver `0x0214E480`'s
bytes appear in `ov05` only, yet a residency run measured `ov01` at **99.8%** "on the
deck-editor screen" with `ov05` at **6.5%**. Both could not be the deck editor.

Iteration 150 proposed this was a **measurement-attribution error** rather than a fact about
the ROM — the old boot navigation was walking into the wrong screen, so the run measured
correctly and *labelled* wrongly. Re-measured by `justoolkit-ed` on pixel-verified screens:

| screen | ov05 | ov01 |
|---|---|---|
| Deck-make **editor** (KomaEdit) | **99.5%** | 4.8% |
| Deck-make **list** (DeckSelect) | 8.0% | **99.6%** |

The prediction was ov05 above 90% on the verified editor with ov01 dropping. That is what
came back. `modules.json` corroborates from static symbols: `ov1` =
DeckSelect/StageSelect/RuleSelect; `ov5` =
DeckMake/KomaList/KomaEdit/KomaState/KomaHelp/KomaIBook/Database/JPower.

So `Overlay-Map.md` was right all along, the old 6.5% figure was taken on the deck *list*
screen, and no code fact needed explaining.

## The overlay-aliasing hypothesis — CONFIRMED_STATIC

`justoolkit` then flagged a consequence: `0x0214E480` lies inside the shared `0x0214CD20`
overlay window, so during battle — when `ov06` is resident, not `ov05` — that address is
`ov06` code. Verified directly by disassembling the same address under both overlays:

```
ov05 0x0214E480:  ldrb r1, [r0, #6]      ov06 0x0214E480:  ldr  r2, [r0, #4]
     0x0214E484:  cmp  r1, #0                 0x0214E484:  ldr  r0, [pc, #0x378]
     0x0214E488:  bne  #0x214e4c4             0x0214E488:  str  r2, [r1]
     0x0214E48C:  ldrb r1, [r0, #0xb]         0x0214E48C:  mov  r1, #0
     0x0214E490:  asr  r1, r1, #4             0x0214E490:  blx  #0x20101f4
```

Raw bytes at that offset, `32` bytes each:

```
ov05: 0610d0e5000051e30d00001a0b10d0e54112a0e10f1001e2030051e30600001a
ov06: 042090e578039fe5002081e50010a0e35707fbfa88008ae5d919dae164239fe5
```

Not equal. The hypothesis is correct: **`0x0214E480` is `ov05`-only code and is not
reachable during a battle.**

## But it is not load-bearing for the damage question

The framing was that "the resolver everyone's been reasoning about is the editor's, and
battle code may never consult it," which would explain the twice-confirmed result that
nature does not affect battle damage. It is true, and it does not add a new explanation,
because **the campaign's battle-side nature conclusion never rested on `0x0214E480`.**

`findings/nature-SOLVED.md` cites the accessor as "the deck-editor accessor at `ov5`
`0x0214E480`" and records **arm9 copies** of the same logic. Those copies are the battle
path, and they are in `arm9`, so they are always resident and not overlay-aliased at all:

```
0x02078CB8: ldrb r0, [r0, #0xb]
0x02078CBC: asr  r0, r0, #4
0x02078CC0: and  r0, r0, #0xf
0x02078CC4: cmp  r0, #3
0x02078CC8: movne r0, #1
0x02078CCC: moveq r0, #0
```

That is the same nibble test as the inner part of `ov05 0x0214E480`, in `arm9`. And
`findings/c0-nature-in-battle.md` already established that the **only** use of this
predicate in `ov06` is at `0x021540AA`, where it selects an *asset filename* — `_b.aar`
with VRAM allowance `0x005F2000` when true, plain `.aar` with `0x005F1000` when false — with
no damage arithmetic at the site.

So "nature does not scale battle damage" was already explained by reading the resident arm9
predicate's single battle use. The overlay-aliasing fact is a real hazard and a good catch,
but it does not change that conclusion or reveal that it was built on sand.

## Audit result: the campaign never made this error

Every citation of `0x0214E480` across `docs/` labels it `ov5` explicitly — "the deck-editor
accessor", "a family of ov5 (menu) special-form dispatch getters". Grepping every mention
for an `ov6`-or-battle attribution returns **0**. Four files cite it: `Overlay-Map.md`,
`GDB-Validation-Queue.md`, `Battle-Engine-Map.md`, `findings/nature-SOLVED.md`.

That is worth recording as a near-miss rather than a save. The correct labelling was
apparently luck of habit — nothing in the campaign's rules required checking whether a
`0x0214Cxxx`–`0x0217xxxx` address was overlay-aliased before reasoning about it in a battle
context. **That rule now exists** (see the charter), because the hazard is real and the
consequence would have been a wrong conclusion about the damage path.

## Declined measurement

`justoolkit` offered a koma-browser residency number and noted KomaList and KomaIBook are
both `ov5`. Correct, so it cannot discriminate between them and the measurement would cost a
run for no information. Declined.

## Not claimed

What `ov06 0x0214E480` actually is — its bytes were read only to prove non-identity. Whether
any *other* overlay-window address the campaign cites has been reasoned about in the wrong
overlay's context; the `0x0214E480` audit was specific to that address, and the general sweep
is queued.
