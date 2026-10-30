"""学习包组装：把各板块内容拼成 Markdown 学习包与 HTML 邮件。"""

from __future__ import annotations

import html
import re

from . import mdhtml, reader, sources
from .util import fmt_hours, fmt_minutes

SLOT_LABEL = {"morning": ("早场", "08:00"), "evening": ("晚场", "20:00")}
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def date_cn(date_str: str) -> str:
    from datetime import datetime

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.year}年{dt.month}月{dt.day}日 {WEEKDAY_CN[dt.weekday()]}"


def pack_title(pack: dict) -> str:
    from datetime import datetime

    dt = datetime.strptime(pack["date"], "%Y-%m-%d")
    slot_cn, _ = SLOT_LABEL[pack["slot"]]
    return f"{dt.month}月{dt.day}日 · {slot_cn} · Daily Learning Pack"


def first_heading(md: str) -> str:
    m = re.search(r"^##\s*(?:\d+｜)?\s*(.+)$", md, re.M)
    return m.group(1).strip() if m else ""


# ------------------------------------------------------------------ Markdown
def to_markdown(pack: dict, week: dict) -> str:
    slot_cn, slot_time = SLOT_LABEL[pack["slot"]]
    lines = [
        f"# Daily Horizon ｜ {date_cn(pack['date'])} · {slot_cn}（{slot_time}）",
        "",
        "## 本周进度总览",
        "",
        f"- 本周已完成场次：**{week['slots_done']} / {week['slots_planned']}**（完成率 {week['progress']:.0%}）",
        f"- 英语精读：**{week['english_count']} 篇** ｜ 累计 **{fmt_hours(week['english_minutes'])} 小时**",
        f"- 行业精读：**{week['sector_count']} 篇** ｜ 累计 **{fmt_hours(week['sector_minutes'])} 小时**",
        f"- 本周累计学习时长：**{fmt_hours(week['total_minutes'])} 小时**",
        "",
        "---",
        "",
        f"## 英语精读 · {pack['english_minutes']} 分钟",
        "",
        pack["english_md"].strip(),
        "",
        "---",
        "",
    ]
    for sec in pack["sectors"]:
        meta = sources.SECTOR_META[sec["key"]]
        lead_mark = "　★ 本周主攻" if sec.get("is_lead") else ""
        lines += [
            f"## {meta['name']} · {sec['minutes']} 分钟{lead_mark}",
            "",
            sec["md"].strip(),
            "",
            "---",
            "",
        ]
    lines += [
        "> 本学习包由 Daily Horizon 自动生成。素材来源仅标注媒体名称，原文版权归原媒体所有。",
        "",
    ]
    return "\n".join(lines)


# ------------------------------------------------------------------ 组件
def _progress_card(week: dict, accent: str = "#0A84FF") -> str:
    pct = max(0.0, min(1.0, week.get("progress", 0)))
    bar_w = int(pct * 100)
    return f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F5F5F7;border-radius:16px;margin:0 0 8px;">
  <tr><td style="padding:18px 20px;">
    <div style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#8E8E93;text-transform:uppercase;margin-bottom:10px;">本周进度 · {week['week']}</div>
    <div style="font-size:26px;font-weight:700;color:#1D1D1F;letter-spacing:-0.5px;line-height:1.1;">
      {week['slots_done']}<span style="font-size:15px;color:#8E8E93;font-weight:500;"> / {week['slots_planned']} 场</span>
    </div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:12px 0 14px;">
      <tr>
        <td style="background:#E5E5EA;border-radius:4px;height:8px;">
          <table role="presentation" width="{bar_w}%" cellpadding="0" cellspacing="0">
            <tr><td style="background:{accent};border-radius:4px;height:8px;font-size:0;line-height:0;">&nbsp;</td></tr>
          </table>
        </td>
      </tr>
    </table>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td width="50%" style="font-size:12.5px;color:#6E6E73;line-height:1.7;">
          <b style="color:#1D1D1F;font-size:15px;">{week['english_count']}</b> 篇英语 · {fmt_hours(week['english_minutes'])} h<br>
          <b style="color:#1D1D1F;font-size:15px;">{week['sector_count']}</b> 篇行业 · {fmt_hours(week['sector_minutes'])} h
        </td>
        <td width="50%" align="right" style="font-size:12.5px;color:#6E6E73;line-height:1.7;">
          累计 <b style="color:#1D1D1F;font-size:15px;">{fmt_hours(week['total_minutes'])}</b> 小时<br>
          完成率 <b style="color:{accent};font-size:15px;">{pct:.0%}</b>
        </td>
      </tr>
    </table>
  </td></tr>
</table>"""


def _section_header(label: str, meta_line: str, color: str) -> str:
    return f"""
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:38px 0 4px;">
  <tr>
    <td width="4" style="background:{color};border-radius:2px;">&nbsp;</td>
    <td style="padding-left:12px;">
      <div style="font-size:12px;font-weight:700;letter-spacing:0.12em;color:{color};text-transform:uppercase;">{html.escape(label)}</div>
      <div style="font-size:12px;color:#8E8E93;margin-top:4px;">{html.escape(meta_line)}</div>
    </td>
  </tr>
