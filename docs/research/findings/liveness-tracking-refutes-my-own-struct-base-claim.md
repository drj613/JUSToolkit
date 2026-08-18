# Liveness tracking refutes my own struct-base claim

Iteration 155. Static only.

Iteration 154 noted that its offset histogram didn't track register liveness, claimed
nothing beyond `+0x00`, and queued a better tool. That tool now exists:
`scripts/decomp/base_offset_scan.py`. Its output overturns one of my own claims.

## The result

```
ov10: 381 pc-relative load site(s)
    +0x00: 394 access(es), 0 store(s)

ov7: 117 pc-relative load site(s)
    +0x00: 153 access(es), 2 store(s)  stores at ['0x21661c0', '0x2166372']
```

**Only `+0x00` survives liveness tracking.** Every other offset in iteration 154's
histogram — `+0x04`, `+0x08`, `+0x0C`, `+0x14`, `+0x24`, `+0x3C`, `+0x48`, and the large
ones up to `+0xC40` — was **register reuse**, not a field access.

`0x0214CCF8` is therefore a **single-word pointer slot**, accessed `547` times across the
two networking overlays, with exactly `2` stores: the init at `0x021661C0` and the teardown
at `0x02166372`, both in `ov7`. Nothing else writes it within the tool's reach.

## Retraction

Iteration 154 stated: "`0x0214CCF8` is a struct base, not a bare pointer slot." **That is
wrong and is retracted.** Iteration 153's original description — a global pointer slot —
was correct, and my "refinement" made the record worse. The mistake was reading an
untracked offset histogram as though it were a field map, which is the exact flaw iteration
154 itself documented one section later. I hedged the *large* offsets but let the *small*
ones through unchallenged ("field `+0x00` is the session pointer; other offsets are accessed
through the same base"). There were no other offsets.

The correct reading is unchanged from iteration 153 and now far better supported: a
liveness pointer, written twice, read constantly, tested by `arm9`'s `0x0208C51C`.

## The tool

`base_offset_scan.py` finds every pc-relative load of a target address (ARM
`ldr Rd,[pc,#imm]` and Thumb `ldr Rd,[pc,#imm8]`), then walks forward up to `24`
instructions, recording every access that uses the loaded register as a base — and stopping
the moment the base could have changed.

It is **conservative by construction**: it halts on any write to the base register, any
branch, call or return, any `ldm`/`pop`, and on any encoding it can't prove safe. When the
base register is `r0`-`r3` or `r12`, calls also stop the walk, since AAPCS lets the callee
clobber those. The upshot, stated in the output: a missing offset is not evidence of
absence, but a reported offset is evidence of presence.

Declared blind spots, printed on every run: a base rematerialised from another register, a
base passed to a callee, a base spilled and reloaded, ARM predicated writes, and
register-offset addressing where there is no immediate to record.

## The bug a positive control caught

The first version of this tool reported **zero** hits for `0x0214CCF4` — a base whose arm9
accessor cluster I had hand-read the day before. A clean-looking negative, and entirely
false.

The cause: the arm9 image was selected with `sorted(glob(...))[0]`, and sorting puts
**`arm7.bin`** ahead of `arm9.bin`. The tool was scanning the ARM7 binary. My earlier
ad-hoc scans used an unsorted glob and got `arm9.bin` only by luck of directory order —
fragile, and it would have broken silently on any machine that enumerated differently.

Fixed by naming `arm9.bin` explicitly and raising if it's absent. The positive control is
now part of `--selftest`, which asserts the tool recovers `+0x00`, `+0x01` and `+0x04` for
`0x0214CCF4` from `9` sites:

```
selftest OK: both hand-read writers of +0x00 found in ov7 (2 stores), no offset >= 0xC40
survives, and the arm9 positive control recovers +0x00/+0x01/+0x04 from 9 sites
```

Those `9` sites also match the `9` pool words the raw scan found in iteration 153, against
the `4` that `xrefs.json` records — so the tool closes the index gap for this case.

**The general lesson.** A scan whose interesting answer is "nothing survived" needs a
positive control, or a broken scan looks exactly like a clean negative. Iteration 154's
suspicion about the naive histogram happened to be right, so a silently-empty tool would
have "confirmed" it — and I would have published a correct conclusion for a wrong reason.

## Not claimed

That `0x0214CCF8` has no other accessed offsets anywhere — only that none survives this
tool's reach, whose blind spots are listed above. The identity of the `7348`-byte object at
`0x021AA0D8` is unchanged from iteration 154, and the networking reading remains
**PLAUSIBLE** for the reason given there: static allocation means no symbol will name it.
