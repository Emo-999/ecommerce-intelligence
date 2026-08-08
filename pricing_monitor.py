#!/usr/bin/env python3
"""
pricing_monitor.py
==================
Catches the changes RSS feeds can't: silent edits to competitor PRICING pages.

How it works — a "before/after photo" of each pricing page:
  1. Fetch the page.
  2. Extract every currency amount on it (the price "fingerprint").
  3. Compare against the fingerprint saved from last run (price_state.json).
  4. Report prices ADDED / REMOVED per competitor. First sighting = baseline.

--------------------------------------------------------------------------
QUICK START
--------------------------------------------------------------------------
    pip install requests beautifulsoup4
    python pricing_monitor.py            # 1st run: captures baselines
    python pricing_monitor.py            # later runs: reports what moved
    -> writes pricing_report.html + updates price_state.json

AUTOMATE (weekly is plenty — pricing changes aren't daily):
    0 8 * * 1 cd /path && /usr/bin/python3 pricing_monitor.py

--------------------------------------------------------------------------
HONEST LIMITATION — read this
--------------------------------------------------------------------------
Pricing pages are often JS-rendered and region-specific. Plain requests()
sees the raw HTML, which for some sites won't contain the prices (they load
via JavaScript) or shows a different region's currency than yours.
  * Any page with 0 prices in raw HTML automatically retries through a
    headless browser (fetch_rendered) IF Playwright is installed:
        pip install playwright && playwright install chromium
    Without Playwright the page is flagged "NO PRICES DETECTED" instead.
  * Region: prefer region-specific URLs in PRICING_PAGES (e.g. Shopify's
    /bg/pricing); most sites geo-detect and ignore query params. REGION_HINT
    still exists for sites that do accept a param.
"""

import argparse
import html as html_mod
import json
import os
import re
import sys

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Missing deps. Run:  pip install requests beautifulsoup4")

from report_style import shell, utcnow

STATE_FILE = "price_state.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")
REGION_HINT = ""   # e.g. "?country=BG" appended to URLs if a site supports it
# Prefer region-specific URLs in PRICING_PAGES over REGION_HINT — most sites
# geo-detect and ignore query params. We track EUR/BGN pages where they exist
# (user is in Bulgaria); geo-IP pages will show whatever the runner's region is.

# --------------------------------------------------------------------------
# PRICING PAGES  ->  (competitor name, url)
# Verify each resolves for YOUR region on first run; prune what you don't track.
# --------------------------------------------------------------------------
PRICING_PAGES = [
    # URLs verified 2026-08. Region notes (user is in Bulgaria; BG uses EUR since 2026):
    ("Shopify",       "https://www.shopify.com/bg/pricing"),    # /bg/ pins EUR page even from US CI runners
    ("BigCommerce",   "https://www.bigcommerce.com/pricing/"),  # USD-only worldwide (no EUR variant exists)
    ("Wix eCommerce", "https://www.wix.com/plans"),             # SSR spans carry USD defaults; plan_compare has the real API
    ("Squarespace",   "https://www.squarespace.com/pricing"),   # prices only in JSON-LD -> extract_jsonld_prices
    ("Ecwid",         "https://www.ecwid.com/pricing"),         # embeds all regions incl. EUR in hidden spans
    ("Shift4Shop",    "https://www.shift4shop.com/pricing.htm"),# geo-routes (?country=notUS from BG, US page from CI)
    # Adobe Commerce / Magento = quote-only, no public prices — omitted on purpose.
]

