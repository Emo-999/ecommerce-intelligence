#!/usr/bin/env python3
"""
ecommerce_monitor.py
====================
A competitive-intelligence aggregator for e-commerce.

It pulls RSS/Atom feeds from competitor platforms (Shopify, BigCommerce,
WooCommerce, Adobe Commerce, and open-source rivals) plus industry news,
filters to a recent window, flags "signal" items (pricing, AI, payments,
checkout, deprecations...), and writes ONE self-contained digest.html.

--------------------------------------------------------------------------
QUICK START
--------------------------------------------------------------------------
    pip install feedparser
    python ecommerce_monitor.py                 # last 7 days -> digest.html
    python ecommerce_monitor.py --days 14 --out weekly.html
    python ecommerce_monitor.py --json out.json # also dump raw data

AUTOMATE (cron, weekday 08:00):
    0 8 * * 1-5 cd /path/to/tool && /usr/bin/python3 ecommerce_monitor.py

On each run, any feed that returns nothing or errors is listed at the end
("FEEDS TO CHECK") so you can correct or prune the SOURCES list below.
SaaS changelog URLs (BigCommerce, Adobe, Retail Dive) move occasionally —
those are the ones most likely to show up there. GitHub `releases.atom`
and WordPress `/feed/` URLs are stable.

Email / Slack delivery: opt-in via env vars — see deliver() at the bottom.
Prefer `python run_all.py` for the combined digest + pricing + overview pass.
"""

import argparse
import datetime as dt
import html
import os
import re
import socket
import sys
import time
from collections import defaultdict

try:
    import feedparser
except ImportError:
    sys.exit("Missing dependency. Run:  pip install feedparser")

from report_style import shell, utcnow

