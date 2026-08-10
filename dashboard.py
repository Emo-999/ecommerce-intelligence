#!/usr/bin/env python3
"""
dashboard.py
============
Екосистемата от табла: седем свързани страници, всяка самостоятелна
аналитична конзола върху общата админ рамка (CloudCart Admin Design System):

  index.html         Табло               общ поглед + KPI
  pricing.html       Цени                планова матрица, детайл, промени
  features.html      Функции             сравнение на възможности (battlecard)
  availability.html  Наличност           недостъпност, инциденти
  activity.html      Пазарна активност   филтрируем поток от източници
  social.html        Социални и реклами  видео ритъм, рекламни библиотеки
  sources.html       Източници           здраве, методика, износ

Изследователски възможности: таблиците се сортират с клик, потокът има жив
филтър, статус значките се опресняват на живо от публичните статус API-та.
Интерфейсът е на български по правилата на дизайн системата; данните
(имена на планове, заглавия от източници) остават в оригинал.
"""

import html as html_mod
import json

import plan_compare as pc
import status_monitor as stm
from report_style import admin_shell, bg_dt, bg_num, bg_when, shell

NAME_MAP = {"Wix eCommerce": "Wix"}   # имена от pricing_monitor -> платформа

NAV = [("index.html", "Табло"), ("pricing.html", "Цени"),
       ("features.html", "Функционалности"), ("availability.html", "Наличност"),
       ("activity.html", "Пазарна активност"),
       ("social.html", "Социални и реклами"),
       ("saved.html", "Запазени"), ("sources.html", "Източници")]

_BOOKMARK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
             'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 '
             '2 2v16z"/></svg>')

# Запазените публикации живеят в localStorage на браузъра (страниците се
# прегенерират всеки ден, затова бутонът снима картичката при запазване).
FAV_JS = """
function ccFavs(){try{return JSON.parse(localStorage.getItem('cc-favs')||'{}')}
catch(e){return {}}}
function ccFavsSave(f){try{localStorage.setItem('cc-favs',
JSON.stringify(f))}catch(e){}}
document.querySelectorAll('.favbtn[data-fav]').forEach(function(b){
var d;try{d=JSON.parse(b.dataset.fav)}catch(e){return}
function paint(){b.classList.toggle('on',!!ccFavs()[d.u]);
b.title=ccFavs()[d.u]?'Премахни от запазените':'Запази за по-късно';}
b.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();
var f=ccFavs();if(f[d.u]){delete f[d.u]}else{d.ts=Date.now();f[d.u]=d}
ccFavsSave(f);paint();});paint();});
"""

EMPTY = "–"     # празна клетка по конвенцията на системата

SORT_JS = """
document.querySelectorAll('table.dense th').forEach(function(th){
th.style.cursor='pointer';th.title='Сортирай';
th.addEventListener('click',function(){
var tb=th.closest('table').tBodies[0],i=[].indexOf.call(th.parentNode.children,th),
rows=[].slice.call(tb.rows),asc=th.dataset.asc!=='1';
th.dataset.asc=asc?'1':'0';
rows.sort(function(a,b){
var x=(a.cells[i]||{}).textContent||'',y=(b.cells[i]||{}).textContent||'';
var nx=parseFloat(x.replace(/[^0-9.\\-]/g,'')),ny=parseFloat(y.replace(/[^0-9.\\-]/g,''));
if(!isNaN(nx)&&!isNaN(ny))return asc?nx-ny:ny-nx;
return asc?x.localeCompare(y):y.localeCompare(x);});
rows.forEach(function(r){tb.appendChild(r)});});});
"""

FILTER_JS = """
var fi=document.getElementById('filterbox');
function applyFilters(){
var q=fi?fi.value.toLowerCase():'';
var act=[].map.call(document.querySelectorAll('.chip.on'),
function(c){return c.dataset.tag});
document.querySelectorAll('.filterable .card').forEach(function(c){
var tags=(c.dataset.tags||'').split(' ');
var okTag=act.every(function(t){return tags.indexOf(t)>-1});
var okQ=!q||c.textContent.toLowerCase().indexOf(q)>-1;
c.style.display=okTag&&okQ?'':'none';});
var vis=document.querySelectorAll(
".filterable .card:not([style*='none'])").length;
var cnt=document.getElementById('viscount');
if(cnt)cnt.textContent=vis;}
if(fi)fi.addEventListener('input',applyFilters);
document.querySelectorAll('.chip[data-tag]').forEach(function(ch){
ch.addEventListener('click',function(){
var grp=ch.dataset.group;
if(!ch.classList.contains('on')&&grp)
document.querySelectorAll(".chip[data-group='"+grp+"']").forEach(
function(c){c.classList.remove('on')});
ch.classList.toggle('on');applyFilters();});});
"""

# Тематични лещи за филтриране: етикет -> сигнали
THEMES = [
    ("ai", "AI и агенти", {"ai", "agent", "llm", "copilot"}),
    ("pricing", "Цени и планове",
     {"pricing", "plan", "fee", "cost", "billing", "subscription"}),
    ("payments", "Плащания", {"payments", "checkout", "tax"}),
    ("migration", "Миграции", {"migration"}),
    ("outage", "Сривове", {"outage"}),
    ("tech", "Технологии", {"api", "graphql", "headless", "deprecation",
                            "breaking", "end of life", "sunset"}),
    ("retail", "Търговия", {"pos", "b2b", "wholesale", "shipping",
                            "fulfillment"}),
]
PRIO_SCORE = 8      # от този резултат нагоре публикацията е "приоритетна"


