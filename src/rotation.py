"""板块轮换策略。

PRD 要求：早晚两套素材完全不重复，板块不固定绑定早/晚，自动轮换。
用户口径已确认：财经早晚各 1 篇（每天 2 篇、内容不同）。

实现方式：
  1. 每场固定四大板块（英语 + 财经 + 旅游 + 消费品），保证结构完整；
  2. 旅游 / 消费品 交替做「当日主攻板块」，主攻的加深度，另一板块走轻量；
  3. 板块出场顺序隔周轮换，视觉与阅读节奏不固定。
"""

from __future__ import annotations

from datetime import date as Date

LEAD_ROTATION = ["travel", "consumer"]


def plan(d: Date, slot: str) -> dict:
    """返回当场的板块顺序、主攻板块、各部分时长分配。"""
    ordinal = d.toordinal()
    slot_offset = 0 if slot == "morning" else 1

    lead = LEAD_ROTATION[(ordinal + slot_offset) % 2]
    side = "consumer" if lead == "travel" else "travel"

    week_parity = (ordinal // 7) % 2
    if week_parity == 0:
        order = ["finance", lead, side]
    else:
        order = [lead, side, "finance"]

    return {
        "order": order,
        "lead": lead,
        "side": side,
        "finance_minutes": 30,
        "lead_minutes": 35,
        "side_minutes": 25,
        "total_minutes": 90,  # 30 + 35 + 25，行业合计恒定 1.5 小时
    }


def english_article_plan(target_words: int) -> list[int]:
    """把 1 小时英语体量拆成 2 篇：一篇长（约 60%），一篇短（约 40%）。"""
    long_form = int(target_words * 0.6)
    return [long_form, target_words - long_form]
