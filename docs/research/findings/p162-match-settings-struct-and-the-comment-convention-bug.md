# P162 — Match-settings struct at `0x020AFE90`, and the tool bug behind P161's error

**Iteration 162. Static only.** Two runtime addresses from the peer closed an open struct and pointed at unnamed rule flags.

## What the peer found

They RAM-diffed the battle rules toggles — flipped each menu switch five times and watched for a byte that followed: **items at `0x020AFEBB`, gimmick at `0x020AFEBC`**, `1` = ON, `0` = OFF.

These aren't standalone booleans. They're fields of the struct at **`0x020AFE90`**, which we've been carrying as an unidentified predicate term:

| address | offset | what it is |
|---|---|---|
| `0x020AFEB4` | `+0x24` | `deck_active_slot` (peer's existing address) |
| `0x020AFEB8` | `+0x28` | the unknown term of path predicate `0x02086BD4` |
| `0x020AFEBB` | `+0x2B` | items (peer, runtime) |
| `0x020AFEBC` | `+0x2C` | gimmick (peer, runtime) |

`CONFIRMED_STATIC`: a liveness-tracked offset scan gives `0x020AFE90` a real field map — **16 distinct offsets from arm9, 9 from ov6, and exactly one from ov5: `+0x24`.** ov5 is the deck editor, and it only touches the deck field. That independently confirms the peer's `deck_active_slot` from a direction they can't see. **This is the match-settings struct.**

## More rule flags than items and gimmicks

arm9 `0x0207541C`–`0x02075474` is a **bitfield unpacker**. It reads a packed bitmask byte at `[r7+0x7C]` and fans each bit into its own byte flag:

```
0x0207542C: 010010e3  tst  r0, #1
0x0207543C: 2b10c0e5  strb r1, [r0, #0x2b]    ; items
0x02075444: 020010e3  tst  r0, #2
0x02075454: 2c10c0e5  strb r1, [r0, #0x2c]    ; gimmick
0x0207545C: 040010e3  tst  r0, #4
0x0207546C: 2d10c3e5  strb r1, [r3, #0x2d]    ; third rule, unnamed
0x02075470: 2e00c3e5  strb r0, [r3, #0x2e]    ; forced to 0, unconditionally
```

`CONFIRMED_STATIC`: bit 0 → items, bit 1 → gimmick, **bit 2 → `+0x2D` (`0x020AFEBD`), a third rule flag of the same shape that nobody has named.** The bit order matches the peer's two findings in sequence — they got addresses from RAM diffing, this got the ordering from the unpacker, and they agree.

The scan also shows single-store byte fields at `+0x2E` (`0x020AFEBE`) and `+0x33` (`0x020AFEC3`). `+0x2E` is written **zero unconditionally** in the same run — `SPECULATIVE`: a rule present in the struct but not exposed in the menu.

**Operational consequence for the harness, passed on:** if a third rule defaults ON, a `rules_off()` that reports `[0, 0]` is only clearing two of at least three.

## The predicate term: its only ARM writer clears it

`findings/the-47-caller-predicate-is-a-network-session-test.md` records that `[0x020AFE90+0x28]`'s "writer in `ov7`/`ov10` was not traced". Sharpened:

```
0x02086D4C: 08009fe5  ldr  r0, [pc, #8]      ; -> 0x020AFE90
0x02086D50: 0010a0e3  mov  r1, #0
0x02086D54: 2810c0e5  strb r1, [r0, #0x28]
```

`CONFIRMED_STATIC`: `+0x28` has **6 accesses and exactly one store ROM-wide in ARM code, and that store writes zero.** Nothing in ARM ever sets it, yet predicate `0x02086BD4` — `([0x020AFE90+0x28] != 0) OR 0x0208C51C()` — treats non-zero as a real state that selects which of three function pairs builds characters.

`not claimed`: which explanation holds. Two candidates, and static analysis can't separate them — a **Thumb** store (P160 measured our index missing ~89% of Thumb literal loads, so very plausible), or a register-offset store whose offset isn't an immediate. Sent to the peer as a watch request: if any rules-menu switch moves `0x020AFEB8`, that names it, and a negative is equally useful because it rules the menu out.

## Root cause of P161's error: the two disassemblers disagree

P161 said the campaign misread a disassembly comment. The real cause is worse — **our two tools print opposite things in the same-looking comment.**

| tool | example | comment means |
|---|---|---|
| `query.py` ARM listing | `0x02086D4C: ldr r0,[pc,#8]  ; = 0x020AFE90` | the **value** (pool is at `0x02086D5C`, holding `0x020AFE90`) |
| `thumb_disasm.py` | `0x0214CD6A: ldr r1,[pc,#0x2dc]  ; = 0x0214D048` | the **pool address** (`Align(pc+4,4)+0x2DC`) |

Both verified by arithmetic: `0x02086D4C + 8 + 8 = 0x02086D5C`, and the listing's `.word` line there reads `0x020AFE90`; `Align(0x0214CD6A+4,4) + 0x2DC = 0x0214D048`.

A reader switching between ARM and Thumb listings sees `; = 0xADDR` and can't tell which meaning they're looking at. That's exactly how `0x0214D928` — a pool word — became "the battle root global" across four documents. **It will happen again until one tool changes.** Queued as a tool fix: make `thumb_disasm.py` print `; pool 0x0214D048 -> 0x02172960` so the comment is unambiguous and carries both.

## Credit and reciprocity

The peer flagged something worth recording alongside their addresses: **every damage measurement in their last two sessions ran with the stage gimmick live**, and on that stage the gimmick is a projectile spawner. They judge the ability-bitset result safe (its baseline held at 384 across six re-measurements, which a stray projectile would have disturbed), but any single-run damage number from those sessions has an unmodelled damage source in the room.

That matters here because "every damage effect found so far is flat" leans on their numbers. It doesn't overturn anything yet, and P157–P159's clearing of the status subsystem is static and unaffected — but it's recorded rather than absorbed silently.

Their gimmick finding also offers a candidate explanation for a P157 puzzle: **six of the 27 ObjShot kinds carry no entity.** If stage hazards occupy kinds in that table, some kinds will never be reachable from any character's move. `SPECULATIVE`, and their pending kind-byte walk would test it.

## Queued by this wake

1. **Find the Thumb writer of `[0x020AFE90+0x28]`.** The ARM-only search is exhausted and returns a single clearing store. Thumb is the untested half and P160 says our index is nearly blind there.
2. **Fix `thumb_disasm.py`'s literal comment** to print pool address *and* value. This is a correctness fix on the tool that caused a four-document error.
3. Name `+0x2D`, `+0x2E`, `+0x33` and the packed source byte `[r7+0x7C]` — the whole match-rules set is one small function away from full documentation.
