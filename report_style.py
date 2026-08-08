#!/usr/bin/env python3
"""
report_style.py
===============
Визуалният слой на всички страници: CloudCart Admin Design System,
1:1 по подадените файлове (theme.css / design.json, семе #8D58E0).

Спазени правила от дизайн брифа (Демо-Магазин-DESIGN-SYSTEM-PROMPT.md):
  * марковият цвят само на шестте места (бутон, връзка, фокус, избрана
    навигация 5–8 %, активен таб, включени контроли); всичко структурно
    е неутрално;
  * рамки, не сенки; три равнини (лента < фон < карта);
  * без емоджи, без движение при посочване, без акцентни ленти по ръба;
  * български интерфейс, дати с точки, числа „1 240,50“, валута след
    числото;
  * tabular-nums на корена, без лигатури в клетки с данни;
  * фокус пръстенът не подлежи на договаряне;
  * Montserrat се сервира локално (reports/fonts/montserrat-var.woff2,
    подрязан с pyftsubset), не от CDN.

Тъмната тема е преизчислена (не обърната) — стойностите идват от
theme.css; превключва се с data-theme="dark", пази се в localStorage.
Цветове за графики: светла #7344BB/#2B7FFF (валидирани), тъмна
#AE82FF/#1CCFB9 (официалните chart токени на системата).
"""

import datetime as _dt


def utcnow():
    """Naive UTC timestamp (datetime.utcnow() replacement, no warning)."""
    return _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)


def to_sofia(d):
    """Наивен UTC -> наивно софийско време (Europe/Sofia, с лятно часово)."""
    try:
        from zoneinfo import ZoneInfo
        aware = d.replace(tzinfo=_dt.timezone.utc)
        return aware.astimezone(ZoneInfo("Europe/Sofia")).replace(tzinfo=None)
    except Exception:
        return d + _dt.timedelta(hours=3)      # разумен резерв за лятото


def bg_dt(dt_obj=None):
    """24.07.2026 14:05 — датите са с точки, часът в 24-часов формат,
    показан в софийско време."""
    d = to_sofia(dt_obj or utcnow())
    return d.strftime("%d.%m.%Y %H:%M")


def bg_when(d):
    """Кога е публикувано: относително до 24 ч. („преди 42 мин“), после
    абсолютно с час („06.08 14:05“). По конвенцията на дизайн брифа."""
    if not d:
        return "–"
    secs = (utcnow() - d).total_seconds()
    if 0 <= secs < 3600:
        return f"преди {max(int(secs // 60), 1)} мин"
    if 0 <= secs < 24 * 3600:
        return f"преди {int(secs // 3600)} ч."
    return to_sofia(d).strftime("%d.%m %H:%M")


def bg_num(x, dec=0):
    """1 240,50 — интервал за хилядите, запетая за десетичните."""
    s = f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s


FONTS = ""      # шрифтът е локален @font-face в CSS, без външни заявки

