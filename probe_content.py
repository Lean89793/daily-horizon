"""云端探针：只验证内容生成与排版，不发信、不写状态。"""

import pathlib
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from src import fetch, llm, mdhtml, official, prompts, sources, package
from src.state import State

root = pathlib.Path(__file__).parent
st = State(root)
now = datetime.now(timezone(timedelta(hours=8)))
rng = random.Random(6)

items = fetch.collect_english(st, 780, 3, now, rng)
print(f"英语素材 {len(items)} 篇")
for i in items:
    print("  ", i["source"], i.get("words"), "词", i["title"][:50])

from src.config import Config

cfg = Config(root)
cli = llm.DeepSeek(cfg.llm_key, cfg.llm_base, cfg.llm_model, cfg.llm_temperature, cfg.llm_timeout)
md = cli.chat(prompts.ENGLISH_SYSTEM, prompts.english_user(items, 780, 60), max_tokens=8000, temperature=0.55)
merged = mdhtml.merge_translations(md)
print("=== 原始长度", len(md), "合并后", len(merged))
print("=== 前 1200 字 ===")
print(merged[:1200])
print("=== ¶ 块检查 ===")
import re
blocks = re.findall(r"####\s*¶\d+(.*?)(?=####|$)", merged, re.S)
for b in blocks[:3]:
    paras = [p.strip() for p in b.strip().split("\n\n") if p.strip()]
    kinds = ["zh" if len(re.findall(r"[\u4e00-\u9fff]", p)) / max(len(p), 1) > 0.25 else ("quote" if p.startswith(">") else "en") for p in paras]
    print("  ¶:", kinds, "| 段数", len(paras))

sec_items = fetch.collect_sector("finance", st, now, rng, want=3)
print(f"\n财经素材 {len(sec_items)} 篇 / {sum(i['chars'] for i in sec_items)} 字")
for i in sec_items:
    print("  ", "官方" if i.get("gov") else "媒体", i["source"], i["chars"], "字", i["title"][:40])
sec = cli.chat(prompts.sector_system("finance"), prompts.sector_user("finance", sec_items, 30), max_tokens=6000, temperature=0.7)
print("=== 财经前 600 字 ===")
print(sec[:600])
