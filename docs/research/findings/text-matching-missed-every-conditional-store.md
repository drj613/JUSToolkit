# Findings: text matching missed 40% of stores — condition codes, not addressing modes

Loop-Atlas iteration 81. Static.

Porting iteration 80's addressing-mode fixes into `find_field_writers.py` meant
replacing its text matching with the raw-word decoder.

The addressing-mode fixes changed nothing for `+0xE8`. **Condition codes did.** The old
regex missed `strne`, `strgt`, `strlo` — every conditionally executed store. That's
**19 of 47 sites, 40%, all invisible.**

Iteration 76's B11 conclusion survives the recount unchanged.

---

## 1. What the regex could not match

```python
MEM = re.compile(r'^(str|strb|strh|…) (\w+), \[(\w+), #(0x[0-9a-fA-F]+|\d+)\]$')
```

ARM bakes the condition into the mnemonic. `strne r1, [r6, #0xe8]` starts with `str`,
then `ne` — the alternation matches `str`, expects a space, gets `n`. No match, no
warning.

Predication is central to ARM. A mnemonic regex must enumerate 15 condition suffixes per
opcode or silently drop them. The raw-word decoder sidesteps this: the condition is in
bits 31–28 and the transfer encoding is the same underneath.

## 2. The recount

`+0xE8` stores, all 16 regions:

| | sites |
|---|---|
| old text regex | 28 |
| new raw-word decode | **47** |
| gained | **19** |
| lost | **0** |

All 19 gained sites are conditional (17 common suffixes, 2 `strlo`). **Zero** came from
post-indexed or writeback forms — those fixes matter for other offsets, not this one.

Lost 0 matters: the new decode is a strict superset, so nothing earlier wakes relied on
has disappeared.

Iteration 76 reported **27**; the old method actually yields 28. The one-site gap is a
base-register filter difference between that inline sweep and this script, not a decode
change.

## 3. B11 is unaffected

Restricted to arm9 and ov6, where the ColPrm record lives and its `+0xE8` is read:

```
DIRECT  str rD,[base,#0xe8]: 2 site(s)
  .  0x02046914 arm9  str r1, [r0, #0xe8]  fn=0x0204641c  companions=[]
  .  0x0207c684 arm9  str r0, [r4, #0xe8]  fn=0x0207c4c0  companions=[]
SPLIT: 0 site(s)
```

Same two sites as iteration 76, both already refuted (`0x02046914` has a pc-relative
global base; `0x0207C684` is `Battle_ColPrmManCreate`'s own `+0xE8`), no companions, no
split-offset stores. **None of the 19 newly visible conditional stores is in arm9 or
ov6.**

The vestigial-field hypothesis stands, now backed by a decoder that sees 40% more of the
ROM's stores.

The three ROM-wide `MATCH` sites — `0x0215D204` (ov5), `0x021536C4` (ov0), `0x0215B9CC`
(ov4) — are all in menu overlays, each with a single non-distinctive companion.
`0x0215D204` was already ruled out at iteration 76 as `KomaHelp_Create`'s.

## 4. What changed in the file

`scan()` now iterates decoded words via `struct_fields.access()` instead of
regex-matching lines. The split-offset pass decodes its `add` from the encoding and uses
`struct_fields.writes()` for the base-reassignment stop, inheriting the writeback fix
from iteration 80. Disassembly text is still read, but only for display and for counting
`stm` and register-offset stores where the exact rendering matters.

Every run now prints an addressing-mode census, so any divergence between the
disassembler's rendering and the encoding is visible instead of silent.

## Predictions status

| Claim | Verdict |
|---|---|
| The old text regex could not match conditionally executed stores | **CONFIRMED_STATIC** — 19 of 47 `+0xE8` sites, all conditional |
| The raw-word decode is a strict superset of the text regex | **CONFIRMED_STATIC** — gained 19, lost 0 |
| Porting the addressing-mode fixes was what mattered for `+0xE8` | **REFUTED** — 0 of the 19 gained sites are post-indexed or writeback |
| Iteration 76's B11 result survives a corrected decoder | **CONFIRMED_STATIC** — same 2 arm9/ov6 sites, same refutations, 0 companions, 0 split |
| Iteration 76's "27 sites" was exactly right | **REFUTED** — the old method actually yields 28; the correct count is 47 |
| The three ROM-wide `MATCH` sites write the ColPrm record | **REFUTED** — all in menu overlays, one companion each, `0x0215D204` already ruled out |

## Next angles, ranked

1. **Audit other text-matching scripts for the same flaw.** `prior_art.py`,
   `alloc_census.py` and `find_jump_tables.py` all match mnemonics; any that enumerate
   opcodes without condition suffixes have this bug. `alloc_census.py` is the biggest
   risk — a conditional `mov r0,#size` before an allocator call would go unresolved.
2. **Resolve `record+0x68`** (carried) — the object whose `+0x20` list holds this
   record's bucket nodes.
3. **Re-run the record map with anchors from the eight per-frame collision stages**
   (carried), now with both decoders corrected.
4. **Re-audit the map's `char+0xNN` offsets** across the three objects (carried).
