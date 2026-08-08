# CLAUDE.md

Context for continuing this project. Read this first.

## What this is
A competitive-intelligence aggregator for e-commerce. It keeps CloudCart aware of
what rival platforms (Shopify, BigCommerce, WooCommerce, Adobe Commerce, and
open-source rivals) and the wider industry are shipping — features, tech, and pricing.

## Architecture
1. **`ecommerce_monitor.py`** — the *feed* side. Pulls RSS/Atom from platform
   changelogs + industry news (`SOURCES` list), filters to a recent window,
   flags "signal" items (pricing/AI/checkout/payments/deprecations via
   `SIGNAL_PATTERNS`, word-boundary regexes), writes the digest. Stateless.
   Delivery (Slack/email) lives at the bottom — `deliver()`, opt-in env vars.
2. **`pricing_monitor.py`** — the *scrape+diff* side, for silent pricing-page
   edits that never hit a feed. Fetches each page in `PRICING_PAGES`, extracts
   every currency amount (the price "fingerprint"), diffs against
   `price_state.json` from the last run. Extraction chain per page:
   visible-text regex → JSON-LD (`extract_jsonld_prices`, e.g. Squarespace) →
   headless browser (auto, only if Playwright is installed).
   **Stateful** — `price_state.json` must persist between runs for diffing.
3. **`plan_compare.py`** — the *analytical* layer: per-vendor extractors turn
   each pricing page into structured plans (name, monthly, annual-billing
   monthly, currency), including CLOUDCART'S OWN plans (the baseline row).
   EUR-normalises via FX_USD_EUR (default = ECB rate, update occasionally),
   diffs run-over-run at plan level, renders the comparison matrix +
   entry-price bars. Extraction recipes were adversarially verified against
   live pages 2026-08-07; each is wrapped so a page redesign degrades to a
   "SOURCES TO CHECK" entry, never a crash. Wix uses Wix's own price API
   (US row) with an SSR-HTML fallback. Plan snapshots persist in
   `price_state.json` under the reserved `_plans` key (the pruner keeps
   `_`-prefixed keys).
4. **`status_monitor.py`** — availability intel. Polls each vendor's PUBLIC
   status API (all CORS-enabled, live-verified 2026-08-08): Atlassian
   Statuspage v2 for Shopify (www.shopifystatus.com — NOT status.shopify.com),
   BigCommerce, Wix, Squarespace, Ecwid, and Shift4 (parent page, incidents
   filtered by `component_filter` regex); CloudCart's own UptimeRobot page
   (getMonitorList = true 30d ratios, getEventFeed = rolling 7d events).
   Computes incidents + downtime minutes over 30 days.
5. **`social_monitor.py`** — marketing intel. YouTube RSS per official channel
   (cadence, launch-flagged titles), Google Ads Transparency SearchSuggestions
   RPC (server-side, no auth — active-ad-count ranges for Shopify/Squarespace),
   Meta Ad Library deep links per page id (+ programmatic counts/EU reach when
   META_AD_TOKEN env is set), X/LinkedIn/Facebook links.
6. **`intel_history.py` / `export_monthly.py`** — the daily evidence trail
   (history/daily.jsonl, one line per vendor per run; last line per day wins)
   and monthly CSV exports (exports/<YYYY-MM>-daily.csv + -summary.csv).
7. **`report_style.py`** — the design system, implemented 1:1 from the
   AUTHORITATIVE files the user provided (in repo root: `theme.css`,
   `design.json`, `Демо-Магазин-DESIGN-SYSTEM-PROMPT (1).md`): CloudCart
   Admin Design System, seed #8D58E0 (purple), light + dark themes
   (recomputed, toggle stored in localStorage), Montserrat SELF-HOSTED
   (reports/fonts/montserrat-var.woff2, subset via fonttools — no Google
   CDN). HARD RULES from the brief: brand color in exactly six places,
   borders never shadows, no emoji/gradients/hover-motion/accent bars,
   UI in BULGARIAN (dates 24.07.2026, numbers 1 240,50, currency AFTER the
   number, "–" for empty cells), tabular-nums on :root, no ligatures in
   data cells, focus ring non-negotiable. Chart pair light #7344BB/#2B7FFF
   (dataviz-validated), dark #AE82FF/#1CCFB9 (system chart tokens).
8. **`dashboard.py`** — the seven-page ecosystem (Bulgarian UI): Табло,
   Цени, Функции, Наличност, Пазарна активност, Социални и реклами,
   Източници. Tables sort on click; activity has a live filter; status
   badges refresh live via the CORS status APIs.
