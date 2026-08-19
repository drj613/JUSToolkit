# Findings: auditing every "0 callers" claim against Thumb

Loop-Atlas iteration 96. Static.

Iteration 95 found a function reached only from Thumb, putting every "0 callers" conclusion
in doubt. Of the **nine** such functions, only `Battle_CharaCreate` had a hidden caller.
**Eight stand** — iteration 94's dead-table result survives.

ROM-wide, **187** of 3691 caller-less ARM functions have a Thumb caller; **16** in battle
code. The blind spot is real and now measured.

> **CORRECTED, iteration 147.** 187 and 16 are both floors — the tool silently dropped
> real callers. Corrected to **340** ROM-wide (ceiling **377**), **31** in ov6.
> The eight "0 callers" claims still stand. Do not quote 187 or 16.
> See [§6](#6-correction-iteration-147-the-187-was-a-floor).

---

## 1. The tool

`scripts/decomp/find_thumb_callers.py`, selftest anchored on iteration 95's hand-verified
`0x0214D65E -> 0x02156A38`.

A naive halfword scan manufactures calls from matching bit patterns, so two filters reject
impossible edges:

**A Thumb `bl` cannot target ARM.** `bl` stays in Thumb; only `blx` switches state. A
`bl` landing on an ARM function is coincidence.

**Overlapping overlays produce phantoms.** Ten overlays share load address `0x0214CD20`.
An "ov8 caller" of an ov6 function is never a real call — the two are never co-resident.

Of 686 decoded edges, **499 rejected** by these two filters.

## 2. The nine claims

| function | campaign claim | Thumb caller? |
|---|---|---|
| `0x02156A38` `Battle_CharaCreate` | 0 callers | **yes** — ov6 `0x0214D65E` `blx` |
| `0x0215FC20` view arm | unreachable (iteration 92) | no |
| `0x0215FB64` arm trampoline | 0 references | no |
| `0x0207D440` ColObj acquire | callback (iteration 71) | no |
| `0x0207D858` ColObj release | callback | no |
| `0x0207D94C` ColObj third method | callback | no |
| `0x021570EC` entity callback | callback (iteration 74) | no |
| `0x02159EF8` state dispatcher | 0 callers | no |
| `0x0215FF74` view handler | 0 callers | no |

One miss out of nine. The function-pointer readings hold, and the arm function that
iteration 94's dead-table depends on remains unreachable.

## 3. ROM-wide

| | count |
|---|---|
| ARM functions with no ARM caller | 3691 |
| …with an accepted Thumb caller | **187** — CORRECTED to **340**, see §6 |
| …of those, in battle code | **16** — CORRECTED to **31** ov6, see §6 |

The 16: `0x02084A64`, `0x0214D95C`, `0x0214F524`, `0x0214F660`, `0x02151BE8`,
`0x02151DD8`, `0x02153074`, `0x0215308C`, `0x02153108`, `0x02153CAC`, `0x02156A38`,
`0x02160A48`, `0x021614B0`, `0x021615AC`, `0x021620C0`, `0x02168590`.

Most callers sit in ov6 `0x0214Cxxx`–`0x0215xxxx`, the uncatalogued Thumb region from
iteration 95. Only `0x02156A38` is a function this campaign has studied.

## 4. The filter that rejected its own anchor

The first version resolved targets by **address range**. Overlays overlap, so `0x02156A38`
resolved to `ov0` and the phantom filter rejected its own verified anchor.

Fixed by using **declared provenance** from `functions.json`. Range-based resolution is
ambiguous by construction — the very hazard the filter targets is what broke it.

## Predictions status

| Claim | Verdict |
|---|---|
| A Thumb `bl` can target an ARM function | **REFUTED** — `bl` does not switch state; decode noise |
| Cross-overlay Thumb edges among ov0–ov9 are real calls | **REFUTED** — overlays share `0x0214CD20`, never co-resident |
| Most decoded Thumb edges into caller-less functions are real | **REFUTED** — 499 of 686 rejected |
| Of the nine "0 callers" functions, only `Battle_CharaCreate` has a Thumb caller | **CONFIRMED_STATIC** — targeted scan, all 16 regions |
| The view arm `0x0215FC20` has a Thumb caller | **REFUTED** — none; dead-table holds |
| The ColObj and entity callbacks were mis-analysed | **REFUTED** — no Thumb callers; function-pointer readings stand |
| 187 of 3691 caller-less ARM functions have a Thumb caller | **REFUTED by iteration 147** — a floor, not the count; the tool's `±2` adjacent-call window dropped real callers. Corrected to **340** confirmed / **377** ceiling. See §6 |
| Range-based region resolution is safe in this ROM | **REFUTED** — rejected a hand-verified anchor; use declared provenance |
| The 16 battle targets are all genuine | **not claimed** — filters remove impossible edges, not every coincidence; only `0x02156A38` hand-verified |

## 6. Correction, iteration 147: the 187 was a floor

Iteration 147: `Battle_ObjShotManCreate` `0x0216A7BC` and
`Battle_ObjCtrlManCreate` `0x02168B88` are both reached from Thumb. Neither appeared
in this audit. Two real manager constructors, missed.

**Root cause — two defects in `plausible()` and `--audit`:**

1. **Adjacent-call window `±2` halfwords; marker scan `±8`.** The two constructors sit
   `14` bytes — `7` halfwords — apart in one init routine. Each should see the other as
   a neighbouring call and score `call`; the narrow window prevented it, so both scored
   `NONE`. Widened to `±8` to match the marker scan. Both now score `call`.
2. **`--audit` required `plausible()` and silently dropped failures.** `--to` reports the
   score and accepts on impossible-edge filters alone, so the two modes disagreed with
   no indication. `--audit` now keeps impossible-edge rejection (decode-level
   impossibility, not doubt) but reports heuristic-failures in a **separate bucket** with
   an explicit floor/ceiling instead of dropping them.

**Corrected figures:**

| | old | new |
|---|---|---|
| ARM functions with no ARM caller | 3691 | 3691 |
| …passing the neighbourhood heuristic | **187** | **340** |
| …plausibility `NONE`, unconfirmed either way | (dropped silently) | **37** |
| …floor / ceiling | 187 | **340 / 377** |
| …in ov6 battle code | **16** | **31** |

The old "16 in battle code" included `0x02084A64`, which has `arm9` provenance — really
**15** ov6 targets. The ov6 count roughly doubled, `15` → `31`:

`0x0214D95C` `0x0214E388` `0x0214E828` `0x0214F524` `0x0214F660` `0x0214F6AC`
`0x02151BE8` `0x02151DD8` `0x021526B4` `0x02153074` `0x0215308C` `0x02153108`
`0x021537E0` `0x021539B8` `0x02153BC8` `0x02153CAC` `0x02156A38` `0x02156D74`
`0x02156F6C` `0x02156FB4` `0x02160A48` `0x021614B0` `0x021615AC` `0x021620C0`
`0x02167F20` `0x02168374` `0x02168590` `0x02168B88` `0x02168C90` `0x0216A7BC`
`0x0216A8C8`

**Counting caveat.** Rejected edges: `499` → `962`. An ordering artefact —
`invalid_edge` now runs *before* the heuristic, so it sees edges the old gate discarded
first. The impossible-edge filters themselves did not change.

**What did not change.** The nine claims in §2 were checked by targeted scan, not by
this audit; the widened window adds no caller to any of them. The eight "0 callers"
conclusions hold. Iteration 94's dead table survives. Separately confirmed still
caller-less from Thumb: `0x0207E864`, `0x0207F7C8`, `0x0207DD40`, `0x0216B2A0`.

**Methodological lesson.** A heuristic gating a *census* turns absence of evidence into
a reported number. The original document hedged correctly — "the 16 battle targets are
all genuine" was marked *not claimed* — but the hedge only covered false positives. The
gap ran the other way too. `--audit` now prints a floor and a ceiling so the uncertainty
is visible in the output, not buried in a caveat.

## Next angles, ranked

1. **Follow `0x0214D65E` upward** (carried) — builds the descriptor whose `+0x0` is the
   `≥0x5F1` struct.
2. **Catalogue ov6's early Thumb region.** `functions.json` starts ov6 Thumb at
   `0x0214DF14`; callers here sit below that — database incomplete.
3. **Read `char+0x7c`'s users** `0x02158B20`, `0x021586D0` (carried).
4. **Map `BattleCol.cpp`** (carried).
