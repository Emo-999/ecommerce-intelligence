# ecommerce-intel

Competitive-intelligence monitor for e-commerce: tracks what rival platforms and
the industry are shipping — features, tech, and pricing. Reports use CloudCart's
brand styling (shared frame in `report_style.py`).

Live dashboard: **https://cloudcart-intel.vercel.app**

One-glance competitor operations console (CC Admin design language): per
vendor — live status (refreshes in your browser from public status APIs),
30-day downtime & incidents, plan prices vs CloudCart with deltas, plan-level
change log, market signals, YouTube cadence, and ad-library activity
(Google active-ad counts; Meta deep links with EU reach by country).

Entry points:
- **`run_all.py`** — the one command: collects everything, appends the daily
  history snapshot, writes `reports/{index,digest,pricing}.html`.
- **`export_monthly.py`** — monthly CSVs (daily detail + per-vendor summary)
  from `history/daily.jsonl`, for comparison against internal numbers.
- **`ecommerce_monitor.py`** / **`pricing_monitor.py`** /
  **`plan_compare.py`** / **`status_monitor.py`** / **`social_monitor.py`**
  — each also runs standalone for a quick check of its slice.

## Setup
```bash
pip install -r requirements.txt
```

## Use
```bash
python run_all.py                    # everything -> reports/index.html
python run_all.py --days 14          # wider feed window
python ecommerce_monitor.py --days 7 # feeds only -> digest.html
python pricing_monitor.py            # prices only -> pricing_report.html
```
The first pricing run records a baseline; changes show from the second run on.

## Delivery (optional)
Set env vars to push results instead of only writing files:
- Slack: `SLACK_WEBHOOK_URL`
- Email: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`, `DIGEST_EMAIL_TO`
  (optional `SMTP_PORT`, default 465/SSL)

## JS-rendered pricing pages (optional)
Pages with 0 prices in raw HTML automatically fall back to a headless browser
if Playwright is installed:
```bash
pip install playwright && playwright install chromium
```
(Squarespace needs no headless — its prices are read from embedded JSON-LD.)

## Automate
`.github/workflows/monitor.yml` runs `run_all.py` weekly and commits the
reports + `price_state.json` back to the repo. Or use cron:
```
0 8 * * 1 cd /path/to/ecommerce-intel && python3 run_all.py
```

Editing sources: change the `SOURCES` list (feeds) or `PRICING_PAGES` list
(pricing) at the top of each file. Both tools report any source they can't read.

See `CLAUDE.md` for architecture and open tasks.
