"""配置加载。非敏感配置放 config.json，密钥一律走环境变量。"""

from __future__ import annotations

import os
import pathlib

from .util import read_json

ROOT = pathlib.Path(__file__).resolve().parent.parent

DEFAULTS = {
    "project": "Daily Horizon",
    "timezone": "Asia/Shanghai",
    "english": {
        "target_words": 780,
        "max_articles": 3,
        "min_words_per_article": 180,
    },
    "industry": {
        "total_minutes": 90,
        "lead_minutes": 40,
        "side_minutes": 25,
        "candidates_per_sector": 4,
    },
    "mail": {
        "host": "smtp.qq.com",
        "port": 465,
        "ssl": True,
        "from_name": "Daily Horizon",
        "subject": "Progress Log｜每日精进 · Daily Learning Pack",
        "mailbox_url": "https://mail.qq.com",
    },
    "llm": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "temperature": 0.6,
        "timeout": 240,
    },
    "panel": {
        "title": "Daily Horizon",
        "subtitle": "每日精进 · 学习面板",
        "url": "",
    },
    "sources": {
        "strict_whitelist": True,
        "per_sector_max": 3,
    },
}


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    def __init__(self, overrides: dict | None = None):
        raw = read_json(ROOT / "config.json", {})
        data = _merge(DEFAULTS, raw)
        if overrides:
            data = _merge(data, overrides)
        self.data = data

        mail = data["mail"]
        self.smtp_host = os.getenv("SMTP_HOST") or mail["host"]
        self.smtp_port = int(os.getenv("SMTP_PORT") or mail["port"])
        self.smtp_ssl = bool(mail.get("ssl", True))
        self.smtp_user = os.getenv("SMTP_USER", "").strip()
        self.smtp_pass = os.getenv("SMTP_PASS", "").strip()
        self.mail_from_name = mail["from_name"]
        self.mail_to = [x.strip() for x in (os.getenv("MAIL_TO") or "").split(",") if x.strip()]
        self.mail_subject = mail["subject"]
        self.mailbox_url = mail.get("mailbox_url", "")

        llm = data["llm"]
        self.llm_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.llm_base = (os.getenv("DEEPSEEK_BASE_URL") or llm["base_url"]).rstrip("/")
        self.llm_model = os.getenv("DEEPSEEK_MODEL") or llm["model"]
        self.llm_temperature = float(llm.get("temperature", 0.6))
        self.llm_timeout = int(llm.get("timeout", 240))

        self.panel_url = (os.getenv("PANEL_URL") or data["panel"].get("url") or "").strip()

    def get(self, *path, default=None):
        cur = self.data
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                return default
            cur = cur[key]
        return cur

    @property
    def dry_run(self) -> bool:
        return os.getenv("DH_DRY_RUN", "") == "1"

    def mail_ready(self) -> bool:
        return bool(self.smtp_user and self.smtp_pass and self.mail_to)

    def llm_ready(self) -> bool:
        return bool(self.llm_key)