9. **`features.json` + features page** — the sales battlecard: 13
   capabilities × 7 vendors, researched against official vendor pages and
   adversarially verified (each cell carries a quotable note + source URL).
   `txn_fees`/`gmv_caps` have INVERTED polarity ("no" is good) — handled in
   dashboard.INVERTED_KEYS. Edit features.json by hand as facts change.
10. **`run_all.py`** — the one command: collects everything, appends the
   history snapshot, writes all pages, delivers the email brief.

## How to run
```bash
pip install -r requirements.txt
python run_all.py                             # -> reports/index.html + both reports
python ecommerce_monitor.py --days 7          # feeds only
python pricing_monitor.py                     # prices only (1st run = baseline)
```
```bash
python export_monthly.py --month 2026-08      # -> exports/*.csv
python status_monitor.py                      # availability check standalone
python social_monitor.py                      # social/ads check standalone
```
GitHub Actions (`.github/workflows/monitor.yml`) runs `run_all.py` DAILY
(06:00 UTC), refreshes the monthly export, commits reports + state + history
back, and deploys to Vercel when the VERCEL_TOKEN secret is set.

## Conventions
- Dependency-light on purpose (feedparser, requests, beautifulsoup4). Don't add
  heavy frameworks. Playwright is optional; the headless fallback activates
  automatically when it's importable.
- `SOURCES` and `PRICING_PAGES` are plain edit-in-place lists at the top of each file.
- Both tools **self-report** broken sources instead of failing silently — feeds
  under "FEEDS TO CHECK", pricing under "no prices detected"; `index.html`
  merges both under "SOURCES TO CHECK". Preserve that.
- No secrets in code. Email/Slack/API keys go through env vars or repo secrets.
- Reports must keep the CloudCart brand look — change visuals in
  `report_style.py` only. The original reference ("CC Brandbook extended.pdf")
  is **corrupted** (UTF-8-mangled binary, unrecoverable) — ask the user for a
  clean re-export if deeper brand fidelity is ever needed; current tokens were
  verified against cloudcart.com's live CSS/logo in 2026-08.

## Current status (2026-08-07)
Live-verified end to end: `run_all.py` ran clean twice — 64 feed items from all
17 sources readable, 6/6 pricing pages fingerprinted, diffing confirmed stable
(second run = 0 changes). All previously broken sources fixed:
- BigCommerce dev changelog → `docs.bigcommerce.com/developer/changelog.rss`
  (titles are bare dates; the change text is in the summary — that's normal).
- Marketplace Pulse → `/articles/recent.atom` (the only feed the site has).
- Shift4Shop pricing → `/pricing.htm` (server-rendered, geo-routes).
- Shopify pricing → `/bg/pricing` (pins Bulgarian EUR page; BG uses EUR since 2026).
- Squarespace prices come from JSON-LD (EUR preferred, USD fallback).

## Deployment
Reports are deployed as a static site: **https://cloudcart-intel.vercel.app**
(Vercel project `cloudcart-intel`, account ekurtisi-1224). Redeploy: copy
`reports/*.html` to a staging dir and `vercel deploy --prod --yes`. Static
snapshot — consider a CI step that redeploys after each weekly run.

## Open tasks
0. **[IMPORTANT — REVIEW/KILL SWITCH] WebMCP pilot** — the origin-trial
   script (webmcp/) is live on pilot store(s). Review by ~2026-10-08:
   if agents bring no value, remove the snippet from the store's
   Custom CSS/JS panel (1 minute, nothing else persists). Token expires
   with the trial period on its own.
1. **Secrets to activate** — VERCEL_TOKEN (auto-deploy; deploy step is wired,
   org/project ids are in monitor.yml), META_AD_TOKEN (Meta ad counts + EU
   reach via ads_archive; needs Meta identity verification first), SLACK/SMTP
   (delivery live test).
2. **Trend charts** — history/daily.jsonl accumulates; once ~2 weeks exist,
   add sparklines (price, downtime, ad counts over time) to the dashboard.
3. **Status archive** — statuspage incidents.json caps at 50 incidents;
   BigCommerce burns that in ~3.5 months. Daily history snapshots already
   preserve the numbers; consider archiving raw incidents too.
4. **CloudCart plan caps** — the matrix compares price only; CloudCart plans
   carry six-month turnover caps (9,999/24,999/249,999/499,999 EUR) and
   product limits that competitors price differently. A cap-aware comparison
   would be the next intelligence step.
5. **(Stretch)** relevance scoring on feed items.

## Gotchas
- `pricing_monitor.py` diffing only works if `price_state.json` survives between
  runs — never gitignore it, and in CI it must be committed back (already handled).
  `run()` prunes state keys that leave `PRICING_PAGES`, so URL swaps rebaseline.
- Pricing pages are region- and JS-dependent: a "change" could be a currency/geo
  shift, not a real price move. Region-pinned URLs (Shopify /bg/) mitigate;
  BigCommerce and Wix quote USD worldwide; Shift4Shop's fingerprint may differ
  between a Bulgarian machine and a US CI runner (geo-routing) — expect a
  one-time diff when switching where it runs.
- European pages use NBSP thousands separators ("12 000 €") — the tokenizer
  groups NBSP-separated triplets but deliberately NOT regular spaces (Ecwid
  flattens adjacent per-region prices into "99 450 €", which must stay two
  numbers). Don't "fix" that without re-checking both pages.
- Ecwid embeds every region's prices in hidden spans; the fingerprint is the EU
  column plus bare-number noise — stable, but multi-currency.
- Plan-extractor anchors are page-markup-specific (CloudCart `data-mapping`
  cards, Shopify's `Плащайте месечно</span></th>` table row, BigCommerce's
  Makeswift `"annualPrice"` blob, Squarespace's translate=no JSON-LD, Ecwid's
  first `.pricing-block` only, Shift4Shop's "enterprise-grade plan for $X"
  callout). When one breaks it self-reports; re-derive from the live page, and
  beware the traps noted in each extractor's docstring.
- CloudCart annual prices are FIRST-YEAR promo prices ("billed annually (for
  the first year)"); competitors' annual prices are steady-state. The matrix
  compares them as-is — keep that asymmetry in mind when quoting deltas.
- Status traps: Shopify's API lives on www.shopifystatus.com (the old host
  301s with an empty body); Shift4Shop shares parent Shift4's page (~110
  components — the component_filter regex keeps only shift4shop/3dcart
  incidents, so 0 incidents there may mean "nothing e-commerce-specific",
  not "nothing at all"); statuspage incident feeds cap at 50 entries;
  CloudCart's UptimeRobot event feed only covers 7 days (30d downtime comes
  from per-monitor ratios instead). Shopify hasn't posted an incident since
  2025-06 — they may under-post; don't read raw incident counts as gospel.
