"""素材采集：解析 RSS/Atom、过滤、去重、补正文。"""

from __future__ import annotations

import random
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

from . import extract, official, sources
from .state import State
from .util import CST, http_get, item_id, log, strip_tags, write_json

MAX_AGE_HOURS = {"english": 96, "sector": 24 * 21}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _text(node) -> str:
    return strip_tags("".join(node.itertext())) if node is not None else ""


def _parse_date(raw: str) -> datetime | None:
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
        return dt.astimezone(CST) if dt.tzinfo else dt.replace(tzinfo=CST)
    except Exception:  # noqa: BLE001
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.astimezone(CST) if dt.tzinfo else dt.replace(tzinfo=CST)
        except ValueError:
            continue
    return None


def _date_from_url(link: str) -> datetime | None:
    """央媒 RSS 常缺 pubDate，但链接里带日期：/n1/2026/1029/c1.html。"""
    patterns = [
        r"/(20\d{2})/(\d{2})(\d{2})/",
        r"/(20\d{2})-(\d{2})/(\d{2})/",
        r"/(20\d{2})(\d{2})(\d{2})[/_\-]",
    ]
    for pat in patterns:
        m = re.search(pat, link)
        if not m:
            continue
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 12, 0, tzinfo=CST)
        except ValueError:
            continue
    return None


def parse_feed(xml_text: str, feed: dict) -> list[dict]:
    """解析 RSS 2.0 / Atom，返回统一结构的条目列表。"""
    items: list[dict] = []
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError:
        return items

    nodes = [n for n in root.iter() if _local(n.tag) in ("item", "entry")]
    for node in nodes:
        title = link = summary = pub = source_name = ""
        for child in node:
            name = _local(child.tag)
            if name == "title":
                title = _text(child)
            elif name == "link":
                link = child.get("href") or _text(child)
            elif name in ("description", "summary", "content"):
                summary = summary or _text(child)
            elif name in ("pubdate", "published", "updated", "date"):
                pub = pub or _text(child)
            elif name == "source":
                source_name = _text(child)

        title = re.sub(r"\s+", " ", title).strip()
        if not title or not link:
            continue

        # Google News 标题尾部带 " - 来源名"
        if source_name and title.endswith(f" - {source_name}"):
            title = title[: -(len(source_name) + 3)].strip()
        elif " - " in title and feed.get("name", "").startswith("Google News"):
            title, source_name = title.rsplit(" - ", 1)

        published = _parse_date(pub) or _date_from_url(link)
        items.append(
            {
                "id": item_id(title),
                "title": title,
                "link": link,
                "source": source_name or feed["name"],
                "feed": feed["name"],
                "summary": summary[:2000],
                "published": published.strftime("%Y-%m-%d %H:%M") if published else "",
                "published_dt": published,
                "tag": feed.get("tag", ""),
                "weight": feed.get("weight", 1),
                "general": feed.get("general", False),
                "gnews": "news.google.com" in link,
            }
        )
    return items


def _age_ok(item: dict, limit_hours: int, now: datetime) -> bool:
    dt = item.get("published_dt")
    if not dt:
        return True  # 无日期不拦，交给 LLM 判时效
    return now - dt <= timedelta(hours=limit_hours)


def _blocked(item: dict, english: bool = False) -> bool:
    blob = f"{item.get('title', '')} {item.get('summary', '')}"
    for kw in sources.SENSITIVE_KEYWORDS + sources.BLOCK_KEYWORDS:
        if kw in blob:
            return True
    if english:
        low = blob.lower()
        for kw in sources.EN_BLOCK_KEYWORDS:
            if kw in low:
                return True
    return False


def _pull(
    feeds: list[dict], limit_hours: int, state: State, now: datetime, rng: random.Random, english: bool = False
) -> list[dict]:
    pool: list[dict] = []
    for feed in feeds:
        try:
            xml_text = http_get(feed["url"], timeout=25, retries=1)
        except Exception as exc:  # noqa: BLE001
            log(f"源不可用 {feed['name']}: {str(exc)[:80]}", "WARN")
            continue
        if feed.get("kind") == "html":
            got = official.parse_list(xml_text, feed)
        else:
            got = parse_feed(xml_text, feed)
        if not got:
            log(f"源返回 0 条（可能已改版或反爬）{feed['name']}", "WARN")
            continue
        fresh = [
            i for i in got
            if not state.is_seen(i["id"]) and _age_ok(i, limit_hours, now) and not _blocked(i, english)
        ]
        log(f"  {feed['name']}: {len(got)} 条，可用 {len(fresh)} 条")
        pool.extend(fresh)

    # 近 24 小时权重更高；同权重内随机，避免每天顺序雷同
    def sort_key(i: dict):
        dt = i.get("published_dt")
        recency = (now - dt).total_seconds() / 3600 if dt else 999
        return (-i["weight"], recency + rng.random() * 6)

    pool.sort(key=sort_key)
    seen_titles, deduped = set(), []
    for i in pool:
        if i["id"] in seen_titles:
            continue
        seen_titles.add(i["id"])
        deduped.append(i)
    return deduped


