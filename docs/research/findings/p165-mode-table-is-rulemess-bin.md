# P165 — The mode table lives in `bin/rulemess.bin`: 22 rule modes and the `144` explained

**Iteration 165. Static only.** Picked up from P164's queue: read ov1 `0x021643A4`, the function that returns the `ctx` whose `[ctx+4]` bases the 16-byte-per-mode descriptor table the classifier reads via `mode_field(ctx, mode) = [[ctx+4] + mode*0x10 + 0xC]` (ov1 `0x0216446C`).

The table isn't in code. It's the header of a shipped data file.

## `0x021643A4` is `RuleData_Create`

`CONFIRMED_STATIC`. Full disassembly, ov1 (`query.py disasm 0x02164390 40 --overlay ov1`):

```
0x021643A4: push {r3, r4, r5, lr}
0x021643A8: ldr  r1, [pc, #0x70]     ; pool 0x02164420 -> 0x0216D350 = "RuleData.cpp"
0x021643AC: ldr  r2, [pc, #0x70]     ; pool 0x02164424 -> 0x0216D340 = "RuleData_Create"
0x021643B0: mov  r0, #8              ; allocation size
0x021643B4: mov  r3, #0x17           ; line 23
0x021643B8: bl   #0x201A21C          ; tracked new(size, file, func, line)
0x021643BC: mov  r1, #0
0x021643C0: mov  r2, #8
0x021643C4: mov  r5, r0
0x021643C8: bl   #0x20517FC          ; memset(obj, 0, 8)
0x021643CC: mov  r1, #0
0x021643D0: ldr  r0, [pc, #0x50]     ; pool 0x02164428 -> 0x0216D360 = "bin/rulemess.bin"
0x021643D4: mov  r2, r1
0x021643D8: bl   #0x2033410          ; resource lookup by path
0x021643DC: mov  r4, r0
0x021643E0: ldr  r1, [r4, #0x1c]
0x021643E4: cmp  r1, #0
0x021643E8: bne  #0x21643F8
0x021643EC: ldr  r1, [r0]            ; lazy load: vtable[+0x10]
0x021643F0: ldr  r1, [r1, #0x10]
0x021643F4: blx  r1
0x021643F8: ldr  r0, [r4, #0x1c]     ; the loaded file object
0x021643FC: mov  r1, #0
0x02164400: str  r0, [r5]            ; ctx+0x0 = file object
0x02164404: ldr  r0, [r0, #4]
0x02164408: ldr  r2, [r0]
0x0216440C: ldr  r2, [r2, #0x2c]     ; vtable[+0x2C]
0x02164410: blx  r2
0x02164414: str  r0, [r5, #4]        ; ctx+0x4 = data pointer
0x02164418: mov  r0, r5
0x0216441C: pop  {r3, r4, r5, pc}
```

Three pool words decode to Shift-JIS/ASCII strings: `0x0216D340` = `RuleData_Create`, `0x0216D350` = `RuleData.cpp`, `0x0216D360` = `bin/rulemess.bin`. The function's own name is baked into the binary.

`ctx` is an 8-byte heap object: `[ctx+0]` = loaded-file object, `[ctx+4]` = data pointer from vtable slot `+0x2C`. **The mode descriptor table is the head of `bin/rulemess.bin`.**

## The table: 22 records × 16 bytes

`jus_files/ripped_jus_files/bin/rulemess.bin`, 1682 bytes. Header word `0x00000160` divided by the 16-byte entry size gives **22 entries**, and `0x160` is where the text block starts. Each entry has three string pointers plus a 32-bit int — matching the `Rulemess + RulemessEntry` format in `docs/articles/specs/texts.md`, parsed by `src/JUS.Tool/Texts/Converters/Binary2Rulemess.cs`. `CONFIRMED_STATIC`.

The int at `+0xC` is the field the classifier reads. All 22 records:

| mode | `+0xC` | description (abridged) |
|---|---|---|
| 0 | 0 | KO for the most points; −1 for being KO'd, −2 for a wipe (**ポイントバトル**) |
| 1 | 2 | no respawn, survive to the end (**デスマッチ**) |
| 2 | 2 | collect every J-symbol; KO to steal them |
| 3 | 0 | the Jump Pirates explain the basics (tutorial) |
| 4 | 2 | collect every item; KO to steal them |
| 5 | 1 | pick up the target and evade for a set time |
| 6 | 1 | destroy every wall in the stage within the time limit |
| 7 | 1 | KO the target character within the time limit |
| 8 | 1 | surprise every opponent at least once |
| 9 | 1 | land char-change attacks (↓+B) to make everyone the same character |
| 10 | 1 | protect the target character from enemy attacks |
| 11 | 1 | evade every attack for the full time |
| 12 | 0 | break treasure chests, grab more targets than the opponent |
| 13 | 0 | point battle, but every opponent uses your deck |
| 14 | 0 | point battle starting from a point deficit |
| 15 | 1 | capture the target character within the time limit |
| 16 | 0 | no respawn, survive to the end (variant wording) |
| 17 | 2 | collect every item (duplicate of 4) |
| 18 | 0 | point battle (duplicate of 0) |
| 19 | 2 | death match (duplicate of 1) |
| 20 | 2 | J-symbols (duplicate of 2) |
| 21 | 1 | KO the target within the time limit (short form of 7) |

