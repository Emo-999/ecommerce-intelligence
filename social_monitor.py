#!/usr/bin/env python3
"""
social_monitor.py
=================
Competitor marketing/content activity from sources that are actually
machine-readable without credentials:

  * YouTube: every channel has a public RSS feed
    (youtube.com/feeds/videos.xml?channel_id=UC...) -> publishing cadence,
    latest video, product-launch signals in titles.
  * Ad libraries: Meta Ad Library and Google Ads Transparency Center are
    login/JS-walled for server-side scraping, so by default we surface
    verified DEEP LINKS per vendor (one click from the dashboard to their
    live ad activity, incl. EU country reach in Meta's UI — DSA data).
    If META_AD_TOKEN is set (Meta Graph API user token), ad counts and EU
    reach are fetched programmatically via the ads_archive endpoint.

SOCIAL_SOURCES filled with live-verified handles/ids (2026-08-08).
"""

import datetime as dt
import os
import re

import feedparser
import requests

from pricing_monitor import UA
from report_style import utcnow

WINDOW_DAYS = 30

# Launch-ish keywords worth flagging in video titles.
LAUNCH_RE = re.compile(
    r"\b(launch|new|introduc|announc|ai|checkout|pricing|pos|b2b|update)",
    re.IGNORECASE)

_MAL = ("https://www.facebook.com/ads/library/?active_status=all&ad_type=all"
        "&country=ALL&view_all_page_id=")
_GAT = "https://adstransparency.google.com"

# vendor -> handles/ids. All YouTube channel ids + links live-verified
# 2026-08-08 (Ecwid's @Ecwid handle is an unrelated personal channel — the id
# below is the official "Ecwid by Lightspeed" channel; Shift4Shop's id is the
# one shift4shop.com's own footer links). meta_page_id = numeric FB page id
# for Ad Library deep links / API. google_ar = Ads Transparency advertiser id
# where confidently identified (BigCommerce/Ecwid/Shift4Shop have none —
# domain-search links instead).
SOCIAL_SOURCES = {
    "CloudCart": {
        "youtube": "UCZpAaKJ0AgLf6jU3Cs1-WIQ",
        "x": "https://x.com/cloudcart",
        "linkedin": "https://www.linkedin.com/company/cloudcart",
        "facebook": "https://www.facebook.com/cloudcart"},
    "Shopify": {
        "youtube": "UCIv38OrggTu3vNkCAo96-CQ",
        "x": "https://x.com/shopify",
        "linkedin": "https://www.linkedin.com/company/shopify",
        "facebook": "https://www.facebook.com/shopify",
        "meta_page_id": "100064482022452",
        "meta_ads": _MAL + "100064482022452",
        "google_ads": _GAT + "/advertiser/AR01625195283841286145?region=anywhere",
        "google_query": "Shopify", "google_ar": "AR01625195283841286145"},
    "BigCommerce": {
        "youtube": "UCgIZY6oj1XHT_FGSQtvLSLg",
        "x": "https://x.com/BigCommerce",
        "linkedin": "https://www.linkedin.com/company/bigcommerce",
        "facebook": "https://www.facebook.com/BigCommerce",
        "meta_page_id": "100064631536174",
        "meta_ads": _MAL + "100064631536174",
        "google_ads": _GAT + "/?region=anywhere&domain=bigcommerce.com"},
    "Wix": {
        "youtube": "UCx96GiJ3qYw2sHccPp5dY_g",
        "x": "https://x.com/wix",
        "linkedin": "https://www.linkedin.com/company/wix-com",
        "facebook": "https://www.facebook.com/wix",
        "meta_page_id": "100064617644523",
        "meta_ads": _MAL + "100064617644523",
        # Wix advertises via regional entities; the corporate WIX.COM LTD
        # advertiser id carries ~1 ad and would mislead — domain search only.
        "google_ads": _GAT + "/?region=anywhere&domain=wix.com"},
    "Squarespace": {
        "youtube": "UCYNxoffNZ2fXLGggyhl8Yqg",
        "x": "https://x.com/squarespace",
        "linkedin": "https://www.linkedin.com/company/squarespace",
        "facebook": "https://www.facebook.com/squarespace",
        "meta_page_id": "100064536500635",
        "meta_ads": _MAL + "100064536500635",
        "google_ads": _GAT + "/advertiser/AR03332077890714992641?region=anywhere",
        "google_query": "Squarespace", "google_ar": "AR03332077890714992641"},
    "Ecwid": {
        "youtube": "UCsoUdGzYRL8yK8ixBafhkKQ",
        "x": "https://x.com/ecwid",
        "linkedin": "https://www.linkedin.com/company/ecwid",
        "facebook": "https://www.facebook.com/ecwid",
        "meta_page_id": "100064707518285",
        "meta_ads": _MAL + "100064707518285",
        "google_ads": _GAT + "/?region=anywhere&domain=ecwid.com"},
    "WooCommerce": {
        "youtube": "UC63GQg3s2QcgOpMzsiF6wwQ",
        "x": "https://x.com/WooCommerce",
        "linkedin": "https://www.linkedin.com/company/woocommerce/",
        "facebook": "https://www.facebook.com/woocommerce",
        "meta_page_id": "154986584179",
        "meta_ads": _MAL + "154986584179",
        "google_ads": _GAT + "/advertiser/AR00942462403386277889?region=anywhere",
        "google_query": "Automattic", "google_ar": "AR00942462403386277889"},
    "Shift4Shop": {
        "youtube": "UC_b1XyRX8gw093PS6rkU6FQ",
        "x": "https://x.com/Shift4Shop",
        "linkedin": "https://www.linkedin.com/company/shift4shop",
        "facebook": "https://www.facebook.com/3dcart",
        "meta_page_id": "61578480932403",
        "meta_ads": _MAL + "61578480932403",
        "google_ads": _GAT + "/?region=anywhere&domain=shift4shop.com"},
}


