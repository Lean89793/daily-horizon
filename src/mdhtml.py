"""Markdown → HTML 渲染（邮件友好：全部内联样式）。

只支持学习包用到的子集：## / ### 标题、段落、**加粗**、*斜体*、> 引用块、- 列表、--- 分隔线。
排版上自动区分英文原文与中文译文（按中日韩字符占比判断），
让精读区块自然形成「深色英文 / 浅色中文 / 灰底生词」的阅读节奏。
"""

from __future__ import annotations

import html
import re

CJK = re.compile(r"[\u4e00-\u9fff]")

STYLE = {
    "h2": "margin:34px 0 8px;font-size:21px;line-height:1.35;font-weight:700;color:#1D1D1F;letter-spacing:-0.2px;",
    "h3": "margin:32px 0 8px;font-size:19px;line-height:1.4;font-weight:700;color:#1D1D1F;letter-spacing:-0.15px;",
    "h4": "margin:24px 0 8px;font-size:15.5px;font-weight:650;color:#1D1D1F;line-height:1.5;",
    "label": "margin:24px 0 8px;font-size:12px;font-weight:600;color:#8E8E93;letter-spacing:0.08em;text-transform:uppercase;",
    "p_en": "margin:0 0 14px;font-size:16px;line-height:1.78;color:#1D1D1F;font-family:-apple-system,'SF Pro Text','Helvetica Neue',Helvetica,Arial,sans-serif;",
    "p_zh": "margin:0 0 16px;font-size:15px;line-height:1.85;color:#6E6E73;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;",
    "lead": "margin:0 0 18px;font-size:16px;line-height:1.8;color:#3A3A3C;",
    "quote": "margin:0 0 18px;padding:13px 16px;background:#F5F5F7;border-radius:12px;font-size:13.5px;line-height:1.75;color:#3A3A3C;",
    "quote_label": "display:block;font-size:11px;font-weight:700;color:#8E8E93;letter-spacing:0.1em;margin-bottom:6px;text-transform:uppercase;",
    "li": "margin:0 0 6px;padding-left:2px;",
    "ul": "margin:0;padding-left:18px;",
    "hr": "border:none;border-top:1px solid #E5E5EA;margin:30px 0;",
    "strong": "font-weight:650;color:#1D1D1F;",
    "em": "font-style:italic;color:#8E8E93;",
}


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", rf'<strong style="{STYLE["strong"]}">\1</strong>', text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", rf'<em style="{STYLE["em"]}">\1</em>', text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def _cjk_ratio(text: str) -> float:
    if not text:
        return 0.0
    return len(CJK.findall(text)) / max(len(text), 1)


def _para(text: str) -> str:
    style = STYLE["p_zh"] if _cjk_ratio(text) > 0.25 else STYLE["p_en"]
    return f'<p style="{style}">{_inline(text)}</p>'


def _quote(lines: list[str], accent: str) -> str:
    label = ""
    body: list[str] = []
    items: list[str] = []

    for raw in lines:
        line = raw[1:].strip() if raw.startswith(">") else raw.strip()
        if not line:
            continue
        m = re.match(r"^\*\*(.+?)\*\*$", line)
        if m and not label and not body and not items:
            label = m.group(1)
            continue
        if line.startswith("- ") or line.startswith("· "):
            items.append(line[2:].strip())
        else:
            body.append(line)

    label_html = f'<span style="{STYLE["quote_label"]}">{html.escape(label)}</span>' if label else ""
    parts = [f'<p style="margin:0 0 4px;font-size:13.5px;line-height:1.8;color:#3A3A3C;">{_inline(p)}</p>' for p in body]
    if items:
        lis = "".join(f'<li style="{STYLE["li"]}">{_inline(i)}</li>' for i in items)
        parts.append(f'<ul style="{STYLE["ul"]}">{lis}</ul>')

    is_vocab = "生词" in label
    border = "" if is_vocab else f"border-left:3px solid {accent};"
    return (
        f'<div style="{STYLE["quote"]}{border}">{label_html}{"".join(parts)}</div>'
    )


def render(md: str, accent: str = "#0A84FF") -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    quote_buf: list[str] = []
    list_buf: list[tuple[str, str]] = []

    def flush_quote():
        nonlocal quote_buf
        if quote_buf:
            out.append(_quote(quote_buf, accent))
            quote_buf = []

    def flush_list():
        nonlocal list_buf
        if list_buf:
            tag = "ol" if list_buf[0][0] == "ol" else "ul"
            lis = "".join(f'<li style="{STYLE["li"]}">{_inline(t)}</li>' for _, t in list_buf)
            out.append(f'<{tag} style="{STYLE["ul"]}">{lis}</{tag}>')
            list_buf = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_quote()
            flush_list()
            i += 1
            continue

        if stripped.startswith(">"):
            flush_list()
            quote_buf.append(stripped)
            i += 1
            continue

        flush_quote()

        if re.match(r"^#{1,4}\s", stripped):
            flush_list()
            level = len(stripped) - len(stripped.lstrip("#"))
            content = stripped[level:].strip()
            if content.startswith("¶"):
                # 段落标记统一走小标签样式，不管模型用几个井号
                tag, style = "h4", STYLE["label"]
            elif level <= 3:
                # # / ## 是模型偶尔越级的兜底，统一按文章标题渲染，避免出现字面井号
                tag, style = "h3", STYLE["h3"]
            else:
                tag, style = "h4", STYLE["h4"]
            out.append(f'<{tag} style="{style}">{_inline(content)}</{tag}>')
            i += 1
            continue

        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            flush_list()
            out.append(f'<hr style="{STYLE["hr"]}">')
            i += 1
            continue

        m_ul = re.match(r"^[-*·]\s+(.*)$", stripped)
        m_ol = re.match(r"^(\d+)[.、]\s+(.*)$", stripped)
        if m_ul:
            list_buf.append(("ul", m_ul.group(1)))
            i += 1
            continue
        if m_ol:
            list_buf.append(("ol", m_ol.group(2)))
            i += 1
            continue

        flush_list()
        out.append(_para(stripped))
        i += 1

    flush_quote()
    flush_list()
    return "\n".join(out)


def plain_text(md: str) -> str:
    """去掉 Markdown 记号，用于邮件纯文本备用版本。"""
    text = re.sub(r"^#{1,6}\s*", "", md, flags=re.M)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"^>\s?", "", text, flags=re.M)
    return text.strip()
