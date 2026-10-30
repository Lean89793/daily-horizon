"""Daily Horizon 主流程。

用法：
  python main.py                    # 按当前时间自动判断早场/晚场
  python main.py --slot morning     # 指定场次
  python main.py --mock --no-mail   # 用样刊内容跑通排版，不发信
  python main.py --force            # 已有记录时强制重跑（手动补发）
"""

from __future__ import annotations

import argparse
import pathlib
import random
import sys
import traceback
from datetime import datetime

from src import fetch, llm, mailer, mdhtml, package, panel, prompts, rotation, sample, sources
from src.config import Config
from src.state import State
from src.util import CST, fmt_minutes, item_id, log, now_cst, write_json, write_text

ROOT = pathlib.Path(__file__).resolve().parent


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Daily Horizon 学习包生成器")
    p.add_argument("--slot", choices=["morning", "evening"], help="场次，缺省按当前时间推断")
    p.add_argument("--date", help="日期 YYYY-MM-DD，缺省今天")
    p.add_argument("--mock", action="store_true", help="使用样刊内容，不联网不调模型")
    p.add_argument("--no-mail", action="store_true", help="只生成不发送")
    p.add_argument("--force", action="store_true", help="忽略已有记录，强制重跑")
    return p.parse_args(argv)


def infer_slot(now: datetime) -> str:
    return "morning" if now.hour < 14 else "evening"


# ------------------------------------------------------------------ 生成
def gen_english(client, items: list[dict], target_words: int, minutes: int) -> str:
    user = prompts.english_user(items, target_words, minutes)
    for attempt in (1, 2):
        md = client.chat(prompts.ENGLISH_SYSTEM, user, max_tokens=8000, temperature=0.55)
        paras = md.count("### ¶")
        if paras >= 4 and len(md) > 1200:
            return md
        log(f"英语输出偏短（{paras} 段 / {len(md)} 字），第 {attempt} 次重试", "WARN")
        user += "\n\n注意：上一次输出段落过少或内容不足，请完整输出全部原文段落，不要省略。"
    return md


def gen_sector(client, sector: str, items: list[dict], minutes: int) -> str:
    user = prompts.sector_user(sector, items, minutes)
    system = prompts.sector_system(sector)
    for attempt in (1, 2):
        md = client.chat(system, user, max_tokens=6000, temperature=0.7)
        if len(md) >= 900:
            return md
        log(f"{sector} 输出过短（{len(md)} 字），第 {attempt} 次重试", "WARN")
        user += "\n\n注意：上一次输出篇幅不足，请按要求字数完整展开。"
    return md


