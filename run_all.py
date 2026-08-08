#!/usr/bin/env python3
"""
run_all.py
==========
One command for the whole intelligence pass:

    python run_all.py                    # -> reports/ (6-page dashboard)
    python run_all.py --days 7 --outdir reports

Collects feeds, pricing fingerprints, structured plans, platform status, and
social/ads activity; appends the daily history snapshot; writes the dashboard
ecosystem (see dashboard.py):
  index / pricing / availability / activity / social / sources .html
plus the legacy single-page digest.html (plain feed digest).

Delivery (Slack/email) is opt-in via env vars in ecommerce_monitor.deliver().
Monthly CSVs: python export_monthly.py.
"""

import argparse
import json
import os

import dashboard as db
import ecommerce_monitor as em
import intel_history
import plan_compare as pc
import pricing_monitor as pm
import social_monitor as sm
import status_monitor as stm


def main():
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="Run the full intelligence pass")
    ap.add_argument("--days", type=int, default=7, help="feed look-back window")
    ap.add_argument("--outdir", default="reports", help="output directory")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    def write(name, html):
        with open(os.path.join(args.outdir, name), "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Wrote {args.outdir}/{name}")

    # ---- collect ----------------------------------------------------------
    items, problems = em.fetch(em.SOURCES, args.days)
    results = pm.run(pm.PRICING_PAGES)

    plans, plan_problems = pc.collect_plans()
    state = pm.load_state()
    plan_changes = pc.diff_plans(pc.load_plan_state(state), plans)
    pc.save_plan_state(state, plans)
    pm.save_state(state)

    status, status_problems = stm.collect_status()
    social, social_problems = sm.collect_social()
    changed = [r for r in results if r["status"] == "changed"]
    print(f"Collected: {len(items)} feed items | {len(changed)} page changes | "
          f"{len(plans)} vendors priced, {len(plan_changes)} plan changes | "
          f"{sum(s['incidents_30d'] for s in status.values())} incidents 30d")

    # ---- daily history snapshot ------------------------------------------
    results_by_vendor = {db.NAME_MAP.get(r["name"], r["name"]): r
                         for r in results}
    snap = {}
    for v in set(list(plans) + list(status) + list(social)):
        p, s = plans.get(v), status.get(v)
        so = social.get(v) or {}
        lv = so.get("latest_video") or {}
        snap[v] = {
            "entry_eur": pc._entry_eur(p["plans"]) if p else None,
            "plans": {pl["name"]: (pl.get("annual") if pl.get("annual")
                                   is not None else pl.get("monthly"))
                      for pl in p["plans"]} if p else {},
            "fingerprints": results_by_vendor.get(v, {}).get("count"),
            "status": s["indicator"] if s else None,
            "ongoing": s["ongoing"] if s else [],
            "incidents_30d": s["incidents_30d"] if s else None,
            "downtime_30d_min": s["downtime_30d_min"] if s else None,
            "videos_30d": so.get("videos_30d"),
            "last_video": (lv.get("title") or "")[:80],
            "google_ads_lo": (so.get("google_count") or {}).get("lo"),
            "google_ads_hi": (so.get("google_count") or {}).get("hi"),
        }
    intel_history.append_snapshot(snap)
    _, hist_dates = intel_history.load_history()

    # ---- dashboard ecosystem ---------------------------------------------
    trouble = [f"feed — {p}" for p in problems]
    trouble += [f"pricing — {r['name']}: {r['status']}" for r in results
                if r["status"] not in ("changed", "baseline", "same")]
    trouble += list(plan_problems) + list(status_problems) + list(social_problems)

    features, positioning = {}, {}
    if os.path.exists("features.json"):
        with open("features.json", encoding="utf-8") as f:
            fj = json.load(f)
        features = fj.get("vendors", {})
        positioning = fj.get("positioning", {})

    write("index.html", db.build_overview(items, results, args.days, plans,
                                          plan_changes, status, social))
    write("pricing.html", db.build_pricing_dash(plans, plan_changes, results))
    write("features.html", db.build_features_dash(features, positioning))
    write("availability.html", db.build_availability_dash(status))
    write("activity.html", db.build_activity_dash(items, args.days, problems))
    write("social.html", db.build_social_dash(social))
    write("saved.html", db.build_saved_page())
    write("sources.html", db.build_sources_dash(trouble, hist_dates, args.days))
    write("digest.html", em.render(items, problems, args.days))

    em.deliver(items, db.build_email(items, results, args.days, plans,
                                     plan_changes, status),
               subject="CloudCart competitive intel — daily brief")


if __name__ == "__main__":
    main()
