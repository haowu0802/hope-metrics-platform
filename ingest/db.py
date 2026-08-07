"""Postgres access."""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Any

import psycopg


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def list_device_ids() -> list[str]:
    sql = """
        SELECT DISTINCT device_id
        FROM mart_device_daily_usage
        ORDER BY device_id
    """
    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return [str(r[0]) for r in cur.fetchall()]


def fetch_daily_usage(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    device_ids: list[str] | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if date_from is not None:
        clauses.append("usage_date >= %(date_from)s")
        params["date_from"] = date_from
    if date_to is not None:
        clauses.append("usage_date <= %(date_to)s")
        params["date_to"] = date_to
    if device_ids:
        clauses.append("device_id = ANY(%(device_ids)s)")
        params["device_ids"] = device_ids
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT device_id, usage_date, active_minutes_day
        FROM mart_device_daily_usage
        {where}
        ORDER BY usage_date DESC, device_id
        LIMIT %(limit)s
    """
    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return [_row_to_dict(r) for r in rows]


def fetch_daily_trend(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    device_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if date_from is not None:
        clauses.append("usage_date >= %(date_from)s")
        params["date_from"] = date_from
    if date_to is not None:
        clauses.append("usage_date <= %(date_to)s")
        params["date_to"] = date_to
    if device_ids:
        clauses.append("device_id = ANY(%(device_ids)s)")
        params["device_ids"] = device_ids
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT usage_date, SUM(active_minutes_day)::int AS active_minutes_day
        FROM mart_device_daily_usage
        {where}
        GROUP BY usage_date
        ORDER BY usage_date
    """
    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return [
        {
            "usage_date": r[0].isoformat() if hasattr(r[0], "isoformat") else str(r[0]),
            "active_minutes_day": int(r[1]),
        }
        for r in rows
    ]


def fetch_device_rank(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    device_ids: list[str] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if date_from is not None:
        clauses.append("usage_date >= %(date_from)s")
        params["date_from"] = date_from
    if date_to is not None:
        clauses.append("usage_date <= %(date_to)s")
        params["date_to"] = date_to
    if device_ids:
        clauses.append("device_id = ANY(%(device_ids)s)")
        params["device_ids"] = device_ids
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT device_id, SUM(active_minutes_day)::int AS active_minutes_sum
        FROM mart_device_daily_usage
        {where}
        GROUP BY device_id
        ORDER BY active_minutes_sum DESC, device_id
        LIMIT %(limit)s
    """
    with psycopg.connect(database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return [
        {"device_id": str(r[0]), "active_minutes_sum": int(r[1])}
        for r in rows
    ]


def summarize_daily_usage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "device_count": 0,
            "row_count": 0,
            "total_minutes": 0,
            "date_from": None,
            "date_to": None,
        }
    devices = {r["device_id"] for r in rows}
    dates = [r["usage_date"] for r in rows]
    return {
        "device_count": len(devices),
        "row_count": len(rows),
        "total_minutes": sum(int(r["active_minutes_day"]) for r in rows),
        "date_from": min(dates),
        "date_to": max(dates),
    }


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


def _row_to_dict(r: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "device_id": r[0],
        "usage_date": r[1].isoformat() if hasattr(r[1], "isoformat") else str(r[1]),
        "active_minutes_day": int(r[2]),
    }


def _parse_ts(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)