</table>"""


# ------------------------------------------------------------------ 邮件
def to_email_html(pack: dict, week: dict, panel_url: str, mailbox_url: str, pack_url: str) -> str:
    slot_cn, slot_time = SLOT_LABEL[pack["slot"]]
    accent = "#0A84FF" if pack["slot"] == "morning" else "#5E5CE6"
    date_label = date_cn(pack["date"])

    blocks = [
        _section_header(
            f"英语精读 · English",
            f"{pack['english_minutes']} 分钟 ｜ {pack['english_words']} 词 ｜ {pack['english_articles']} 篇",
            accent,
        ),
        f'<div style="padding-top:14px;">{mdhtml.render(pack["english_md"], accent)}</div>',
    ]

    for sec in pack["sectors"]:
        meta = sources.SECTOR_META[sec["key"]]
        tag = f"{meta['name']} · {meta['en']}"
        if sec.get("is_lead"):
            tag += "　★ 主攻"
        blocks.append(_section_header(tag, f"{sec['minutes']} 分钟 ｜ {meta['mode']}", meta["color"]))
        blocks.append(f'<div style="padding-top:14px;">{mdhtml.render(sec["md"], meta["color"])}</div>')

    panel_btn = ""
    if panel_url:
        panel_btn = f"""
        <td align="center" style="padding:0 4px;">
          <a href="{html.escape(panel_url)}" style="display:block;padding:12px 18px;background:#1D1D1F;border-radius:12px;color:#FFFFFF;font-size:14px;font-weight:600;text-decoration:none;">打开学习面板</a>
        </td>"""
    mail_btn = ""
    if mailbox_url:
        mail_btn = f"""
        <td align="center" style="padding:0 4px;">
          <a href="{html.escape(mailbox_url)}" style="display:block;padding:12px 18px;background:#F5F5F7;border-radius:12px;color:#1D1D1F;font-size:14px;font-weight:600;text-decoration:none;">查看本期邮件</a>
        </td>"""
    archive_btn = ""
    if pack_url:
        archive_btn = f"""
        <td align="center" style="padding:0 4px;">
          <a href="{html.escape(pack_url)}" style="display:block;padding:12px 18px;background:#F5F5F7;border-radius:12px;color:#1D1D1F;font-size:14px;font-weight:600;text-decoration:none;">网页版存档</a>
        </td>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>Progress Log｜每日精进 · Daily Learning Pack</title>
</head>
<body style="margin:0;padding:0;background:#F2F2F7;font-family:-apple-system,'PingFang SC','Helvetica Neue',Arial,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{html.escape(pack.get('preview', ''))}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F2F2F7;padding:26px 12px;">
<tr><td align="center">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#FFFFFF;border-radius:22px;overflow:hidden;">
  <tr><td style="padding:30px 30px 18px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td>
          <div style="font-size:11px;font-weight:700;letter-spacing:0.18em;color:{accent};text-transform:uppercase;">Progress Log</div>
          <div style="font-size:22px;font-weight:700;color:#1D1D1F;letter-spacing:-0.4px;margin-top:6px;">Daily Learning Pack</div>
          <div style="font-size:13px;color:#8E8E93;margin-top:6px;">{date_label} ｜ {slot_cn} {slot_time}</div>
        </td>
        <td align="right" style="vertical-align:top;">
          <span style="display:inline-block;padding:6px 12px;background:{accent}14;color:{accent};border-radius:999px;font-size:12px;font-weight:600;">{slot_cn}</span>
        </td>
      </tr>
    </table>
  </td></tr>
  <tr><td style="padding:0 30px 6px;">{_progress_card(week, accent)}</td></tr>
  <tr><td style="padding:0 30px 30px;">
    {''.join(blocks)}
  </td></tr>
  <tr><td style="padding:22px 30px 30px;background:#FAFAFC;border-top:1px solid #F0F0F2;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
      {panel_btn}{archive_btn}{mail_btn}
    </tr></table>
    <div style="font-size:11.5px;color:#A1A1A6;line-height:1.8;margin-top:18px;text-align:center;">
      本邮件由 Daily Horizon 自动生成并发送 · 素材均来自官方或权威渠道，每篇标注机构与原文链接，版权归原作者所有<br>
      生成时间 {pack.get('generated_at', '')}
    </div>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""


def to_page_html(pack: dict, week: dict, panel_url: str, pack_id: str = "") -> str:
    """归档网页版：样式与邮件一致，但注入阅读计时与位置记忆脚本。"""
    page = to_email_html(pack, week, panel_url, "", "").replace("background:#F2F2F7;", "background:#F5F5F7;")
    if pack_id:
        page = page.replace("</body>", reader.script(pack_id) + "\n</body>")
    return page
