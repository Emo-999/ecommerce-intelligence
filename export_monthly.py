#!/usr/bin/env python3
"""
export_monthly.py
=================
Turn the daily history trail into shareable analytics:

    python export_monthly.py                     # current month
    python export_monthly.py --month 2026-08     # specific month
    -> exports/<month>-daily.csv     one row per vendor per day
    -> exports/<month>-summary.csv   one row per vendor (month aggregates)

Columns are stable so month-over-month files can be diffed / pivoted in
Excel or BI tooling against CloudCart's own numbers.
"""

import argparse
import csv
import json
import os
import sys

from intel_history import load_history
from report_style import utcnow

DAILY_COLS = ["date", "vendor", "status", "ongoing_incidents",
              "incidents_30d", "downtime_30d_min", "entry_eur",
              "plan_prices", "fingerprints", "videos_30d", "last_video"]


def export(month, outdir="exports"):
    latest, dates = load_history()
    rows = [line for (d, _v), line in sorted(latest.items())
            if d and d.startswith(month)]
    if not rows:
        print(f"No history for {month} (history/daily.jsonl has "
              f"{len(dates)} days total). Run run_all.py first.")
        return False
    os.makedirs(outdir, exist_ok=True)

    daily_path = os.path.join(outdir, f"{month}-daily.csv")
    with open(daily_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(DAILY_COLS)
        for r in rows:
            plans = r.get("plans") or {}
            w.writerow([
                r.get("date"), r.get("vendor"),
                r.get("status", ""), len(r.get("ongoing") or []),
                r.get("incidents_30d", ""), r.get("downtime_30d_min", ""),
                r.get("entry_eur", ""),
                "; ".join(f"{k}={v}" for k, v in plans.items()),
                r.get("fingerprints", ""), r.get("videos_30d", ""),
                r.get("last_video", ""),
            ])

    by_vendor = {}
    for r in rows:
        by_vendor.setdefault(r["vendor"], []).append(r)
    summary_path = os.path.join(outdir, f"{month}-summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["vendor", "days_tracked", "days_degraded",
                    "max_incidents_30d", "max_downtime_30d_min",
                    "entry_eur_first", "entry_eur_last", "entry_eur_change",
                    "plan_price_changes", "videos_30d_last"])
        for vendor, vrows in sorted(by_vendor.items()):
            vrows.sort(key=lambda r: r["date"])
            entry = [r.get("entry_eur") for r in vrows
                     if r.get("entry_eur") not in (None, "")]
            plan_snaps = [json.dumps(r.get("plans") or {}, sort_keys=True)
                          for r in vrows]
            changes = sum(1 for a, b in zip(plan_snaps, plan_snaps[1:])
                          if a != b)
            degraded = sum(1 for r in vrows
                           if r.get("status") not in ("none", "", None,
                                                      "nopage", "unknown"))
            w.writerow([
                vendor, len(vrows), degraded,
                max((r.get("incidents_30d") or 0) for r in vrows),
                max((r.get("downtime_30d_min") or 0) for r in vrows),
                entry[0] if entry else "", entry[-1] if entry else "",
                (round(entry[-1] - entry[0], 2) if len(entry) >= 2 else ""),
                changes,
                vrows[-1].get("videos_30d", ""),
            ])

    print(f"Wrote {daily_path} ({len(rows)} rows) and {summary_path} "
          f"({len(by_vendor)} vendors)")
    return True


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Export monthly intel CSVs")
    ap.add_argument("--month", default=utcnow().strftime("%Y-%m"),
                    help="YYYY-MM (default: current month)")
    ap.add_argument("--outdir", default="exports")
    args = ap.parse_args()
    export(args.month, args.outdir)


if __name__ == "__main__":
    main()