def _yt_feed(channel_id):
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def _collect_youtube(channel_id):
    cutoff = utcnow() - dt.timedelta(days=WINDOW_DAYS)
    feed = feedparser.parse(_yt_feed(channel_id))
    if not feed.entries:
        raise ValueError("YouTube RSS returned no entries")
    videos_30d, flagged = 0, []
    latest = None
    for e in feed.entries:
        t = e.get("published_parsed")
        when = dt.datetime(*t[:6]) if t else None
        title = (e.get("title") or "").strip()
        if latest is None:
            latest = {"title": title,
                      "date": when.strftime("%b %d") if when else "?",
                      "link": e.get("link", "")}
        if when and when >= cutoff:
            videos_30d += 1
            if LAUNCH_RE.search(title):
                flagged.append(title)
    return {"videos_30d": videos_30d, "latest_video": latest,
            "flagged_titles": flagged[:5],
            "channel": f"https://www.youtube.com/channel/{channel_id}"}


def _google_ads_count(query, ar_id):
    """Google Ads Transparency Center internal SearchSuggestions RPC — works
    server-side without auth and returns an active-ad-count RANGE per
    advertiser. Undocumented endpoint: wrapped so a shape change degrades to
    a SOURCES TO CHECK entry, not a crash."""
    import json as _json
    r = requests.post(
        "https://adstransparency.google.com/anji/_/rpc/SearchService/"
        "SearchSuggestions?authuser=",
        headers={"User-Agent": UA,
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"f.req": _json.dumps({"1": query, "2": 10})}, timeout=20)
    r.raise_for_status()
    for item in r.json().get("1", []):
        adv = item.get("1", {})
        if adv.get("2") == ar_id:
            rng = ((adv.get("4") or {}).get("2") or {})
            lo, hi = rng.get("1"), rng.get("2")
            if lo is not None:
                return {"lo": int(lo), "hi": int(hi or lo),
                        "region": adv.get("3", "")}
    raise ValueError(f"advertiser {ar_id} not in suggestions for '{query}'")


def _meta_api_ads(page_id, token):
    """Meta ads_archive: active ad count + EU reach for a page. Requires a
    Graph API token with Ad Library API access (user opts in via env)."""
    r = requests.get(
        "https://graph.facebook.com/v21.0/ads_archive",
        params={"access_token": token, "search_page_ids": page_id,
                "ad_active_status": "ACTIVE", "ad_type": "ALL",
                "ad_reached_countries": '["BG","DE","FR","GB","US"]',
                "fields": "id,eu_total_reach,ad_delivery_start_time",
                "limit": 100},
        headers={"User-Agent": UA}, timeout=25)
    r.raise_for_status()
    data = r.json().get("data", [])
    reach = sum(a.get("eu_total_reach") or 0 for a in data)
    return {"active_ads": len(data), "eu_reach_sample": reach}


def collect_social():
    """Returns (social_by_vendor, problems)."""
    out, problems = {}, []
    token = os.environ.get("META_AD_TOKEN", "")
    for vendor, cfg in SOCIAL_SOURCES.items():
        rec = {"links": {}, "videos_30d": None, "latest_video": None,
               "flagged_titles": [], "channel": "", "ads_api": None,
               "google_count": None}
        for key in ("x", "linkedin", "facebook", "meta_ads", "google_ads"):
            if cfg.get(key):
                rec["links"][key] = cfg[key]
        try:
            if cfg.get("youtube"):
                rec.update(_collect_youtube(cfg["youtube"]))
        except Exception as exc:
            problems.append(f"social — {vendor} youtube: {exc}")
        if cfg.get("google_ar"):
            try:
                rec["google_count"] = _google_ads_count(cfg["google_query"],
                                                        cfg["google_ar"])
            except Exception as exc:
                problems.append(f"social — {vendor} google ads: {exc}")
        if token and cfg.get("meta_page_id"):
            try:
                rec["ads_api"] = _meta_api_ads(cfg["meta_page_id"], token)
            except Exception as exc:
                problems.append(f"social — {vendor} meta ads api: {exc}")
        out[vendor] = rec
    return out, problems


def main():
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    social, problems = collect_social()
    for v, s in social.items():
        lv = s.get("latest_video") or {}
        print(f"{v:14} videos_30d={s.get('videos_30d')} "
              f"latest={lv.get('date')} {str(lv.get('title'))[:60]}")
        for t in s.get("flagged_titles", []):
            print(f"    ! {t[:80]}")
    for p in problems:
        print("  check:", p)


if __name__ == "__main__":
    main()