# ------------------------------------------------------------------ 英语
def collect_english(state: State, target_words: int, max_articles: int, now: datetime, rng: random.Random) -> list[dict]:
    feeds = official.GOV_FEEDS.get("english", []) + sources.ENGLISH_FEEDS
    pool = _pull(feeds, MAX_AGE_HOURS["english"], state, now, rng, english=True)

    # 题材闸门：只要政治 / 经济 / 国际贸易；社会民生与娱乐直接剔除
    def topic_ok(it: dict, strict: bool) -> bool:
        blob = f"{it.get('title', '')} {it.get('summary', '')}".lower()
        if any(k in blob for k in sources.EN_TOPIC_EXCLUDE):
            return False
        if strict and not any(k in blob for k in sources.EN_TOPIC_INCLUDE):
            return False
        return True

    strict_pool = [i for i in pool if topic_ok(i, True)]
    if len(strict_pool) < 3:
        have = {i["id"] for i in strict_pool}
        strict_pool += [i for i in pool if i["id"] not in have and topic_ok(i, False)]
    log(f"英语选题过滤：{len(pool)} → {len(strict_pool)} 条（政治/经济/贸易）")
    pool = strict_pool

    picked: list[dict] = []
    words = 0

    for item in pool:
        body = extract.article_text(item["link"], max_words=max(520, target_words // 2))
        wc = len(body.split())
        min_words = 120 if item.get("official") else 150
        if wc < min_words:
            log(f"  跳过（正文过短 {wc} 词）: {item['title'][:50]}")
            continue
        item["body"] = body
        item["words"] = wc
        picked.append(item)
        words += wc
        if len(picked) >= max_articles or (words >= target_words * 1.25 and len(picked) >= 2):
            break

    log(f"英语素材：{len(picked)} 篇 / 约 {words} 词")
    return picked


# ------------------------------------------------------------------ 行业
def collect_sector(sector: str, state: State, now: datetime, rng: random.Random, want: int = 3) -> list[dict]:
    feeds = official.GOV_FEEDS.get(sector, []) + sources.SECTOR_FEEDS.get(sector, [])
    pool = _pull(feeds, MAX_AGE_HOURS["sector"], state, now, rng)

    # 综合源（如界面新闻）会把体育娱乐混进来，按板块关键词优先排序
    kws = sources.SECTOR_KEYWORDS.get(sector, [])
    # 官方源优先进入抽正文队列（否则关键词排序会把部委通稿挤到 9 条上限之外）
    pool.sort(key=lambda i: (0 if i.get("gov") else 1,
                             -sum(1 for k in kws if k in f"{i['title']} {i['summary']}")))

    picked: list[dict] = []
    solid: list[dict] = []
    thin: list[dict] = []

    for item in pool:
        blob = f"{item['title']} {item['summary']}"
        hits = sum(1 for k in kws if k in blob) if kws else 1
        # 综合源里与板块无关的条目直接丢弃，避免旅游板块写进体育新闻
        if kws and item.get("general") and hits == 0:
            continue
        # 官方条目最多解析 3 篇，避免把扫描预算全吃光、媒体内容补不进来
        if item.get("gov") and sum(1 for p in solid if p.get("gov")) >= 3:
            continue
        if "news.google.com" in item["link"]:
            # Google News 是跳板链接，正文抓不到（实测 full=0），摘要又只有三四十字的标题
            # 直接按摘要处理，避免为上百条条目白白发起网络请求
            body = ""
        else:
            body = extract.article_text(item["link"], max_words=1800)
        if len(body) >= 120:
            item["text_quality"] = "full"
        else:
            # 正文抓不到时退回摘要，但摘要本身必须够长，否则等于只有标题
            summary = (item.get("summary") or "").strip()
            # 政府通稿天然短（百余字），门槛放低，否则部委口径永远进不来
            if len(summary) < (90 if item.get("gov") else 150):
                continue
            body = summary
            item["text_quality"] = "summary"
        if not body.strip():
            continue
        item["body"] = body
        item["chars"] = len(body)
        (solid if item["text_quality"] == "full" else thin).append(item)

        # 央媒短讯多，单篇只有几百字，凑够可读体量再多取几篇
        # 同时要求至少 2 篇非官方媒体，避免一个板块全是部委通稿
        media_ok = sum(1 for p in solid if not p.get("gov")) >= 2
        if len(solid) >= want and sum(p["chars"] for p in solid) >= 1200 and media_ok:
            break
        if len(solid) + len(thin) >= want * 4:
            break

    # 官方口径最多 2 篇（保证权威），其余用信息量最大的媒体内容补齐
    cand = sorted(solid, key=lambda x: -x["chars"]) + sorted(thin, key=lambda x: -x["chars"])
    gov = [i for i in cand if i.get("gov")][:2]
    media = [i for i in cand if not i.get("gov")]
    picked = gov + media[: max(0, want - len(gov))]
    picked.sort(key=lambda x: (0 if x.get("gov") else 1, -x["chars"]))

    log(f"{sector} 素材：{len(picked)} 篇 / {sum(p.get('chars', 0) for p in picked)} 字"
        f"（全文 {len(solid)} / 摘要 {len(thin)}）")
    return picked


def dump_candidates(items: list[dict], path) -> None:
    write_json(path, [{k: v for k, v in i.items() if k != "published_dt"} for i in items])
