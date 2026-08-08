#!/usr/bin/env python3
"""
status_monitor.py
=================
Competitor platform availability: current status + incident history +
computed downtime, from each vendor's PUBLIC status page API.

Most SaaS status pages are Atlassian Statuspage instances exposing:
    /api/v2/status.json     -> {"status": {"indicator": "none|minor|major|critical", "description": ...}}
    /api/v2/incidents.json  -> {"incidents": [{name, impact, created_at, resolved_at, ...}]}  (recent history)
which is enough to answer "are they down right now, how often were they down
in the last 30 days, and for how long". STATUS_SOURCES is filled with
endpoints verified live (2026-08-08); a vendor without a public status page
is listed with kind "none" and reported as "no public status page" —
that fact itself is competitive information.

Downtime = sum of (resolved_at - created_at) overlapped with the window,
for incidents whose impact is minor/major/critical (maintenance excluded).
"""

import datetime as dt
import re

import requests

from pricing_monitor import UA
from report_style import utcnow

WINDOW_DAYS = 30
COUNTED_IMPACTS = {"minor", "major", "critical"}

# vendor -> config. kind: "statuspage" (Atlassian v2) | "uptimerobot" | "none".
# All endpoints + CORS live-verified 2026-08-08. Notes:
#  * Shopify: use www.shopifystatus.com directly (status.shopify.com 301s and
#    the bare-host API path returns a bodyless 301).
#  * Shift4Shop has NO own status page; parent Shift4's page covers ~110
#    components across all Shift4 products — component_filter narrows
#    incidents to Shift4Shop-relevant ones (name or component match).
#  * CloudCart runs an UptimeRobot public page: getMonitorList carries true
#    per-monitor 30d uptime ratios; getEventFeed is a rolling 7-day window.
#  * incidents.json is hard-capped at the 50 most recent incidents.
STATUS_SOURCES = {
    "CloudCart": {
        "kind": "uptimerobot", "page": "https://status.cloudcart.com",
        "api": "https://status.cloudcart.com/api/getMonitorList/Xp6MXTnl73",
        "events": "https://status.cloudcart.com/api/getEventFeed/Xp6MXTnl73",
        "cors": True},
    "Shopify": {
        "kind": "statuspage", "page": "https://www.shopifystatus.com",
        "api": "https://www.shopifystatus.com/api/v2/status.json",
        "incidents": "https://www.shopifystatus.com/api/v2/incidents.json",
        "cors": True},
    "BigCommerce": {
        "kind": "statuspage", "page": "https://status.bigcommerce.com",
        "api": "https://status.bigcommerce.com/api/v2/status.json",
        "incidents": "https://status.bigcommerce.com/api/v2/incidents.json",
        "cors": True},
    "Wix": {
        "kind": "statuspage", "page": "https://status.wix.com",
        "api": "https://status.wix.com/api/v2/status.json",
        "incidents": "https://status.wix.com/api/v2/incidents.json",
        "cors": True},
    "Squarespace": {
        "kind": "statuspage", "page": "https://status.squarespace.com",
        "api": "https://status.squarespace.com/api/v2/status.json",
        "incidents": "https://status.squarespace.com/api/v2/incidents.json",
        "cors": True},
    "Ecwid": {
        "kind": "statuspage", "page": "https://status.ecwid.com",
        "api": "https://status.ecwid.com/api/v2/status.json",
        "incidents": "https://status.ecwid.com/api/v2/incidents.json",
        "cors": True},
    "WooCommerce": {
        # self-hosted: наличността зависи от хостинга на всеки търговец;
        # липсата на централна статус страница сама по себе си е аргумент.
        "kind": "none", "page": "https://woocommerce.com"},
    "Shift4Shop": {
        "kind": "statuspage", "page": "https://status.shift4.com",
        "api": "https://status.shift4.com/api/v2/status.json",
        "incidents": "https://status.shift4.com/api/v2/incidents.json",
        "cors": True, "component_filter": r"shift4shop|3dcart"},
}


def _get_json(url, timeout=20):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _parse_ts(s):
    """Statuspage timestamps: ISO-8601 with offset. Return aware datetime."""
    if not s:
        return None
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _overlap_minutes(start, end, win_start, win_end):
    lo, hi = max(start, win_start), min(end, win_end)
    return max((hi - lo).total_seconds() / 60.0, 0.0)


def _statuspage(vendor, cfg):
    now = utcnow().replace(tzinfo=dt.timezone.utc)
    win_start = now - dt.timedelta(days=WINDOW_DAYS)

    res = {"vendor": vendor, "page": cfg.get("page", ""), "kind": cfg["kind"],
           "indicator": "unknown", "description": "", "ongoing": [],
           "incidents_30d": 0, "downtime_30d_min": 0.0, "recent": [],
           "live_api": cfg["api"] if cfg.get("cors") else ""}

    st = _get_json(cfg["api"])
    res["indicator"] = st.get("status", {}).get("indicator", "unknown")
    res["description"] = st.get("status", {}).get("description", "")

    if cfg.get("incidents"):
        import re as _re
        flt = cfg.get("component_filter")
        inc = _get_json(cfg["incidents"]).get("incidents", [])
        if flt:
            rx = _re.compile(flt, _re.IGNORECASE)
            inc = [i for i in inc if rx.search(i.get("name", "")) or any(
                rx.search(c.get("name", "")) for c in i.get("components", []))]
        for i in inc:
            created = _parse_ts(i.get("created_at"))
            resolved = _parse_ts(i.get("resolved_at"))
            impact = (i.get("impact") or "none").lower()
            if not created:
                continue
            if i.get("status") not in ("resolved", "completed", "postmortem"):
                res["ongoing"].append(i.get("name", "incident"))
            if impact not in COUNTED_IMPACTS:
                continue
            end = resolved or now
            if end < win_start:
                continue
            mins = _overlap_minutes(created, end, win_start, now)
            if mins <= 0:
                continue
            res["incidents_30d"] += 1
            res["downtime_30d_min"] += mins
            if len(res["recent"]) < 5:
                res["recent"].append({
                    "name": i.get("name", "incident"), "impact": impact,
                    "start": created.strftime("%b %d %H:%M"),
                    "minutes": round(mins),
                    "resolved": bool(resolved)})
    res["downtime_30d_min"] = round(res["downtime_30d_min"], 1)
    return res


