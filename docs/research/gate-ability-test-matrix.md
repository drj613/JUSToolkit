# Gate-ability test matrix — the 12 rows behind the ±25% damage gates

Asset for the settle-or-waive decision on the damage gate bits
(bead `jus-wayfinder-map-digi.12`). Static mining only; no emulator.

Sources: [p213](findings/p213-flag-word-is-plus-0x44-ability-10-sets-bit-5.md),
[p227](findings/p227-kind2-abilities-are-stat-modifiers.md),
[abilities-all-57-named.md](findings/abilities-all-57-named.md),
[ability-descriptions-57.txt](findings/ability-descriptions-57.txt),
[chr_b-Complete-Mapping.md](chr_b-Complete-Mapping.md).
Beads cited inline. Table bytes re-read from disk for this doc, not copied
from p213.

## 1. The 12×3 table, dumped fresh

Read from `jus_files/overlays/ov06.bin` at file offset `0x2439C`
(= runtime `0x021710BC` − load base `0x0214CD20`, base from
`jus_files/overlays/overlays.json`: `ram_address` 34917664). Raw bytes:

```
09 00 01  0B 00 02  0A 01 01  0C 01 02  0D 02 01  15 02 02
10 04 01  11 04 02  12 05 01  13 05 02  17 03 01  18 03 02
```

Byte-identical to the table quoted in p213. Decoded with the mask tables
(`0x02092E78` = bits 4..9 subtract, `0x02092E90` = bits 12..17 add;
variant 1 = subtract table, variant 2 = add table):

| row | ability id | maskIdx | variant | gate-word bit | name (JP / gloss) | read by damage routine? |
|---|---|---|---|---|---|---|
| 0 | 9 | 0 | sub | **4** | 打撃耐性ＵＰ / Blunt resistance UP | yes |
| 1 | 11 | 0 | add | **12** | 打撃弱点 / Blunt weakness | yes |
| 2 | 10 | 1 | sub | **5** | 斬撃耐性ＵＰ / Slash resistance UP | yes |
| 3 | 12 | 1 | add | **13** | 斬撃弱点 / Slash weakness | yes |
| 4 | 13 | 2 | sub | **6** | 見切り / Evasion (less damage from Specials) | yes |
| 5 | 21 | 2 | add | **14** | 直撃 / Direct hit (more damage from Specials) | yes |
| 6 | 23 | 3 | sub | 7 | 重量級 / Heavyweight (knockback shorter) | no |
| 7 | 24 | 3 | add | 15 | 軽量級 / Lightweight (knockback longer) | no |
| 8 | 16 | 4 | sub | 8 | 収集 / Collection (more SP from coins) | no |
| 9 | 17 | 4 | add | 16 | 浪費 / Waste (less SP from coins) | no |
| 10 | 18 | 5 | sub | 9 | 調理 / Cooking (more HP from food) | no |
| 11 | 19 | 5 | add | 17 | 大食い / Big eater (less HP from food) | no |

### In-game descriptions (from ability-descriptions-57.txt)

- **9** 打撃耐性ＵＰ: 「相手から受けるパンチやキックなどの打撃ダメージが軽減される能力。」
- **11** 打撃弱点: 「打撃攻撃を受けた時のダメージが少し大きくなってしまうマイナス能力。」
- **10** 斬撃耐性ＵＰ: 「剣や刀の相手からの斬られるダメージが軽減される能力。」
- **12** 斬撃弱点: 「剣や刀の相手からの斬られるダメージが**軽減される**能力。」 —
  note: this is the *same "reduced" text as ability 10*. The name says
  weakness, the description says reduced. Looks like a copy error in the
  game's own text data; the code adds (bit 13, add table) regardless.
- **13** 見切り: 「相手の必殺技で受けるダメージが軽減される能力。」
- **21** 直撃: 「必殺技で受けるダメージが大きくなってしまうマイナス能力。」
- **23/24** 重量級/軽量級: knockback distance shorter/longer.
- **16/17** 収集/浪費: SP gained from coins bigger/smaller.
- **18/19** 調理/大食い: HP recovered from food bigger/smaller.

### Owner-context flags

The owner (experienced player) reports no passive is visibly described in
the UI as "damage up/down vs a class". Two findings, recorded as findings
and not errors:

1. **Rows 0–5 do carry class-damage wording in the JP text** — blunt
   ("punches and kicks"), slash ("swords and blades"), and specials. If the
   owner played a localization or skimmed menus, the wording may not have
   surfaced; either way the disk text and the code agree here.
2. **Rows 6–11 sound completely unrelated to damage** (knockback, coins,
   food) — and that is *consistent*: the damage routine only reads bits
   4/5/6 and 12/13/14. Bits 7–9/15–17 exist in the same gate word but are
   consumed elsewhere (unlocated; damage.md §5). The "+0x44 word" is a
   general passive-flag word, not a damage-only word. Mismatched names for
   those rows are expected, not suspicious.

## 2. Carrier census (chr_b record +0x03, five sparse bytes)

Scanned all 74 records of `jus_files/ripped_jus_files/bin/chr_b.bin`
(74 × 60 B; list layout per bead `jus-ondisk-ability-list-at-chrb-0x03-kfc`,
p223). Names from chr_b-Complete-Mapping.md.

