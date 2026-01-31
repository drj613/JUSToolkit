# Damage Formula - SOLVED

> **STATUS: FORMULA CONFIRMED (2026-01-30)**
>
> The damage formula was solved. All previous "anomalies" are explained.

---

## Confirmed Formula

```
jsoul_damage = floor(jpower.damage1 / 5) + (tier - 2)
actual_damage = floor(jsoul_damage × nature_multiplier)
```

**Key insight:** Uses `damage1` component only, NOT `damage1+damage2+damage3`!

---

## Verified Test Data

| Character     | tier | B Damage | damage1 | Formula Check |
| ------------- | ---- | -------- | ------- | ------------- |
| Nami          | 2    | 6        | 30      | 30/5+0=6 ✓    |
| Train         | 2    | 7        | 35      | 35/5+0=7 ✓    |
| Goku          | 2    | 8        | 40      | 40/5+0=8 ✓    |
| Luffy         | 2    | 8        | 40      | 40/5+0=8 ✓    |
| Robin         | 2    | 8        | 40      | 40/5+0=8 ✓    |
| Franky        | 2    | 8        | 40      | 40/5+0=8 ✓    |
| Naruto        | 2    | 8        | 40      | 40/5+0=8 ✓    |
| Buu           | 2    | 9        | 45      | 45/5+0=9 ✓    |
| Bankai Ichigo | 1    | 9        | 50      | 50/5-1=9 ✓    |
| Ichigo        | 2    | 10       | 50      | 50/5+0=10 ✓   |
| Caramelman    | 3    | 13       | 60      | 60/5+1=13 ✓   |
| Kyuubi Naruto | 1    | 8        | 45      | 45/5-1=8 ✓    |

---

## Previous Mysteries - EXPLAINED

### "Goku B=8 Mystery"

- **Old assumption:** Formula uses `total = damage1+damage2+damage3`
- **Problem:** Block 0 has total=50 entries, which would give 10 damage, not 8
- **Solution:** Formula uses `damage1` only. Goku B uses entry with damage1=40

### "Buu B=9 Anomaly"

- **Old assumption:** No jpower entry has total=45
- **Solution:** Buu uses entry with damage1=45 (45/5+0=9)

### "Divisor ÷5 vs ÷7"

- **Old assumption:** Some characters use ÷7 (Goku Y=14 from total=100)
- **Solution:** All characters use ÷5 on `damage1`. Goku Y uses damage1=70 →
  70/5=14

---

## Remaining Unknown

**jpower Entry Selection Mechanism:**

- How does the game choose which jpower entry to use for each move?
- Characters sharing jpower blocks (Goku/Buu, Luffy/Robin) get different entries
- Likely determined by collision file `damageFlags` field pointing to jpower ID
- See issue: JUS-9lp.1

---

_Solved: 2026-01-30_
