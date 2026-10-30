"""邮件发送（SMTP，SSL / STARTTLS 自适应）。"""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from .util import log


def send(cfg, subject: str, html_body: str, text_body: str, to: list[str] | None = None) -> str:
    if not cfg.mail_ready():
        raise RuntimeError("邮件配置不完整：需要 SMTP_USER / SMTP_PASS / MAIL_TO")

    recipients = to or cfg.mail_to
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((cfg.mail_from_name, cfg.smtp_user))
    msg["To"] = ", ".join(recipients)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    context = ssl.create_default_context()
    if cfg.smtp_ssl:
        with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, timeout=60, context=context) as s:
            s.login(cfg.smtp_user, cfg.smtp_pass)
            s.send_message(msg)
    else:
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=60) as s:
            s.ehlo()
            s.starttls(context=context)
            s.login(cfg.smtp_user, cfg.smtp_pass)
            s.send_message(msg)

    log(f"邮件已发送 → {', '.join(recipients)}")
    return ", ".join(recipients)
