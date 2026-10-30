"""从新闻页提取正文。

思路：剥掉脚本/导航/侧栏，优先取 <article>，退化到 <body>，
再收集所有有实质长度的 <p> 段落。对 BBC / Guardian / NPR / 中文媒体的
通用版面效果好；遇到付费墙或纯 JS 渲染会返回空，由上层降级处理。
"""

from __future__ import annotations

import re

from .util import UA, http_get, strip_tags


def _decode_html(raw_bytes: bytes, header_charset: str | None) -> str:
    if header_charset:
        try:
            return raw_bytes.decode(header_charset, errors="replace")
        except LookupError:
            pass
    m = re.search(rb'<meta[^>]+charset=["\']?([\w\-]+)', raw_bytes[:4096], re.I)
    if m:
        try:
            return raw_bytes.decode(m.group(1).decode("ascii", "ignore"), errors="replace")
        except LookupError:
            pass
    return raw_bytes.decode("utf-8", errors="replace")


def _clean_html(doc: str) -> str:
    doc = re.sub(r"(?is)<(script|style|noscript|svg|iframe|form)[^>]*>.*?</\1>", " ", doc)
    doc = re.sub(r"(?is)<!--.*?-->", " ", doc)
    for tag in ("nav", "header", "footer", "aside"):
        doc = re.sub(rf"(?is)<{tag}\b[^>]*>.*?</{tag}>", " ", doc)
    return doc


NOISE_PATTERNS = [
    r"hide caption", r"toggle caption", r"image source", r"image caption",
    r"getty images", r"^photo\s*[:/]", r"^credit\s*[:/]", r"^source\s*[:/]",
    r"^read more", r"^related\s*[:/]", r"^subscribe", r"^sign up",
    r"^share this", r"^advertisement$", r"^\W*$",
]


def _is_noise(text: str) -> bool:
    low = text.lower()
    for pat in NOISE_PATTERNS:
        if re.search(pat, low):
            return True
    # 主体是英文但没有任何句末标点，多半是图注或按钮
    if len(text) < 90 and not re.search(r"[.!?。！？]", text):
        return True
    return False


def _paragraphs(fragment: str) -> list[str]:
    out, seen = [], set()
    for raw in re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", fragment):
        text = strip_tags(raw)
        text = re.sub(r"\s*([,.;:!?])\s*", r"\1 ", text).strip()
        if len(text) < 45:
            continue  # 版权行、图片说明、按钮文字
        if _is_noise(text):
            continue
        key = text[:60].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def article_text(url: str, max_words: int = 1400) -> str:
    """抓取正文，返回以空行分段的纯文本；失败返回空字符串。"""
    try:
        page = _fetch(url)
    except Exception:  # noqa: BLE001
        return ""
    if not page:
        return ""

    doc = _clean_html(page)
    m = re.search(r"(?is)<article\b[^>]*>(.*?)</article>", doc)
    scope = m.group(1) if m else doc
    paras = _paragraphs(scope)

    if len(paras) < 3:  # article 区块没抓到，退回全页
        paras = _paragraphs(doc)

    body: list[str] = []
    words = 0
    for p in paras:
        body.append(p)
        words += len(p.split())
        if words >= max_words:
            break
    return "\n\n".join(body)


def _fetch(url: str) -> str:
    import urllib.request

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read()
        charset = resp.headers.get_content_charset()
        final_url = resp.geturl()
    doc = _decode_html(raw, charset)

    # Google News 的链接是跳转壳，解出真实地址再抓一次
    if "news.google.com" in final_url:
        real = _gnews_target(doc)
        if real and "news.google.com" not in real:
            try:
                return _fetch(real)
            except Exception:  # noqa: BLE001
                return doc
    return doc


def _gnews_target(doc: str) -> str:
    """从 Google News 中转页里抽出真实链接。"""
    for pat in (
        r'data-n-au="(https?://[^"]+)"',
        r'<meta[^>]+http-equiv="refresh"[^>]+url=(https?://[^"]+)"',
        r'"url":\s*"(https?://[^"]+)"',
    ):
        m = re.search(pat, doc, re.I)
        if m:
            return m.group(1)
    return ""
