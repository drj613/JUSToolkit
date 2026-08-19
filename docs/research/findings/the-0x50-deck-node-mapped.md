# Findings: the `0x50` deck node, and two walkers over it

Loop-Atlas iteration 107. Static.

The player slot's 16 nodes are mapped: **20 fields** plus the list pointer, `0x50`
bytes each.

Two functions walk the active list. One halves `+0x16` into `+0x18` under a flag; the
other bails out on a different flag bit. `+0x3C` is a flags word with four bits in play.

---

## 1. The node

| offset | kind | notes |
|---|---|---|
| `+0x000` | ldr | list next pointer (`ldr ip,[ip]`) |
| `+0x008` | str | *(added iteration 117 — omitted here by a truncated scan read; receives a table lookup indexed by `node+0x40`)* |
| `+0x00C` | strh, addr | initialised to `-1` by the slot allocator |
| `+0x00E` | strb | |
| `+0x00F` | ldrb, strb | bit `0x10` gates the halving |
| `+0x010` | addr | |
| `+0x012`, `+0x013` | strb | |
| `+0x016` | ldrsh | signed source value |
| `+0x018` | strh | destination — set to `0` or to `+0x016 / 2` |
| `+0x034` | str | |
| `+0x038` | ldr, str | |
| `+0x03C` | ldr, str ×6 | **flags word** |
| `+0x040` | ldrb, strb ×5 | non-zero = skip this node |
| `+0x041`–`+0x048` | strb | byte cluster, written at init |

`0x02076E38` is the node initialiser; writes most of the byte cluster.

## 2. Walker one — the flag-gated halving

`0x0207871C(slot, mode)`:

```
0x02078730  ldrb r2, [ip, #0x40]
0x02078738  bne  #0x207877c          ; non-zero -> skip
0x0207873C  ldrb r2, [ip, #0xf]
0x02078740  tst  r2, #0x10
0x02078744  cmpne r1, #0
0x02078748  ldreq r2, [ip, #0x3c]
0x0207874C  orreq r2, r2, #0x5000
0x02078754  strheq r3, [ip, #0x18]   ; = 0
0x0207875C  ldr  r2, [ip, #0x3c]
0x02078760  bic  r2, r2, #0x1000
0x02078764  orr  r2, r2, #0x4000
0x0207876C  ldrsh r2, [ip, #0x16]
0x02078770  add  r2, r2, r2, lsr #31
0x02078774  asr  r2, r2, #1
0x02078778  strh r2, [ip, #0x18]     ; = +0x16 / 2
```

If `+0x0F` bit `0x10` is clear **or** `mode == 0`: set flags `0x5000` and zero `+0x18`.
Otherwise clear `0x1000`, set `0x4000`, and store `+0x16` halved with round-toward-zero.

`Battle_Add` runs this on every slot twice — `mode = 0` then `mode = 1`.

## 3. Walker two — early exit on a flag

`0x020785B8(slot, r1)`:

```
0x020785BC  ldr  r5, [r0, #0x558]
0x020785C8  popeq {…}                ; empty list
0x020785CC  mov  r4, #0x64
0x020785D4  ldr  r0, [r5, #0x3c]
0x020785D8  tst  r0, #0x2000
0x020785DC  popne {…}                ; bit set -> abandon the whole walk
0x020785E0  bic  r0, r0, #0x1000
0x020785E8  ldrb r0, [r5, #0x40]
```

`+0x40` skips one node; `+0x3C` bit `0x2000` stops the whole traversal.

## 4. `+0x3C` bits observed

| bit | seen |
|---|---|
| `0x1000` | cleared by both walkers |
| `0x2000` | tested by walker two; set means stop |
| `0x4000` | set by walker one on the halving path |
| `0x5000` | set by walker one on the zeroing path (`0x4000 \| 0x1000`) |

## Predictions status

| Claim | Verdict |
|---|---|
| The node is `0x50` bytes with the list pointer at `+0x000` | **CONFIRMED_STATIC** — `ldr ip,[ip]` at `0x0207877C`; stride `0x50` from iteration 106 |
| `+0x040` non-zero skips a node | **CONFIRMED_STATIC** — `ldrb`; `cmp`; `bne` at `0x02078730`–`0x02078738` |
| `+0x018` receives `+0x016` halved, rounding toward zero | **CONFIRMED_STATIC** — `add r2,r2,r2,lsr #31`; `asr r2,r2,#1` |
| The halving is gated on `+0x00F` bit `0x10` and the mode argument | **CONFIRMED_STATIC** — `tst r2,#0x10`; `cmpne r1,#0` |
| `+0x03C` is a flags word | **CONFIRMED_STATIC** — four distinct bit operations across two walkers |
| `+0x03C` bit `0x2000` aborts the whole walk | **CONFIRMED_STATIC** — `tst`; `popne` at `0x020785D8`, before any node work |
| `0x02076E38` initialises the node | **CONFIRMED_STATIC** — writes `+0x0E`, `+0x0F`, `+0x12`, `+0x13`, `+0x34`, `+0x38`, `+0x3C`, `+0x40`–`+0x48` |
| The node is a koma record | **not claimed** — the shape fits a per-card record, but nothing here names it |
| `+0x016`/`+0x018` are a cost and its halved value | **not claimed** — the halving is confirmed; what the value means is not |
| The `0x64` in walker two is a limit or a percentage | **not claimed** — loaded before the loop, use untraced |

## Next angles, ranked

1. **Read `0x02076E38` whole** — the node initialiser and sole writer of most bytes.
   Its arguments should reveal what a node represents.
2. **Trace the `0x64` in `0x020785B8`** and the rest of that walker past `+0x40`.
3. **Trace `+0x5CC` and `+0x5CD`** at `0x02078290` (carried).
4. **Read the deck's other three list heads** `+0x18D4`, `+0x18D8`, `+0x18E0` (carried).
