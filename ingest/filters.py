"""Dashboard query helpers (filters, shareable URLs)."""

from __future__ import annotations

from datetime import date
from urllib.parse import urlencode


def parse_iso_date(raw: str | None) -> date | None:
    if not raw or not str(raw).strip():
        return None
    try:
        return date.fromisoformat(str(raw).strip()[:10])
    except ValueError:
        return None


def normalize_device_ids(raw: list[str] | None) -> list[str]:
    if not raw:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        for part in str(item).split(","):
            value = part.strip()
            if value and value not in seen:
                seen.add(value)
                out.append(value)
    return out


def build_query(**parts: str | None | list[str]) -> str:
    """Build ?a=1&b=2 from non-empty parts. Lists become repeated keys."""
    pairs: list[tuple[str, str]] = []
    for key, value in parts.items():
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                if item:
                    pairs.append((key, str(item)))
            continue
        text = str(value).strip()
        if text:
            pairs.append((key, text))
    if not pairs:
        return ""
    return "?" + urlencode(pairs)
