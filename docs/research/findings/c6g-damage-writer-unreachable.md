Now let me rewrite the findings doc the user pasted (the C6g iteration, not the file on disk — they're different documents).

Here's the rewritten markdown:

---

# C6g — +0x134 confirmed; its writer is beyond static analysis

Loop-Atlas iteration 29.

## +0x134 is the pending-damage field

The harness watched all four sibling fields across a session:

```
f=0    hp=7168   dmg=0     sp_drain=0  heal=0  sp_add=0
f=77   hp=7168   dmg=512   sp_drain=0  heal=0  sp_add=0   <-- frame BEFORE the drop
f=78   hp=6784   dmg=0
f=129  hp=7168   dmg=512
f=130  hp=6784   dmg=0
```

`+0x134` goes non-zero exactly one frame before each HP drop. The others stay zero. Field map confirmed:

| offset | meaning |
|---|---|
| `+0x134` | pending HP damage (positive magnitude) |
| `+0x138` | pending SP drain |
| `+0x140` | pending HP heal |
| `+0x144` | pending SP add |

## No offset-based technique can find the writer

Four searches, all negative — logged so nobody reruns them:

| technique | result |
|---|---|
| ARM word stores to `+0x134`/`+0x138`, all binaries | 18 sites, **2 in ov6** — both are the vtable initialiser at `0x02161C1C`/`0x02161C2C`, a different object |
| Folded base: `add rY,rZ,#N` then store landing at `+0x134` | **0** — the pitfall from physics-writers claim 5 doesn't apply here |
| Any data-processing instruction with immediate `0x134`/`0x138` | **0** in ov6, **0** in arm9 |
| `lsl rX,rY,#6` (displayed→raw signature) followed by a store of that register | **0** in ov6 |

What's left: **100 register-offset stores** in ov6 (`str rD,[rN,rM]`), where the offset lives in a register and can't be recovered from the instruction alone. That's the wall.

This is the fourth static technique to fail on this question. Unlike earlier rounds, I can now name exactly which forms were excluded rather than just saying "not found."

## Way forward

This gap is exactly what Tier-2 task **D0.3** (headless Ghidra import) solves: data-flow analysis resolves register-offset stores by tracking what the offset register held. Already specified in `Decomp-Tier2-Plan.md`.

The cheap alternative is empirical: since `+0x134` goes non-zero one frame before the drop, **bisecting that frame** — breaking at candidate points and checking whether the field is already set — names the writer in logarithmic runs.

## Correction: every damage figure was net of one heal frame

The pending value is **512** (8.000); the observed dip was **384** (6.000). Training auto-heal fires in the same frame as the hit, so every dip reading was `true − 128`. Corrected targets:

| move | true | previously recorded |
|---|---|---|
| B | **8.000** | 6.000 |
| DOWN+B | **7.000** | 5.000 |
| X | 4.000 *(inferred)* | 2.000 |

**The flat −2 survives**: a constant offset on both sides cancels in a difference, which is why the two-move design was robust to an error neither session spotted. Ratios were never constant, and still aren't.

**One earlier claim is weakened, and it was mine:** I wrote that the owner's independent "a punch does 6" validated the whole measurement chain. It matches the **net** figure — the owner was also watching training mode with heal on. It still validates the HP scale, address derivation, and dip-reading method; it does not independently confirm raw move damage. An external check is only as strong as the conditions it shares with yours.

## Method note

Both sessions independently made the same mistake this phase: citing `GDB-Validation-Queue.md`/`scripts/gdb/README.md` in planning without reading them, while chasing the exact thing those documents recorded. The rule: **read the loose-ends doc before the conclusions doc.** Conclusions say what's settled; loose ends say what someone already tried — and that's what actually saves time.