| ability | carriers (chr_b: name) |
|---|---|
| 9 | 12 Luffy, 18 Robin, **67 Edajima** |
| 11 | **none** — orphan, matches p227's inert-id list |
| 10 | 17 Sanji, 56 Arale, **67 Edajima** |
| 12 | 12 Luffy, 18 Robin |
| 13 | 21 Kyuubi Naruto, 23 Sakura, 28 Jotaro, 54 Tsuna, 61 Kenshiro, 62 Raoh, 63 Seiya, 64 Gold Seiya |
| 21 | 47 Bo-bobo, 48 Shinsetsu, 49 Don Patch, 50 Super Patch |
| 23 | 17 Sanji, 58 Caramelman, 66 Momotaro |
| 24 | 15 Nami, 19 Franky, 27 Anna, 37 Train, 41 Rukia, 43 Hitsugaya, 46 Lenalee, 59 Muhyo, 69 Fuusuke |
| 16 | 15 Nami, 19 Franky, 27 Anna |
| 17 | 31 Killua, 51 Ryotsu |
| 18 | 14 Zoro |
| 19 | 10 Frieza, 53 Kagura |

Note: chr_b-Complete-Mapping.md's header corrects record 24 to Kyuubi
Naruto vs the body table's Kakashi ordering for rows 21/24; neither carries
a gate ability except 13 on record 21, listed with the corrected name.

**Every row except ability 11 has at least one carrier.** Ability 11
(打撃弱点 → bit 12, add, class 1) is carried by no character — the only
one of the six damage-readable bits that cannot be armed from a stock deck.

## 3. Test matrix for the six readable bits

Firing conditions per damage.md §4: class table `0x02092E68` maps the
attack's element class index → category (indices 0–1 → cat 1 "blunt",
2–11 → cat 2 "slash", 12–15 → cat 0 immune). Bits 6/14 use the element
condition instead: element type 4 or 5, else `[sl+0x14] & 0xF0` (specials).

| bit | armed by | carriers (deck options) | fires when | effect | status |
|---|---|---|---|---|---|
| 4 | 9 打撃耐性ＵＰ | Luffy, Robin, **Edajima** | class cat == 1 | −25% of base | **live-confirmed** (`jus-gate-word-read-live-0x2010-nbz`) |
| 5 | 10 斬撃耐性ＵＰ | Sanji, Arale, **Edajima** | class cat == 2 | −25% | **live-confirmed** (`jus-bit5-fired-and-nature-observed-w5n`; earlier untested per `jus-bit5-ability-10-untested-mvk`) |
| 6 | 13 見切り | Kyuubi Naruto, Sakura, Jotaro, Tsuna, Kenshiro, Raoh, Seiya ×2 | element cond. (specials) | −25% | untested |
| 12 | 11 打撃弱点 | **nobody** | class cat == 1 | +25% | **uncoverable from stock decks** |
| 13 | 12 斬撃弱点 | Luffy, Robin | class cat == 2 | +25% | armed-but-blocked observed live (cat 1 hit); firing untested |
| 14 | 21 直撃 | Bo-bobo, Shinsetsu, Don Patch, Super Patch | element cond. (specials) | +25% | untested |

**Cheapest deck: chr_b 67 Edajima**, ability slots `[9, 10, 0, 0, 56]` —
arms bits 4 **and** 5 in one fighter, predicted/confirmed gate word
`0x00000030` (p227 §"The Edajima prediction", bead `jus-5bg`).

## 4. Suggested live session plan

Minimal coverage of all six readable bits, three decks:

1. **Deck A — Edajima (chr_b 67)** as target. One blunt (cat-1) hit →
   bit 4 fires (−25%); one slash (cat-2) hit → bit 5 fires (−25%). Both
   already live-confirmed; re-running them is a free sanity anchor,
   `[r8+0x44]` should read `0x0030`.
2. **Deck B — Luffy (chr_b 12)** as target (abilities `[9, 25, 12]`,
   gate word predicts `0x2010`). One cat-2 (slash) hit → **bit 13 fires**
   (+25%) — the add path, never yet seen firing. Same capture with a cat-1
   hit reproduces the armed-but-blocked observation in reverse (bit 4
   fires, bit 13 blocked).
3. **Deck C — any 見切り carrier (e.g. Jotaro, chr_b 28) vs any 直撃
   carrier (e.g. Don Patch, chr_b 49)**. Land one special each way:
   special into Jotaro → **bit 6** (−25%); special into Don Patch →
   **bit 14** (+25%). One match covers both element-condition gates.

Total: 3 decks, ~6 landed hits (breakpoint `0x02082584` is a hit oracle,
bead `jus-first-attributed-measurement-d6u`).

### Waive candidates

- **Bit 12 (ability 11)**: no carrier exists → cannot be exercised from
  stock content. Automatic waive candidate unless someone edits a chr_b
  ability slot or pokes the bitset *before* the ov6 `0x02157114` assembly
  pass (~30–80 frames after load, bead
  `jus-gate-word-assembled-after-load-68g`).
- **Rows 6–11 (bits 7–9 / 15–17)**: not read by the damage routine at all;
  their consumers are unlocated. Out of scope for the damage-gate bead —
  waive from *this* bead regardless of carriers. Of these, all six
  abilities have carriers, so they stay testable later if the consumers
  are ever found.

So of the 12 table rows: 2 confirmed (9, 10), 3 testable now (12, 13, 21),
1 uncoverable (11), 6 out of damage scope (23, 24, 16, 17, 18, 19).
