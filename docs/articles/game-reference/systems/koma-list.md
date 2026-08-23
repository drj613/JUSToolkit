# Koma (character) list — extracted from the Genroh guide

`koma-list.json` is a machine-readable dump of section **C5. Koma (Character) List**
of the GameFAQs Jump Ultimate Stars guide by Genroh (v2.5), source id `gf-45856`.
It was produced by `sources/gamefaqs/parse_koma_list.py` (stdlib Python 3, no
arguments — it reads the raw text and rewrites this JSON).

**Caveat: unverified community data.** Every number and effect string here was
transcribed by a fan from play, not dumped from the game. Treat J-Soul values,
natures, and effect wording as a starting hypothesis to confirm against the ROM,
not as ground truth. The guide also contains typos (character and move names are
romanized inconsistently); the parser keeps the guide's spelling as-is.

**Scope: no gem costs.** Only in-battle mechanics are captured. Every `Cost:` line
in the guide (gem prices for buying a koma or an evolution-chart node) is skipped
on purpose and is not represented anywhere in the JSON.

## Shape

```
{
  "metadata": { source, source_version, source_lines, note, scope_note, ... },
  "series": [
    {
      "series": "DRAGON BALL",
      "mangaka": "Akira Toriyama",
      "series_symbol": "An orange ball with a star (a dragon ball)",
      "roster": { "battle": [...], "support": [...], "help": [...] },
      "characters": [
        {
          "name": "SON GOKU",
          "series": "DRAGON BALL",
          "boosts": [ {"name": "Arale", "series": "Dr. Slump"}, ... ],
          "passive_effects": ["..."],
          "ultimate_action": "Hold Select to slowly regain SP energy.",
          "evolution_chart": ["[H]-|-[B4]-[B5]-...", ...],
          "notes": [],
          "koma": [ ... ],
          "unparsed": []
        }
      ],
      "unparsed": []
    }
  ]
}
```

### Character fields

| Field | Meaning |
| --- | --- |
| `name` | Character heading exactly as printed in the guide. |
| `boosts` | Characters whose presence in the deck boosts this one. `series` is set when the guide names a cross-series partner, e.g. `Arale(Dr. Slump)`. |
| `passive_effects` | Always-on effects, one string per bullet. |
| `ultimate_action` | Effect of holding Select (null when the guide left it blank — Kurapica). |
| `evolution_chart` | Raw ASCII chart rows, kept verbatim: `[H]` help, `[S2]`/`[S3]` support, `[B4]`-`[B8]` battle, `[AB*]` alternate battle, `[E]` evolution path, `[D]` data, `[C]` info character, `[ST]` stage, `[Q]` quiz, `[G]` galaxy. |
| `notes` | Free-form `NOTE:`/`TIP:` lines about the character's normal attacks. |
| `koma` | One entry per koma (see below), in guide order. |

### Koma entry fields

`role` is derived from koma size, not from the section header, because a few
characters (Kenshiro, Kinnikuman, Muhyo, Momotaro, ...) omit the `-BATTLE KOMA-`
header entirely:

- `help` — 1 koma. `effect` (the help effect text) and `unlock` (where you get it).
- `support` — 2-3 koma. One entry in `specials` (the support move), `nature`, `shape`.
- `battle` — 4-8 koma. `j_soul` (starting HP), `nature`, two `specials` (A and B), `shape`.
- `unlock` — non-koma evolution-chart nodes. `kind` is one of `data`, `stage`,
  `quiz`, `info_character`, `galaxy`, `evolution_path`; `text` holds the guide's
  lines (e.g. `["Unlocks Luffy's alternate 6 koma"]`).

Other keys on a koma entry:

| Field | Meaning |
| --- | --- |
| `size` | Koma count (1-8). |
| `nature` | Koma nature: Power / Knowledge / Laughter (null in 4 places where the guide left it blank). |
| `j_soul` | Battle koma HP. Present on battle koma; null in 2 entries the guide left blank (Arale 7-koma, Kenshin 6-koma). |
| `specials` | `{slot, name, effects, attack_nature}`. `slot` is `"A"`/`"B"` for battle koma and null for support koma. `effects` are the guide's parenthetical riders, e.g. `(Causes Confusion effect)`. `attack_nature` can differ from the koma's own nature (Goku's 4-koma Special B is Laughter). `alt_names` appears once, where the guide printed two names for one move. |
| `shape` | Raw ASCII koma footprint rows (`[][]`). |
| `form_name` | Alternate form this koma turns the character into (`SUPER SAIYJIN SON GOKU`, `LUFFY GEAR 2ND`, ...). 19 entries. |
| `boosts`, `passive_effects`, `ultimate_action` | Present when the guide restates them for an alternate form; they override the character-level values for that koma. |
| `unlock_note` | Cross-character unlock hints, e.g. `(Buy the path to this Koma in Kaiousama's Evolution Chart)`, or `(You start with this)`. |
| `notes` | `NOTE:`/`TIP:` lines attached to that koma. |
| `unparsed` | Lines the parser could not classify. Empty everywhere in the current output. |

## Extraction stats

Source slice: lines 3738-14878 of `sources/gamefaqs/raw/45856-genroh-guide.txt`.

| Count | Value |
| --- | --- |
| Series | 41 |
| Characters | 305 (56 with battle koma) |
| Koma entries | 1188 |
| — help | 305 (all with effect text and an unlock note) |
| — support | 363 (2-koma 179, 3-koma 184) |
| — battle | 202 (4:58, 5:62, 6:54, 7:16, 8:12) |
| — unlock nodes | 318 (data 143, evolution paths 48, quiz 42, info character 41, stage 35, galaxy 9) |
| J-Soul values | 200 (2 more battle koma have a blank J-Soul in the guide) |
| Special moves | 763, of which 743 carry an attack nature and 440 carry effect text |
| Boost links | 210 |
| Passive effect bullets | 144 |
| Alternate-form names | 19 |
| Unparsed lines | 0 |

Validation: the counts of `N Koma:` headers (565), `J-Soul:` values (200),
`Evolution Chart:` blocks (305), `Boost:` lines and `Ultimate Action:` lines in the
raw text all match the JSON exactly, so nothing was dropped. Spot-checked Goku
(including the Super Saiyjin 6-koma and Vegetto 8-koma forms), Zoro, Yoh, Naruto,
Kenshiro, Sena, and Aya against the raw text.

Known quirks in the source, handled rather than fixed:

- One stray `=====` separator inside Roronoa Zoro's entry splits his battle koma;
  the parser rejoins them by checking whether a character name follows.
- Hiei's section header is misspelled `-BATLE KOMA-`.
- Four support koma and two battle koma have blank natures / J-Soul in the guide.
- Kurapica's `Ultimate Action:` is blank.
- Two of Naruto's 4-koma Special A entries have a blank `Attack Nature:`.
