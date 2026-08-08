#!/usr/bin/env python3
"""
intel_history.py
================
The daily evidence trail. Every run_all pass appends one JSON line per vendor
to history/daily.jsonl: prices, plan snapshot, availability, social activity.
Committed to the repo by CI, so the file accumulates day over day and becomes
the raw material for monthly exports and trend charts.

One line = {"ts", "date", "vendor", "entry_eur", "plans", "fingerprints",
"status", "downtime_30d_min", "incidents_30d", "videos_30d", ...}
Multiple runs on the same day are fine — consumers take the LAST line per
(date, vendor).
"""

import json
import os

from report_style import utcnow

HISTORY_FILE = os.path.join("history", "daily.jsonl")


def append_snapshot(vendors_data, path=HISTORY_FILE):
    """vendors_data: {vendor: {...metrics...}}. Appends one line per vendor."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    now = utcnow()
    with open(path, "a", encoding="utf-8") as f:
        for vendor, data in vendors_data.items():
            line = {"ts": now.isoformat(timespec="seconds"),
                    "date": now.strftime("%Y-%m-%d"), "vendor": vendor, **data}
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


def load_history(path=HISTORY_FILE):
    """Returns {(date, vendor): last-line-that-day} plus ordered date list."""
    if not os.path.exists(path):
        return {}, []
    latest = {}
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                line = json.loads(raw)
            except ValueError:
                continue
            latest[(line.get("date"), line.get("vendor"))] = line
    dates = sorted({d for d, _ in latest})
    return latest, dates
