"""Shared helpers for Hope Feishu KPI digests (daily / weekly / monthly)."""

from __future__ import annotations

import os
from datetime import date, datetime
from urllib.parse import urlparse, urlunparse
from zoneinfo import ZoneInfo

CN_TZ = ZoneInfo("Asia/Shanghai")

_DEFAULT_PUBLIC = (
    "https://hope-metrics-metabase.fly.dev/public/dashboard/"
    "df568889-d528-46f4-a9c7-115e4c36b93c"
)
_DEFAULT_LOGIN = "https://hope-metrics-metabase.fly.dev/dashboard/3"


def connect_fn():
    try:
        import psycopg

        return psycopg.connect
    except ImportError:
        import psycopg2 as psycopg  # type: ignore

        return psycopg.connect


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL required for Feishu reports")
    return url


def stale_device_days() -> int:
    return int(os.environ.get("STALE_DEVICE_DAYS", "2"))


def public_dashboard_url() -> str:
    """Handout link without device filter query params."""
    raw = (os.environ.get("METABASE_PUBLIC_URL") or _DEFAULT_PUBLIC).strip() or _DEFAULT_PUBLIC
    parsed = urlparse(raw)
    return urlunparse(parsed._replace(query="", fragment=""))


def login_dashboard_url() -> str:
    return (os.environ.get("METABASE_DEMO_URL") or _DEFAULT_LOGIN).strip() or _DEFAULT_LOGIN


def pct_delta(current: int | float | None, baseline: int | float | None) -> str:
    if current is None or baseline is None or baseline == 0:
        return "—"
    delta = (float(current) - float(baseline)) / float(baseline) * 100.0
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.0f}%"


def fmt_ts_cn(value) -> str:
    if value is None:
        return "—"
    if hasattr(value, "astimezone"):
        return value.astimezone(CN_TZ).strftime("%m-%d %H:%M")
    return str(value)[:16]


def now_cn_str() -> str:
    return datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M")


def today_cn(cur) -> date:
    cur.execute("select (timezone('Asia/Shanghai', now()))::date")
    return cur.fetchone()[0]


def dashboard_footer_lines() -> list[str]:
    return [
        f"公开看板（免登录）：{public_dashboard_url()}",
        f"登录看板：{login_dashboard_url()}",
    ]


def fetch_freshness(cur) -> tuple:
    cur.execute(
        """
        select max(_loaded_at), max(window_start)
        from raw_device_usage_hour
        """
    )
    last_ingest_at, last_event_at = cur.fetchone()
    cur.execute("select max(usage_date) from mart_fleet_daily_cn_demo")
    mart_through = cur.fetchone()[0]
    return last_ingest_at, last_event_at, mart_through


def freshness_line(last_ingest_at, last_event_at, mart_through) -> str:
    return (
        f"数据新鲜度：最近接入 {fmt_ts_cn(last_ingest_at)} · "
        f"最近事件 {fmt_ts_cn(last_event_at)} · "
        f"mart 覆盖至 {mart_through or '—'}"
    )


def cohort_counts(cur) -> tuple[int, int]:
    cur.execute(
        """
        select count(*)::int,
               count(*) filter (where has_resource_metrics)::int
        from mart_device_summary_cn_demo
        """
    )
    return cur.fetchone()


def stale_snapshot(cur, stale_days: int, limit: int = 8) -> list[tuple]:
    cur.execute(
        """
        select display_name_zh, days_since_seen
        from mart_device_staleness_demo
        where days_since_seen >= %s
        order by days_since_seen desc, device_id
        limit %s
        """,
        (stale_days, limit),
    )
    return cur.fetchall()
