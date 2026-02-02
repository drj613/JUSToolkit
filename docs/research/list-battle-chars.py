#!/usr/bin/env python3
"""Output all character names from battle-chars-passives.json."""
import json
from pathlib import Path

path = Path(__file__).resolve().parent / "battle-chars-passives.json"
with path.open(encoding="utf-8") as f:
    data = json.load(f)

for entry in data:
    print(entry["name"])
