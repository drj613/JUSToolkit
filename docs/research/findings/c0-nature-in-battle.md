# C0 Findings: Battle Nature = Artwork Selector, Plus 6 New Damage Callers

Loop-Atlas iteration 16. Static analysis of `jus_files/overlays/ov06.bin` as raw bytes (the committed `ov6.txt` listing mis-decodes the Thumb regions that matter here).

Three results. The lead I was chasing turned out **not** to be the damage multiplier — but following it uncovered six damage call sites nobody had found, and independently confirmed the nature triangle from instructions.

## 1. The battle nature check picks artwork, not damage

`0x021540AA` (ov06, Thumb) calls the nature predicate `0x02078CB8`. The branch on its result chooses between two asset filenames:

```
cmp  r0,#0            ; predicate: does this panel have an explicit nature?
add  r0,sp,#0x38      ; string build buffer
beq  .no_override
  ldr r1,[pc,#0x250]  -> "battle/chr/??_?_??_b.aar"     r7 = 0x005F2000
  b   .after
.no_override:
  ldr r1,[pc,#0x250]  -> "battle/chr/??_?_??.aar"       r7 = 0x005F1000
.after:
  ... ldrb r1,[r5,#0x41]   ; chr_b index
      lsl  r2,r1,#3        ; index * 8
      ldr  r1,[table + r2] ; 8-byte-stride table at 0x020924B0 -> the character's short code
```

A panel with an explicit nature override loads the **`_b` sprite archive** with `0x1000` more VRAM. That fits: alternate-nature variants use different art — Naruto's 笑 4-koma has different artwork from his 力 4-koma.

**This is the only use of the nature predicate in the battle overlay.** CONFIRMED by Thumb-aware caller scan. No damage arithmetic here at all. The lead was real, but it was asset selection.

## 2. The HP-apply function has 14 callers, not 8

Caller scan covering both **ARM `BL` and Thumb `BL`/`BLX`**, validated against the known pair (`0x021540AA` → `0x02078CB8`). Results for `0x020783CC` across arm9 + all 14 overlays:

| kind | sites |
|---|---|
| ARM `bl` (previously known) | `0x02157DC0`, `0x021582C4`, `0x02158BC0`, `0x02159274`, `0x021592D0`, `0x0215952C`, `0x02159668`, `0x0215A318` |
| **Thumb `blx` (new)** | **`0x02150DD8`, `0x021513D8`, `0x021513EE`, `0x021514E6`, `0x021515B2`, `0x02151636`** |

All 14 live in ov06; none elsewhere.

**Validated against hardware.** The GDB breakpoint captured `lr = 0x02150ddd`. My scan puts a Thumb `blx` at `0x02150DD8` — return address `0x02150DDC`, `| 1` for Thumb = **`0x02150DDD`**. Exact match. That's the training auto-heal caller observed 14,736 times.

**The five remaining Thumb sites are the best candidates for melee damage.** The earlier 14,736-hit observation only saw deltas from one caller and speculated melee might bypass this function. Simpler explanation: melee fires through one of these five previously-unknown Thumb sites, and none triggered because no melee hit landed during that window.

## 3. Nature triangle confirmed from instructions

At `0x02160944`–`0x021609B8` (ov06, ARM), a loop compares character natures. Nature is read from runtime struct `+0x13` (where the load path stores it) via pointer chain `[r2] → +0x118 → +0x56C`:

```
ldrb r0,[r0,#0x13]        ; subject's nature
...
cmp  r0,#0                ; Power?
bne  ...
  ldrb r3,[r3,#0x13]      ; other character's nature
  cmp  r3,#0x2            ; ... Laughter
  ldreq/addeq [r7,#0x60]  ; count it
cmp  r0,#1                ; Knowledge?
  ldrb r3,[r3,#0x13]
  cmp  r3,#0x0            ; ... Power
else                      ; Laughter
  ldrb r3,[r3,#0x13]
  cmp  r3,#0x1            ; ... Knowledge
```

The tested pairs are **(mine 0, theirs 2), (mine 1, theirs 0), (mine 2, theirs 1)**.

Against the established triangle — Power beats Knowledge beats Laughter beats Power — every pair is "**theirs beats mine**." So this counts how many characters hold the advantageous nature over the subject, accumulating into `[r7, #0x60]`.

Two things this pins down, **CONFIRMED from instructions, not descriptions**:

- The **enum mapping** `0 = 力 Power, 1 = 知 Knowledge, 2 = 笑 Laughter` is correct — a wrong mapping would make these comparisons incoherent.
- The **triangle direction** matches the documentation.

It's a **counter, not a multiplier**. Best guesses for the consumer: the SP-gain passive "increase SP when attacking or blocking characters of an opposing nature" (owner category 36), a deck-level nature bonus, or an AI evaluation heuristic. Whoever reads `[r7, #0x60]` settles it.

## Where the multiplier isn't

Ruled out: the battle nature predicate (`0x021540AA`, asset selection) and the triangle-counting loop (`0x02160944`, counter). Nature is read at 10 sites in ov06 via struct `+0x13`; two clusters are now explained. The rest are unexamined:

`0x021548F4`, `0x0215DD7C`, `0x0215F594`, `0x02160260`, `0x02163DFC`, `0x021672D8`

## Method note

The `ov6.txt` disassembly mis-decodes Thumb regions, and all of this iteration's evidence sits in Thumb code. Reading raw overlay bytes was necessary. Combined with the ARM-only caller scan that earlier produced a false "zero callers," **two separate wrong conclusions this session came from tools that silently only handled ARM.** Any claim about this ROM's control flow should state whether Thumb was covered.