def item_tags(it):
    """data-tags за картичка: теми + вид източник + приоритет + свежест."""
    tags = [slug for slug, _, sigs in THEMES
            if sigs & set(it.get("signals") or [])]
    tags.append({"Community": "community", "Platform": "platform",
                 "Newsletter": "newsletter",
                 "Industry": "press"}.get(it.get("category"), "press"))
    if (it.get("score") or 0) >= PRIO_SCORE:
        tags.append("prio")
    return " ".join(tags)


def is_fresh(it, hours=48):
    from report_style import utcnow
    d = it.get("date")
    return bool(d and (utcnow() - d).total_seconds() < hours * 3600)


def news_card(it, show_score=False):
    sig = "".join(f"<span class=sig>{esc(s)}</span>" for s in it["signals"])
    d = bg_when(it["date"])
    new = "<span class=newmark>НОВО</span>" if is_fresh(it) else ""
    score = (f"<span class=score>приоритет {it.get('score', 0)}</span>"
             if show_score and it.get("score") else "")
    fav = json.dumps({"u": it["link"], "t": it["title"],
                      "s": it["source"], "d": d,
                      "g": it["signals"]}, ensure_ascii=False)
    favbtn = (f"<button type=button class=favbtn "
              f"data-fav=\"{esc(fav)}\">{_BOOKMARK}</button>")
    return (f"<div class=card data-tags='{item_tags(it)}'>{favbtn}{score}{new}"
            f"<a href='{esc(it['link'])}' target=_blank>{esc(it['title'])}"
            f"</a>{('<div>' + sig + '</div>') if sig else ''}"
            f"<div class=row><span class=src>{esc(it['source'])}</span>"
            f"<span>{d}</span></div></div>")


def esc(s):
    return html_mod.escape(str(s))


def bg_down(minutes):
    """36 ч 27 м — недостъпност в човешки вид."""
    if minutes <= 0:
        return "0 м"
    h, m = divmod(round(minutes), 60)
    return f"{h} ч {m:02} м" if h else f"{m} м"


def kpi_row(kpis):
    """kpis = [(стойност, надпис, тревожно?)]"""
    return "<div class=tiles>" + "".join(
        f"<div class=tile><div class='n{' hot' if hot else ''}'>{n}</div>"
        f"<div class=l>{l}</div></div>" for n, l, hot in kpis) + "</div>"


def status_badge(s, vendor):
    if not s:
        return f"<span class='badge badge-na'>{EMPTY}</span>"
    cls, label = {
        "none": ("badge-ok", "Работи"),
        "minor": ("badge-warn", "Влошено"),
        "major": ("badge-err", "Частичен срив"),
        "critical": ("badge-err", "Голям срив"),
        "nopage": ("badge-na", "Без статус страница"),
    }.get(s["indicator"], ("badge-na", "Неизвестно"))
    return (f"<span class='badge {cls}' data-vendor='{esc(vendor)}'>"
            f"<span class=dt></span>{label}</span>")


def live_status_js(status):
    apis = {v: {"u": s["live_api"], "k": s["kind"]}
            for v, s in status.items() if s.get("live_api")}
    if not apis:
        return ""
    return """
var A=%s,M={none:['badge-ok','Работи'],minor:['badge-warn','Влошено'],
major:['badge-err','Частичен срив'],critical:['badge-err','Голям срив']};
Object.keys(A).forEach(function(v){fetch(A[v].u).then(function(r){return r.json()})
.then(function(j){var i;
if(A[v].k==='uptimerobot'){var c=((j.statistics||{}).counts)||{};
i=(c.down|0)===0?'none':((c.down|0)>=2?'major':'minor');}
else{i=(j.status&&j.status.indicator)||'unknown';}
var c2=M[i];if(!c2)return;
document.querySelectorAll("[data-vendor='"+v+"'],[data-vendor='"+v+"-d']")
.forEach(function(el){el.className='badge '+c2[0];
el.innerHTML="<span class=dt></span>"+c2[1]+" <span class=approx>на живо</span>";});})
.catch(function(){});});
""" % json.dumps(apis)


def _entry_plan(plans_info):
    if not plans_info:
        return None
    for p in plans_info["plans"]:
        val = p.get("annual") if p.get("annual") is not None else p.get("monthly")
        if val:
            eur, approx = pc.to_eur(val, p["currency"])
            if eur:
                return {"name": p["name"], "eur": eur, "approx": approx,
                        "basis": ("годишно плащане" if p.get("annual")
                                  is not None else "месечно плащане")}
    return None


def price_txt(p):
    """Цена в клетка: валутата е след числото (29 $ ≈ 25 €)."""
    val = p.get("annual") if p.get("annual") is not None else p.get("monthly")
    if val is None:
        return esc(p.get("note") or "по договаряне")
    sym = {"EUR": "€", "USD": "$"}.get(p["currency"], p["currency"])
    prefix = "от " if "from" in (p.get("note") or "") else ""
    txt = f"{prefix}{bg_num(val, 2 if val % 1 else 0)} {sym}"
    eur, approx = pc.to_eur(val, p["currency"])
    if approx and eur is not None:
        txt += f" <span class=approx>≈ {bg_num(eur)} €</span>"
    return txt


