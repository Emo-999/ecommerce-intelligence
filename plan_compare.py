#!/usr/bin/env python3
"""
plan_compare.py
===============
The *analytical* layer on top of pricing_monitor's raw fingerprints:
structured plan -> price extraction per vendor, normalised to EUR, compared
against CloudCart's own plans, and diffed run-over-run at PLAN level
("Shopify Grow 56 -> 59") instead of token level.

Per-vendor extractors parse the RAW page HTML (no JS) using recipes that were
extracted and independently re-verified against the live pages on 2026-08-07.
Every extractor is wrapped: a failure degrades to a SOURCES TO CHECK entry,
never a crash. Geo notes: all anchors chosen to be geo-stable from US CI
(Shopify pinned to /bg/, Ecwid embeds all regions, Shift4Shop's US and non-US
bodies are identical, Wix uses its own price API with US fallback).

Run standalone for a quick text matrix:  python plan_compare.py
"""

import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

from pricing_monitor import UA, fetch_html
from report_style import bg_num, utcnow

# USD->EUR reference rate; override with env FX_USD_EUR.
# Default = ECB reference rate on 2026-08-07 (via frankfurter.app).
FX_USD_EUR_DEFAULT = 0.87

CC = "CloudCart"          # baseline vendor name used across the module


def fx_usd_eur():
    try:
        return float(os.environ.get("FX_USD_EUR") or FX_USD_EUR_DEFAULT)
    except ValueError:
        return FX_USD_EUR_DEFAULT


def to_eur(amount, currency):
    """Normalise a monthly price to EUR. Returns (eur_value, approximate?)."""
    if amount is None:
        return None, False
    if currency == "EUR":
        return float(amount), False
    if currency == "USD":
        return float(amount) * fx_usd_eur(), True
    return None, False            # unknown currency: don't guess


def _num(s):
    """'2 100' / '2,100.00' / '1,9' / '39' -> float (EU + US formats)."""
    s = re.sub(r"[\s  ]", "", str(s))
    if "," in s and "." in s:
        s = s.replace(",", "") if s.rfind(".") > s.rfind(",") else \
            s.replace(".", "").replace(",", ".")
    elif "," in s:
        tail = s.split(",")[-1]
        s = s.replace(",", "." if len(tail) <= 2 else "")
    return float(s)


def _sort_plans(plans):
    """Cheapest -> priciest by EUR-normalised price; quote-only plans last."""
    def key(p):
        val = p.get("annual") if p.get("annual") is not None else p.get("monthly")
        eur, _ = to_eur(val, p["currency"])
        return eur if eur is not None else float("inf")
    plans.sort(key=key)
    return plans


# --------------------------------------------------------------------------
# Extractors. Each takes the page's raw HTML and returns plans
# cheapest->priciest: {"name", "monthly", "annual", "currency", "note"}
# where monthly/annual are per-month prices (billed monthly / billed
# annually) as floats, or None when not offered/shown.
# --------------------------------------------------------------------------
def _cloudcart(html):
    """Cards: div.cc-cards__item[data-mapping][data-months], price in
    span.js-price-value. months: 1=monthly, 12=annual (first-year promo)."""
    slug_names = {"entry-pack": "Baby Pack", "starter-pack-2": "Starter Pack",
                  "cc-pro-2": "CC Pro", "cc-master": "CC Master"}
    marks = list(re.finditer(r'data-mapping="([\w-]+)"\s+data-months="(\d+)"',
                             html))
    per = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(html)
        pm = re.search(r'js-price-value[^>]*>\s*(\d+)\s*<', html[m.start():end])
        if pm:
            per.setdefault(m.group(1), {})[int(m.group(2))] = float(pm.group(1))
    plans = []
    for slug, name in slug_names.items():
        d = per.get(slug)
        if d:
            plans.append({"name": name, "monthly": d.get(1), "annual": d.get(12),
                          "currency": "EUR",
                          "note": "0% transaction fee; annual price is a "
                                  "first-year promo"})
    if not plans:
        raise ValueError("no CloudCart plan cards matched")
    if "BGN" in html or "лв" in html:
        raise ValueError("page shows BGN again — currency assumption broken")
    return _sort_plans(plans)


