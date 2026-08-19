# P163 — Rule-select screen fully mapped; time limit stored as frames

**Iteration 163. Static analysis plus owner ground truth.** The owner sent a screenshot of the ルールセレクト (rule select) screen and corrected their earlier count of settings. That named the field I couldn't identify and gave the settings-copy function its purpose.

## Ground truth (OBSERVED — beats disassembly for *what*, silent on layout)

Six settings, two rows:

| row | setting | shown as | kind |
|---|---|---|---|
| 1 | ルール (rule / mode) | ポイント (Point) | multi-valued — death match / point battle / collect stars |
| 1 | じかん (time) | `60` | value |
| 1 | COM | 1人 (1 person) | count |
| 2 | アイテム (items) | OFF | boolean |
| 2 | ギミック (gimmick) | OFF | boolean |
| 2 | チームせん (team battle) | OFF | boolean |

Per-player rows show つよさ (strength, ふつう = normal) and チーム (team, なし = none) — per-player, not global.

**Exactly three booleans.** The bitmask at `[r7+0x7C]` carries exactly three bits. That closes the open field by elimination.

## `0x0207538C` is the settings-copy function

`CONFIRMED_STATIC`: arm9 `0x0207538C` (512 bytes) copies a source settings object in `r7` into the match-settings struct at `0x020AFE90`:

| source | width | destination | what it is |
|---|---|---|---|
| `[r7+0x70]` | word | `+0x18` | `not claimed` |
| `[r7+0x75]` | byte | `+0x0C` | `not claimed` |
| `[r7+0x76]` | byte | `+0x10` | **ルール / mode** — see below |
| `[r7+0x77]` | signed byte | — | read 3×; `SPECULATIVE`: per-player つよさ or チーム |
| `[r7+0x78]` | signed byte | `+0x14` | `not claimed` |
| `[r7+0x79]` | byte | `+0x33` | `PLAUSIBLE`: COM count |
| `[r7+0x7A]` | **halfword** | `+0x1C` | **じかん / time limit**, converted to frames |
| `[r7+0x7C]` bit 0 | bit | `+0x2B` | アイテム / items |
| `[r7+0x7C]` bit 1 | bit | `+0x2C` | ギミック / gimmick |
| `[r7+0x7C]` bit 2 | bit | `+0x2D` | **チームせん / team battle** |
| — | — | `+0x2E` | forced to `0` unconditionally; `not claimed` |

`CONFIRMED_STATIC` for `+0x2D` = team battle, by elimination: three booleans on screen, three bits in the mask, bits 0 and 1 already confirmed as items and gimmick at runtime by `justoolkit-ed` (`0x020AFEBB`, `0x020AFEBC`). P162 called this "a third rule flag nobody has named." Named.

## Time limit is a frame count — two independent constants prove it

The copy isn't a straight copy. `+0x1C` runs through a converter with two paths:

```
0x020753F0: 7610d7e5  ldrb  r1, [r7, #0x76]   ; the mode
0x020753F4: 1cbc03eb  bl    #0x216446c        ; mode -> some classification
0x020753F8: 010050e3  cmp   r0, #1
0x02075400: ba27d7e1  ldrh  r2, [r7, #0x7a]   ; the menu value
0x02075404: 3c00a003  moveq r0, #0x3c         ; 60
0x0207540C: 92000000  muleq r0, r2, r0        ; A: value * 60
0x02075410: 9000a013  movne r0, #0x90         ; 144
0x02075414: 01208212  addne r2, r2, #1
0x02075418: 92000010  mulne r0, r2, r0        ; B: (value+1) * 144
0x0207541C: 01004012  subne r0, r0, #1        ;    ... - 1
0x02075420: 1c0081e5  str   r0, [r1, #0x1c]
```

`CONFIRMED_STATIC`: **`+0x1C` is the time limit in frames.** Path A is `value * 60` — menu value in seconds, times 60 fps. The screenshot's じかん `60` yields `3600` frames = 60 seconds. Consistent.

The cross-check comes from unrelated code. ov6 `0x02150AE6` writes the same field:

```
0x02150ae2: 4905  ldr r1, [pc, #0x14]   ; pool 0x02150AF8 = 0x00004650
0x02150ae4: 4802  ldr r0, [pc, #0x8]    ; pool 0x02150AF0 = 0x020AFE90
0x02150ae6: 61c1  str r1, [r0, #0x1c]
```

`0x00004650` = **18000** = 300 s × 60 fps = **exactly 5:00**. A round wall-clock default from separate code, same field, same units. Frame count is the only interpretation where both `value * 60` and `18000` make sense.

`not claimed`: path B, `(value+1) * 144 - 1`. 144 isn't a frame-rate multiple of anything obvious, so at least one mode reads じかん as something other than seconds. The discriminator `0x0216446C` (**ov1** — P164)(mode)` returning 1 is unread.

`PLAUSIBLE`: `+0x10` is the mode. It receives `[r7+0x76]`, which gates the time conversion — exactly the kind of setting that changes how another setting is read.

## Correcting the record

P162 said the bitfield unpacker showed "more rule flags than items and gimmick" and implied more were hiding. Half right. There is exactly **one** more boolean, `+0x2D`, now named. The owner first said four rules; their screenshot corrected it to six. Both counts are on record because the correction matters — without it I'd have hunted for a fourth boolean that doesn't exist.

`+0x2E` forced to zero remains unexplained. All six settings are accounted for, so it's not a rule-select field. `SPECULATIVE`: a derived flag reset per match.

## Consequences for the harness (sent to `justoolkit-ed`)

1. Their `rules_off()` clears **two of three** booleans. チームせん at `0x020AFEBD` is untouched, so every run has had team battle in whatever state the mode default leaves it.
2. All their measurements are training-mode, which the owner says lacks mode and time limit. So **four of six rules have never been varied** across the campaign's runtime data.
3. All six can now be set from RAM instead of menu taps — `0x020AFEB0` (mode, if `+0x10` holds), `0x020AFEAC` (time-limit frames, `+0x1C`), `0x020AFEBB`/`BC`/`BD` (the three booleans), `0x020AFEC3` (COM count, if `+0x33` holds). Writing frames directly also sidesteps the two-branch converter.

## Queued by this wake

1. **Read `0x0216446C(mode)`** — returns 1 for modes that take じかん in seconds. Names the three modes and explains path B's `144`.
2. Confirm `+0x10` is the mode by finding a reader that switches on it three ways.
3. Identify `+0x2E`, and the `[r7+0x70]`/`+0x75`/`+0x78` fields with no owner-visible setting.
4. Still open from P162: the **Thumb** writer of `[0x020AFE90+0x28]`, the predicate term whose only ARM store clears it.