CSS = """
@font-face{font-family:"Montserrat";
src:url("fonts/montserrat-var.woff2") format("woff2-variations");
font-weight:100 900;font-style:normal;font-display:swap}
:root{
--bg:#F4F5F9;--fg:#24252D;--card:#FFFFFF;--muted:#585F71;--mid:#8380AB;
--border:#DBDEEA;--border-1:#EBEDF4;
--primary:#7344BB;--primary-hover:#9D67F4;--on-primary:#FFFFFF;
--primary-soft:rgba(115,68,187,.07);
--side-bg:#EBEDF4;--side-fg:#716E94;--side-border:#C5C9DC;
--ok-bg:#D5F6E3;--ok-fg:#06281E;--warn-bg:#FEF9C3;--warn-fg:#422006;
--err-bg:#FFE0E0;--err-fg:#490606;--destructive:#E91A19;
--input:#FFFFFF;--ghost-fg:#6D758A;--ghost-hover:#0000000D;
--focus:#9D67F4;
--chart-ours:#7344BB;--chart-comp:#2B7FFF;
--r-xs:2px;--r-sm:4px;--r-md:6px;--r-lg:8px;--r-xl:12px;
--row-h:50px;--row-pad-y:9px;
--dur-fast:100ms;--dur-base:160ms;--dur-slow:240ms;
--ease:cubic-bezier(.19,.91,.38,1)}
[data-theme="dark"]{
--bg:#0A0A14;--fg:#F7F8F8;--card:#1A1A2B;--muted:#8C93A4;--mid:#AEB1CD;
--border:#34314E;--border-1:#1A1A2B;
--primary:#AE82FF;--primary-hover:#C9B1FF;--on-primary:#1A1A2B;
--primary-soft:rgba(174,130,255,.10);
--side-bg:#1A1A2B;--side-fg:#C5C9DC;--side-border:#34314E;
--ok-bg:#7BDAAD;--ok-fg:#06281E;--warn-bg:#FEF08A;--warn-fg:#422006;
--err-bg:#FFA09F;--err-fg:#490606;--destructive:#FF6867;
--input:#FFFFFF0D;--ghost-fg:#DBDEEA;--ghost-hover:#FFFFFF1A;
--focus:#C9B1FF;
--chart-ours:#AE82FF;--chart-comp:#1CCFB9}
*{box-sizing:border-box}
html{font-family:"Montserrat",system-ui,sans-serif;font-size:15px;
line-height:23px;color:var(--fg);background:var(--bg);
font-variant-numeric:tabular-nums lining-nums}
body{margin:0;background:var(--bg);color:var(--fg);font-size:15px;
line-height:23px}
:is(td,th,.sku,.mono,input,code,.num){font-variant-ligatures:none;
font-feature-settings:"liga" 0,"calt" 0,"dlig" 0}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
a{color:var(--primary);text-decoration:none}
a:hover{color:var(--primary-hover)}
h1,h2,h3,h4,h5{margin:0;color:var(--fg)}
h1{font-size:28px;line-height:36px;font-weight:600}
h3{font-size:19px;line-height:27px;font-weight:600}
h4{font-size:15px;line-height:22px;font-weight:600}
/* ---------- обикновена рамка (под-справки, писма) ---------- */
.wrap{max-width:900px;margin:0 auto;padding:24px 16px 60px}
/* ---------- админ рамка: лента < фон < карта ---------- */
.app{display:flex;min-height:100vh}
.side{flex:0 0 200px;background:var(--side-bg);
border-right:1px solid var(--side-border);padding:16px 0;
position:sticky;top:0;height:100vh;overflow-y:auto}
.side .mark{display:block;padding:0 16px 14px;font-weight:700;font-size:17px;
color:var(--fg);border-bottom:1px solid var(--side-border);margin-bottom:10px}
.side .tagl{display:block;font-size:12px;line-height:17px;font-weight:600;
letter-spacing:.44px;color:var(--side-fg);margin-top:2px}
.sitem{display:block;padding:9px 16px;font-size:14px;line-height:20px;
font-weight:600;color:var(--side-fg);
transition:background var(--dur-fast) var(--ease),color var(--dur-fast) var(--ease)}
.sitem:hover{background:var(--ghost-hover);color:var(--fg)}
.sitem.on{background:var(--primary-soft);color:var(--primary)}
.side .sfoot{padding:12px 16px;font-size:11px;line-height:16px;
color:var(--side-fg);border-top:1px solid var(--side-border);margin-top:12px}
.themebtn{display:inline-flex;align-items:center;gap:6px;margin:10px 16px 0;
padding:6px 10px;background:transparent;border:1px solid var(--side-border);
border-radius:var(--r-md);color:var(--side-fg);font:inherit;font-size:12px;
font-weight:600;cursor:pointer}
.themebtn:hover{background:var(--ghost-hover)}
.themebtn svg{width:13px;height:13px}
.main{flex:1;min-width:0;max-width:1280px;padding:24px 24px 80px}
.page-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:12px;
margin-bottom:16px}
.page-head h1{font-size:28px;line-height:36px;font-weight:600}
.page-head .meta{margin:0}
@media(max-width:800px){.app{display:block}
.side{position:static;height:auto;width:100%;border-right:none;
border-bottom:1px solid var(--side-border);display:flex;flex-wrap:wrap;
align-items:center;gap:2px;padding:8px 12px}
.side .mark{border:none;margin:0;padding:0 12px 0 0}
.side .tagl{display:none}.side .sfoot{display:none}.themebtn{margin:0}
.sitem{border-radius:var(--r-md);padding:5px 10px}
.main{padding:16px 12px 60px}
body{font-size:16px}}
/* ---------- типография на секции ---------- */
.meta{color:var(--muted);font-size:13.5px;line-height:20px;margin-bottom:16px}
h2.sec,h2{font-size:18px;line-height:26px;font-weight:600;color:var(--fg);
margin:40px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--border)}
section{scroll-margin-top:16px}
/* ---------- карти ---------- */
.card{background:var(--card);border:1px solid var(--border);
border-radius:var(--r-lg);padding:12px 16px;margin-bottom:8px}
.card a{font-weight:600}
.row{display:flex;justify-content:space-between;gap:12px;margin-top:6px;
font-size:13.5px;line-height:20px;color:var(--muted)}
.src{color:var(--muted);font-weight:600}
.sig{display:inline-block;background:var(--primary-soft);color:var(--primary);
border-radius:var(--r-xs);padding:2px 8px;font-size:12.5px;line-height:18px;
font-weight:600;margin:6px 5px 0 0}
.empty{color:var(--muted);font-style:italic;font-size:14px}
.warn{margin-top:24px;font-size:13.5px;color:var(--muted);
border-top:1px solid var(--border);padding-top:12px}
.warn b{color:var(--err-fg);background:var(--err-bg);padding:1px 6px;
border-radius:var(--r-xs)}
.name{font-weight:600;color:var(--fg)}
.chg{font-weight:600;color:var(--warn-fg);background:var(--warn-bg);
padding:1px 6px;border-radius:var(--r-xs)}
.sub{font-size:13.5px;line-height:20px;color:var(--muted);margin-top:4px}
.sub a{font-weight:400}
/* ---------- значки ---------- */
.badge{display:inline-flex;align-items:center;gap:6px;font-size:13px;
line-height:19px;font-weight:600;padding:3px 10px;border-radius:var(--r-sm);
white-space:nowrap}
.badge .dt{width:6px;height:6px;border-radius:50%;background:currentColor}
.badge-ok{background:var(--ok-bg);color:var(--ok-fg)}
.badge-warn{background:var(--warn-bg);color:var(--warn-fg)}
.badge-err{background:var(--err-bg);color:var(--err-fg)}
.badge-na{background:transparent;color:var(--muted);
border:1px solid var(--border)}
.pill{font-size:12px;font-weight:600;padding:2px 9px;
border-radius:var(--r-sm);border:1px solid var(--border);color:var(--muted);
float:right}
.pill-hot{border-color:transparent;color:var(--err-fg);background:var(--err-bg)}
/* ---------- KPI ---------- */
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
gap:8px;margin-bottom:12px}
.tile{background:var(--card);border:1px solid var(--border);
border-radius:var(--r-lg);padding:12px 16px}
.tile .n{font-size:32px;line-height:38px;font-weight:600;color:var(--fg)}
.tile .n.hot{color:var(--destructive)}
.tile .l{font-size:12px;line-height:17px;font-weight:600;
letter-spacing:.44px;color:var(--muted);margin-top:2px}
/* ---------- бутони ---------- */
.btn{display:inline-block;background:var(--primary);color:var(--on-primary);
font-weight:600;font-size:14px;height:38px;line-height:38px;padding:0 18px;
border-radius:var(--r-md);text-decoration:none;margin:6px 8px 0 0;
transition:background var(--dur-fast) var(--ease)}
.btn:hover{background:var(--primary-hover);color:var(--on-primary)}
.btn.ghost{background:transparent;color:var(--primary);
border:1px solid var(--border);line-height:36px}
.btn.ghost:hover{background:var(--ghost-hover)}
/* ---------- таблици ---------- */
.tablewrap{overflow-x:auto;border:1px solid var(--border);
border-radius:var(--r-lg);background:var(--card)}
table.dense,.matrix{width:100%;border-collapse:collapse;font-size:14px;
line-height:21px;background:var(--card)}
.matrix{min-width:640px}
table.dense th,.matrix th{text-align:left;font-size:12px;line-height:17px;
font-weight:600;letter-spacing:.33px;color:var(--muted);
padding:8px 12px;border-bottom:1px solid var(--border);white-space:nowrap}
table.dense td,.matrix td{padding:var(--row-pad-y) 12px;
border-bottom:1px solid var(--border-1);vertical-align:middle;
height:var(--row-h)}
table.dense tbody tr:last-child td,.matrix tbody tr:last-child td{border-bottom:none}
table.dense tbody tr:hover td{background:var(--bg);
transition:background var(--dur-fast) var(--ease)}
td.num,.num{text-align:right;white-space:nowrap}
table.dense th.num{text-align:right;width:1%;white-space:nowrap;
padding-right:24px}
table.dense td.num{width:1%;padding-right:24px}
.matrix .vname a,.dense .vname a{color:var(--fg);font-weight:600}
.matrix tr.ours td,.dense tr.ours td{background:var(--primary-soft)}
.matrix .na{color:var(--mid)}
.pname{font-weight:600;color:var(--fg);font-size:13px;line-height:18px}
.pprice{margin-top:1px}
.approx{color:var(--muted);font-size:12.5px}
.delta{display:inline-block;font-size:12.5px;line-height:18px;font-weight:600;
border-radius:var(--r-sm);padding:1px 6px;margin-top:3px}
.delta.up{background:var(--ok-bg);color:var(--ok-fg)}
.delta.down{background:var(--err-bg);color:var(--err-fg)}
.basis{font-size:13px;line-height:19px;color:var(--muted);margin:10px 2px 0}
/* ---------- ленти (сравнение на величини) ---------- */
.bars{margin-top:4px}
.barrow{display:flex;align-items:center;gap:12px;padding:3px 0}
.barlabel{flex:0 0 230px;font-size:14px;font-weight:600;color:var(--fg);
text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bartrack{flex:1;display:flex;align-items:center;gap:8px}
.bar{height:14px;border-radius:0 var(--r-sm) var(--r-sm) 0;
background:var(--chart-comp);min-width:3px}
.bar.ours{background:var(--chart-ours)}
.barval{font-size:14px;color:var(--fg);white-space:nowrap}
@media(max-width:640px){.barlabel{flex-basis:120px}}
/* ---------- измерител в клетка ---------- */
.meter{display:inline-block;width:64px;height:6px;background:var(--bg);
border:1px solid var(--border);border-radius:3px;vertical-align:middle;
margin-right:6px}
.meter i{display:block;height:100%;background:var(--destructive);
border-radius:2px;min-width:2px}
.cellmain{color:var(--fg)}
.cellmain b{font-weight:600}
.okmuted{color:var(--muted)}
.linkrow a{display:inline-block;font-size:13px;font-weight:600;
margin-right:8px}
.foot{margin-top:40px;font-size:12px;line-height:17px;color:var(--muted);
border-top:1px solid var(--border);padding-top:12px}
.brand{display:flex;align-items:baseline;gap:10px;margin-bottom:16px;
border-bottom:1px solid var(--border);padding-bottom:12px}
.brand .mark{font-weight:700;font-size:17px;color:var(--fg)}
.brand .tag{font-size:12px;letter-spacing:.44px;color:var(--muted);
font-weight:600}
input#filterbox{width:100%;height:40px;background:var(--input);
border:1px solid var(--border);border-radius:var(--r-md);padding:0 12px;
font:inherit;color:var(--fg);margin-bottom:12px}
/* ---------- филтърни чипове (избраният е едно от шестте маркови места) --- */
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.chip{font:inherit;font-size:14px;line-height:20px;font-weight:600;
padding:6px 14px;background:var(--card);border:1px solid var(--border);
border-radius:var(--r-md);color:var(--muted);cursor:pointer;
transition:background var(--dur-fast) var(--ease),color var(--dur-fast) var(--ease)}
.chip:hover{background:var(--ghost-hover);color:var(--fg)}
.chip.on{background:var(--primary-soft);color:var(--primary);
border-color:transparent}
.newmark{display:inline-block;font-size:12px;line-height:17px;font-weight:600;
letter-spacing:.44px;color:var(--ok-fg);background:var(--ok-bg);
border-radius:var(--r-xs);padding:1px 6px;margin-right:6px}
.score{float:right;font-size:12.5px;color:var(--mid)}
/* ---------- матрица на възможностите: бърз преглед + детайл при клик --- */
tr.frow{cursor:pointer}
tr.frow:hover td{background:var(--bg)}
tr.frow.open td{background:var(--primary-soft)}
tr.frow .fname{font-weight:600;color:var(--fg)}
tr.frow .fhint{font-size:12.5px;color:var(--mid);font-weight:400}
tr.frow.open .fhint{color:var(--primary)}
tr.fdetail>td{background:var(--bg);padding:12px}
.fdgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));
gap:8px}
.fd{background:var(--card);border:1px solid var(--border);
border-radius:var(--r-md);padding:10px 12px}
.fd.ours{background:var(--primary-soft)}
.fdv{display:flex;justify-content:space-between;align-items:center;gap:8px;
font-weight:600;color:var(--fg)}
.fdnote{font-size:13.5px;line-height:20px;color:var(--muted);margin-top:6px}
.fd .sub{margin-top:6px}
"""

