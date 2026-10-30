"""官方渠道采集：政府部委 / 统计机构 / 行业协会 / 政府英文站的列表页解析。

这些站点多数没有 RSS，但列表页结构稳定（<a href> + 日期），
用「链接正则 + 标题长度」即可稳定抽出条目，比新闻聚合站权威得多。
"""

from __future__ import annotations

import html as htmllib
import re
from datetime import datetime
from urllib.parse import urljoin

from .util import CST, item_id, strip_tags

# kind=html 表示走 HTML 列表解析；weight 高于商业源，保证官方口径优先进入候选池
GOV_FEEDS = {
    "finance": [
        {
            "name": "中国人民银行",
            "url": "http://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html",
            "link_re": r"/\d{15,}/index\.html",
            "date_re": r"/(20\d{2})(\d{2})(\d{2})\d{6,}/",
            "weight": 5,
        },
        {
            "name": "国家统计局",
            "url": "https://www.stats.gov.cn/sj/zxfb/",
            "link_re": r"/t20\d{6}_\d+\.html",
            "weight": 5,
        },
        {
            "name": "国家发展改革委",
            "url": "https://www.ndrc.gov.cn/xwdt/xwfb/",
            "link_re": r"/t20\d{6}_\d+\.html",
            "weight": 4,
        },
        {
            "name": "商务部",
            "url": "http://www.mofcom.gov.cn/xwfb/",
            "link_re": r"/art/20\d{2}/art_[0-9a-f]+\.html",
            "weight": 4,
        },
        {
            "name": "中国证监会",
            "url": "http://www.csrc.gov.cn/csrc/c100028/common_list.shtml",
            "link_re": r"/csrc/c100028/c\d+/content\.shtml",
            "weight": 3,
        },
    ],
    "travel": [
        {
            "name": "文化和旅游部",
            "url": "https://www.mct.gov.cn/whzx/whyw/",
            "link_re": r"/t20\d{6}_\d+\.htm",
            "weight": 5,
        },
        {
            "name": "中国民用航空局",
            "url": "http://www.caac.gov.cn/XWZX/MHYW/",
            "link_re": r"/t20\d{6}_\d+\.html",
            "weight": 5,
        },
    ],
    "consumer": [
        {
            "name": "中国家具协会",
            "url": "http://www.cnfa.com.cn/",
            "link_re": r"/infodetails\d+\.html",
            "weight": 3,
        },
        {
            "name": "商务部·消费",
            "url": "http://www.mofcom.gov.cn/xwfb/",
            "link_re": r"/art/20\d{2}/art_[0-9a-f]+\.html",
            "weight": 4,
            "general": True,
        },
    ],
    "english": [
        {
            "name": "Gov.cn English",
            "url": "https://english.www.gov.cn/news/",
            "link_re": r"content_WS[0-9a-f]+\.htm",
            "weight": 5,
        },
    ],
}

for _feeds in GOV_FEEDS.values():
    for _f in _feeds:
        _f["kind"] = "html"
        _f.setdefault("limit", 12)

ANCHOR_RE = re.compile(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)
NOISE = {"更多", "查看更多", "详细", "详情", "下一页", "上一页", "首页"}

# 礼仪性/程序性通稿：对精读毫无价值，直接排除
PROTOCOL_SKIP = [
    "会见", "调研", "走访", "慰问", "贺信", "题词", "合影", "出席开幕式",
    "任免", "任命", "免去", "干部大会", "座谈", "答记者问",
]


def parse_list(page: str, feed: dict) -> list[dict]:
    """把列表页解析成与 RSS 同构的条目。"""
    link_re = re.compile(feed["link_re"])
    date_re = re.compile(feed["date_re"]) if feed.get("date_re") else None
    items: list[dict] = []
    seen_links: set[str] = set()

    for m in ANCHOR_RE.finditer(page):
        href, inner = m.group(1), m.group(2)
        if not link_re.search(href):
            continue
        text = htmllib.unescape(strip_tags(inner))
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 10 or len(text) > 100 or text in NOISE:
            continue
        if any(kw in text for kw in PROTOCOL_SKIP):
            continue

        full = urljoin(feed["url"], href)
        if full in seen_links:
            continue
        seen_links.add(full)

        published = None
        if date_re:
            dm = date_re.search(href)
            if dm:
                try:
                    published = datetime(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)), 12, 0, tzinfo=CST)
                except ValueError:
                    published = None
        if published is None:
            dm = re.search(r"t(20\d{2})(\d{2})(\d{2})_", href)
            if dm:
                try:
                    published = datetime(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)), 12, 0, tzinfo=CST)
                except ValueError:
                    published = None

        items.append(
            {
                "id": item_id(text),
                "title": text,
                "link": full,
                "source": feed["name"],
                "feed": feed["name"],
                "summary": "",
                "published": published.strftime("%Y-%m-%d %H:%M") if published else "",
                "published_dt": published,
                "tag": feed.get("tag", ""),
                "weight": feed.get("weight", 3),
                "general": feed.get("general", False),
                "gnews": False,
                "gov": True,
            }
        )
        if len(items) >= feed.get("limit", 12):
            break

    return items