# --------------------------------------------------------------------------
# Табло
# --------------------------------------------------------------------------
def build_overview(items, results, days, plans, plan_changes, status, social):
    vendors = [pc.CC] + sorted(v for v in pc.EXTRACTORS if v != pc.CC)
    changed = [r for r in results if r["status"] == "changed"]
    signal_items = [i for i in items if i["signals"]]
    degraded = [v for v, s in status.items()
                if s["indicator"] in ("minor", "major", "critical")]
    entries = {v: _entry_plan(plans.get(v)) for v in vendors}
    ranked = sorted([(e["eur"], v) for v, e in entries.items() if e])
    rank = next((i + 1 for i, (_, v) in enumerate(ranked) if v == pc.CC), None)
    comp_down = sum(s["downtime_30d_min"] for v, s in status.items()
                    if v != pc.CC)
    max_down = max([s["downtime_30d_min"] for s in status.values()] + [1])
    cc_entry = entries.get(pc.CC)

    kpis = kpi_row([
        (len(vendors) - 1, "следени конкуренти", False),
        (len(degraded), "влошени в момента", bool(degraded)),
        (bg_down(comp_down), "недостъпност при тях, 30 дни", False),
        (len(plan_changes), "промени в планове", bool(plan_changes)),
        (len(changed), "промени по страници", bool(changed)),
        (len(signal_items), f"пазарни сигнали, {days} дни", False),
        (f"№{rank} от {len(ranked)}" if rank else EMPTY,
         "нашата входна цена (1 = най-евтина)", False),
    ])

    head = "".join(f"<th>{h}</th>" for h in
                   ["Платформа", "Статус", "Надеждност, 30 дни",
                    "Входен план на месец", "Спрямо CloudCart",
                    "Маркетинг, 30 дни"])
    rows = []
    for v in vendors:
        s, so, e = status.get(v), social.get(v) or {}, entries.get(v)
        if s and s["kind"] != "none":
            d = s["downtime_30d_min"]
            if d <= 0 and s["incidents_30d"] == 0:
                rel = "<span class=okmuted>няма докладвани инциденти</span>"
            else:
                w = max(d / max_down * 100, 2)
                n = s["incidents_30d"]
                rel = (f"<span class=meter><i style='width:{w:.0f}%'></i></span>"
                       f"<span class=cellmain><b>{bg_down(d)}</b> недостъпност"
                       f" · {n} инцидент{'а' if n != 1 else ''}</span>")
        else:
            rel = "<span class=okmuted>няма публична статус страница</span>"
        if e:
            price = (f"<span class=cellmain><b>{'≈ ' if e['approx'] else ''}"
                     f"{bg_num(e['eur'])} €</b>/мес.</span>"
                     f"<div class=sub>{esc(e['name'])} · {e['basis']}</div>")
        else:
            price = EMPTY
        if v == pc.CC:
            delta = "<span class=pname>нашата база</span>"
        elif e and cc_entry:
            pct = (e["eur"] - cc_entry["eur"]) / cc_entry["eur"] * 100
            word = "по-скъп" if pct > 0 else "по-евтин"
            cls = "up" if pct > 0 else "down"
            delta = (f"<span class='delta {cls}'>{'+' if pct > 0 else ''}"
                     f"{pct:.0f} % {word}</span>")
        else:
            delta = EMPTY
        facts = []
        nvid = so.get("videos_30d")
        if nvid is not None:
            facts.append(f"<b>{nvid}</b> видеа")
        gc = so.get("google_count")
        if gc:
            facts.append(f"<b>{bg_num(gc['lo'])}–{bg_num(gc['hi'])}</b> "
                         f"Google реклами")
        api = so.get("ads_api")
        if api:
            facts.append(f"<b>{api['active_ads']}</b> Meta реклами")
        links = "".join(
            f"<a href='{esc(u)}' target=_blank>{lbl}</a>"
            for lbl, u in [("Meta", (so.get('links') or {}).get('meta_ads')),
                           ("Google", (so.get('links') or {}).get('google_ads'))]
            if u)
        mkt = (f"<span class=cellmain>{' · '.join(facts) if facts else EMPTY}"
               f"</span><div class='sub linkrow'>{links}</div>")
        cls = " class=ours" if v == pc.CC else ""
        url = plans[v]["url"] if v in plans else "#"
        rows.append(
            f"<tr{cls}><td class=vname><a href='{esc(url)}' target=_blank>"
            f"{esc(v)}</a></td><td>{status_badge(s, v)}</td>"
            f"<td>{rel}</td><td>{price}</td><td>{delta}</td><td>{mkt}</td></tr>")

    glance = (f"<div class=tablewrap><table class=dense><thead><tr>{head}"
              f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
              "<div class=basis>Как се чете: зелено означава, че входният им "
              "план е ПО-СКЪП от нашия (ценово предимство за нас), червено "
              "означава, че ни подбиват. Знакът ≈ отбелязва преизчислена "
              "цена от долари. Лентата показва дела на всяка платформа от "
              "най-лошата 30-дневна недостъпност в групата. Статусът се "
              "опреснява на живо от публичните статус API-та, останалите "
              "числа са от последното събиране. Клик върху заглавие на "
              "колона сортира. Всяка секция вляво е самостоятелно табло."
              "</div>")

    highlights = []
    for c in plan_changes[:3]:
        highlights.append(f"<div class=card><span class=name>{esc(c['vendor'])}"
                          f" {esc(c['plan'])}</span> <span class=chg>"
                          f"{esc(c['field'])}: {c['old']} → {c['new']}</span>"
                          f"<div class=sub><a href='pricing.html'>Виж в "
                          f"„Цени“</a></div></div>")
    worst = sorted(((s["downtime_30d_min"], v) for v, s in status.items()
                    if v != pc.CC), reverse=True)
    if worst and worst[0][0] > 0:
        d, v = worst[0]
        highlights.append(f"<div class=card><span class=name>{esc(v)}</span> "
                          f"<span class=cellmain>най-ненадежден конкурент: "
                          f"<b>{bg_down(d)}</b> недостъпност за 30 дни</span>"
                          f"<div class=sub><a href='availability.html'>Виж в "
                          f"„Наличност“</a></div></div>")

    # Горещото сега: най-релевантното от последното събиране, най-отгоре.
    hot = sorted((i for i in items if (i.get("score") or 0) > 0),
                 key=lambda i: (i["score"],), reverse=True)[:6]
    hot_html = ""
    if hot:
        hot_html = ("<h2>Горещото сега</h2>"
                    + "".join(news_card(i, show_score=True) for i in hot)
                    + "<a class='btn ghost' href='activity.html'>Отвори "
                    "целия поток</a>")

    body = (kpis + hot_html + "<h2>Конкурентите с един поглед</h2>" + glance
            + "<h2>Какво заслужава внимание</h2>"
            + ("".join(highlights) or "<div class=empty>Спокоен период: без "
               "промени и сривове.</div>"))
    return admin_shell("Табло",
                       f"{bg_dt()} ч. · статус на живо · дневно събиране",
                       NAV, body,
                       extra_js=live_status_js(status) + SORT_JS + FAV_JS,
                       active="index.html")


