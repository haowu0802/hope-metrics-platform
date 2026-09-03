"""Feishu/Lark incoming-webhook helper."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

DEFAULT_FEISHU_KEYWORD = "hope"


def feishu_webhook_url() -> str:
    return os.environ.get("FEISHU_WEBHOOK_URL", "").strip()


def feishu_keyword() -> str:
    return os.environ.get("FEISHU_KEYWORD", DEFAULT_FEISHU_KEYWORD).strip() or DEFAULT_FEISHU_KEYWORD


def with_feishu_keyword(text: str) -> str:
    """Ensure bot keyword is present (Feishu rejects posts that omit it)."""
    kw = feishu_keyword()
    if kw.lower() in text.lower():
        return text
    return f"{text.rstrip()}\n\n#{kw}"


def send_feishu_text(text: str, *, require_url: bool = False) -> str:
    """Post a text message. Returns 'sent' | 'logged'; raises on HTTP failure when URL set."""
    text = with_feishu_keyword(text)
    url = feishu_webhook_url()
    if not url:
        if require_url:
            raise RuntimeError(
                "FEISHU_WEBHOOK_URL unset. Set it in GitHub Actions secrets or local .env."
            )
        logger.info("FEISHU_WEBHOOK_URL unset; alert body:\n%s", text)
        return "logged"

    body = json.dumps(
        {"msg_type": "text", "content": {"text": text}},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", "replace")
            logger.info("Feishu webhook ok status=%s body=%s", resp.status, raw[:300])
            return "sent"
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        logger.error("Feishu webhook HTTP %s: %s", e.code, detail)
        raise
