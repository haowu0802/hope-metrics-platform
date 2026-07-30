"""Postgres access."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import psycopg


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def fetch_daily_usage(limit: int = 90) -> list[dict[str, Any]]:
    sql = """
        SELECT device_id, usage_date, active_minutes_day
        FROM mart_device_daily_usage
        ORDER BY usage_date DESC, device_id
        LIMIT %(limit)s
    """
    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"limit": limit})
            rows = cur.fetchall()
    return [
        {
            "device_id": r[0],
            "usage_date": r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1]),
            "active_minutes_day": int(r[2]),
        }
        for r in rows
    ]


def insert_usage_hour(event: dict[str, Any]) -> int:
    window_start = _parse_ts(event["window_start"])
    window_end = _parse_ts(event["window_end"])
    active_minutes = int(event["active_minutes"])

    sql = """
        INSERT INTO raw_device_usage_hour (
            schema_version,
            probe_version,
            device_id,
            window_start,
            window_end,
            active_minutes,
            payload
        ) VALUES (
            %(schema_version)s,
            %(probe_version)s,
            %(device_id)s,
            %(window_start)s,
            %(window_end)s,
            %(active_minutes)s,
            %(payload)s::jsonb
        )
        RETURNING id
    """
    params = {
        "schema_version": str(event["schema_version"]),
        "probe_version": str(event["probe_version"]),
        "device_id": str(event["device_id"]),
        "window_start": window_start,
        "window_end": window_end,
        "active_minutes": active_minutes,
        "payload": json.dumps(event, default=str),
    }
    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            assert row is not None
            return int(row[0])


def _parse_ts(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)
