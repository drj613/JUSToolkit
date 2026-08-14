# scripts/emu/spike/s2_timing_monitor.py
"""Externally measure the spike callback rate and stalls.

Run while s1_s2_update_probe.lua is active. Reports effective callback
frequency and the largest inter-update gap over 30 seconds. If the
emulator's video output is smooth AND rate ~= 60/s with max gap < 100ms,
per-frame file I/O is acceptable.
"""
import json
import time

SPIKE = "/tmp/jus_emu_spike.json"
DURATION = 30.0

seen = 0
gaps = []
last_t = None
last_c = None
t_start = time.time()
t_end = t_start + DURATION

while time.time() < t_end:
    try:
        with open(SPIKE) as f:
            c = json.load(f)["count"]
    except (OSError, ValueError, KeyError):
        time.sleep(0.005)
        continue
    now = time.time()
    if c != last_c:
        if last_c is not None:
            gaps.append(now - last_t)
            if c > last_c:
                seen += c - last_c
            # c < last_c means the probe script restarted; skip the delta
        last_t, last_c = now, c
    time.sleep(0.002)

elapsed = time.time() - t_start
print("updates seen: %d (%.1f/s), max gap %.1f ms" %
      (seen, seen / elapsed, max(gaps) * 1000 if gaps else -1))
