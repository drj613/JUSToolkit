# Findings: `Battle_Add` maps the battle module's root object

Loop-Atlas iteration 100. Static.

`Battle_Add` (1539 halfwords, 144 calls) is the battle module's construction sequence.
Fifteen callees carry assert-string names — the subsystem roster. Eleven of their results
land in the `0x170` root object at `[0x02172960]` at known offsets, giving a top-level
architectural map from one function.

---

## 1. The root object's subsystem slots

Every store follows the same idiom:

```
0x0214D41C  ldr r1, [pc, #0x248]   ; -> 0x0214D668, holding 0x02172960
0x0214D41E  ldr r1, [r1, #0x0]     ; r1 = the root object
0x0214D420  add r1, #0xf0
0x0214D422  str r0, [r1, #0x0]     ; root+0xF0 = the Marker
```

`0x0214D668` and `0x0214D928` both hold `0x02172960` — both literal pools reach the same global.

| offset | subsystem | constructor |
|---|---|---|
| `+0x0D0` | DemoKo | `Battle_DemoKoCreate` `0x021537E0` |
| `+0x0D4` | Pause | `Battle_PauseCreate` `0x0214E388` |
| `+0x0D8` | Pause (WiFi) | `Battle_PauseWiFiCreate` `0x0214F524` |
| `+0x0F0` | Marker | `Battle_MarkerCreate` `0x02167F20` |
| `+0x0F4` | ComicDeck (battle) | `Battle_ComicDeckCreate` `0x02152110` |
| `+0x104` | map conveyor | `BattleMapInitConveyor` `0x02161CB4` |
| `+0x108` | **object manager** | `Battle_ObjManCreate` `0x02083204` |
| `+0x10C` | object-control manager | `Battle_ObjCtrlManCreate` `0x02168B88` |
| `+0x110` | shot manager | `Battle_ObjShotManCreate` `0x0216A7BC` |
| `+0x114` | ComicDeck (shared) | `ComicDeckCreate` `0x02075FBC` |
| `+0x128` | AI | `BattleAI_Create` `0x02172A60` |

`+0x104`–`+0x114` is a contiguous block of five manager pointers. All eleven offsets fit
inside the `0x170` allocation.

Four named callees had no resolvable store: `Battle_CharaParamCreate`,
`Battle_CameraCreate`, `EffectFlags`, and `Battle_CharaCreate` (the in-loop call whose
result goes through the descriptor path; see iteration 97).

## 2. The collision managers are built elsewhere

`Battle_Add` does **not** call `Battle_ColPrmManCreate` `0x0207C4C0`,
`Battle_ColJointManCreate` `0x0207BD40`, or `Battle_ColManCreate` `0x0207AD3C`.

Their globals — `0x0214BE10`, `0x0214BE0C`, `0x0214BE14` — sit in a different block from
the root at `0x02172960`, so the collision layer is initialised elsewhere. `+0x108` holds
`Battle_ObjManCreate`'s result, and `0x0214BE14` is the BattleObj manager global recorded
earlier, suggesting that constructor writes its own global as well as returning; that is
**not claimed** here.

## 3. Scale

| | |
|---|---|
| extent | `0x0214CD20`–`0x0214D926`, 1539 halfwords |
| calls | 144, to 82 distinct targets |
| named callees | 15 of 82 |
| root slots recovered | 11 |

`0x0203B414` (17×) and `0x0203B424` (14×) are the most-called targets — both arm9 library
functions with no assert-string name.

## Predictions status

| Claim | Verdict |
|---|---|
| `Battle_Add` spans `0x0214CD20`–`0x0214D926` | **CONFIRMED_STATIC** — first `pop {…,pc}` after prologue |
| Both literal pools reach the same root global | **CONFIRMED_STATIC** — `[0x0214D668]` and `[0x0214D928]` both `0x02172960` |
| Eleven subsystem pointers at the offsets above | **CONFIRMED_STATIC** — `ldr`/`ldr`/`add #OFF`/`str` at each site |
| Subsystem results go into their own globals | **REFUTED** *(first reading)* — `add r1,#OFF` step missed; they go into the root |
| All recovered offsets fit the `0x170` allocation | **CONFIRMED_STATIC** — highest is `+0x128` |
| `Battle_Add` builds the collision managers | **REFUTED** — calls none of `0x0207C4C0`, `0x0207BD40`, `0x0207AD3C` |
| `Battle_ObjManCreate` also writes `0x0214BE14` | **not claimed** — result reaches `root+0x108`; global recorded from other work |
| The four unresolved callees store nowhere | **not claimed** — no store resolved in the window searched |

## Next angles, ranked

1. **Read `Battle_ObjManCreate` `0x02083204`** — lands at `root+0x108`; connects this map
   to the collision work via the pooled-entity constructor.
2. **Find what initialises the collision managers** — `Battle_Add` does not.
3. **Identify `0x0203B414` and `0x0203B424`** — 31 calls between them from this function.
4. **Read `char+0x7c`'s users** `0x02158B20`, `0x021586D0` (carried).
