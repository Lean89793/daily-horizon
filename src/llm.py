"""DeepSeek 客户端（OpenAI 兼容协议），纯标准库。"""

from __future__ import annotations

import re
import time

from .util import http_post_json, log


class LLMError(RuntimeError):
    pass


class DeepSeek:
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.6, timeout: int = 240):
        if not api_key:
            raise LLMError("缺少 DEEPSEEK_API_KEY")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.calls = 0
        self.tokens = {"prompt": 0, "completion": 0}

    def chat(self, system: str, user: str, max_tokens: int = 6000, temperature: float | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        started = time.time()
        try:
            resp = http_post_json(
                f"{self.base_url}/chat/completions",
                payload,
                {"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
                retries=2,
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"模型调用失败：{exc}") from exc

        self.calls += 1
        usage = resp.get("usage") or {}
        self.tokens["prompt"] += int(usage.get("prompt_tokens", 0))
        self.tokens["completion"] += int(usage.get("completion_tokens", 0))

        try:
            content = resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"返回结构异常：{str(resp)[:300]}") from exc

        elapsed = time.time() - started
        log(
            f"LLM ok · {elapsed:.1f}s · in {usage.get('prompt_tokens', '?')} / out {usage.get('completion_tokens', '?')}"
        )
        return _clean(content)

    def chat_json(self, system: str, user: str, max_tokens: int = 4000) -> dict:
        import json

        raw = self.chat(system, user, max_tokens=max_tokens, temperature=0.1)
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", raw, re.S)
            if not m:
                raise LLMError("JSON 解析失败")
            return json.loads(m.group(0))


def _clean(text: str) -> str:
    text = text.strip()
    # 去掉整体包裹的代码块围栏
    text = re.sub(r"^```(?:markdown|md)?\s*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    return text.strip()