def _shopify(html):
    """BG page. Annual-billing prices from headline cards; monthly-billing
    prices from the comparison table row anchored on 'Плащайте месечно'."""
    annual = {}
    for m in re.finditer(
            r'<p>(Basic|Grow|Advanced|Plus)</p><p>'
            r'(?:<small class="text-xs">от</small>)?\s*(?:<!--\s*-->)?\s*'
            r'([\d\s ]+?)\s*€', html):
        annual[m.group(1)] = _num(m.group(2))
    monthly = {}
    # Anchor on the <th> variant — the phrase also appears in prose and
    # in an RSC JSON blob whose slices contain unrelated text-t8 spans.
    i = html.find("Плащайте месечно</span></th>")
    if i != -1:
        row = html[i:html.find("</tr>", i)]
        cells = re.findall(r'<span class="text-t8">([^<]*?)</span>', row)
        if len(cells) != 4:            # Basic, Grow, Advanced, Plus — in order
            cells = []
        for name, cell in zip(["Basic", "Grow", "Advanced", "Plus"], cells):
            pm = re.search(r'([\d\s ]+(?:,\d+)?)\s*€', cell)
            if pm:
                monthly[name] = _num(pm.group(1))
    plans = []
    for name in ("Basic", "Grow", "Advanced"):
        if name in annual or name in monthly:
            plans.append({"name": name, "monthly": monthly.get(name),
                          "annual": annual.get(name), "currency": "EUR",
                          "note": ""})
    if "Plus" in annual or "Plus" in monthly:
        plans.append({"name": "Plus",
                      "monthly": annual.get("Plus") or monthly.get("Plus"),
                      "annual": None, "currency": "EUR",
                      "note": "from-price; no annual option"})
    if not plans:
        raise ValueError("no Shopify plans matched")
    return _sort_plans(plans)


def _bigcommerce(html):
    """Makeswift JSON blob: '"annualPrice":{"value":"$29"}' etc., exactly 4 of
    each; plan name = last Core/Growth/Scale/Performance text before it."""
    ann = [(m.start(), m.group(1)) for m in
           re.finditer(r'"annualPrice":\{"value":"([^"]+)"', html)]
    mon = [m.group(1) for m in
           re.finditer(r'"monthlyPrice":\{"value":"([^"]+)"', html)]
    names = [(m.start(), m.group(1)) for m in
             re.finditer(r'"text":"(Core|Growth|Scale|Performance)"', html)]

    def parse(v):
        try:
            return float(v.replace("$", "").replace(",", ""))
        except (ValueError, AttributeError):
            return None

    plans = []
    for i, (pos, aval) in enumerate(ann):
        name = None
        for npos, nname in names:
            if npos < pos:
                name = nname
            else:
                break
        a = parse(aval)
        mo = parse(mon[i]) if i < len(mon) else None
        note = ""
        if a is None and mo is None:
            fl = re.search(r'starting at \$([\d,]+) per month, billed annually',
                           html)
            note = (f"custom; from ${fl.group(1)}/mo annually" if fl
                    else "custom pricing")
        plans.append({"name": name or f"Tier {i + 1}", "monthly": mo,
                      "annual": a, "currency": "USD", "note": note})
    if not plans:
        raise ValueError("Makeswift price blob not found")
    return _sort_plans(plans)


def _wix(html):
    """Tier A: Wix's own live Prices collection (2 requests, US row = the
    fallback Wix itself serves Bulgaria). Tier B: SSR spans on /plans HTML."""
    try:
        hdr = {"User-Agent": UA}
        t = requests.get("https://www.wix.com/plans/_api/v1/access-tokens",
                         headers=hdr, timeout=25).json()
        instance = t["apps"]["675bbcef-18d8-41f5-800e-131ec9e08762"]["instance"]
        r = requests.post(
            "https://www.wix.com/_api/cloud-data/v2/items/query",
            headers={**hdr, "Authorization": instance,
                     "Content-Type": "application/json"},
            json={"dataCollectionId": "Prices",
                  "query": {"paging": {"limit": 200}}, "environment": "LIVE"},
            timeout=25).json()
        rows = {it["data"]["title"]: it["data"] for it in r["dataItems"]}
        row = rows.get("US") or next(iter(rows.values()))
        cur = row.get("currencyCode", "USD")
        plans = []
        for key, name in [("light", "Light"), ("core", "Core"),
                          ("business", "Business"),
                          ("businessElite", "Business Elite")]:
            plans.append({"name": name, "monthly": None,
                          "annual": float(row[key]), "currency": cur,
                          "note": "yearly billing only (paid upfront)"})
        return _sort_plans(plans)
    except Exception:
        pass                                   # fall back to SSR HTML below

    price_re = re.compile(
        r'wixui-rich-text__text">\$</span>.{0,600}?'
        r'wixui-rich-text__text">(\d+(?:\.\d{1,2})?)</span>', re.S)
    plans = []
    for name in ("Business Elite", "Business", "Core", "Light"):
        vals = set()
        for m in re.finditer(">" + re.escape(name) + "<", html):
            pm = price_re.search(html, m.end(), m.end() + 2500)
            if pm:
                vals.add(float(pm.group(1)))
        if len(vals) > 1:
            raise ValueError(f"Wix {name}: inconsistent prices {sorted(vals)}")
        if vals:
            plans.append({"name": name, "monthly": None, "annual": vals.pop(),
                          "currency": "USD",
                          "note": "yearly billing only (paid upfront)"})
    if not plans:
        raise ValueError("Wix: API and SSR fallback both empty")
    return _sort_plans(plans)