# ------------------------------------------------------------------ 主流程
def run(args: argparse.Namespace) -> int:
    cfg = Config()
    state = State(ROOT)
    now = now_cst()
    date_str = args.date or now.strftime("%Y-%m-%d")
    slot = args.slot or infer_slot(now)
    slot_cn = "早场" if slot == "morning" else "晚场"

    log(f"==== Daily Horizon · {date_str} {slot_cn} ====")

    existing = state.slot_record(date_str, slot)
    if existing and existing.get("status") == "ok" and not args.force:
        log("该场次已生成并发送，跳过（需要重发请加 --force）")
        return 0

    plan = rotation.plan(datetime.strptime(date_str, "%Y-%m-%d").date(), slot)
    log(f"板块顺序：{plan['order']}，主攻 {plan['lead']}")

    rng = random.Random(f"{date_str}-{slot}")

    # ---------- 素材 ----------
    if args.mock:
        english_items = [
            {"title": "Global shipping costs ease as new container capacity comes online", "source": "BBC News",
             "published": "2026-10-28", "body": "", "words": 186},
            {"title": "Cities are turning empty offices into housing, slowly", "source": "The Guardian",
             "published": "2026-10-27", "body": "", "words": 142},
        ]
        sector_items = {k: [{"title": f"{k} 样刊素材", "source": "样刊", "published": "2026-10-28",
                             "body": "", "text_quality": "full"}] for k in ("finance", "travel", "consumer")}
    else:
        log("采集英语素材…")
        english_items = fetch.collect_english(state, cfg.get("english", "target_words", default=780),
                                             cfg.get("english", "max_articles", default=3), now, rng)
        if not english_items:
            log("英语素材全部不可用（可能网络受限），本场终止", "ERROR")
            return 2
        sector_items = {}
        for key in plan["order"]:
            log(f"采集 {key} 素材…")
            sector_items[key] = fetch.collect_sector(key, state, now, rng, want=3)
            if not sector_items[key]:
                log(f"{key} 无可用素材，本场跳过该板块", "WARN")

    # ---------- 生成 ----------
    if args.mock:
        english_md = sample.ENGLISH_MD
        sector_md = {"finance": sample.FINANCE_MD, "travel": sample.TRAVEL_MD, "consumer": sample.CONSUMER_MD}
        cost_note = "mock"
    else:
        if not cfg.llm_ready():
            log("缺少 DEEPSEEK_API_KEY", "ERROR")
            return 2
        client = llm.DeepSeek(
            cfg.llm_key, cfg.llm_base, cfg.llm_model, cfg.llm_temperature, cfg.llm_timeout
        )
        log("生成英语精读…")
        english_md = mdhtml.merge_translations(
            gen_english(client, english_items, cfg.get("english", "target_words", default=780), 60)
        )
        sector_md = {}
        for key in plan["order"]:
            if not sector_items.get(key):
                continue
            log(f"生成 {key} 板块…")
            minutes = plan.get(f"{'lead' if plan['lead'] == key else ('finance' if key == 'finance' else 'side')}_minutes", 25)
            sector_md[key] = mdhtml.merge_translations(
                gen_sector(client, key, sector_items[key], minutes)
            )
        cost_note = f"calls={client.calls} tokens={client.tokens['prompt']}+{client.tokens['completion']}"

    # ---------- 组装 ----------
    sectors = []
    for key in plan["order"]:
        if key not in sector_md:
            continue
        minutes_key = "lead_minutes" if plan["lead"] == key else ("finance_minutes" if key == "finance" else "side_minutes")
        sectors.append(
            {
                "key": key,
                "minutes": plan[minutes_key],
                "md": sector_md[key],
                "is_lead": plan["lead"] == key,
                "title": package.first_heading(sector_md[key]) or sources.SECTOR_META[key]["name"],
            }
        )

    # 某板块素材不足被跳过时，把 90 分钟按比例重分配给仍在的板块，保持总时长口径不变
    target_total = plan["total_minutes"]
    cur_total = sum(s["minutes"] for s in sectors)
    if sectors and cur_total and cur_total != target_total:
        scale = target_total / cur_total
        for s in sectors:
            s["minutes"] = max(10, int(round(s["minutes"] * scale / 5) * 5))
        diff = target_total - sum(s["minutes"] for s in sectors)
        sectors[0]["minutes"] += diff
        log(f"板块缺失，时长已重分配：{[(s['key'], s['minutes']) for s in sectors]}")

    words = sum(int(i.get("words") or 0) for i in english_items)
    pack = {
        "date": date_str,
        "slot": slot,
        "english_md": english_md,
        "english_words": words,
        "english_minutes": 60,
        "english_articles": len(english_items),
        "sectors": sectors,
        "generated_at": now.strftime("%Y-%m-%d %H:%M"),
        "preview": (package.first_heading(english_md) or "今日学习包")[:90],
    }

    # ---------- 存档 ----------
    md_text = package.to_markdown(pack, state.week_stats(now))
    md_path = ROOT / "data" / "packs" / f"{date_str}-{slot}.md"
    write_text(md_path, md_text)

    base_url = cfg.panel_url.rstrip("/")
    pack_rel = f"packs/{date_str}-{slot}.html"
    pack_url = f"{base_url}/{pack_rel}" if base_url else pack_rel

    payload = {
        "status": "ok",
        "generated_at": pack["generated_at"],
        "english_articles": pack["english_articles"],
        "english_minutes": 60,
        "sector_minutes": sum(s["minutes"] for s in sectors),
        "english_title": package.first_heading(english_md),
        "lead_title": next((s["title"] for s in sectors if s["is_lead"]), ""),
        "sectors": [{"key": s["key"], "title": s["title"], "minutes": s["minutes"]} for s in sectors],
        "pack_url": pack_rel,
        "cost": cost_note,
    }

    week_preview = _preview_week(state, date_str, slot, payload, now)
    email_html = package.to_email_html(pack, week_preview, cfg.panel_url, cfg.mailbox_url, pack_url)
    page_html = package.to_page_html(pack, week_preview, cfg.panel_url, f"{date_str}-{slot}")
    write_text(ROOT / "docs" / pack_rel, page_html)
    log(f"存档：{md_path.name} / docs/{pack_rel}")

    # 标题保留 PRD 固定模板作前缀，后缀区分早晚场
    subject_line = f"{cfg.mail_subject}｜{date_str[5:].replace(chr(45), chr(47))} {slot_cn}"

    # ---------- 发送 ----------
    sent = False
    if args.no_mail or cfg.dry_run:
        log("跳过发送（--no-mail / DRY_RUN）")
    elif not cfg.mail_ready():
        log("邮件未配置，仅生成不发送", "WARN")
    else:
        subject = subject_line
        try:
            mailer.send(cfg, subject, email_html, mdhtml.plain_text(md_text))
            sent = True
        except Exception as exc:  # noqa: BLE001
            log(f"发送失败：{exc}", "ERROR")
            payload["status"] = "partial"

    payload["sent"] = sent
    payload["subject"] = subject_line

    # ---------- 记录与面板 ----------
    state.record(date_str, slot, payload)
    for it in english_items:
        if it.get("body") or args.mock:
            state.mark_seen(item_id(it["title"]), it["title"], it.get("source", ""), date_str, slot, "english")
    for key, items in sector_items.items():
        for it in items:
            state.mark_seen(item_id(it["title"]), it["title"], it.get("source", ""), date_str, slot, key)
    pruned = state.prune(date_str)
    state.save()
    if pruned:
        log(f"清理过期去重记录 {pruned} 条")

    _write_panel(cfg, state, date_str, slot, now)

    log(f"完成 ｜ {pack['english_articles']} 篇英语 / {len(sectors)} 个板块 ｜ 发送：{'是' if sent else '否'}")
    if not sent and not (args.no_mail or cfg.dry_run) and cfg.mail_ready():
        return 3
    return 0


