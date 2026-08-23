# Hitsugaya — Character Research Notes

- **Source guide**: "Hitsugaya Character FAQ"
- **Author**: FFandMMfan
- **Version**: 1.3 (revision history: 1.0, 1.2, 1.3)
- **GameFAQs FAQ ID**: gf-46708
- **Note**: Unverified community source (fan-authored guide, not verified against game data/disassembly).

## Koma Forms / Evolution

- Nature: all Koma are **Knowledge** type. No alternate/branch Koma — single linear path.
- Evolution chart: `[H] -> [B4] -> [B5] -> [B6]`, with `[B4] -> [S2] -> [S3]` branch off the Help Koma line.

### Koma Shapes
- Support 2: vertical domino `[]` / `[]` (2 cells)
- Support 3: horizontal `[][][]` (3 cells)
- Battle 4: 2x2 square
- Battle 5: 2x2 square plus one cell on top-left (5 cells, per ASCII: row1 `  []`, row2 `[][]`, row3 `[][]`)
- Battle 6: 2x3 rectangle (6 cells)

### J-Soul values
- Battle 4: 136
- Battle 5: 152
- Battle 6: 168

## Passive Effects (always on, cannot double up)
- Always can Air Dash
- Immune to Freeze
- Immune to Burn

## Help/Support Koma

- **Help Koma**: grants attached character Immunity to Freeze.
- **Support Koma 2**: stabs sword into ground, circular icy shockwave, causes Freeze.
  - Damage: 22 vs Power/Knowledge, 33 vs Laughter.
  - No knockback noted; circular hit radius (hits above/below/sides).
- **Support Koma 3**: charges then fires forward ice beam, causes Freeze. Damage scales with beam contact duration (longer against wall).
  - Damage: 30 vs Power/Knowledge, 45 vs Laughter (best-case numbers).

## Basic Moveset (as Battle Character)

Damage figures are author's "best possible" numbers assuming full/perfect hit connection; actual damage varies a lot with hit timing/charge (author notes single-hit damage can be as low as 1 if only the tip connects).

- **B / B+left/right / B+Up**: simple slashes. 9 dmg to P/K, 13 to L.
- **B in Air**: horizontal air slash. 9 dmg to P/K, 13 to L.
- **B+Down**: ground shockwave, force-switches opponent's battle character. 18 dmg P/K, 27 L.
- **Y**: downward slash + ice wave, can be charged. 2 hits. Max: 18 dmg P/K, 27 L. Charging does NOT increase damage — only increases how long the ice wave persists.
  - Note: despite appearing to freeze on hit, Y attacks do NOT actually apply Freeze status even fully charged (author explicitly debunks this).
- **Y+left/right**: dashing slash leaving ice trail, chargeable. Up to 3 hits (3rd hit hitbox small, usually only 2 land).
  - 3 hits: 14 dmg P/K, 21 L.
  - 2 hits: 13 dmg P/K, 19 L.
  - Charging increases dash distance only.
- **Y+Up**: jumping upward slash + ice trail, chargeable. 1–8 hits.
  - First hit: 12 dmg P/K, 18 L.
  - Max (8 hits): 19 dmg P/K, 28 L.
  - Charging increases jump height (more chance to land all 8 hits), not per-hit damage.
- **Y+Down**: hooked rope swing, guard break. 18 dmg P/K, 27 L.
- **Y in Air**: downward slash + ice arc below him, chargeable. 2 hits, max 18 dmg P/K, 27 L. Charging extends hang time, arc size, and duration.

### Combos (author notes he has very few good ones — many moves have charge/knockback that break chaining)
- `B -> B+forward/B+up`: both deal 18 P/K / 27 L; described as quick.
- `B or B+up -> Y (uncharged)`: 3-hit sequence, only worthwhile if all hits land. 27 dmg P/K, 40 dmg L (author's "strongest basic combo").

### Ultimate Action
- Hitsugaya sheathes sword, sighs, text bubble appears. If breath or text bubble hits opponent: he regains some SP (amount unspecified) and opponent is stunned for ~1 second.

## Battle Koma Specials

### Battle Koma 4 (J-Soul 136, Knowledge, 2x2 shape)
- **Special A**: large forward ice beam, up to 10 hits, damage tied to hit count, inflicts Freeze. Same concept as Support 3 but stronger.
  - Max damage: 49 vs Laughter, 33 vs Power/Knowledge.
- **Special B**: ground stab + icy shockwave (same as Support 2), inflicts Freeze, 1 hit.
  - Damage: 36 vs Laughter, 24 vs Power/Knowledge.
- Author rates this his best Koma overall.

### Battle Koma 5 (J-Soul 152, Knowledge, shape: 1 cell top-center + 2x2 below = 5 cells)
- **Special A**: ice blast spiking up/outward, fast, inflicts Freeze.
  - Damage: 48 vs Laughter, 32 vs Power/Knowledge.
- **Special B**: summons Matsumoto (Vice-Captain), creates smoke veil causing Blind + heavy damage; veil spawns at enemy's prior position (easily evaded/blocked per author).
  - Damage: 48 vs Laughter, 32 vs Power/Knowledge.

### Battle Koma 6 (J-Soul 168, Knowledge, 2x3 shape)
- **Special A** ("Bankai"): dash forward, pierce with ice lance, inflicts Freeze. Author calls it slow to start/execute, easily blocked/seen coming; his worst special overall despite being "Bankai."
  - Damage: 72 vs Laughter, 48 vs Power/Knowledge.
- **Special B**: same as 5-Koma's Matsumoto summon (Blind), slightly more damage, still easily blocked.
  - Damage: 60 vs Laughter, 40 vs Power/Knowledge.
- Author strongly advises against using this Koma (poor J-Soul-to-hit-rate tradeoff, awkward 6-slot shape).

## Mechanic-Revealing Observations
- Charging some moves (Y, Y+forward, Y in air) does not raise per-hit damage — it changes duration/range/hang-time/jump height instead. This suggests separate "charge" parameters affect hitbox lifetime/travel rather than a damage multiplier for this character.
- Y-family attacks visually resemble freeze-inducing hits but do not apply Freeze status — a case where visual FX and status application are decoupled.
- Damage against Laughter-type opponents is consistently ~1.5x the Power/Knowledge value across nearly every move (e.g., 9→13, 18→27, 22→33, 30→45, 33→49, 24→36, 32→48, 48→72, 40→60) — suggests a fixed type-based damage multiplier (author unconfirmed exact ratio, but pattern is consistent ~1.5x throughout this Koma's moves).
- Force-switch effect on B+Down and Down+B-type moves indicates a distinct "force switch" hit property separate from knockback/launch.
