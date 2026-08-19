# Findings: `record+0x40` bit `0x200` is the free flag

Loop-Atlas iteration 121. Static.

A loop at `0x0207C788` links the 128 embedded records onto `manager+0x08` and sets
**bit `0x200` in `record+0x40`** on each one. This is the record's **in-use flag**,
explaining two previously unexplained bit manipulations — the installer's `bic` (iteration 77)
and the teardown's post-`memset` `orr`.

---

## 1. The linking loop

```
0x0207C788  add r5, r0, #0x400        ; r0 was r4+0x54, so r5 = r4+0x454
0x0207C78C  mov r6, #0
0x0207C790  mov r1, r5
0x0207C794  add r0, r4, #8            ; the record free pool
0x0207C798  bl  #0x2037b98            ; link
0x0207C79C  ldr r0, [r5, #0x40]
0x0207C7A4  orr r0, r0, #0x200
0x0207C7A8  str r0, [r5, #0x40]
0x0207C7AC  cmp r6, #0x80             ; 128 records
0x0207C7B0  add r5, r5, #0x188        ; the record stride
```

This answers iteration 120's open question: the clearing loop only zeroes; this one links.
The record count is now confirmed **a third time** — directly from a `cmp`.

## 2. The flag's full lifecycle

| stage | site | operation |
|---|---|---|
| construction | `0x0207C7A4` | `orr #0x200` — **free** |
| install | `0x0207CB2C` | `bic #0x200` — **in use** |
| teardown | `0x0207CE6C` | `orr #0x200` — **free** again |

Three sites, one bit. `record+0x40` bit `0x200` means *this record is on the free pool*.

## 3. Two loose ends closed

Iteration 77 logged the installer's `bic r0,r0,#0x200` and the teardown's `+0x40` touch as
unexplained. Both now resolve: the installer marks the record in use; the teardown re-marks
it free because `memset(record, 0, 0x188)` just before had cleared the flag with everything
else. A flag set *after* a wipe is one the wipe was not supposed to clear.

## Predictions status

| Claim | Verdict |
|---|---|
| A loop links the 128 records onto `manager+0x08` | **CONFIRMED_STATIC** — `add r0,r4,#8`; `bl #0x2037b98` at `0x0207C798` |
| It runs 128 times with stride `0x188` from `+0x454` | **CONFIRMED_STATIC** — `cmp r6,#0x80`; `add r5,r5,#0x188`; base `r4+0x454` |
| The clearing loop also links the records | **REFUTED** *(iteration 120's open question)* — a separate loop does |
| `record+0x40` bit `0x200` is set at construction | **CONFIRMED_STATIC** — `orr r0,r0,#0x200` at `0x0207C7A4` |
| It is cleared when a record is installed | **CONFIRMED_STATIC** — `bic r0,r0,#0x200` at `0x0207CB2C` |
| It is set again at teardown, after the `memset` | **CONFIRMED_STATIC** — `orr r0,r0,#0x200` at `0x0207CE6C` |
| The bit means "on the free pool" | **CONFIRMED_STATIC** — the three lifecycle points are consistent and exhaustive |
| The installer's `bic` was an unexplained manipulation | **REFUTED** *(iteration 77)* — it marks the record in use |
| Other `+0x40` bits have known meanings | **not claimed** — `0x800` gates delta application; the rest are unexamined |

## Next angles, ranked

1. **Map manager header `+0x360`–`+0x453`** — last unexamined span, `0xF4` bytes.
2. **Read `+0x0EC`, `+0x0F0`, `+0x0F4`** (carried).
3. **Enumerate other `record+0x40` bits** — `0x200` and `0x800` known; six accesses in the constructor path alone.
4. **Read `Battle_MoveManCreate` `0x02082A50`** (carried).