# --------------------------------------------------------------------------
# Цени
# --------------------------------------------------------------------------
def build_pricing_dash(plans, plan_changes, results):
    changed = [r for r in results if r["status"] == "changed"]
    all_plans = sum(len(p["plans"]) for p in plans.values())
    entries = {v: _entry_plan(p) for v, p in plans.items()}
    ranked = sorted([(e["eur"], v) for v, e in entries.items() if e])
    kpis = kpi_row([
        (len(plans), "остойностени платформи", False),
        (all_plans, "следени планове", False),
        (len(plan_changes), "промени в планове", bool(plan_changes)),
        (len(changed), "промени по страници", bool(changed)),
        (f"{bg_num(ranked[0][0])} € ({esc(ranked[0][1])})" if ranked else EMPTY,
         "най-евтин вход", False),
    ])
    body = [kpis, "<h2>Планова матрица спрямо CloudCart</h2>",
            pc.render_matrix(plans)]
    bars = pc.render_entry_bars(plans)
    if bars:
        body.append("<h2>Входни цени по платформа</h2>" + bars)
    body.append("<h2>Промени по планове</h2>"
                + pc.render_plan_changes(plan_changes))

    body.append("<h2>Детайл по платформа</h2>")
    for v, info in plans.items():
        rows = ""
        for p in info["plans"]:
            monthly = EMPTY
            if p.get("monthly") is not None:
                sym = {"EUR": "€", "USD": "$"}.get(p["currency"], "")
                monthly = f"{bg_num(p['monthly'])} {sym}"
            rows += (f"<tr><td>{esc(p['name'])}</td>"
                     f"<td class=num>{price_txt(p)}</td>"
                     f"<td class=num>{monthly}</td>"
                     f"<td class=sub>{esc(p['note'] or '')}</td></tr>")
        body.append(
            f"<div class=card><span class=name>{esc(v)}</span> "
            f"<span class=sub><a href='{esc(info['url'])}' target=_blank>"
            f"{esc(info['url'])}</a></span>"
            f"<div class=tablewrap style='margin-top:8px'><table class=dense>"
            f"<thead><tr><th>План</th><th class=num>На месец, годишно "
            f"плащане</th><th class=num>На месец, месечно плащане</th>"
            f"<th>Бележки</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div></div>")

    body.append("<h2>Отпечатъци на ценовите страници</h2>")
    order = {"changed": 0, "baseline": 1, "no-prices": 2, "same": 3}
    for r in sorted(results, key=lambda x: order.get(x["status"], 9)):
        pill = {"changed": "ПРОМЯНА", "baseline": "базова снимка",
                "same": "без промяна", "no-prices": "няма цени"}.get(
                    r["status"], "грешка")
        pcls = "pill pill-hot" if r["status"] == "changed" else "pill"
        toks = ""
        if r["status"] == "changed":
            toks = "".join(f"<span class='tok tadd'>+ {esc(p)}</span>"
                           for p in r["added"])
            toks += "".join(f"<span class='tok trem'>&minus; {esc(p)}</span>"
                            for p in r["removed"])
        body.append(f"<div class=card><span class=name>{esc(r['name'])}</span>"
                    f"<span class='{pcls}'>{pill}</span>{toks}"
                    f"<div class=sub>{r['count']} ценови стойности · "
                    f"<a href='{esc(r['url'])}' target=_blank>{esc(r['url'])}"
                    f"</a></div></div>")
    return admin_shell("Цени",
                       f"{bg_dt()} ч. · нормализирано в евро, курс "
                       f"≈ {str(pc.fx_usd_eur()).replace('.', ',')} USD→EUR",
                       NAV, "".join(body), extra_js=SORT_JS,
                       active="pricing.html")


# --------------------------------------------------------------------------
# Функции (battlecard)
# --------------------------------------------------------------------------
FEATURE_LABELS = {
    "free_tier": "Безплатен план или пробен период",
    "txn_fees": "Такси върху продажбите",
    "pos": "Вграден POS за физическа търговия",
    "b2b": "B2B и търговия на едро",
    "multilang": "Многоезичен магазин",
    "multicurrency": "Продажби в няколко валути",
    "ai_tools": "AI инструменти",
    "app_store": "Магазин за приложения",
    "api_headless": "API и headless",
    "hosting": "Хостинг, SSL и CDN включени",
    "eu_local": "Пригодност за България и ЕС",
    "support": "Поддръжка",
    "gmv_caps": "Лимити на оборота",
}
STATUS_MARK = {
    "yes": ("badge-ok", "Да"),
    "partial": ("badge-warn", "Частично"),
    "addon": ("badge-warn", "С добавка"),
    "no": ("badge-err", "Не"),
    "unknown": ("badge-na", "Непотвърдено"),
}
# При тези възможности отсъствието е предимството (няма такси, няма лимити):
# значките и сметката за силни страни обръщат полярността.
INVERTED_KEYS = {"txn_fees", "gmv_caps"}
STATUS_MARK_INV = {
    "no": ("badge-ok", "Няма"),
    "partial": ("badge-warn", "Частично"),
    "addon": ("badge-warn", "Частично"),
    "yes": ("badge-err", "Има"),
    "unknown": ("badge-na", "Непотвърдено"),
}


