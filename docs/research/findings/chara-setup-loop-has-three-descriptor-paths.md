# The chara setup loop fills two descriptor words from three alternative sources

Iteration 151. Static only. Region `ov6`, Thumb.

Iteration 150 fixed a bug in `thumb_disasm.py` that decoded every `cmp Rd,#imm` as `mov Rd,#imm`. It flagged potential blast-radius in the iterations 95–96 `ov6` Thumb work. This pass re-read that work. **The published claims survive, with one exception — and the exception is a `CONFIRMED_STATIC` row.**

## First, the good news: cited addresses were unaffected

Every address cited across all seven Thumb findings docs was checked against the halfword actually present. Three fell in the `0x2800`–`0x2FFF` range whose meaning changed:

| doc | address | halfword | verdict |
|---|---|---|---|
| `thumb-disassembler-and-the-chara-setup-loop.md` | `0x0214D680` | `0x2968` | **literal pool** — word is `0x02172968` |
| `thumb-callers-and-the-0x1b4-struct-floor.md` | `0x0214D668` | `0x2960` | **literal pool** — word is `0x02172960` |
| `battle-add-and-the-thumb-allocation-gap.md` | `0x0214D048` | `0x2960` | **literal pool** — word is `0x02172960` |

All three are pointer words sitting inside literal pools, not instructions, and all three docs already treat them as data. `0x0214D662` loads from `0x0214D668` (`ldr r1,[pc,#0x8c]`) and `0x0214D664` branches over the pool to `0x0214D694`, with `46c0` padding at `0x0214D666` — the pool boundary is explicit in the code. A fourth flag, `ov6 0x02152304`, lives in ARM code and is a false positive of the halfword scan.

No published claim rests on a mis-decoded instruction *at a cited address*.

## But nine real instructions in the code range changed meaning

Scanning the setup routine's code range `0x0214D400`–`0x0214D662` for halfwords in `0x2800`–`0x2FFF` turns up **9**: `0x0214D428`, `0x0214D432`, `0x0214D4AA`, `0x0214D4E0`, `0x0214D580`, `0x0214D590`, `0x0214D600`, `0x0214D60A`, `0x0214D632`. None were cited, but three of them are the guards that choose how the call descriptor gets built.

## The correction: three paths, not one

All three paths converge on the `Battle_CharaCreate` call at `0x0214D658`, and each sets `r0 = r5` (the loop index) before its two calls. The difference is which pair of functions fills descriptor words `+0x08` (`sp+0x50`) and `+0x0C` (`sp+0x54`).

**Path A — both guards pass:**

```
0x0214D5FA: add  r1, sp, #0x28
0x0214D5FC: ldrb r1, [r1, r5]      ; per-slot enable byte
0x0214D5FE: str  r1, [sp, #0x0]
0x0214D600: cmp  r1, #0x0          ; was read as `mov r1, #0x0`
0x0214D602: beq  #0x0214D62E
0x0214D604: add  r1, r2, #0
0x0214D606: add  r1, #0x56
0x0214D608: ldrb r1, [r0, r1]      ; second gate byte
0x0214D60A: cmp  r1, #0x0          ; was read as `mov r1, #0x0`
0x0214D60C: beq  #0x0214D62E
```

Falls through to `blx #0x02173004` → `sp+0x50` and `blx #0x02173014` → `sp+0x54`. This is the path the original document described.

**Path B — either guard is zero, and a predicate holds:**

```
0x0214D62E: blx #0x02086BD4
0x0214D632: cmp r0, #0x0           ; was read as `mov r0, #0x0`
0x0214D634: beq #0x0214D648
0x0214D638: blx #0x020875B0        -> sp+0x50
0x0214D640: blx #0x020875D8        -> sp+0x54
0x0214D646: b   #0x0214D658
```

**Path C — that predicate returns zero:**

```
0x0214D648: blx #0x02028920        -> sp+0x50
0x0214D652: blx #0x020208EC        -> sp+0x54
```

Falls straight into `0x0214D658`.

So `+0x08`/`+0x0C` get filled by **`0x02173004`/`0x02173014`**, or **`0x020875B0`/`0x020875D8`**, or **`0x02028920`/`0x020208EC`** — three pairs, six functions. The original table named one pair as *the* source.

**Why this was invisible.** When read as `mov r1, #0x0`, the guards looked like register clears, and the `beq` after each appeared to test a flag set further back. That made the branch structure unreadable — the two alternative paths looked like unreachable tails rather than arms of a selection.

## New: `sp+0x28` is a per-slot enable byte array

`0x0214D54C`–`0x0214D554` initialises it: `[0] = 0`, `[1] = 1`. Path A indexes it by the loop counter (`ldrb r1,[r1,r5]`), so it is a per-slot flag, and the byte also gets stashed at `sp+0x0` before the test. With only `[0]` and `[1]` written here, slot `0` takes the non-Path-A route and slot `1` takes Path A; what fills indices `≥ 2` is **not claimed** — no other writer to this array was traced this pass.

## The loop bound is the battle root, which converges with iteration 147b

```
0x0214D78E: ldr r0, [pc, #0x198]   ; = 0x0214D928
0x0214D790: ldr r2, [r0, #0x0]
0x0214D792: mov r0, #0x56
0x0214D794: lsl r0, r0, #2         ; 0x56 << 2 = 0x158
0x0214D796: ldr r0, [r2, r0]
0x0214D798: cmp r5, r0
0x0214D79A: bge #0x0214D79E
```

The loop runs `r5` from `0` while `r5 < [root + 0x158]`, where `root = [0x0214D928]`.

**`0x0214D928` is the same battle-root global** that iteration 147b found holding the ObjShot manager at `root+0x110` and the ObjCtrl manager at `root+0x10C`. Two unrelated passes — one tracing projectile manager construction, one re-reading a character setup loop — landed on the same global from different directions. That also pins down the original document's unexplained "`ldr r3,[r2,#0x158]` — a count on `r2`": `r2` is the battle root, and `+0x158` is the character count.

## Not claimed

Which of the six descriptor-filling functions does what — none were read. What writes `sp+0x28` beyond indices `0` and `1`. Whether the second gate byte at `[r0 + r2 + 0x56]` is related to the first. And the `0x0214D428` / `0x0214D432` / `0x0214D4AA` / `0x0214D4E0` / `0x0214D580` / `0x0214D590` sites were confirmed as changed but not read in context — they are earlier in the routine, before the descriptor fill.