# --------------------------------------------------------------------------
# SOURCES  ->  (display name, feed url, category)
# category is just for grouping in the digest: "Platform" or "Industry".
# Edit freely. Tags in [brackets] are notes to you, not used by the code.
# --------------------------------------------------------------------------
SOURCES = [
    # ---- Competitor platforms -------------------------------------------
    ("Shopify — Product & Merchant", "https://changelog.shopify.com/feed.xml", "Platform"),        # verified
    ("Shopify — Developer / API",    "https://shopify.dev/changelog/feed.xml", "Platform"),        # verified
    ("WooCommerce — Releases",       "https://github.com/woocommerce/woocommerce/releases.atom", "Platform"),
    ("WooCommerce — Dev blog",       "https://developer.woocommerce.com/feed/", "Platform"),
    ("Adobe Commerce / Magento",     "https://github.com/magento/magento2/releases.atom", "Platform"),
    ("BigCommerce — Dev changelog",  "https://docs.bigcommerce.com/developer/changelog.rss", "Platform"),  # verified 2026-08; titles are dates, change text is in summary
    ("PrestaShop — Releases",        "https://github.com/PrestaShop/PrestaShop/releases.atom", "Platform"),
    ("Medusa — Releases",            "https://github.com/medusajs/medusa/releases.atom", "Platform"),
    ("Saleor — Releases",            "https://github.com/saleor/saleor/releases.atom", "Platform"),
    ("Vendure — Releases",           "https://github.com/vendure-ecommerce/vendure/releases.atom", "Platform"),
    ("Sylius — Releases",            "https://github.com/Sylius/Sylius/releases.atom", "Platform"),
    # -- vendor voices (blogs/newsrooms), verified 2026-08-08 ---------------
    ("BigCommerce — Blog",     "https://www.bigcommerce.com/rss.xml", "Platform"),
    ("Wix — Blog",             "https://www.wix.com/blog/blog-feed.xml", "Platform"),
    ("WooCommerce — Blog",     "https://woocommerce.com/blog/feed/", "Platform"),
    ("Squarespace — Blog",     "https://www.squarespace.com/blog?format=rss", "Platform"),
    ("Squarespace — Newsroom", "https://newsroom.squarespace.com/blog?format=rss", "Platform"),
    ("Shift4 — Press",         "https://investors.shift4.com/news-events/press-releases/rss", "Platform"),
    ("Lightspeed — Blog",      "https://www.lightspeedhq.com/blog/feed/", "Platform"),  # closest live Ecwid voice
    ("Salesforce — Commerce",  "https://www.salesforce.com/blog/category/commerce/feed/", "Platform"),
    ("Shopware — Releases",    "https://github.com/shopware/shopware/releases.atom", "Platform"),

    # ---- Industry news ---------------------------------------------------
    ("Practical Ecommerce",   "https://www.practicalecommerce.com/feed", "Industry"),
    ("Digital Commerce 360",  "https://www.digitalcommerce360.com/feed/", "Industry"),
    ("Modern Retail",         "https://www.modernretail.co/feed/", "Industry"),
    ("Retail Dive",           "https://www.retaildive.com/feeds/news/", "Industry"),   # verified 2026-08
    ("TechCrunch — Commerce", "https://techcrunch.com/tag/e-commerce/feed/", "Industry"),
    ("Marketplace Pulse",     "https://www.marketplacepulse.com/articles/recent.atom", "Industry"),  # verified 2026-08
    ("Ecommerce News Europe", "https://ecommercenews.eu/feed/", "Industry"),            # verified 2026-08; EU focus
    ("ChannelX",              "https://channelx.world/feed/", "Industry"),              # verified 2026-08
    ("InternetRetailing",     "https://internetretailing.net/feed/", "Industry"),       # verified 2026-08
    # -- wider press, verified 2026-08-08 -----------------------------------
    ("Retail TouchPoints",    "https://www.retailtouchpoints.com/feed", "Industry"),
    ("PYMNTS",                "https://www.pymnts.com/feed/", "Industry"),
    ("Finextra",              "https://www.finextra.com/rss/headlines.aspx", "Industry"),  # event items carry FUTURE dates
    ("EcommerceBytes",        "https://www.ecommercebytes.com/feed/", "Industry"),
    ("Search Engine Land",    "https://searchengineland.com/feed", "Industry"),
    ("E-commerce Germany",    "https://ecommercegermany.com/feed/", "Industry"),
    ("Ecommerce News NL",     "https://www.ecommercenews.nl/feed/", "Industry"),
    ("Product Hunt — e-commerce", "https://www.producthunt.com/feed?category=e-commerce", "Industry"),
    # -- български и балкански медии ----------------------------------------
    ("Капитал",               "https://www.capital.bg/rss/", "Industry"),
    ("Economic.bg — Бизнес",  "https://www.economic.bg/rss/biznes.xml", "Industry"),
    ("Regal.bg",              "https://www.regal.bg/rss/", "Industry"),
    ("БЕА (e-commerce асоциация)", "https://beabg.com/feed/", "Industry"),
    ("Netokracija",           "https://www.netokracija.com/feed", "Industry"),

    # ---- Communities (merchants talking about these platforms daily) -----
    # Reddit rate-limits hard: _parse_feed() spaces these out and retries.
    # Complaints/migration threads here are direct sales opportunities.
    ("r/shopify",      "https://www.reddit.com/r/shopify/.rss", "Community"),
    ("r/bigcommerce",  "https://www.reddit.com/r/bigcommerce/.rss", "Community"),
    ("r/squarespace",  "https://www.reddit.com/r/squarespace/.rss", "Community"),
    ("r/wix",          "https://www.reddit.com/r/WIX/.rss", "Community"),
    ("r/woocommerce",  "https://www.reddit.com/r/woocommerce/.rss", "Community"),
    ("r/ecommerce",    "https://www.reddit.com/r/ecommerce/.rss", "Community"),
    ("r/Magento",      "https://www.reddit.com/r/Magento/.rss", "Community"),
    ("r/shopifyDev",   "https://www.reddit.com/r/shopifyDev/.rss", "Community"),
    ("r/AmazonSeller", "https://www.reddit.com/r/AmazonSeller/.rss", "Community"),
    ("r/EtsySellers",  "https://www.reddit.com/r/EtsySellers/.rss", "Community"),
    ("r/PrestaShop",   "https://www.reddit.com/r/PrestaShop/.rss", "Community"),
    # -- живи форуми на търговци, verified 2026-08-08 -----------------------
    ("WooCommerce Support Forum", "https://wordpress.org/support/plugin/woocommerce/feed/", "Community"),
    ("WooCommerce Reviews",       "https://wordpress.org/support/plugin/woocommerce/reviews/feed/", "Community"),
    ("Shopify Community",         "https://community.shopify.com/latest.rss", "Community"),
    # -- технологичен пулс (HN заявки, SO тагове), verified 2026-08-08 ------
    ("HN — agentic commerce", "https://hnrss.org/newest?q=%22agentic+commerce%22", "Community"),
    ("HN — Shopify",          "https://hnrss.org/newest?q=shopify", "Community"),
    ("HN — AI shopping",      "https://hnrss.org/newest?q=%22ai+shopping%22", "Community"),
    ("HN — ecommerce",        "https://hnrss.org/newest?q=ecommerce", "Community"),
    ("SO — woocommerce",      "https://stackoverflow.com/feeds/tag/woocommerce", "Community"),
    ("SO — shopify",          "https://stackoverflow.com/feeds/tag/shopify", "Community"),
    ("SO — magento2",         "https://stackoverflow.com/feeds/tag/magento2", "Community"),
]

