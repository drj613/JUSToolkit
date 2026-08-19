## P197 — offset-as-argument class, closed except for computed offsets

P196's shape-finding generalised to `+0x134`: if a **generic field setter** like `set_field(obj, offset, value)` writes the value, then `0x134` never shows up near the store. The store is `str rV,[rObj,rOff]` with the offset in a register the caller passed in. That fully explains the zero candidates — the nulls are real but say nothing about this shape. The searches were correct; the search *space* was wrong.

Reordered ahead of the 20 `mov #0x800` sites because it targets the carrier, not the flag.

### Encoding arithmetic, verified against real bytes

The runtime loop supplied ARM immediate encodings. I checked the load-bearing one against actual ROM bytes instead of recomputing it the same way: `0x02151124` disassembles from bytes `4d0fa0e3` — `mov r0, #0x134`, i.e. `0x4D` rotated, exactly as computed. The table and the ROM agree through different routes.

| Value | ARM immediate |
|---|---|
| `0x134` | `mov #0x4D ror 30` |
| `0xE8` | `mov #0xE8 ror 0` |
| `0x130` | `mov #0x13 ror 28` |
| `0x800` | `mov #0x02 ror 22` |
| `0x40` | `mov #0x40 ror 0` |

### All 35 `mov #0x134` sites are allocation sizes

Every one is `mov r0` — the *first* argument, not an offset. Three checked directly:

```
0x02151124 (ov0): mov r0,#0x134 / mov r3,#0x3e  / bl 0x0201A21C
0x0214D7A0 (ov1): mov r0,#0x134 / mov r3,#0x3e  / bl 0x0201A21C
0x021AF950 (ov12): mov r0,#0x134 / mov r3,#0xfd / bl 0x0201A21C
```

`0x0201A21C` is the tagged allocator (38 callers), signature `(size, file, func, line)`. `0x134` here is a **308-byte allocation size** and `r3` is a source line number. `CONFIRMED_STATIC`. Same constant, entirely different role — rule 20, fourth collision in this investigation.

None of the 35 is in ov6.

### The offset is never pool-loaded either

| Search | Result |
|---|---|
| Literal loads of value `0x134` | **0 anywhere** |
| Literal loads of value `0x130` | **0 anywhere** |
| Literal loads of value `0x800` | 6 in **ov8**, Thumb |

Control: a literal-load search for the known `0x0207D9A0` returns its hits, so the instrument reaches.

### The class closes; the remaining sliver is nameable

For a generic setter to receive offset `0x134`, the constant has to be materialised somehow:

- **ARM `mov`** — checked. All 35 are allocator sizes.
- **Pool load** — checked. Zero anywhere.
- **Thumb `movs`** — impossible. `0x134` exceeds Thumb's `imm8` range (0–255). (This is why the ov12 stores could use `adds r0,#0xE8` directly — `0xE8` fits, `0x134` does not.)

`CONFIRMED_STATIC`: no ARM-immediate or pool-loaded materialisation of `0x134` or `0x130` exists in arm9 or any overlay. **The one route left is a COMPUTED offset** — built by arithmetic rather than loaded as a constant, e.g. a base offset plus an index. That sliver stays named rather than calling the class closed.

### Note for the bit-11 search

`0x800` *is* pool-loaded at six ov8 Thumb sites. ov8 aliases ov6 — ov0 through ov9 all load at `0x0214CD20` — so ov8 and ov6 cannot both be resident, which excludes these if ov6 is the resident overlay in battle. That is a structural exclusion from the aliasing map, not a guess about what ov8 does (rule 16). The 20 unexamined `mov #0x800` argument sites remain open.
