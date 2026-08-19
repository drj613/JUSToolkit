## P189 — the scope correction was wrong; the register-offset scanner always covered arm9

I told the runtime loop that arm9 hadn't been swept by the P181 register-offset scanner. That was wrong, and the record needed fixing before they planned around it.

`regoff_store_scan.py` builds its region list arm9-first:

```
def regions():
    out = [("arm9", os.path.join(ROOT, "jus_files/arm9/arm9.bin"), 0x02000000)]
    ...  # then every overlay from overlays.json
```

The scanner has covered arm9 and all overlays since P181. Re-run with an arm9 positive control:

| Offset | Result | arm9 hits |
|---|---|---|
| `+0x40` (control) | candidates across many regions | **4** — instrument demonstrably reaches arm9 |
| `+0xE8` | 30 candidates, concentrated in ov12 (12) and ov10 (12) | 0 |
| `+0x130` | **0 candidates anywhere** | 0 |
| `+0x134` | **0 candidates anywhere** | 0 |

`CONFIRMED_STATIC`: no split or register-offset store to `+0x130` or `+0x134` exists in arm9 or any overlay, on an instrument proven to reach arm9. The original P181 wording — "0 anywhere" — was accurate. The P188 narrowing to "ov6-only" was the error.

### What went wrong

I found an arm9 hit with a different tool (the `search-imm` immediate-offset sweep) and concluded my scanners had been ov6-scoped. One had been — the iteration-76 sweep. I applied that scope to the other without opening it. **I narrowed my own accurate claim against my memory of the tool rather than against the tool itself.**

This is rule 3 inverted. Rule 3 says don't demote a fact you derived because it conflicts with someone else's summary. Here the conflicting summary was mine, and being the author made it feel like knowledge rather than a claim to check. The correction was unprompted and in good faith — which is exactly why nobody was going to catch it. A volunteered retraction reads as conscientious, so it gets less scrutiny than the claim it replaces, not more.

**New rule 15: a correction is a claim. Check a narrowing against the artifact the same way you'd check the thing you're narrowing.** When you retract something, say which tool established the original and re-run it.

### Where this leaves B11

Stronger than P188 said.

| Route | Status |
|---|---|
| Immediate-offset stores to `+0xE8`/`+0x130`/`+0x134` | closed **globally**, control `0x0215AC08`; only bulk initialisers `0x0207C744`, `0x02161C2C` |
| Split / register-offset stores to `+0x130`/`+0x134` | closed **globally**, arm9 control = 4 hits on `+0x40` |
| Caller chain upstream of `0x02156DDC` | no chain — callback via generic arm9 `0x02028384`, 690 callers |
| The `0x0215C360` tree | flag and list maintenance at every depth, subtree exhausted |
| Bit-11 setter by immediate search | all 12 sites resolved, none stores to `+0x40` |

The queued `P189b` ("sweep arm9 with the scanner") is a **no-op — already done** and is retired.

The encoding argument gets firmer. Both `+0x134` and the bit-11 mask are invisible to immediate-form search, and now `+0x134` is confirmed invisible to register-offset search across every region. `SPECULATIVE` still, but better founded: whatever stages the damage does so through an encoding neither scanner models — most likely a pool-loaded mask or a computed address. That's exactly the case an instruction trace answers and static search cannot, which supports the runtime loop's bounded single-frame trace over further scanning.