# Signals that make an item worth a second look: label -> regex fragment.
# Matched case-insensitively on word boundaries, so "ai" no longer fires
# inside "email" and "pos" inside "possible". Edit freely.
SIGNAL_PATTERNS = {
    "pricing":      r"pric(?:e|es|ing)",
    "plan":         r"plans?",
    "fee":          r"fees?",
    "cost":         r"costs?",
    "billing":      r"billing",
    "subscription": r"subscriptions?",
    "checkout":     r"checkout",
    "payments":     r"pay(?:ments?)?",
    "tax":          r"tax(?:es)?",
    "shipping":     r"shipping",
    "fulfillment":  r"fulfil\w*",
    "ai":           r"ai|a\.i",     # the \b(...)\b wrapper makes "a.i." work too
    "agent":        r"agents?|agentic",
    "llm":          r"llms?",
    "copilot":      r"copilot",
    "pos":          r"pos",
    "b2b":          r"b2b",
    "wholesale":    r"wholesale",
    "headless":     r"headless",
    "graphql":      r"graphql",
    "api":          r"apis?",
    "deprecation":  r"deprecat\w*",
    "sunset":       r"sunset",
    "breaking":     r"breaking",
    "end of life":  r"end[- ]of[- ]life|eol",
    # opportunity signals — merchants unhappy or moving between platforms
    "migration":    r"migrat\w*|switch(?:ing|ed)?|leav(?:e|ing)|alternatives?",
    "outage":       r"outage|down|offline|not working",
}
_SIGNAL_RES = {label: re.compile(r"\b(?:%s)\b" % pat, re.IGNORECASE)
               for label, pat in SIGNAL_PATTERNS.items()}

# Relevance scoring: not all signals are equal. AI/agentic moves rank highest
# (current strategic focus), then money and dissatisfaction signals. A recent
# item from a competitor's own changelog outranks old general press.
SIGNAL_WEIGHTS = {
    "agent": 6, "ai": 5, "llm": 5, "copilot": 5,
    "migration": 4, "pricing": 4, "outage": 3, "fee": 3,
    "checkout": 3, "payments": 3, "deprecation": 3, "sunset": 3,
    "breaking": 3, "end of life": 3,
    "plan": 2, "cost": 2, "billing": 2, "subscription": 2,
    "pos": 2, "b2b": 2, "wholesale": 2, "headless": 2,
    "tax": 1, "shipping": 1, "fulfillment": 1, "graphql": 1, "api": 1,
}
CATEGORY_BOOST = {"Platform": 2, "Community": 1, "Industry": 0}


def _score(signals, category, when):
    """0 = no signals; otherwise weighted signals + source boost + freshness."""
    s = sum(SIGNAL_WEIGHTS.get(x, 1) for x in signals)
    if not s:
        return 0
    s += CATEGORY_BOOST.get(category, 0)
    if when and (utcnow() - when).total_seconds() < 48 * 3600:
        s += 2
    return s

