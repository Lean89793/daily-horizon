"""云端探针：只看采集构成，不发信、不写状态。"""

import pathlib
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from src import fetch, official, sources
from src.state import State

root = pathlib.Path(__file__).parent
st = State(root)
now = datetime.now(timezone(timedelta(hours=8)))
rng = random.Random(4)

print("=== 官方源可用性 ===")
for sector, feeds in official.GOV_FEEDS.items():
    for f in feeds:
        pool = fetch._pull([f], fetch.MAX_AGE_HOURS["sector"], st, now, rng)
        print(f"{sector:9s} {f['name']:14s} -> {len(pool)} 条")

print("\n=== 板块最终构成 ===")
for sec in ("finance", "travel", "consumer"):
    items = fetch.collect_sector(sec, st, now, rng, want=3)
    total = sum(i["chars"] for i in items)
    print(f"\n[{sec}] {len(items)} 篇 / {total} 字")
    for i in items:
        flag = "官方" if i.get("gov") else "媒体"
        print(f"   [{flag}] {i['source']:10s} {i['chars']:5d}字 {i['title'][:38]}")

print("\n=== 英语源 ===")
en = fetch.collect_english(st, 780, 3, now, rng)
print(f"英语 {len(en)} 篇 / {sum(i.get('words', 0) for i in en)} 词")
for i in en:
    print(f"   {i['source']:16s} {i.get('words', 0):4d}词 {i['title'][:44]}")