# Тема: чете localStorage преди боядисване (без проблясък), после бутонът
# превключва. Иконите са вграден SVG (Lucide sun/moon), не знаци.
_THEME_HEAD_JS = ("(function(){try{var t=localStorage.getItem('cc-theme');"
                  "if(t)document.documentElement.setAttribute('data-theme',t);"
                  "}catch(e){}})();")

_SUN = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/>'
        '<path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/>'
        '<path d="M2 12h2"/><path d="M20 12h2"/>'
        '<path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>')
_MOON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
         'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
         '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>')

_THEME_BTN_JS = """
var tb=document.getElementById('themebtn');
if(tb){tb.addEventListener('click',function(){
var r=document.documentElement,
d=r.getAttribute('data-theme')==='dark'?'':'dark';
if(d)r.setAttribute('data-theme',d);else r.removeAttribute('data-theme');
try{localStorage.setItem('cc-theme',d)}catch(e){}
tb.querySelector('.tlab').textContent=d?'Светла тема':'Тъмна тема';});}
"""

_HEAD = ('<!doctype html><html lang="bg"><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">')


def shell(title, subtitle, body_html):
    """Обикновена страница (под-справки, писма) — без странична лента."""
    return (
        f"{_HEAD}<title>{title}</title><script>{_THEME_HEAD_JS}</script>"
        f"{FONTS}<style>{CSS}</style>"
        f"<body><div class=wrap>"
        f"<header class=brand><span class=mark>CloudCart</span>"
        f"<span class=tag>Конкурентно разузнаване</span></header>"
        f"<h1>{title}</h1><div class=meta>{subtitle}</div>"
        f"{body_html}"
        f"<footer class=foot>ecommerce-intelligence, вътрешна употреба"
        f"</footer></div></body></html>"
    )