# --------------------------------------------------------------------------
# Core logic
# --------------------------------------------------------------------------
def _entry_date(entry):
    """Best-effort published datetime; None if the feed omits one."""
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return dt.datetime(*t[:6])
    return None


def _signals(text):
    # Feed summaries can be raw HTML (GitHub release notes). Strip tags and
    # bare URLs first so hrefs like /ai/logo.png don't fire false signals.
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return sorted(label for label, rx in _SIGNAL_RES.items() if rx.search(text))


FEED_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) ecommerce-intel/1.0")


def _parse_feed(url):
    """feedparser with a real UA. Reddit throttles unauthenticated clients
    hard (~1 req/10s/IP, stricter in bursts) — space out generously and
    retry twice with growing pauses; a daily CI run can afford the wait."""
    if "reddit.com" in url:
        time.sleep(15)
    feed = feedparser.parse(url, agent=FEED_UA)
    if "reddit.com" in url and not feed.entries:
        for pause in (30, 60):
            time.sleep(pause)
            feed = feedparser.parse(url, agent=FEED_UA)
            if feed.entries:
                break
    return feed


def fetch(sources, days):
    """Return (items, problems). items = list of dicts, newest first."""
    # feedparser fetches via urllib with NO timeout — one stalled host would
    # otherwise wedge the whole run (and the weekly CI job) indefinitely.
    socket.setdefaulttimeout(30)
    cutoff = utcnow() - dt.timedelta(days=days)
    items, problems, seen = [], [], set()

    for name, url, category in sources:
        try:
            feed = _parse_feed(url)
        except Exception as exc:                      # network / parse blow-up
            problems.append(f"{name}: грешка: {exc}")
            continue
        if getattr(feed, "bozo", 0) and not feed.entries:
            problems.append(f"{name}: нечетим или празен ({url})")
            continue
        if not feed.entries:
            problems.append(f"{name}: без записи ({url})")
            continue

        kept = 0
        for e in feed.entries:
            when = _entry_date(e)
            if when and when < cutoff:
                continue
            # Some feeds (Finextra) list events dated in the future — keep
            # the item but drop the date so it can't outrank real news.
            if when and (when - utcnow()).total_seconds() > 86400:
                when = None
            link = (e.get("link") or "").strip()
            # Feed data is untrusted: only http(s) links may reach an href
            # (blocks javascript:/data: schemes at the single ingestion point).
            if not link.lower().startswith(("http://", "https://")):
                link = ""
            if link and link in seen:
                continue
            seen.add(link)
            title = html.unescape(e.get("title", "(no title)")).strip()
            summary = html.unescape(e.get("summary", "")).strip()
            signals = _signals(title + " " + summary)
            items.append({
                "source": name,
                "category": category,
                "title": title,
                "link": link,
                "date": when,
                "signals": signals,
                "score": _score(signals, category, when),
            })
            kept += 1
        if kept == 0:
            problems.append(f"{name}: работи, но без нови публикации от {days} дни")

    items.sort(key=lambda x: x["date"] or dt.datetime.min, reverse=True)
    return items, problems