def _mark(key, status):
    table = STATUS_MARK_INV if key in INVERTED_KEYS else STATUS_MARK
    return table.get(status, ("badge-na", "?"))


def _is_good(key, status):
    return status == "no" if key in INVERTED_KEYS else status == "yes"


def build_features_dash(feature_data, positioning=None):
    """feature_data: {vendor: {"features": {key: {status, note, source_url}},
    "summary": str}}; positioning: кураторският блок от features.json."""
    if not feature_data:
        return admin_shell("Функции", "Данните още се събират.", NAV,
                           "<div class=empty>Матрицата на възможностите се "
                           "изгражда. Опитайте при следващото събиране.</div>",
                           active="features.html")
    vendors = [pc.CC] + sorted(v for v in feature_data if v != pc.CC)
    vendors = [v for v in vendors if v in feature_data]

    def get(v, key):
        return (feature_data[v]["features"] or {}).get(key)

    pos = positioning or {}
    n_diff = len(pos.get("differentiators") or [])
    n_gaps = sum(len(v) for v in (pos.get("gaps") or {}).values())
    kpis = kpi_row([
        (len(FEATURE_LABELS), "сравнени възможности", False),
        (len(vendors), "платформи", False),
        (n_diff, "само при нас", False),
        (n_gaps, "полета за догонване", bool(n_gaps)),
    ])

    head = "".join(f"<th>{esc(h)}</th>"
                   for h in ["Възможност"] + vendors)
    ncols = len(vendors) + 1
    rows = []
    for key, label in FEATURE_LABELS.items():
        # ред за бърз преглед: само присъди, детайлът се отваря с клик
        cells = [f"<td><span class=fname>{esc(label)}</span> "
                 f"<span class=fhint>детайли</span></td>"]
        detail = []
        for v in vendors:
            f = get(v, key)
            if not f:
                cells.append(f"<td class=na>{EMPTY}</td>")
                continue
            cls, mark = _mark(key, f["status"])
            note = esc(f.get("note") or "")
            cells.append(f"<td><span class='badge {cls}' title=\"{note}\">"
                         f"{mark}</span></td>")
            src = f.get("source_url") or ""
            srcline = (f"<div class=sub><a href='{esc(src)}' target=_blank>"
                       f"източник</a></div>" if src else "")
            ours = " ours" if v == pc.CC else ""
            detail.append(f"<div class='fd{ours}'><div class=fdv>{esc(v)} "
                          f"<span class='badge {cls}'>{mark}</span></div>"
                          f"<div class=fdnote>{note}</div>{srcline}</div>")
        rows.append(f"<tr class=frow data-k='{key}'>{''.join(cells)}</tr>")
        rows.append(f"<tr class=fdetail id='d-{key}' style='display:none'>"
                    f"<td colspan={ncols}><div class=fdgrid>"
                    f"{''.join(detail)}</div></td></tr>")

    matrix = (f"<div class=tablewrap><table class='dense matrix'><thead><tr>"
              f"{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
              "<div class=basis>Погледът върху значките показва къде печелим "
              "и къде не. Клик върху ред отваря пълните бележки с цитат за "
              "търговски разговор и връзка към проверения източник за всяка "
              "платформа.</div>")

    body = [kpis, "<h2>Матрица на възможностите</h2>", matrix]

    # Стратегическа позиция: курирана от екипа, не изведена механично —
    # фокус върху функционалност и въздействие, по измерения.
    diffs = pos.get("differentiators") or []
    if diffs:
        body.append("<h2>Само при нас: с какво се отличаваме</h2>")
        for d in diffs:
            body.append(f"<div class=card><span class=name>"
                        f"{esc(d['title'])}</span> <span class='badge "
                        f"badge-ok'>отличител</span>"
                        f"<div class=sub>{esc(d['note'])}</div></div>")
    adv = pos.get("advantages") or {}
    if adv:
        body.append("<h2>Къде водим</h2>")
        for dim, points in adv.items():
            pts = "".join(f"<div class=sub>• {esc(p)}</div>" for p in points)
            body.append(f"<div class=card><span class=name>{esc(dim)}</span>"
                        f"{pts}</div>")
    gaps_d = pos.get("gaps") or {}
    if gaps_d:
        body.append("<h2>Къде догонваме: технология, финанси, маркетинг</h2>")
        for dim, points in gaps_d.items():
            pts = "".join(f"<div class=sub>• {esc(p)}</div>" for p in points)
            body.append(f"<div class=card><span class=name>{esc(dim)}</span>"
                        f" <span class='badge badge-warn'>за догонване"
                        f"</span>{pts}</div>")
    if pos:
        body.append("<div class=basis>Позицията е курирана от екипа върху "
                    "проверените факти от матрицата и данните от мониторинга "
                    "(реклами, видео ритъм, наличност); редактира се в "
                    "features.json → positioning.</div>")

    body.append("<h2>Резюме по платформа</h2>")
    for v in vendors:
        body.append(f"<div class=card><span class=name>{esc(v)}</span>"
                    f"<div class=sub>{esc(feature_data[v].get('summary', ''))}"
                    f"</div></div>")
    features_js = """
document.querySelectorAll('tr.frow').forEach(function(r){
r.addEventListener('click',function(e){
if(e.target.closest('a'))return;
var d=document.getElementById('d-'+r.dataset.k);
var open=d.style.display!=='none';
d.style.display=open?'none':'';
r.classList.toggle('open',!open);});});
"""
    return admin_shell("Функционалности",
                       f"{bg_dt()} ч. · проверени срещу официалните страници",
                       NAV, "".join(body), extra_js=features_js,
                       active="features.html")