Reproducible with `python3` over the file: entry `i` starts at `i*16`; fields at `+0`, `+4`, `+8` are string pointers, `+0xC` is the int.

## Pointer correction: `.bin` text pointers are self-relative, not absolute

`CONFIRMED_STATIC` — and it ate most of the wake. `docs/articles/specs/texts.md` calls these "Absolute pointers." They aren't. **A pointer's target is `its own file position + its value`.**

Read as absolute, only the first pointer in any file lands on a string; every later one drifts by 4 bytes per preceding pointer. Two independent lines of evidence:

- **Empirical sweep.** Self-relative decoding across `rulemess.bin`, `stage.bin`, `ability_t.bin`, `komatxt.bin`, `title.bin`, and `clearlst.bin`: **1,347 of 1,347 pointers** land on a string start (right after a NUL). Absolute decoding: only 22 of 1,347 hit.
- **Source semantics.** `JusText.ReadIndirectString` in `src/JUS.Tool/Texts/JusText.cs:90` does `reader.Stream.PushToPosition(reader.Stream.Position + reader.ReadInt32())` — C# evaluates the left operand first, so the base is the pointer's position before the read advances it.

Codex got the raw header and text bytes with no addresses and no hypothesis before I had a conclusion. It reproduced the 4-bytes-per-pointer drift, rejected the absolute reading, and refused to invent a fix — which pushed me to the six-file control sweep instead of rationalizing the first record's lucky hit.

This corrects documentation this loop didn't write. The C# tool has always been right; the prose describing it is wrong. Anyone hand-parsing a JUS `.bin` text file from that description will get garbage after the first string.

## The `144` — three-way agreement with the runtime loop

P163 found the time-limit conversion branches on the classifier: `+0xC == 1` gives `じかん * 60`, anything else gives `(じかん + 1) * 144 - 1`. `144` had no explanation.

Now it does, and it falls out of the mode categories:

- Modes with `+0xC == 1` are the **mission** rules — every one says 時間内に ("within the time limit") or 一定時間 ("for a set time"). For those, じかん is seconds and `*60` is a frame count.
- Modes with `+0xC` of `0` or `2` are the **versus** rules — point battle, death match, symbol/item collection. They take path B.

The runtime loop (bead `jus-1g6`) independently confirmed `0x020AFEA0` as the rule mode — `0` = ポイントバトル, `1` = デスマッチ — by tapping the ルール pill and reading the screenshot at each value. It also measured `0x020AFEAC` = **4463** with じかん 30, at both mode 0 and mode 1.

The static table predicts exactly that: mode 0's `+0xC` is `0`, mode 1's is `2`, neither is `1`, so both take path B — and `(30 + 1) * 144 - 1 = 4463`. `CROSS_CONFIRMED`: a data-file field and a runtime frame count agreeing through representations that share no machinery.

Promotions:

- `0x020AFEA0` = rule mode, index into the rulemess table → **`CROSS_CONFIRMED`** (was `PLAUSIBLE`; runtime evidence from `jus-1g6`).
- `0x020AFEAC` = time limit in frames, path-B encoded for versus modes → **`CROSS_CONFIRMED`**.
- Mode `2` = J-symbol collection → `PLAUSIBLE`. The runtime loop saw a third mode on the pill but didn't record its name; the table says J-symbols. One screenshot settles it.

## What `144` is *not* explained as

**Runtime follow-up (bead `jus-uvs`, closed).** Two framebuffer reads with the emulator's own framecount: `4453` frames at TIME 28, `5673` at TIME 20 — 8 displayed units across 1220 frames, `152.5` frames/unit. The display is integer-quantised, so the honest bracket is 122–203 frames/unit. `144` sits near the centre; `じかん`-as-seconds (60 frames/unit) is outside by ~2.5× and is **refuted**. So a じかん-30 point battle runs ~74 s and one unit is ~2.4 s, and the formula is complete as stated. Their caveat, kept rather than rounded off: this pins frames-not-seconds but does **not** independently pin `144` — that still rests on the table's `+0xC` agreeing with `4463`.

**Not affected by `jus-vkj`.** The runtime harness's `advance(N)` does not advance `N` frames (requested 2300 gave 5310), so any duration summed from requested advances is unsound. Every number used here is either a single RAM read or a framecount the emulator reported at capture, so nothing in this finding depends on advance-and-count.

`not claimed`: why the constant is `144` or why the `- 1`. At 60 fps, `4463` frames is 74.4 seconds for じかん 30, so じかん isn't seconds in versus modes — one unit is 2.4 s if the counter ticks once per frame. Could also be that the counter decrements faster than once per frame, or it isn't a 60 Hz counter. **Static analysis can't tell.** Needs one wall-clock measurement — filed as a request to the runtime loop.

## Queued by this wake

1. **Wall-clock a じかん-30 point battle** (runtime). Separates the 2.4 s-per-unit reading from a faster-decrementing counter.
2. **Find the reader of the other three fields.** The classifier only reads `+0xC`; something renders the three description strings on the rule-select screen. That code also confirms entry stride from a second angle.
3. Still open from P164: the **five-way disassembly sweep** of every claimed address in the `0x0214CD20` window, and the **Thumb** writer of `[0x020AFE90+0x28]`.
4. Still open, highest value: the term `V` in `duration = base + (base/10) * (V*2)` — `root+0x4C`, pending a runtime dump.