def _squarespace(html):
    """JSON-LD block (translate=no) -> @graph SoftwareApplication nodes.
    EUR offers preferred; Plus currently exists in USD only."""
    data = None
    m = re.search(r'<script type="application/ld\+json" translate="no">'
                  r'(.*?)</script>', html, re.S)
    if m:
        try:
            data = json.loads(m.group(1))
        except ValueError:
            data = None
    if not data or "@graph" not in data:
        for block in re.findall(
                r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                html, re.S):
            try:
                d = json.loads(block)
            except ValueError:
                continue
            if isinstance(d.get("@graph"), list) and any(
                    n.get("@type") == "SoftwareApplication"
                    for n in d["@graph"]):
                data = d
                break
    if not data:
        raise ValueError("JSON-LD pricing block not found")

    plans = []
    for n in data["@graph"]:
        if n.get("@type") != "SoftwareApplication":
            continue
        name = n.get("name", "").removeprefix("Squarespace ")
        offers = n.get("offers") or []
        if isinstance(offers, dict):
            offers = [offers]
        sel, cur = [], None
        for cur in ("EUR", "USD"):
            sel = [o for o in offers if o.get("priceCurrency") == cur]
            if sel:
                break
        monthly = annual = None
        for o in sel:
            dur = (o.get("priceSpecification") or {}).get("billingDuration")
            price = float(o["price"])
            if dur == "P1M":
                monthly = price
            elif dur == "P1Y":
                annual = round(price / 12, 2)   # P1Y price is the yearly total
        if monthly is None and annual is None:
            continue
        plans.append({"name": name, "monthly": monthly, "annual": annual,
                      "currency": cur,
                      "note": "USD only (no EUR offer)" if cur == "USD" else ""})
    if not plans:
        raise ValueError("no SoftwareApplication plans in JSON-LD")
    return _sort_plans(plans)


def _ecwid(html):
    """First div.pricing-block only (a lower comparison table repeats the same
    spans); per card: h2 name + hidden price-EU spans for both cycles."""
    soup = BeautifulSoup(html, "html.parser")
    block = soup.select_one("div.pricing-block")
    if not block:
        raise ValueError("pricing-block not found")
    plans = []
    for card in block.select("div.card"):
        h2 = card.select_one("div.card__details h2")
        if not h2:
            continue

        def val(sel, _card=card):
            el = _card.select_one(sel)
            return float(el.get_text(strip=True)) if el else None

        monthly = val("span.price__sum.monthly span.price-EU")
        annual = val("span.price__sum.annual span.price-EU")
        if monthly is None and annual is None:
            continue
        plans.append({"name": h2.get_text(strip=True), "monthly": monthly,
                      "annual": annual, "currency": "EUR", "note": ""})
    if not plans:
        raise ValueError("no Ecwid plan cards parsed")
    return _sort_plans(plans)


def _shift4shop(html):
    """Single-plan page; the unique 'enterprise-grade plan for $X/month'
    callout is the price anchor (US and non-US bodies are identical)."""
    m = re.search(r'enterprise-grade plan for\s*'
                  r'\$([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*/\s*month', html)
    if not m:
        raise ValueError("plan price anchor not found")
    return [{"name": "End-to-End eCommerce",
             "monthly": float(m.group(1).replace(",", "")), "annual": None,
             "currency": "USD",
             "note": "single plan; US storefronts get it free with Shift4 "
                     "Payments"}]


def _woocommerce(html):
    """Woo е GPL софтуер без ценова страница за скрейпване: колоната показва
    реалната издръжка (проверена 2026-08), не етикета „безплатно"."""
    return [
        {"name": "Woo Core", "monthly": 0.0, "annual": None,
         "currency": "EUR",
         "note": "безплатен GPL софтуер; хостинг, домейн и разширения се "
                 "плащат отделно"},
        {"name": "Реална издръжка", "monthly": None, "annual": None,
         "currency": "EUR",
         "note": "≈ 30–75 €/мес. за малък магазин: managed хостинг 18–45 €, "
                 "WPML 99 €/г., B2B 157 €/г.; WooPayments 1,5% + 0,25 €"},
    ]