# --------------------------------------------------------------------------
# Наличност
# --------------------------------------------------------------------------
def build_availability_dash(status):
    comp = {v: s for v, s in status.items() if v != pc.CC}
    total_inc = sum(s["incidents_30d"] for s in comp.values())
    total_down = sum(s["downtime_30d_min"] for s in comp.values())
    cc = status.get(pc.CC)
    worst = max(comp.items(), key=lambda kv: kv[1]["downtime_30d_min"],
                default=(None, None))
    kpis = kpi_row([
        (bg_down(cc["downtime_30d_min"]) if cc else EMPTY,
         "CloudCart, 30 дни", False),
        (bg_down(total_down), "конкурентите общо, 30 дни", total_down > 60),
        (total_inc, "инциденти при конкурентите", False),
        (esc(worst[0]) if worst[0] else EMPTY, "най-ненадежден конкурент",
         False),
    ])
    max_down = max([s["downtime_30d_min"] for s in status.values()] + [1])
    bars = []
    for v, s in sorted(status.items(),
                       key=lambda kv: -kv[1]["downtime_30d_min"]):
        w = max(s["downtime_30d_min"] / max_down * 100, 1)
        cls = "ours" if v == pc.CC else ""
        bars.append(f"<div class=barrow><div class=barlabel>{esc(v)}</div>"
                    f"<div class=bartrack><div class='bar {cls}' "
                    f"style='width:{w:.1f}%'></div><span class=barval>"
                    f"{bg_down(s['downtime_30d_min'])}</span></div></div>")
    body = [kpis, "<h2>Недостъпност, последни 30 дни</h2>",
            "<div class=bars>" + "".join(bars) + "</div>",
            "<div class=basis>Минути в инцидент по публичната статус "
            "страница на всяка платформа (поддръжката е изключена). "
            "CloudCart е в лилаво. Уговорка: платформите сами докладват — "
            "тих канал може да значи надеждност ИЛИ премълчаване; Shopify "
            "не е публикувал инцидент от 06.2025 г.</div>",
            "<h2>Инциденти по платформа</h2>"]
    for v, s in status.items():
        if s["kind"] == "none":
            body.append(f"<div class=card><span class=name>{esc(v)}</span> "
                        f"<span class='badge badge-na'>без публична статус "
                        f"страница</span></div>")
            continue
        inc = "".join(
            f"<div class=sub>• {esc(r['start'])}: {esc(r['name'])} "
            f"[{r['impact']}] · {bg_down(r['minutes'])}"
            f"{'' if r['resolved'] else ' · <b>ТЕЧАЩ</b>'}</div>"
            for r in s["recent"]) or "<div class=sub>Няма скорошни инциденти.</div>"
        note = (" <span class=approx>(7-дневен прозорец)</span>"
                if s["kind"] == "uptimerobot" else "")
        body.append(
            f"<div class=card><span class=name>{esc(v)}</span> "
            f"{status_badge(s, v + '-d')} "
            f"<span class=sub>{esc(s['description'])}</span>"
            f"<div class=sub><b>{s['incidents_30d']}</b> инцидента{note} · "
            f"<b>{bg_down(s['downtime_30d_min'])}</b> недостъпност · "
            f"<a href='{esc(s['page'])}' target=_blank>статус страница</a>"
            f"</div>{inc}</div>")
    return admin_shell("Наличност",
                       f"{bg_dt()} ч. · значките се опресняват на живо",
                       NAV, "".join(body),
                       extra_js=live_status_js(status) + SORT_JS,
                       active="availability.html")


# --------------------------------------------------------------------------
# Пазарна активност
# --------------------------------------------------------------------------
def build_activity_dash(items, days, problems):
    import datetime as _dtm
    ranked = sorted(items, key=lambda i: ((i.get("score") or 0),
                                          i.get("date") or _dtm.datetime.min),
                    reverse=True)
    signal_items = [i for i in items if i["signals"]]
    prio = [i for i in items if (i.get("score") or 0) >= PRIO_SCORE]
    ai_items = [i for i in items if set(i["signals"]) & THEMES[0][2]]
    srcs = sorted({i["source"] for i in items})
    kpis = kpi_row([
        (len(items), f"публикации, {days} дни", False),
        (len(prio), "приоритетни", bool(prio)),
        (len(ai_items), "за AI и агенти", bool(ai_items)),
        (len(signal_items), "със сигнал", False),
        (len(srcs), "активни източници", False),
    ])
    chips = ["<div class=chips>"]
    chips.append("<button type=button class=chip data-tag=prio>"
                 "Само приоритетни</button>")
    for slug, label, _ in THEMES:
        chips.append(f"<button type=button class=chip data-tag={slug} "
                     f"data-group=theme>{label}</button>")
    for slug, label in (("community", "Общности"), ("platform", "Платформи"),
                        ("newsletter", "Бюлетини"), ("press", "Преса")):
        chips.append(f"<button type=button class=chip data-tag={slug} "
                     f"data-group=src>{label}</button>")
    chips.append("</div>")

    body = [kpis, "".join(chips),
            "<input id=filterbox placeholder='Филтрирай по дума, източник "
            "или сигнал'>",
            f"<h2>Поток по приоритет · показани <span id=viscount>"
            f"{len(ranked)}</span> публикации</h2>",
            "<div class=filterable>"]
    for it in ranked:
        body.append(news_card(it, show_score=True))
    body.append("</div>")
    broken = [p for p in problems if "работи, но" not in p]
    if broken:
        body.append("<div class=warn><b>ИЗТОЧНИЦИ ЗА ПРОВЕРКА</b><ul>"
                    + "".join(f"<li>{esc(p)}</li>" for p in broken)
                    + "</ul></div>")
    return admin_shell("Пазарна активност",
                       f"{bg_dt()} ч. · подредено по приоритет · дневници на "
                       f"платформите, браншова преса и общности · последни "
                       f"{days} дни", NAV,
                       "".join(body), extra_js=FILTER_JS + FAV_JS,
                       active="activity.html")