# Currency amounts we recognise: $39  €105  £29  $2,300  12 000 €  лв.  BGN/EUR/USD/GBP
# _NUM's first branch groups NBSP thousands separators ("12 000" on Shopify's
# BG page) so it fingerprints as 12000€ instead of a bare 000€. Regular spaces
# deliberately do NOT group: pages like Ecwid flatten adjacent per-region
# prices into "99 450 €", which must stay two numbers, not merge into 99450.
_NUM = r"\d{1,3}(?:[  ]\d{3})+(?:[.,]\d{1,2})?|\d[\d.,]*"
# Alphabetic currency codes need word boundaries (IGNORECASE would otherwise
# turn "30 European countries" into a phantom token "30Eur" and false diffs).
_CODE_GUARD = r"(?![A-Za-zА-Яа-я])"
PRICE_RE = re.compile(
    r"(?:[$€£]|\b(?:лв\.?|USD|EUR|GBP|BGN))\s?(?:" + _NUM + r")"             # symbol first
    r"|(?:" + _NUM + r")\s?(?:[€£]|(?:лв\.?|EUR|GBP|BGN)" + _CODE_GUARD + r")",  # symbol after
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
def fetch_html(url):
    r = requests.get(url + REGION_HINT, headers={"User-Agent": UA}, timeout=25)
    r.raise_for_status()
    return r.text


def fetch_rendered(url):
    """Headless-browser fetch for JS-rendered pages. Needs:
    pip install playwright && playwright install chromium"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(user_agent=UA)
        page.goto(url + REGION_HINT, wait_until="networkidle", timeout=45000)
        rendered = page.content()
        b.close()
        return rendered


def _playwright_available():
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


def extract_prices(raw_html):
    """Return a sorted, de-duped set of normalised price tokens found on the page."""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    found = set()
    for m in PRICE_RE.findall(text):
        tok = re.sub(r"\s+", "", m)
        # normalise codes to symbols case-insensitively ("eur 25" == "EUR 25")
        tok = re.sub(r"usd", "$", tok, flags=re.IGNORECASE)
        tok = re.sub(r"eur", "€", tok, flags=re.IGNORECASE)
        tok = re.sub(r"gbp", "£", tok, flags=re.IGNORECASE)
        tok = re.sub(r"bgn", "лв", tok, flags=re.IGNORECASE)
        found.add(tok.rstrip(".,"))              # "$0." (sentence end) -> "$0"
    return sorted(found, key=lambda s: (len(s), s))


# Some pages (Squarespace) put prices only in schema.org JSON-LD, never in
# visible text. First currency below that yields offers wins for the page.
PREFERRED_CURRENCIES = ("EUR", "USD")
CURRENCY_SYMBOL = {"EUR": "€", "USD": "$", "GBP": "£", "BGN": "лв"}


def _fmt_amount(value):
    """25.00 -> '25', 14.5 -> '14.5', keep strings sane."""
    s = str(value).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s) and "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def extract_jsonld_prices(raw_html):
    """Harvest price/priceCurrency pairs from <script type=application/ld+json>."""
    soup = BeautifulSoup(raw_html, "html.parser")
    offers = []            # (currency, amount) tuples

    def walk(node):
        if isinstance(node, dict):
            price, cur = node.get("price"), node.get("priceCurrency")
            if price not in (None, "") and cur:
                offers.append((str(cur).upper(), _fmt_amount(price)))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            walk(json.loads(tag.string or ""))
        except (ValueError, TypeError):
            continue

    for cur in PREFERRED_CURRENCIES:
        picks = {amt for c, amt in offers if c == cur}
        if picks:
            sym = CURRENCY_SYMBOL.get(cur, cur)
            return sorted({f"{sym}{a}" for a in picks}, key=lambda s: (len(s), s))
    return []


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def run(pages):
    """Return a list of per-page result dicts and the updated state."""
    state = load_state()
    now = utcnow().isoformat(timespec="seconds")
    results = []

    for name, url in pages:
        res = {"name": name, "url": url, "status": None, "added": [],
               "removed": [], "count": 0, "rendered": False, "via": "text"}
        try:
            raw = fetch_html(url)
            prices = extract_prices(raw)
            # Fallback 1 (free): prices hidden in schema.org JSON-LD.
            if not prices:
                prices = extract_jsonld_prices(raw)
                if prices:
                    res["via"] = "json-ld"
        except Exception as exc:
            res["status"] = f"error: {exc}"
            results.append(res)
            continue

        # Fallback 2: 0 prices anywhere in raw HTML usually means JS-rendered.
        # Retry with a headless browser if Playwright is installed.
        if not prices and _playwright_available():
            try:
                rendered = fetch_rendered(url)
                prices = extract_prices(rendered) or extract_jsonld_prices(rendered)
                res["rendered"] = True
            except Exception as exc:
                res["status"] = f"error: headless fetch failed: {exc}"
                results.append(res)
                continue

        res["count"] = len(prices)
        if not prices:
            res["status"] = "no-prices"          # likely JS-rendered
            results.append(res)
            continue

        prev = state.get(url, {}).get("prices")
        if prev is None:
            res["status"] = "baseline"
        else:
            added = [p for p in prices if p not in prev]
            removed = [p for p in prev if p not in prices]
            res["added"], res["removed"] = added, removed
            res["status"] = "changed" if (added or removed) else "same"

        state[url] = {"name": name, "prices": prices, "checked": now}
        results.append(res)

    # Drop state for URLs no longer tracked (e.g. after a URL swap) so the
    # committed file stays an honest mirror of PRICING_PAGES. Keys starting
    # with "_" are other modules' state (plan_compare) — preserve them.
    tracked = {url for _, url in pages}
    state = {u: v for u, v in state.items()
             if u in tracked or u.startswith("_")}
    save_state(state)
    return results


# --------------------------------------------------------------------------
# HTML report — shared CloudCart-branded frame lives in report_style.py
# --------------------------------------------------------------------------
def render(results):
    now = utcnow().strftime("%Y-%m-%d %H:%M UTC")
    changed = [r for r in results if r["status"] == "changed"]
    subtitle = (f"{now} &middot; {len(results)} pages &middot; "
                f"<b style='color:#7A7AFF'>{len(changed)} changed</b>")
    out = []

    # Changed first (the whole point), then everything else compact.
    order = {"changed": 0, "baseline": 1, "no-prices": 2, "same": 3}
    for r in sorted(results, key=lambda x: order.get(x["status"], 9)):
        pill = {"changed": "CHANGED", "baseline": "baseline saved",
                "same": "no change", "no-prices": "no prices detected"
                }.get(r["status"], "error")
        pill_cls = "pill pill-hot" if r["status"] == "changed" else "pill"
        head = f"<span class=name>{html_mod.escape(r['name'])}</span>" \
               f"<span class='{pill_cls}'>{pill}</span>"
        body = ""
        if r["status"] == "changed":
            body += "<div class=chg>Price change detected</div>"
            body += "".join(f"<span class='tok tadd'>+ {html_mod.escape(p)}</span>"
                            for p in r["added"])
            body += "".join(f"<span class='tok trem'>&minus; {html_mod.escape(p)}</span>"
                            for p in r["removed"])
        elif r["status"] == "baseline":
            via = {"json-ld": " from JSON-LD", "text": ""}.get(r.get("via"), "")
            hl = " via headless browser" if r.get("rendered") else ""
            body = f"<div class=sub>Captured {r['count']} prices{via}{hl}. " \
                   f"Changes will show from next run.</div>"
        elif r["status"] == "no-prices":
            body = "<div class=sub>0 prices even after fallback — check the URL " \
                   "or region.</div>" if r.get("rendered") else \
                   "<div class=sub>0 prices in raw HTML — likely JS-rendered. " \
                   "Install Playwright to enable the automatic headless fallback " \
                   "(pip install playwright &amp;&amp; playwright install chromium).</div>"
        elif r["status"] == "same":
            body = f"<div class=sub>{r['count']} prices, unchanged.</div>"
        else:
            body = f"<div class=sub>{html_mod.escape(str(r['status']))}</div>"
        out.append(f"<div class=card>{head}{body}"
                   f"<div class=sub><a href='{html_mod.escape(r['url'])}' "
                   f"target=_blank>{html_mod.escape(r['url'])}</a></div></div>")
    return shell("Competitor pricing monitor", subtitle, "".join(out))


def main():
    if hasattr(sys.stdout, "reconfigure"):       # Windows cp1252 consoles/pipes
        sys.stdout.reconfigure(errors="replace") # 'лв' tokens must not crash print
    ap = argparse.ArgumentParser(description="Competitor pricing-change monitor")
    ap.add_argument("--out", default="pricing_report.html")
    args = ap.parse_args()

    results = run(PRICING_PAGES)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(render(results))

    changed = [r for r in results if r["status"] == "changed"]
    print(f"Wrote {args.out}  ({len(changed)} changed, {len(results)} pages)")
    for r in results:
        tag = r["status"].upper()
        extra = " (headless)" if r.get("rendered") else ""
        if r["status"] == "changed":
            extra += f"  +{r['added']} -{r['removed']}"
        print(f"  [{tag:10}] {r['name']}{extra}")


if __name__ == "__main__":
    main()
