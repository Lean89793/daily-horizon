"""状态库：素材去重 + 每日记录 + 周统计。

单一 data/state.json 持久化，GitHub Actions 每次运行后提交回仓库，
因此跨天、跨场次去重都能生效；周统计由每日记录实时汇总，不存在口径漂移。
"""

from __future__ import annotations

import pathlib
from datetime import datetime, timedelta

from .util import iso_week_key, read_json, write_json

SEEN_TTL_DAYS = 120
SLOTS_PER_WEEK = 14  # 7 天 x 早/晚


class State:
    def __init__(self, root: pathlib.Path):
        self.path = pathlib.Path(root) / "data" / "state.json"
        self.data = read_json(
            self.path, {"version": 1, "seen": {}, "days": {}, "history": []}
        )
        self.data.setdefault("seen", {})
        self.data.setdefault("days", {})
        self.data.setdefault("history", [])

    # ------------------------------------------------------------ 去重
    def is_seen(self, sid: str) -> bool:
        return sid in self.data["seen"]

    def mark_seen(self, sid: str, title: str, source: str, date: str, slot: str, sector: str = "english") -> None:
        self.data["seen"][sid] = {
            "title": title[:160],
            "source": source,
            "date": date,
            "slot": slot,
            "sector": sector,
        }

    def prune(self, today: str) -> int:
        """清理过期去重记录，避免文件无限膨胀。"""
        cutoff = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=SEEN_TTL_DAYS)).strftime("%Y-%m-%d")
        before = len(self.data["seen"])
        self.data["seen"] = {
            k: v for k, v in self.data["seen"].items() if v.get("date", "9999-99-99") >= cutoff
        }
        return before - len(self.data["seen"])

    # ------------------------------------------------------------ 场次记录
    def record(self, date: str, slot: str, payload: dict) -> None:
        self.data["days"].setdefault(date, {})[slot] = payload
        self.data["history"] = [h for h in self.data["history"] if h.get("key") != f"{date}#{slot}"]
        self.data["history"].append(
            {"key": f"{date}#{slot}", "date": date, "slot": slot, "status": payload.get("status", "ok")}
        )
        self.data["history"] = self.data["history"][-60:]

    def slot_record(self, date: str, slot: str) -> dict | None:
        return self.data["days"].get(date, {}).get(slot)

    # ------------------------------------------------------------ 周统计
    def week_stats(self, ref: datetime) -> dict:
        monday = ref - timedelta(days=ref.weekday())
        days = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        english_count = english_minutes = sector_count = sector_minutes = 0
        slots_done = 0
        sectors_hit = {"finance": 0, "travel": 0, "consumer": 0}
        daily = []

        for d in days:
            rec = self.data["days"].get(d, {})
            done_today = 0
            flags = {}
            for slot in ("morning", "evening"):
                r = rec.get(slot)
                done = bool(r and r.get("status") in ("ok", "partial"))
                flags[slot] = done
                if not done:
                    continue
                slots_done += 1
                done_today += 1
                english_count += int(r.get("english_articles", 0))
                english_minutes += int(r.get("english_minutes", 0))
                secs = r.get("sectors", [])
                sector_count += len(secs)
                sector_minutes += int(r.get("sector_minutes", 0))
                for s in secs:
                    key = s.get("key")
                    if key in sectors_hit:
                        sectors_hit[key] += 1
            daily.append(
                {
                    "date": d,
                    "slots": done_today,
                    "morning": flags.get("morning", False),
                    "evening": flags.get("evening", False),
                }
            )

        return {
            "week": iso_week_key(monday),
            "week_start": monday.strftime("%Y-%m-%d"),
            "week_end": (monday + timedelta(days=6)).strftime("%Y-%m-%d"),
            "english_count": english_count,
            "english_minutes": english_minutes,
            "sector_count": sector_count,
            "sector_minutes": sector_minutes,
            "total_minutes": english_minutes + sector_minutes,
            "slots_done": slots_done,
            "slots_planned": SLOTS_PER_WEEK,
            "progress": round(slots_done / SLOTS_PER_WEEK, 4),
            "sectors": sectors_hit,
            "daily": daily,
        }

    def recent_packs(self, limit: int = 6) -> list:
        out = []
        for date in sorted(self.data["days"].keys(), reverse=True):
            for slot in ("evening", "morning"):
                r = self.data["days"][date].get(slot)
                if not r:
                    continue
                out.append(
                    {
                        "date": date,
                        "slot": slot,
                        "title": r.get("english_title") or r.get("lead_title") or "学习包",
                        "url": r.get("pack_url", ""),
                        "english_articles": r.get("english_articles", 0),
                        "minutes": int(r.get("english_minutes", 0)) + int(r.get("sector_minutes", 0)),
                    }
                )
                if len(out) >= limit:
                    return out
        return out

    def save(self) -> None:
        write_json(self.path, self.data)