# --------------------------------------------------------------------------
# Социални и реклами
# --------------------------------------------------------------------------
def build_social_dash(social):
    active = [v for v, s in social.items() if (s.get("videos_30d") or 0) > 0]
    kpis = kpi_row([
        (len(social), "следени платформи", False),
        (len(active), "с видео този месец", False),
        (sum(s.get("videos_30d") or 0 for s in social.values()),
         "видеа за 30 дни, общо", False),
    ])
    body = [kpis]
    for v, so in social.items():
        lv = so.get("latest_video") or {}
        facts = []
        if so.get("videos_30d") is not None:
            facts.append(f"<b>{so['videos_30d']}</b> видеа за 30 дни")
        gc = so.get("google_count")
        if gc:
            facts.append(f"<b>{bg_num(gc['lo'])}–{bg_num(gc['hi'])}</b> "
                         f"активни Google реклами (регион {esc(gc['region'])})")
        api = so.get("ads_api")
        if api:
            facts.append(f"<b>{api['active_ads']}</b> активни Meta реклами · "
                         f"обхват в ЕС ≈ {bg_num(api['eu_reach_sample'])}")
        tt = so.get("tiktok")
        if tt:
            facts.append(f"TikTok: <b>{bg_num(tt['videos'])}</b> видеа · "
                         f"{bg_num(tt['followers'])} последователи")
        note = (f"<div class=sub>{esc(so['note'])}</div>"
                if so.get("note") else "")
        flagged = note + "".join(f"<div class=sub>• {esc(t[:90])}</div>"
                                 for t in so.get("flagged_titles", []))
        latest = (f"<div class=sub>Най-ново: <a href='"
                  f"{esc(lv.get('link', ''))}' target=_blank>"
                  f"{esc((lv.get('title') or '')[:80])}</a> "
                  f"({esc(lv.get('date', ''))})</div>" if lv else "")
        links = "".join(
            f"<a href='{esc(u)}' target=_blank>{k.replace('_', ' ')}</a>"
            for k, u in (so.get("links") or {}).items())
        if so.get("channel"):
            links = (f"<a href='{esc(so['channel'])}' target=_blank>"
                     f"youtube</a>") + links
        body.append(
            f"<div class=card><span class=name>{esc(v)}</span>"
            f"<div class=cellmain style='margin-top:4px'>"
            f"{' · '.join(facts) if facts else 'няма данни за активност'}"
            f"</div>{latest}{flagged}"
            f"<div class='sub linkrow' style='margin-top:6px'>{links}</div>"
            f"</div>")
    body.append(
        "<div class=basis>Видео ритъмът идва от публичните канали в YouTube. "
        "Google броячите са от Центъра за прозрачност на рекламите (без "
        "удостоверяване; Wix рекламира чрез регионални дружества, затова има "
        "само търсеща връзка). Библиотеката на Meta е на един клик за всяка "
        "платформа и показва обхват в ЕС ПО ДЪРЖАВИ (данни по DSA) — "
        "най-бързият поглед къде рекламират агресивно. Задайте METAAD_TOKEN, "
        "за да влизат броячите на Meta автоматично.</div>")
    return admin_shell("Социални и реклами", f"{bg_dt()} ч.", NAV,
                       "".join(body), extra_js=SORT_JS, active="social.html")


# --------------------------------------------------------------------------
# Запазени публикации (изцяло от localStorage; страницата е статична)
# --------------------------------------------------------------------------
def build_saved_page():
    saved_js = """
var box=document.getElementById('savedlist');
function render(){
var f=ccFavs(),arr=Object.keys(f).map(function(k){return f[k]})
.sort(function(a,b){return (b.ts||0)-(a.ts||0)});
document.getElementById('savedcount').textContent=arr.length;
box.textContent='';
if(!arr.length){var e=document.createElement('div');e.className='empty';
e.textContent='Няма запазени публикации. Отбележете със знака за '+
'запазване върху която и да е картичка в „Табло“ или „Пазарна активност“.';
box.appendChild(e);return;}
arr.forEach(function(d){
var c=document.createElement('div');c.className='card';
var rm=document.createElement('button');rm.className='favbtn on';
rm.title='Премахни от запазените';
rm.innerHTML=%s;
rm.addEventListener('click',function(){var f=ccFavs();delete f[d.u];
ccFavsSave(f);render();});
c.appendChild(rm);
var a=document.createElement('a');a.href=d.u;a.target='_blank';
a.textContent=d.t;c.appendChild(a);
if(d.g&&d.g.length){var gs=document.createElement('div');
d.g.forEach(function(s){var sp=document.createElement('span');
sp.className='sig';sp.textContent=s;gs.appendChild(sp);});c.appendChild(gs);}
var r=document.createElement('div');r.className='row';
var s1=document.createElement('span');s1.className='src';s1.textContent=d.s;
var s2=document.createElement('span');
s2.textContent=(d.d||'')+' · запазено '+new Date(d.ts||0)
.toLocaleDateString('bg-BG');
r.appendChild(s1);r.appendChild(s2);c.appendChild(r);
box.appendChild(c);});}
render();
""" % json.dumps(_BOOKMARK)
    body = (kpi_row([("<span id=savedcount>0</span>", "запазени публикации",
                      False)])
            + "<h2>За четене по-късно</h2><div id=savedlist></div>"
            "<div class=basis>Запазените се пазят локално в този браузър "
            "(localStorage), затова остават и след като публикацията излезе "
            "от 7-дневния прозорец на потока. Друг браузър или устройство "
            "има свой собствен списък.</div>")
    return admin_shell("Запазени", "лично, само в този браузър", NAV, body,
                       extra_js=FAV_JS + saved_js, active="saved.html")


