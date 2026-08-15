# Findings: query 71 walks a contact matrix inside the BattleColPrm manager

Loop-Atlas iteration 52. Static. Used `scripts/decomp/struct_fields.py`.

Query 71 — the move-script predicate that loops over other entities — reads a **2D array at
`ColPrm+0x158`**: `0x30`-byte elements, rows of 4. It reads element fields `+0x00` and `+0x18`.

Three globals named; one independently confirms an existing map claim:

| global | contents | evidence |
|---|---|---|
| `*(0x0214BE10)` | the **BattleColPrm manager** | 7 of 9 references are in arm9 `BattleColPrm.cpp`, and `0x0207C844` **writes** it (`str r4,[r1,#0x0]`) |
| `*(0x02172960)` | the battle context | 127 references, dominated by ov11 `BattleAI.cpp`, `BattleAI_Deck.cpp`, `BattleAI_State.cpp` |
| `0x0214BE14` | the **BattleObj manager** | 22 references, **all** in arm9 `BattleObj.cpp` |

---

## 1. Resolving an arithmetic inconsistency

Query 71 computes an address with stride `0x30`, then reads `+0x158` off it:

```
0x02157EC4  ldr r0, [pc, #0xd4]      ; = 0x02172960   (battle context)
0x02157EC8  ldr r1, [pc, #0xd8]      ; = 0x0214BE10   (ColPrm)
0x02157ECC  ldr r0, [r0]
0x02157ED0  ldr lr, [r1]             ; lr = the ColPrm manager
0x02157ED4  ldr r6, [r0, #0x158]     ; loop bound, from the battle context
0x02157EDC  add r2, r5, #0x100
0x02157EE0  mov r0, #0xc0
0x02157EE4  mov r1, #0x30
0x02157EEC  ldrsb r4, [r2, #0xe0]    ; self index, character+0x1E0
0x02157EF0  cmp ip, r4
0x02157EF4  beq #0x2157f20           ; skip self
0x02157EF8  mla r3, r4, r0, lr       ; r3 = lr + self*0xC0
0x02157EFC  mla r4, ip, r1, r3       ; r4 = r3 + ip*0x30
0x02157F00  ldr r3, [r4, #0x158]
0x02157F10  ldr r3, [r4, #0x170]
```

`+0x158` is far past a `0x30`-byte element, so `lr` can't be an array base. Checking how `BattleColPrm.cpp`
uses the same global resolves it.

**Answer: `lr` is the manager object, not an array base.** `0x0207C844` stores into `[0x0214BE10]`, and
other sites read large offsets (`[mgr+0xD0]`, `[mgr+0x70]`, both walked as list heads via
`ldr r0,[rX,#0x8]`). The manager is a big struct with an **array embedded at `+0x158`**:

```
ColPrm manager
  +0x70   list head
  +0xD0   list head
  +0x158  contact array:  row stride 0xC0, element stride 0x30
            0xC0 / 0x30 = 4 elements per row
          element +0x00   read by query 71
          element +0x18   read by query 71   (0x170 - 0x158 = 0x18)
```

Both reads land inside one `0x30` element — the "bare array base" reading cannot produce that.

## 2. What query 71 actually asks

Indexed `[self][ip]`: `self` is the character's own index (`ldrsb` from `character+0x1E0`, signed), `ip`
runs to `[battleContext+0x158]`, skipping `ip == self`. Returns true if either element field is non-zero.

That's a **pair-wise matrix keyed by (self, other)** — the shape of a contact/overlap table — in the
manager whose source file is `BattleColPrm.cpp` ("battle collision parameters"). The predicate reads as
*"am I in contact with any other entity?"*.

**PLAUSIBLE**, not confirmed: the semantics come from the module name plus the access shape. The array's
contents are a runtime pointer, so nothing static can read them.

Four elements per row matches a 4-entity battle, but `[battleContext+0x158]` hasn't been verified as 4,
and the row stride is a fixed width regardless of active entity count.

## 3. `0x0214BE14` independently confirms map claim 1

`Battle-Engine-Map.md` projectile-entities claim 1 records `0x0214BE14` as the "manager singleton literal"
for the pooled-entity constructor. All **22** references are in arm9 `BattleObj.cpp` — the generic object
pool attributed by module range in iteration 42. Two unrelated methods, one conclusion.

The two managers sit adjacent: `0x0214BE10` (ColPrm) and `0x0214BE14` (BattleObj), in a globals block
that also holds the chr_b base pointer at `0x0214BD80`.

## 4. The tool earned its keep

`struct_fields.py` with anchor `0x02157F00:4` returned exactly `+0x158` and `+0x170` — no phantoms. One
command instead of a hand-walk, with the six-wake guards applied automatically.

## Predictions status

| Claim | Verdict |
|---|---|
| `*(0x0214BE10)` is the BattleColPrm manager | **CONFIRMED_STATIC** — written at `0x0207C844`; 7 of 9 refs in `BattleColPrm.cpp` |
| `0x0214BE14` is the BattleObj manager | **CONFIRMED_STATIC** — 22 of 22 refs in `BattleObj.cpp`; confirms map claim 1 |
| `*(0x02172960)` is a battle-wide context | **PLAUSIBLE** — 127 refs, dominated by ov11 `BattleAI*` |
| Query 71 indexes an array of `0x30`-byte elements based at `lr` | **REFUTED** — `+0x158` exceeds one element |
| The array is embedded at `ColPrm+0x158`, elements `0x30`, rows `0xC0` | **CORRECTED (iteration 56)** — geometry right, base wrong: it is `+0x154`. The writer at `0x02081340` computes `add r2,sl,#0x154` explicitly, so query 71's reads are element `+0x04` and `+0x1C`. See `findings/contact-array-writer-found.md`. |
| The array is a pair-wise contact matrix | **PLAUSIBLE** — `[self][other]` indexing plus the `BattleColPrm.cpp` module name |
| Rows hold 4 elements because battles have 4 entities | **not claimed** — `0xC0/0x30 = 4` is a fixed width; the active count is unverified |
| The array's contents can be read statically | **REFUTED** — the base is a runtime pointer |

## Next angles, ranked

1. **Map the ColPrm manager** with `struct_fields.py`, anchoring on arm9 `BattleColPrm.cpp` sites.
   Known: list heads at `+0x70` and `+0xD0`, contact array at `+0x158`. Fully anchorable now.
2. **Name the `0x30`-byte contact element's fields** — only `+0x00` and `+0x18` known, from one query.
3. **Confirm `character+0x1E0` is the entity index.** Read as a signed byte, used as an array row index.
   Check: does anything else write it with a small counter?
4. Still open: NoteTrack `+0x7C`/`+0x80`/`+0x84` objects, `prmData+0x0C/+0x10/+0x14`, the 68-entry table
   at `0x02171FEC`, the 24 positive `ProjectileId` values, and the harness watchpoint recipe.
