import pathlib, random, sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from src.state import State
from src import fetch, sources, extract

root = pathlib.Path(__file__).parent
st = State(root)
now = datetime.now(timezone(timedelta(hours=8)))
rng = random.Random(11)

print("=== 源可用性 ===")
for sec, feeds in sources.SECTOR_FEEDS.items():
    for f in feeds:
        items = fetch._pull([f], fetch.MAX_AGE_HOURS["sector"], st, now, rng)
        print(f"{sec:9s} {f.get('name'):24s} {len(items):3d} 条")

print("=== consumer 逐条抽取测试（前 12 条）===")
feeds = sources.SECTOR_FEEDS.get("consumer", [])
pool = fetch._pull(feeds, fetch.MAX_AGE_HOURS["sector"], st, now, rng)
kws = sources.SECTOR_KEYWORDS.get("consumer", [])
if kws:
    pool.sort(key=lambda i: -sum(1 for k in kws if k in f"{i['title']} {i['summary']}"))
for item in pool[:12]:
    body = extract.article_text(item["link"], max_words=1800)
    print(f"full={len(body):5d} sum={len((item.get('summary') or '').strip()):4d} "
          f"src={item.get('source')} | {item['title'][:34]}")

print("=== 新版 collect_sector ===")
for sec in ("consumer", "travel", "finance"):
    picked = fetch.collect_sector(sec, st, now, rng, want=3)
    print(f"[{sec}] {len(picked)} 篇 共 {sum(p['chars'] for p in picked)} 字")
    for p in picked:
        print("   -", p["text_quality"], p["chars"], p["title"][:36])