# --------------------------------------------------------------------------
# Източници и методика
# --------------------------------------------------------------------------
def build_sources_dash(trouble, hist_dates, days):
    kpis = kpi_row([
        (len(hist_dates), "дни история", False),
        (len([t for t in trouble if "работи, но" not in t]),
         "източници за преглед", bool([t for t in trouble if "работи, но" not in t])),
        ("06:00 UTC", "дневно събиране (CI)", False),
    ])
    quiet = [t for t in trouble if "работи, но" in t]
    broken = [t for t in trouble if "работи, но" not in t]
    body = [kpis, "<h2>Здраве на източниците при това събиране</h2>"]
    if broken:
        body.append("<div class=warn><b>ИЗТОЧНИЦИ ЗА ПРОВЕРКА</b><ul>"
                    + "".join(f"<li>{esc(t)}</li>" for t in broken)
                    + "</ul></div>")
    else:
        body.append("<div class=empty>Няма повредени източници.</div>")
    if quiet:
        body.append("<h2>Тихи източници</h2><div class=basis>Тези канали "
                    "отговарят нормално, просто нямат публикация в прозореца "
                    "на събиране. Не изискват действие: нискочестотните "
                    "(месечни издания, GitHub releases) се появяват тук "
                    "редовно.</div>"
                    + "".join(f"<div class=sub>• {esc(t)}</div>"
                              for t in quiet))
    body.append("""
<h2>Какво се следи и как</h2>
<div class=card><span class=name>Цени на планове</span><div class=sub>
Структурирано извличане от живите ценови страници (включително нашата, като
база), нормализирано в евро, сравнявано по план всеки ден. Рецептите са
проверени срещу живите страници от независим втори агент.</div></div>
<div class=card><span class=name>Отпечатъци на ценови страници</span>
<div class=sub>Всички валутни стойности на страницата, сравнени с предния
ден — мрежата, която улавя тихи редакции.</div></div>
<div class=card><span class=name>Наличност</span><div class=sub>
Публичните статус API-та (Statuspage и UptimeRobot): инциденти и изчислена
недостъпност за 30 дни; значките се опресняват на живо. Данните са
самодокладвани от платформите.</div></div>
<div class=card><span class=name>Пазарна активност</span><div class=sub>
RSS и Atom от дневниците на платформите, браншовата преса и общностите
(Reddit), с маркиране по ключови думи: цени, AI, плащания, миграция,
сривове.</div></div>
<div class=card><span class=name>Социални и реклами</span><div class=sub>
Публични канали в YouTube (ритъм и език на пусканията), Център за
прозрачност на Google (брой активни реклами), Библиотека с реклами на Meta
(връзки; обхват в ЕС по държави в интерфейса на Meta, програмно с
METAAD_TOKEN).</div></div>
<div class=card><span class=name>Функционалности</span><div class=sub>
Матрицата на възможностите е изследвана срещу официалните страници на
платформите и проверена от независим агент; всяка клетка носи източник.
</div></div>
<h2>Износ за анализ</h2>
<div class=card><span class=name>Дневна история</span><div class=sub>
history/daily.jsonl: по един запис на платформа на ден (цени, планове,
наличност, активност). Натрупва се от CI без ограничение.</div></div>
<div class=card><span class=name>Месечни CSV файлове</span><div class=sub>
exports/ГГГГ-ММ-daily.csv (ден по ден) и -summary.csv (обобщение по
платформа: влошени дни, ценови промени, недостъпност) — опресняват се
всеки ден и са готови за Excel или BI сравнение с вътрешните ни числа.
</div></div>""")
    return admin_shell("Източници", f"{bg_dt()} ч.", NAV, "".join(body),
                       active="sources.html")


# --------------------------------------------------------------------------
def build_email(items, results, days, plans, plan_changes, status):
    """Кратък бюлетин за писмо: без лента, скриптове и относителни връзки."""
    changed = [r for r in results if r["status"] == "changed"]
    degraded = [v for v, s in status.items()
                if s["indicator"] in ("minor", "major", "critical")]
    out = [kpi_row([(len(plan_changes), "промени в планове", bool(plan_changes)),
                    (len(changed), "промени по страници", bool(changed)),
                    (len(degraded), "влошени сега", bool(degraded))])]
    out.append("<h2>Промени по планове</h2>")
    out.append(pc.render_plan_changes(plan_changes))
    if degraded:
        out.append("<h2>Влошени платформи</h2>")
        for v in degraded:
            out.append(f"<div class=card><span class=name>{esc(v)}</span> "
                       f"<span class=sub>{esc(status[v]['description'])}"
                       f"</span></div>")
    sig = sorted((i for i in items if i["signals"]),
                 key=lambda i: (i.get("score") or 0), reverse=True)[:8]
    if sig:
        out.append(f"<h2>Основни сигнали, {days} дни</h2>")
        for it in sig:
            out.append(f"<div class=card><a href='{esc(it['link'])}'>"
                       f"{esc(it['title'])}</a><div class=sub>"
                       f"{esc(it['source'])}</div></div>")
    return shell("Конкурентно разузнаване: дневен бюлетин",
                 f"{bg_dt()} ч.", "".join(out))