def admin_shell(title, subtitle, nav_items, body_html, extra_js="",
                active=""):
    """Админ рамка: странична лента (равнина 1) + съдържание.
    nav_items = [(href, надпис)]; active = текущата страница."""
    nav = "".join(
        f"<a class='sitem{' on' if href == active else ''}' "
        f"href='{href}'>{label}</a>" for href, label in nav_items)
    return (
        f"{_HEAD}<title>{title}</title><script>{_THEME_HEAD_JS}</script>"
        f"{FONTS}<style>{CSS}</style>"
        f"<body><div class=app>"
        f"<aside class=side><span class=mark>CloudCart"
        f"<span class=tagl>Конкурентно разузнаване</span></span>{nav}"
        f"<button class=themebtn id=themebtn type=button>{_MOON}"
        f"<span class=tlab>Тъмна тема</span></button>"
        f"<div class=sfoot>ecommerce-intelligence<br>вътрешна употреба</div>"
        f"</aside>"
        f"<main class=main>"
        f"<div class=page-head><h1>{title}</h1>"
        f"<div class=meta>{subtitle}</div></div>"
        f"{body_html}"
        f"<footer class=foot>ecommerce-intelligence, вътрешна употреба"
        f"</footer></main></div>"
        f"<script>{_THEME_BTN_JS}{extra_js}</script></body></html>"
    )