def _uptimerobot(vendor, cfg):
    """UptimeRobot public status page (CloudCart's own). getMonitorList gives
    per-monitor 30d uptime ratios (true 30d downtime); getEventFeed is a
    rolling 7-day event window (recent incident list)."""
    res = {"vendor": vendor, "page": cfg.get("page", ""), "kind": cfg["kind"],
           "indicator": "unknown", "description": "", "ongoing": [],
           "incidents_30d": 0, "downtime_30d_min": 0.0, "recent": [],
           "live_api": cfg["api"] if cfg.get("cors") else ""}
    ml = _get_json(cfg["api"])
    mons = (ml.get("psp") or {}).get("monitors") or []
    counts = (ml.get("statistics") or {}).get("counts") or {}
    down = counts.get("down", 0)
    total = counts.get("total", len(mons))
    res["indicator"] = "none" if not down else (
        "major" if down >= max(total // 4, 2) else "minor")
    res["description"] = (f"{counts.get('up', total - down)}/{total} "
                          f"monitors up")
    # true 30d downtime: average of per-monitor 30d uptime ratios
    ratios = []
    for m in mons:
        try:
            ratios.append(float((m.get("30dRatio") or {}).get("ratio")))
        except (TypeError, ValueError):
            continue
    if ratios:
        avg = sum(ratios) / len(ratios)
        res["downtime_30d_min"] = round((100 - avg) / 100 * 30 * 1440, 1)
    if down:
        res["ongoing"] = [m.get("name", "monitor") for m in mons
                          if m.get("statusClass") not in ("success",)][:5]
    if cfg.get("events"):
        ev = _get_json(cfg["events"]).get("results") or []
        downs = [e for e in ev if e.get("label") == "down"]
        res["incidents_30d"] = len(downs)      # 7-day window (feed limit)
        for e in downs[:5]:
            m = re.search(r"(\d+)", e.get("duration") or "")
            res["recent"].append({
                "name": f"{e.get('monitor', 'monitor')} down",
                "impact": "minor",
                "start": e.get("timeGMT", ""),
                "minutes": int(m.group(1)) if m else 0,
                "resolved": True})
    return res


def _instatus(vendor, cfg):
    """Instatus summary.json: {"page": ..., "activeIncidents": [...]}. Less
    history than Statuspage; incidents computed from what it exposes."""
    now = utcnow().replace(tzinfo=dt.timezone.utc)
    win_start = now - dt.timedelta(days=WINDOW_DAYS)
    res = {"vendor": vendor, "page": cfg.get("page", ""), "kind": cfg["kind"],
           "indicator": "none", "description": "All systems operational",
           "ongoing": [], "incidents_30d": 0, "downtime_30d_min": 0.0,
           "recent": [], "live_api": ""}
    data = _get_json(cfg["api"])
    active = data.get("activeIncidents") or []
    if active:
        res["indicator"] = "major"
        res["description"] = active[0].get("name", "Active incident")
        res["ongoing"] = [a.get("name", "incident") for a in active]
    for i in (data.get("incidents") or []):
        created = _parse_ts(i.get("started") or i.get("createdAt"))
        resolved = _parse_ts(i.get("resolvedAt"))
        if not created:
            continue
        end = resolved or now
        if end < win_start:
            continue
        mins = _overlap_minutes(created, end, win_start, now)
        if mins <= 0:
            continue
        res["incidents_30d"] += 1
        res["downtime_30d_min"] += mins
    res["downtime_30d_min"] = round(res["downtime_30d_min"], 1)
    return res


def collect_status():
    """Returns (status_by_vendor, problems). Vendors with kind 'none' get an
    explicit no-status-page record rather than being skipped."""
    out, problems = {}, []
    for vendor, cfg in STATUS_SOURCES.items():
        try:
            if cfg["kind"] == "statuspage":
                out[vendor] = _statuspage(vendor, cfg)
            elif cfg["kind"] == "uptimerobot":
                out[vendor] = _uptimerobot(vendor, cfg)
            elif cfg["kind"] == "instatus":
                out[vendor] = _instatus(vendor, cfg)
            else:
                out[vendor] = {"vendor": vendor, "page": cfg.get("page", ""),
                               "kind": "none", "indicator": "nopage",
                               "description": "no public status page",
                               "ongoing": [], "incidents_30d": 0,
                               "downtime_30d_min": 0.0, "recent": []}
        except Exception as exc:
            problems.append(f"status — {vendor}: {exc}")
    return out, problems


def fmt_downtime(minutes):
    if minutes <= 0:
        return "0m"
    h, m = divmod(round(minutes), 60)
    return f"{h}h {m:02}m" if h else f"{m}m"


def main():
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    status, problems = collect_status()
    for v, s in status.items():
        print(f"{v:14} [{s['indicator']:8}] {s['description']}  "
              f"30d: {s['incidents_30d']} incidents, "
              f"{fmt_downtime(s['downtime_30d_min'])} downtime")
        for r in s["recent"]:
            print(f"    - {r['start']} [{r['impact']}] {r['name']} "
                  f"({fmt_downtime(r['minutes'])})")
    for p in problems:
        print("  check:", p)


if __name__ == "__main__":
    main()
