"""素材源白名单。

分两类：
  - 英语新闻：海外官方/权威媒体 RSS + 新华英文（国内可直连的兜底源）。
  - 行业素材：央媒与财经媒体频道 RSS（给真实原文链接，正文可抓）+ Google News 关键词聚合。

所有源均于 2026-10-29 实测：36氪、环球旅讯、中国日报 RSS 已失效，已移除。
新增源只需在对应列表追加，name 会作为邮件里的「来源」标注。
"""

from __future__ import annotations

# ---------------------------------------------------------------- 英语新闻
# tag: politics / business / culture / ideas —— 对应 PRD 的四个方向
# domestic=True 表示国内网络可直连，海外源被墙时作为兜底
ENGLISH_FEEDS = [
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "tag": "politics", "weight": 2},
    {"name": "BBC Business", "url": "https://feeds.bbci.co.uk/news/business/rss.xml", "tag": "business", "weight": 4},
    {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss", "tag": "politics", "weight": 2},
    {"name": "The Guardian Business", "url": "https://www.theguardian.com/business/rss", "tag": "business", "weight": 4},
    {"name": "The Guardian Culture", "url": "https://www.theguardian.com/culture/rss", "tag": "culture", "weight": 3},
    {"name": "NPR World", "url": "https://feeds.npr.org/1004/rss.xml", "tag": "politics", "weight": 2},
    {"name": "The Conversation", "url": "https://theconversation.com/articles.atom", "tag": "ideas", "weight": 3},
    {"name": "Xinhua English", "url": "http://www.xinhuanet.com/english/rss/worldrss.xml", "tag": "politics", "weight": 1, "domestic": True},
]

# ---------------------------------------------------------------- 行业素材
# 板块键：finance 财经 / travel 旅游 / consumer 消费品
# general=True 表示综合源，需靠 SECTOR_KEYWORDS 过滤归属
SECTOR_FEEDS = {
    "finance": [
        {"name": "中新财经", "url": "https://www.chinanews.com.cn/rss/finance.xml", "weight": 3},
        {"name": "华尔街见闻", "url": "https://dedicated.wallstreetcn.com/rss.xml", "weight": 3},
        {"name": "界面新闻", "url": "https://a.jiemian.com/index.php?m=article&a=rss", "weight": 2, "general": True},
        {"name": "钛媒体", "url": "https://www.tmtpost.com/rss", "weight": 1, "general": True},
        {
            "name": "Google News·券商研报",
            "url": "https://news.google.com/rss/search?q=%E5%88%B8%E5%95%86%E7%A0%94%E6%8A%A5+OR+%E8%A1%8C%E4%B8%9A%E7%A0%94%E7%A9%B6+OR+%E4%B8%8A%E5%B8%82%E5%85%AC%E5%8F%B8%E8%B0%83%E7%A0%94+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "weight": 2,
        },
    ],
    "travel": [
        {"name": "品橙旅游", "url": "https://www.pinchain.com/rss", "weight": 3},
        {
            "name": "Google News·旅游产业",
            "url": "https://news.google.com/rss/search?q=%E6%97%85%E6%B8%B8%E4%BA%A7%E4%B8%9A+OR+%E6%96%87%E6%97%85+OR+%E6%99%AF%E5%8C%BA+OR+%E9%85%92%E5%BA%97%E4%B8%9A%E6%8A%A5+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "weight": 3,
        },
        {
            "name": "Google News·旅游政策",
            "url": "https://news.google.com/rss/search?q=%E6%96%87%E6%97%85%E9%83%A8+OR+%E5%85%A5%E5%A2%83%E6%97%85%E6%B8%B8+OR+%E5%85%8D%E7%AD%BE+OR+%E8%88%AA%E7%A9%BA%E5%A4%8D%E8%8B%8F+when:14d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "weight": 2,
        },
    ],
    "consumer": [
        {"name": "华丽志", "url": "https://www.luxe.co/feed", "weight": 3},
        {
            "name": "Google News·家居餐具",
            "url": "https://news.google.com/rss/search?q=%E5%AE%B6%E5%B1%85+OR+%E9%A4%90%E5%85%B7+OR+%E5%8E%A8%E5%85%B7+OR+%E9%AA%A8%E7%93%B7+OR+%E5%AE%B6%E7%94%B5+%E8%A1%8C%E4%B8%9A+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "weight": 3,
        },
        {
            "name": "Google News·消费趋势",
            "url": "https://news.google.com/rss/search?q=%E6%B6%88%E8%B4%B9%E5%93%81+OR+%E6%B8%A0%E9%81%93+OR+%E5%93%81%E7%89%8C+OR+%E5%87%BA%E6%B5%B7%E9%9B%B6%E5%94%AE+when:7d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "weight": 2,
        },
        {"name": "界面新闻", "url": "https://a.jiemian.com/index.php?m=article&a=rss", "weight": 2, "general": True},
        {"name": "钛媒体", "url": "https://www.tmtpost.com/rss", "weight": 1, "general": True},
    ],
}

SECTOR_META = {
    "finance": {"name": "财经泛读", "en": "Finance", "color": "#00A6A6", "mode": "泛读"},
    "travel": {"name": "旅游精读", "en": "Travel", "color": "#FF9F0A", "mode": "精读"},
    "consumer": {"name": "消费品精读", "en": "Consumer", "color": "#BF5AF2", "mode": "精读"},
}

# 过滤：明显广告/软文/无关内容
BLOCK_KEYWORDS = [
    "广告", "推广", "优惠券", "限时特惠", "点击购买", "招商加盟", "代理招募",
    "抽奖", "直播预告", "招聘", "招聘启事", "讣告", "彩票",
]

# 英文源过滤：灾难/犯罪/战争类不适合做精读，且容易触发内容风险
EN_BLOCK_KEYWORDS = [
    "deadly", "death toll", "killed", "kills ", "shooting", "murder", "rape",
    "suicide", "corpse", "wounded", "injured", "missile", "airstrike", "air strike",
    "war ", "invasion", "refugee", "hostage", "obituary", "dies at", "found dead",
    "horoscope", "royal family", "celebrity gossip", "trial", "verdict", "sentenced",
    "earthquake", "hurricane", "wildfire", "flood", "outbreak", "epidemic",
]

# 行业素材关键词：用于跨板块频道的归属判断（如界面新闻是综合源）
SECTOR_KEYWORDS = {
    "finance": ["金融", "证券", "基金", "银行", "保险", "债券", "股市", "A股", "港股", "美股",
                "利率", "汇率", "货币", "信贷", "融资", "IPO", "上市", "财报", "营收", "利润",
                "经济", "GDP", "通胀", "消费价格", "央行", "监管", "资管", "私募", "投行", "研报"],
    "travel": ["旅游", "文旅", "景区", "酒店", "民宿", "航空", "航线", "机场", "旅行社", "OTA",
               "出境", "入境", "签证", "免签", "度假", "目的地", "游客", "客源", "邮轮", "研学"],
    "consumer": ["家居", "家具", "餐具", "厨具", "陶瓷", "骨瓷", "家电", "建材", "卫浴", "家纺",
                 "日用", "消费品", "零售", "渠道", "品牌", "电商", "线下门店", "出海", "供应链"],
}

# 政治敏感词——命中即跳过，避免内容风险
SENSITIVE_KEYWORDS = [
    "台独", "藏独", "疆独", "港独", "法轮", "六四", "达赖",
]