EXTRACTORS = {
    CC:            ("https://cloudcart.com/pricing", _cloudcart),
    "Shopify":     ("https://www.shopify.com/bg/pricing", _shopify),
    "BigCommerce": ("https://www.bigcommerce.com/pricing/", _bigcommerce),
    "Wix":         ("https://www.wix.com/plans", _wix),
    "WooCommerce": ("https://woocommerce.com/pricing/", _woocommerce),
    "Squarespace": ("https://www.squarespace.com/pricing", _squarespace),
    "Ecwid":       ("https://www.ecwid.com/pricing", _ecwid),
    "Shift4Shop":  ("https://www.shift4shop.com/pricing.htm", _shift4shop),
}


# --------------------------------------------------------------------------
# Collection + plan-level diffing
# --------------------------------------------------------------------------
def collect_plans():
    """Fetch every vendor page and run its extractor.
    Returns (plans_by_vendor, problems)."""
    plans, problems = {}, []
    for vendor, (url, fn) in EXTRACTORS.items():
        try:
            got = fn(fetch_html(url))
            if not got:
                raise ValueError("extractor returned no plans")
            plans[vendor] = {"url": url, "plans": got}
        except Exception as exc:
            problems.append(f"plan extraction — {vendor}: {exc}")
    return plans, problems


def diff_plans(prev, current):
    """Compare plan snapshots. Returns change dicts:
    {"vendor", "plan", "field", "old", "new", "currency"}."""
    changes = []
    for vendor, cur in current.items():
        old = (prev or {}).get(vendor, {}).get("plans")
        if not old:
            continue                       # first sighting: baseline, no diff
        old_by_name = {p["name"]: p for p in old}
        for p in cur["plans"]:
            o = old_by_name.get(p["name"])
            if not o:
                changes.append({"vendor": vendor, "plan": p["name"],
                                "field": "new plan", "old": None,
                                "new": p.get("annual") or p.get("monthly"),
                                "currency": p["currency"]})
                continue
            for field in ("monthly", "annual"):
                if o.get(field) != p.get(field):
                    changes.append({"vendor": vendor, "plan": p["name"],
                                    "field": field, "old": o.get(field),
                                    "new": p.get(field),
                                    "currency": p["currency"]})
        for name in old_by_name:
            if name not in {p["name"] for p in cur["plans"]}:
                changes.append({"vendor": vendor, "plan": name,
                                "field": "plan removed", "old": None,
                                "new": None, "currency": ""})
    return changes


# --------------------------------------------------------------------------
# Rendering — comparison matrix + entry-price bars (CloudCart-brand,
# palette validated: coral #FF4B51 for us, #5C7BC0 for competitors)
# --------------------------------------------------------------------------
def _fmt(p):
    """Цена в клетка: валутата е след числото, по конвенцията на системата."""
    val = p.get("annual") if p.get("annual") is not None else p.get("monthly")
    if val is None:
        return p.get("note") or "по договаряне"
    sym = {"EUR": "€", "USD": "$"}.get(p["currency"], p["currency"])
    prefix = "от " if "from" in (p.get("note") or "") else ""
    txt = f"{prefix}{bg_num(val, 2 if val % 1 else 0)} {sym}"
    eur, approx = to_eur(val, p["currency"])
    if approx and eur is not None:
        txt += f" <span class=approx>≈ {bg_num(eur)} €</span>"
    return txt


def _entry_eur(plans):
    for p in plans:
        val = p.get("annual") if p.get("annual") is not None else p.get("monthly")
        if val:
            eur, _ = to_eur(val, p["currency"])
            if eur:
                return eur
    return None


