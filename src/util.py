"""通用工具：日志、HTTP、时间、文本处理。纯标准库实现。"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def now_cst() -> datetime:
    return datetime.now(CST)


def log(msg: str, level: str = "INFO") -> None:
    ts = now_cst().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    if level == "ERROR":
        print(line, file=sys.stderr, flush=True)


def http_get(url: str, timeout: int = 25, retries: int = 2) -> str:
    """带重试的 GET，返回解码后的文本。失败抛异常。"""
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                charset = resp.headers.get_content_charset() or "utf-8"
            try:
                return raw.decode(charset, errors="replace")
            except LookupError:
                return raw.decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise last  # type: ignore[misc]


def http_post_json(url: str, payload: dict, headers: dict, timeout: int = 180, retries: int = 2) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=body, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", UA)
            for k, v in headers.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:400]
            except Exception:  # noqa: BLE001
                pass
            last = RuntimeError(f"HTTP {exc.code}: {detail}")
            if exc.code in (400, 401, 403, 422):
                break  # 参数/鉴权问题，重试无意义
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
    raise last  # type: ignore[misc]


def strip_tags(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def item_id(title: str) -> str:
    """素材唯一标识：规范化标题后取哈希。跨天、跨场次去重都用它。"""
    norm = re.sub(r"[\s\u3000]+", "", title).lower()
    norm = re.sub(r"[^\w\u4e00-\u9fff]", "", norm)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]


def en_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", text))


def cjk_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def iso_week_key(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


def read_json(path, default):
    import pathlib

    p = pathlib.Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        log(f"读取 {p} 失败({exc})，使用默认值", "ERROR")
        return default


def write_text(path, text: str) -> None:
    import pathlib

    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def write_json(path, data) -> None:
    import pathlib

    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def fmt_minutes(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} 分钟"
    h, m = divmod(minutes, 60)
    return f"{h} 小时" if m == 0 else f"{h} 小时 {m} 分"


def fmt_hours(minutes: int) -> str:
    return f"{minutes / 60:.1f}".rstrip("0").rstrip(".")
