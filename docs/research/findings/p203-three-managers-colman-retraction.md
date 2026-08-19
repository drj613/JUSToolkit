## P203 — Retracting P202's naming: `0x0220DDE0` is the `Battle_ColMan`, and there are three managers

Runtime's live scan found 19 objects at stride `0x188` from base `+0x454`, and flagged that 19 might be the constructed count rather than the declared length. Answering that statically resolved their caveat and overturned my P202 identification.

### RETRACTED: `0x0220DDE0` is not the `Battle_ObjMan`

P202 called it `Battle_ObjMan` (`0x42D8`, `BattleObj.cpp`). Wrong. I mixed up "constructed by a function called from `Battle_ObjManCreate`" with "is the `Battle_ObjMan`." The actual chain:

```
0x020833C8: bl 0x0207AD3C     ; allocates and returns an object -> r5
0x020833D8: mov r0, r5
0x020833DC: bl 0x0207C4C0     ; receives it in r0, keeps it in r6, allocates its OWN object into r4
0x020833E0: str r0, [r4, #0x8c]
```

`0x0207AD3C` allocates via the tagged allocator: size `0x219C`, strings `BattleCol.cpp` / `Battle_ColManCreate`, line `0xF9`. So `0x0220DDE0` is the **`Battle_ColMan`**, spanning `0x0220DDE0`–`0x0220FF7C`.

Three managers, not one:

| Object | Size | Source | Allocated by |
|---|---|---|---|
| `Battle_ObjMan` | `0x42D8` | `BattleObj.cpp` | `0x0208321C` |
| `Battle_ColMan` — **this is `0x0220DDE0`** | `0x219C` | `BattleCol.cpp` / `Battle_ColManCreate` line `0xF9` | `0x0207AD3C` |
| `Battle_ColPrmMan` | `0xFB54` | `BattleColPrm.cpp` / `Battle_ColPrmManCreate` line `0x132` | `0x0207C4C0`, stored at `+0x8C` of its caller's object |

### Also retracted: the `0x022100D4` containment

P202 called `0x022100D4` "ObjMan-internal." Against the true size it sits at `ColMan+0x22F4`, and `0x22F4 > 0x219C`, so it's **outside** the `ColMan`. Withdrawn. It survived P202 only because I checked containment against a size I'd assumed — a range test passes for any object large enough, so it couldn't have caught the wrong name.

The scratch containments do survive: player `+0x1E5C`, opponent `+0x1FE4`, term source `+0x2088`, all under `0x219C`.

### CONFIRMED, and convergent: base `+0x454`, stride `0x188`

```
0x0207C77C: add r0, r4, #0x54
0x0207C788: add r5, r0, #0x400      ; r5 = r4 + 0x454
0x0207C78C: mov r6, #0
0x0207C790: (body)
0x0207C7A4: orr r0, r0, #0x200      ; set bit 9 of +0x40
0x0207C7A8: str r0, [r5, #0x40]
0x0207C7AC: cmp r6, #0x80           ; 128 iterations
0x0207C7B0: add r5, r5, #0x188      ; stride
0x0207C7B4: blt 0x0207C790
```

Runtime's live scan implied base `+0x454` and stride `0x188`; my static read of the construction loop gives base `+0x454` and stride `0x188`. Two representations, no shared machinery. `CROSS_CONFIRMED`.

### Their caveat, answered from the allocation bound

The `0x80` loop belongs to the **`ColPrmMan`** — `0x454 + 128 × 0x188 = 0xC854`, which fits inside `0xFB54`. It can't be the `ColMan`.

For the `ColMan`, size settles it:

| Slots | Bytes needed | vs `0x219C` |
|---|---|---|
| 19 | `0x216C` | fits, with `0x30` to spare |
| 20 | `0x22F4` | **overflows** |

So **19 is the declared length** for the `ColMan`'s array, not just the constructed count — established by the allocation bound, a different representation from their signature count. Their caveat was right to raise and resolves in the direction they lacked evidence for.

`SPECULATIVE`: the `ColMan`'s 19-slot array and the `ColPrmMan`'s 128-slot array share base offset `+0x454` and stride `0x188`, suggesting the same element type in two managers with different capacities. Same-offset-same-stride is suggestive, not proof — rule 20 applies to strides too.

### What this changes about the empty list

`ObjMan+0x48` was the wrong name too: the list stage 4 walks is **`ColMan+0x48`**, and the collision stage receives the `ColMan`. Our two fighters sit in slots 17 and 18 of the `ColMan`'s 19-slot array, a different structure from the `+0x48` list — which is empty on a landed hit, making the whole stage a no-op.