# --------------------------------------------------------------------------
# HTML rendering — shared CloudCart-branded frame lives in report_style.py
# --------------------------------------------------------------------------
def render(items, problems, days):
    now = utcnow().strftime("%Y-%m-%d %H:%M UTC")
    by_cat = defaultdict(list)
    for it in items:
        by_cat[it["category"]].append(it)

    subtitle = (f"{now} &middot; последни {days} дни &middot; "
                f"{len(items)} публикации от "
                f"{len({i['source'] for i in items})} източника")
    out = []

    for cat in ("Platform", "Industry", "Community"):
        rows = by_cat.get(cat, [])
        label = {"Platform": "Конкурентни платформи",
                 "Industry": "Новини от бранша",
                 "Community": "Пулс на общността"}[cat]
        out.append(f"<h2>{label} &mdash; {len(rows)}</h2>")
        if not rows:
            out.append("<div class=empty>Няма нищо ново в този прозорец.</div>")
        for it in rows:
            d = it["date"].strftime("%b %d") if it["date"] else "—"
            sig = "".join(f"<span class=sig>{html.escape(s)}</span>" for s in it["signals"])
            link = html.escape(it["link"])
            title = html.escape(it["title"])
            out.append(
                f"<div class=card><a href='{link}' target=_blank>{title}</a>"
                f"{('<div>'+sig+'</div>') if sig else ''}"
                f"<div class=row><span class=src>{html.escape(it['source'])}</span>"
                f"<span>{d}</span></div></div>")

    if problems:
        out.append("<div class=warn><b>ИЗТОЧНИЦИ ЗА ПРОВЕРКА</b> "
                   "(поправете или махнете от SOURCES):<ul>")
        out += [f"<li>{html.escape(p)}</li>" for p in problems]
        out.append("</ul></div>")

    return shell("Дайджест: пазарна активност", subtitle, "".join(out))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main():
    if hasattr(sys.stdout, "reconfigure"):       # Windows cp1252 consoles/pipes
        sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="E-commerce competitive digest")
    ap.add_argument("--days", type=int, default=7, help="look-back window")
    ap.add_argument("--out", default="digest.html", help="HTML output file")
    ap.add_argument("--json", help="optional JSON dump of raw items")
    args = ap.parse_args()

    items, problems = fetch(SOURCES, args.days)

    page = render(items, problems, args.days)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Wrote {args.out}  ({len(items)} items, {len(problems)} feeds to check)")

    if args.json:
        import json
        payload = [{**it, "date": it["date"].isoformat() if it["date"] else None}
                   for it in items]
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Wrote {args.json}")

    for p in problems:
        print("  check:", p)

    deliver(items, page)


# --------------------------------------------------------------------------
# DELIVERY — opt-in via env vars, skipped when unset. No secrets in code.
#   Slack:  SLACK_WEBHOOK_URL
#   Email:  SMTP_HOST, SMTP_USER, SMTP_PASS, DIGEST_EMAIL_TO
#           (optional SMTP_PORT, default 465 = SSL)
# --------------------------------------------------------------------------
def _slack_escape(s):
    """Slack mrkdwn: & < > must be entity-escaped in message text."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def send_slack(webhook_url, items, title="E-commerce digest"):
    import json
    import urllib.request
    picks = [i for i in items if i["signals"]] or items
    lines = []
    for i in picks[:20]:
        src = _slack_escape(i["source"])
        # inside <url|label>, "|" and ">" terminate the construct early
        label = _slack_escape(i["title"]).replace("|", "/")
        link = i["link"].replace("|", "%7C")
        lines.append(f"*{src}* — <{link}|{label}>" if link else f"*{src}* — {label}")
    body = {"text": f"*{_slack_escape(title)}*\n" + "\n".join(lines)}
    req = urllib.request.Request(webhook_url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20)


def send_email(html_body, subject="E-commerce intelligence digest"):
    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["DIGEST_EMAIL_TO"]
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT") or "465")   # unset CI secret == ""
    if port == 465:                      # implicit SSL
        with smtplib.SMTP_SSL(host, port, timeout=30) as s:
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)
    else:                                # 587/25 etc.: STARTTLS submission
        with smtplib.SMTP(host, port, timeout=30) as s:
            s.starttls()
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)


def deliver(items, html_body, subject="E-commerce intelligence digest"):
    """Push the digest via any delivery channel whose env vars are set."""
    hook = os.environ.get("SLACK_WEBHOOK_URL")
    if hook:
        try:
            send_slack(hook, items, title=subject)
            print("Delivered to Slack.")
        except Exception as exc:
            print(f"  check: Slack delivery failed: {exc}")
    if all(os.environ.get(k) for k in
           ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "DIGEST_EMAIL_TO")):
        try:
            send_email(html_body, subject=subject)
            print(f"Emailed digest to {os.environ['DIGEST_EMAIL_TO']}.")
        except Exception as exc:
            print(f"  check: email delivery failed: {exc}")


if __name__ == "__main__":
    main()