def _preview_week(state: State, date_str: str, slot: str, payload: dict, now: datetime) -> dict:
    """把本场计入统计后再算周数据，让邮件里的进度条包含今天这一场。"""
    days = state.data["days"]
    backup = days.get(date_str, {}).get(slot)
    days.setdefault(date_str, {})[slot] = payload
    stats = state.week_stats(now)
    if backup is None:
        days[date_str].pop(slot, None)
        if not days[date_str]:
            days.pop(date_str, None)
    else:
        days[date_str][slot] = backup
    return stats


def _write_panel(cfg: Config, state: State, date_str: str, slot: str, now: datetime) -> None:
    week = state.week_stats(now)
    today: dict[str, dict] = {}
    for s in ("morning", "evening"):
        rec = state.slot_record(date_str, s)
        if rec:
            today[s] = {
                "done": True,
                "title": rec.get("english_title") or rec.get("lead_title") or "",
                "url": rec.get("pack_url", ""),
            }
    html_text = panel.render(
        week,
        today,
        state.recent_packs(6),
        now.strftime("%Y-%m-%d %H:%M"),
        cfg.get("panel", "subtitle", default="每日精进 · 学习面板"),
    )
    write_text(ROOT / "docs" / "index.html", html_text)
    write_json(ROOT / "docs" / "data.json", {"week": week, "today": today, "updated_at": now.strftime("%Y-%m-%d %H:%M")})
    log("面板已刷新：docs/index.html")


def main() -> int:
    args = parse_args(sys.argv[1:])
    try:
        return run(args)
    except Exception:  # noqa: BLE001
        log("运行异常：\n" + traceback.format_exc(), "ERROR")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