def render_matrix(plans_by_vendor):
    """Vendors × plan-tier columns, CloudCart first and highlighted."""
    if not plans_by_vendor:
        return ""
    vendors = [CC] + sorted(v for v in plans_by_vendor if v != CC)
    vendors = [v for v in vendors if v in plans_by_vendor]
    ncols = min(max(len(plans_by_vendor[v]["plans"]) for v in vendors), 5)
    cc_entry = _entry_eur(plans_by_vendor[CC]["plans"]) \
        if CC in plans_by_vendor else None

    head = "".join(f"<th>{t}</th>" for t in
                   ["Платформа"] + [f"Ниво {i + 1}" for i in range(ncols)])
    rows = []
    for v in vendors:
        info = plans_by_vendor[v]
        cells = [f"<td class=vname><a href='{info['url']}' target=_blank>"
                 f"{v}</a></td>"]
        plist = info["plans"][:ncols]
        for i in range(ncols):
            if i >= len(plist):
                cells.append("<td class=na>—</td>")
                continue
            p = plist[i]
            delta = ""
            if v != CC and i == 0 and cc_entry:
                val = p.get("annual") if p.get("annual") is not None \
                    else p.get("monthly")
                eur, _ = to_eur(val, p["currency"])
                if eur:
                    pct = (eur - cc_entry) / cc_entry * 100
                    cls = "up" if pct > 0 else "down"
                    delta = (f"<span class='delta {cls}'>"
                             f"{'+' if pct > 0 else ''}{pct:.0f} % спрямо нас"
                             f"</span>")
            cells.append(f"<td><div class=pname>{p['name']}</div>"
                         f"<div class=pprice>{_fmt(p)}</div>{delta}</td>")
        cls = " class=ours" if v == CC else ""
        rows.append(f"<tr{cls}>{''.join(cells)}</tr>")

    return ("<div class=tablewrap><table class=matrix>"
            f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody>"
            "</table></div>"
            "<div class=basis>Цени на месец при годишно плащане, където се "
            "предлага; доларовите цени са преизчислени по курс ≈ "
            + f"{fx_usd_eur():.2f}".replace(".", ",") +
            " USD→EUR (променя се с FX_USD_EUR). Нивата подреждат плановете "
            "на всяка платформа от най-евтин към най-скъп, без претенция за "
            "функционално съответствие. Зелено: входният план на конкурента "
            "е по-скъп от нашия.</div>")


def render_entry_bars(plans_by_vendor):
    """Horizontal bar comparison of cheapest paid plan (EUR/mo)."""
    entries = []
    for v, info in plans_by_vendor.items():
        for p in info["plans"]:
            val = p.get("annual") if p.get("annual") is not None \
                else p.get("monthly")
            if val:
                eur, approx = to_eur(val, p["currency"])
                if eur:
                    entries.append((v, p["name"], eur, approx))
                break
    if len(entries) < 2:
        return ""
    entries.sort(key=lambda e: e[2])
    top = max(e[2] for e in entries)
    bars = []
    for v, plan, eur, approx in entries:
        w = max(eur / top * 100, 2)
        cls = "ours" if v == CC else ""
        label = f"{v} · {plan}"
        val = f"{'≈ ' if approx else ''}{bg_num(eur)} €/мес."
        bars.append(
            f"<div class=barrow title='{label}: {val}'>"
            f"<div class=barlabel>{label}</div>"
            f"<div class=bartrack><div class='bar {cls}' "
            f"style='width:{w:.1f}%'></div>"
            f"<span class=barval>{val}</span></div></div>")
    return ("<div class=bars>" + "".join(bars) + "</div>"
            "<div class=basis>Най-евтиният платен план на всяка платформа, "
            "на месец при годишно плащане.</div>")


def render_plan_changes(changes):
    if not changes:
        return ("<div class=empty>Няма промени в плановете от предното "
                "събиране.</div>")
    out = []
    for c in changes:
        sym = {"EUR": "€", "USD": "$"}.get(c["currency"], "")
        if c["field"] in ("monthly", "annual"):
            basis = ("месечно плащане" if c["field"] == "monthly"
                     else "годишно плащане")
            old = f"{bg_num(c['old'])} {sym}" if c["old"] is not None else "–"
            new = f"{bg_num(c['new'])} {sym}" if c["new"] is not None else "–"
            body = (f"<span class=name>{c['vendor']} {c['plan']}</span> "
                    f"<span class=chg>{old} → {new}</span> "
                    f"<span class=sub>({basis})</span>")
        else:
            lbl = {"new plan": "нов план",
                   "plan removed": "премахнат план"}.get(c["field"], c["field"])
            body = (f"<span class=name>{c['vendor']} {c['plan']}</span> "
                    f"<span class=chg>{lbl}</span>")
        out.append(f"<div class=card>{body}</div>")
    return "".join(out)


# --------------------------------------------------------------------------
def load_plan_state(state):
    return state.get("_plans", {}).get("vendors", {})


def save_plan_state(state, plans_by_vendor):
    state["_plans"] = {"vendors": plans_by_vendor,
                       "checked": utcnow().isoformat(timespec="seconds")}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    plans, problems = collect_plans()
    for v, info in plans.items():
        print(f"\n{v}  ({info['url']})")
        for p in info["plans"]:
            print(f"  {p['name']:20} monthly={p['monthly']} "
                  f"annual={p['annual']} {p['currency']}  {p['note']}")
    for pr in problems:
        print("  check:", pr)


if __name__ == "__main__":
    main()