- Social traps: youtube.com/@Ecwid is an unrelated personal channel — the
  official id is hardcoded from shift4shop/ecwid site footers; the Google
  ad-count RPC (SearchSuggestions) is undocumented and may change shape (it
  self-reports on failure); Wix runs ads via regional entities, so no Google
  ad count is shown for them (domain-search link only). Meta Ad Library is
  bot-walled — deep links open it for humans; programmatic needs META_AD_TOKEN.
- Reddit rate-limits unauthenticated RSS to ~1 request/10s per IP —
  _parse_feed() sleeps 15s before each reddit fetch and retries twice
  (30s/60s); expect an occasional "no entries" self-report anyway.
- Source universe (~60 feeds, all live-verified 2026-08-08): platform
  changelogs + vendor blogs/newsrooms, EU + payments press, Bulgarian media
  (Капитал, Economic.bg, Regal.bg, БЕА), merchant forums (wp.org Woo
  support/reviews, Shopify Community Discourse latest.rss), 11 subreddits,
  HN query feeds (hnrss.org), SO tag feeds, Product Hunt e-commerce.
  KNOWN DEAD ENDS (don't re-add): Shopify blog/engineering have no working
  feeds (changelogs are the coverage); The Paypers, eSeller365 (frozen),
  commercetools/Adobe blogs (no RSS), Squarespace forum (Cloudflare wall),
  Ecwid blog (stale since 2026-03). Finextra event items carry FUTURE
  dates — fetch() nulls dates >24h ahead so they can't outrank real news.
- Trustpilot ratings CANNOT be scraped plainly (AWS WAF JS challenge on all
  profiles incl. TLS impersonation). Partial live route that works:
  widget.trustpilot.com/trustbox-data/... businessUnit JSON (trustScore,
  numberOfReviews) — but only for vendors paying for TrustBox (Wix,
  Squarespace today). Not integrated; revisit if coverage grows.
- Design files in repo root (theme.css/design.json/*.md) are the user's
  authoritative design-system export — never restyle against anything else,
  and read the brief's rules before touching visuals. The old "CC Brandbook
  extended.pdf" remains corrupted/irrelevant.
