"""学习面板渲染：Apple 桌面小组件风格，纯静态单文件。

数据在生成时嵌入 HTML，因此面板不需要前端请求、没有加载态，
打开即最新；链接由 GitHub Pages 固定，永远不变。
"""

from __future__ import annotations

import html

from .util import fmt_hours

CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#F5F5F7; --bg2:#EFEFF2; --card:#FFFFFF; --text:#1D1D1F; --sub:#6E6E73;
  --muted:#8E8E93; --line:#E8E8ED; --fill:#F2F2F7;
  --blue:#0A84FF; --violet:#5E5CE6; --teal:#00A6A6; --orange:#FF9F0A; --purple:#BF5AF2;
  --shadow:0 1px 2px rgba(0,0,0,.04),0 8px 28px rgba(0,0,0,.05);
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#000000; --bg2:#0B0B0D; --card:#1C1C1E; --text:#F5F5F7; --sub:#A1A1A6;
    --muted:#8E8E93; --line:#2C2C2E; --fill:#2C2C2E;
    --shadow:0 1px 2px rgba(0,0,0,.5),0 8px 28px rgba(0,0,0,.4);
  }
}
html{-webkit-text-size-adjust:100%}
body{
  background:radial-gradient(120% 80% at 50% 0%, var(--bg2) 0%, var(--bg) 55%);
  color:var(--text); min-height:100vh;
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","PingFang SC","Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased; padding:40px 20px 64px;
}
.wrap{max-width:1000px;margin:0 auto}
.topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:34px}
.brand{display:flex;align-items:center;gap:10px;font-size:15px;font-weight:650;letter-spacing:-.2px}
.brand svg{display:block}
.chip{
  font-size:12px;font-weight:600;color:var(--sub);background:var(--card);
  border:1px solid var(--line);padding:7px 13px;border-radius:999px;letter-spacing:.01em;
}
.hero{margin-bottom:26px}
.hero h1{font-size:34px;line-height:1.1;letter-spacing:-1.2px;font-weight:700}
.hero p{margin-top:10px;font-size:14.5px;color:var(--sub);letter-spacing:-.1px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.card{
  background:var(--card);border-radius:26px;padding:22px;box-shadow:var(--shadow);
  display:flex;flex-direction:column;justify-content:space-between;min-height:158px;
  border:1px solid rgba(0,0,0,.02);
}
@media (prefers-color-scheme: dark){.card{border-color:rgba(255,255,255,.04)}}
.s2{grid-column:span 2}.s4{grid-column:span 4}
.flat{justify-content:flex-start;min-height:auto}
.label{
  font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:var(--muted);display:flex;align-items:center;gap:7px;
}
.dot{width:7px;height:7px;border-radius:50%;flex:0 0 auto}
.num{font-size:40px;font-weight:700;letter-spacing:-1.8px;line-height:1;font-feature-settings:"tnum";margin-top:14px}
.num small{font-size:15px;font-weight:600;color:var(--muted);letter-spacing:-.2px;margin-left:3px}
.sub{font-size:13px;color:var(--sub);margin-top:9px;line-height:1.5}
.track{height:9px;border-radius:5px;background:var(--fill);overflow:hidden;margin-top:16px}
.track>i{display:block;height:100%;border-radius:5px;transform-origin:left;
  background:linear-gradient(90deg,#0A84FF,#5AC8FA);animation:grow 1.1s cubic-bezier(.22,1,.36,1) both}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.meta{display:flex;justify-content:space-between;align-items:baseline;margin-top:12px;font-size:12.5px;color:var(--sub)}
.meta b{color:var(--text);font-weight:650}

/* 14 格打卡条：每天一组，上=早场 下=晚场 */
.ticks{display:flex;gap:6px;margin-top:16px}
.day{flex:1;display:flex;flex-direction:column;gap:3px}
.day i{display:block;height:11px;border-radius:3px;background:var(--fill)}
.day i.on{background:linear-gradient(90deg,#0A84FF,#5AC8FA)}

/* 今日 */
.today{display:flex;flex-direction:column;gap:10px;margin-top:16px}
.slot{
  display:flex;align-items:center;gap:12px;padding:13px 15px;background:var(--fill);
  border-radius:16px;text-decoration:none;color:inherit;transition:transform .18s ease,opacity .18s ease;
}
.slot:hover{transform:translateY(-1px);opacity:.92}
.slot .time{font-size:12px;font-weight:700;color:var(--muted);letter-spacing:.02em;width:44px;flex:0 0 auto}
.slot .title{flex:1;font-size:13.5px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.slot .pill{font-size:11px;font-weight:700;padding:4px 9px;border-radius:999px;flex:0 0 auto}
.pill.done{background:rgba(48,209,88,.14);color:#28A745}
.pill.wait{background:rgba(142,142,147,.14);color:var(--muted)}

/* 板块 */
.sectors{display:flex;flex-direction:column;gap:13px;margin-top:16px}
.sec-row{display:flex;align-items:center;gap:11px;font-size:13px}
.sec-row .name{width:66px;flex:0 0 auto;color:var(--sub);font-weight:600}
.sec-row .bar{flex:1;height:7px;border-radius:4px;background:var(--fill);overflow:hidden}
.sec-row .bar i{display:block;height:100%;border-radius:4px;transform-origin:left;animation:grow 1s cubic-bezier(.22,1,.36,1) both}
.sec-row .val{width:34px;text-align:right;font-variant-numeric:tabular-nums;color:var(--text);font-weight:650;font-size:12.5px}

/* 列表 */
.list{display:flex;flex-direction:column;margin-top:6px}
.row{
  display:flex;align-items:center;gap:14px;padding:13px 2px;border-bottom:1px solid var(--line);
  text-decoration:none;color:inherit;transition:opacity .18s ease;
}
.row:last-child{border-bottom:none}
.row:hover{opacity:.6}
.row .d{font-size:12.5px;color:var(--muted);width:74px;flex:0 0 auto;font-variant-numeric:tabular-nums}
.row .t{flex:1;font-size:13.5px;font-weight:550;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .m{font-size:12px;color:var(--muted);flex:0 0 auto}
.row svg{opacity:.35;flex:0 0 auto}
.empty{padding:26px 0;text-align:center;color:var(--muted);font-size:13px}
.foot{margin-top:26px;font-size:11.5px;color:var(--muted);line-height:1.9;text-align:center}

@media (max-width:820px){
  body{padding:26px 16px 48px}
  .grid{grid-template-columns:repeat(2,1fr);gap:13px}
  .s4,.s2{grid-column:span 2}
  .hero h1{font-size:27px;letter-spacing:-.9px}
  .card{border-radius:22px;padding:19px;min-height:auto}
  .num{font-size:33px;letter-spacing:-1.3px}
}
@media (max-width:420px){
  .grid{grid-template-columns:1fr}
  .s4,.s2{grid-column:span 1}
}
"""

ICON = {
    "english": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
    "sector": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M7 14l3-4 3 3 4-6"/></svg>',
    "clock": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    "arrow": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>',
    "logo": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#0A84FF" stroke-width="1.6"/><path d="M2.6 13.6h18.8" stroke="#0A84FF" stroke-width="1.6" stroke-linecap="round"/><path d="M12 2.4a10 10 0 0 1 0 19.2" stroke="#5E5CE6" stroke-width="1.6"/></svg>',
}

SLOT_CN = {"morning": ("早场", "08:00"), "evening": ("晚场", "20:00")}


def _card_today(today: dict) -> str:
    rows = []
    for slot in ("morning", "evening"):
        info = today.get(slot) or {}
        cn, t = SLOT_CN[slot]
        done = bool(info.get("done"))
        title = info.get("title") or ("学习包尚未生成" if not done else "已完成")
        url = info.get("url") or ""
        pill = '<span class="pill done">已推送</span>' if done else '<span class="pill wait">待生成</span>'
        inner = f'<span class="time">{t}</span><span class="title">{html.escape(title)}</span>{pill}'
        if url:
            rows.append(f'<a class="slot" href="{html.escape(url)}">{inner}</a>')
        else:
            rows.append(f'<div class="slot">{inner}</div>')
    return f'<div class="today">{"".join(rows)}</div>'


def _ticks(week: dict) -> str:
    cells = []
    for d in week.get("daily", []):
        m = "on" if d.get("morning") else ""
        e = "on" if d.get("evening") else ""
        cells.append(
            f'<div class="day" title="{d["date"]} · {d["slots"]}/2 场">'
            f'<i class="{m}"></i><i class="{e}"></i></div>'
        )
    return f'<div class="ticks">{"".join(cells)}</div>'


def _sector_rows(week: dict) -> str:
    counts = week.get("sectors", {})
    total = max(1, sum(counts.values()))
    meta = [
        ("finance", "财经", "#00A6A6"),
        ("travel", "旅游", "#FF9F0A"),
        ("consumer", "消费品", "#BF5AF2"),
    ]
    rows = []
    for key, name, color in meta:
        n = counts.get(key, 0)
        width = max(4, int(n / total * 100)) if n else 0
        rows.append(
            f'<div class="sec-row"><span class="name">{name}</span>'
            f'<span class="bar"><i style="width:{width}%;background:{color}"></i></span>'
            f'<span class="val">{n}</span></div>'
        )
    return f'<div class="sectors">{"".join(rows)}</div>'


def _recent(rows: list[dict]) -> str:
    if not rows:
        return '<div class="empty">本周还没有学习包记录</div>'
    items = []
    for r in rows:
        cn, _ = SLOT_CN.get(r["slot"], (r["slot"], ""))
        date_label = r["date"][5:].replace("-", "/")
        m = f'{r["minutes"]} min'
        href = r.get("url") or "#"
        items.append(
            f'<a class="row" href="{html.escape(href)}">'
            f'<span class="d">{date_label} {cn}</span>'
            f'<span class="t">{html.escape(r["title"])}</span>'
            f'<span class="m">{m}</span>{ICON["arrow"]}</a>'
        )
    return f'<div class="list">{"".join(items)}</div>'


def render(week: dict, today: dict, recent: list[dict], updated_at: str, subtitle: str) -> str:
    pct = max(0.0, min(1.0, week.get("progress", 0)))
    remaining = max(0, week["slots_planned"] - week["slots_done"])
    eng_avg = round(week["english_minutes"] / week["english_count"]) if week["english_count"] else 0
    sec_avg = round(week["sector_minutes"] / week["sector_count"]) if week["sector_count"] else 0

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Daily Horizon ｜ 学习面板</title>
<style>{CSS}</style>
</head>
<body><div class="wrap">

  <div class="topbar">
    <div class="brand">{ICON["logo"]}<span>Daily Horizon</span></div>
    <div class="chip">{week['week']} · {week['week_start'][5:].replace('-', '/')} – {week['week_end'][5:].replace('-', '/')}</div>
  </div>

  <div class="hero">
    <h1>本周学习</h1>
    <p>{html.escape(subtitle)}</p>
  </div>

  <div class="grid">

    <div class="card s2">
      <div>
        <div class="label"><span class="dot" style="background:#0A84FF"></span>本周完成场次</div>
        <div class="num">{week['slots_done']}<small>/ {week['slots_planned']} 场</small></div>
        <div class="track"><i style="width:{int(pct*100)}%"></i></div>
        <div class="meta"><span>完成率 <b>{pct:.0%}</b></span><span>还剩 <b>{remaining}</b> 场</span></div>
      </div>
      {_ticks(week)}
    </div>

    <div class="card">
      <div class="label" style="color:var(--blue)">{ICON["english"]}英语精读</div>
      <div class="num">{week['english_count']}<small>篇</small></div>
      <div class="sub">{fmt_hours(week['english_minutes'])} 小时 · 均 {eng_avg} 分钟/篇</div>
    </div>

    <div class="card">
      <div class="label" style="color:var(--orange)">{ICON["sector"]}行业精读</div>
      <div class="num">{week['sector_count']}<small>篇</small></div>
      <div class="sub">{fmt_hours(week['sector_minutes'])} 小时 · 均 {sec_avg} 分钟/篇</div>
    </div>

    <div class="card s2">
      <div class="label" style="color:var(--violet)">{ICON["clock"]}今日安排</div>
      {_card_today(today)}
    </div>

    <div class="card s2">
      <div class="label"><span class="dot" style="background:#FF9F0A"></span>本周板块分布</div>
      {_sector_rows(week)}
      <div class="sub">累计 {fmt_hours(week['total_minutes'])} 小时 · 行业与英语分开计时</div>
    </div>

    <div class="card s4 flat">
      <div class="label">最近学习包</div>
      {_recent(recent)}
    </div>

  </div>

  <div class="foot">
    数据更新于 {html.escape(updated_at)}　·　每天早上 08:00 / 晚上 20:00 自动刷新<br>
    Daily Horizon 每次推送后自动重建本页，链接固定不变
  </div>

</div></body></html>"""
