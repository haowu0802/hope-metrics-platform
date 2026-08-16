"""Alert when donated devices look unused (China calendar staleness)."""

from __future__ import annotations

import logging
import os
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from hope_feishu import send_feishu_text

logger = logging.getLogger(__name__)

METABASE_STALE_URL = os.environ.get(
    "METABASE_DEMO_URL",
    "https://hope-metrics-metabase.fly.dev/dashboard/3",
).strip()


def check_stale_devices() -> None:
    """Query mart_device_staleness_demo; Feishu (or log) when is_stale devices exist."""
    try:
        import psycopg

        connect = psycopg.connect
    except ImportError:
        import psycopg2 as psycopg  # type: ignore

        connect = psycopg.connect

    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL required for stale-device check")

    stale_days = int(os.environ.get("STALE_DEVICE_DAYS", "2"))
    sql = """
        SELECT device_id, display_name_zh, last_seen_date, days_since_seen
        FROM mart_device_staleness_demo
        WHERE days_since_seen >= %s
        ORDER BY days_since_seen DESC, device_id
        LIMIT 50
    """
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (stale_days,))
            rows = cur.fetchall()

    if not rows:
        # Still notify on manual/demo runs so the channel is visibly alive.
        mode = send_feishu_text(
            f"【Hope 捐赠电脑闲置告警】当前无设备达到 ≥{stale_days} 北京日历日闲置阈值。\n"
            f"看板：{METABASE_STALE_URL}"
        )
        logger.info("no stale devices; cleared notice mode=%s", mode)
        return

    lines = [
        f"【Hope 捐赠电脑闲置告警】{len(rows)} 台设备已 ≥{stale_days} 个北京日历日无活跃",
        f"看板：{METABASE_STALE_URL}",
        "",
    ]
    for device_id, name_zh, last_seen, days in rows:
        label = name_zh or device_id
        lines.append(f"· {label}（{device_id}）最近活跃={last_seen} 闲置={days}天")
    mode = send_feishu_text("\n".join(lines))
    logger.info("stale alert delivered mode=%s count=%s", mode, len(rows))


def _feishu_on_failure(context) -> None:
    ti = context.get("task_instance")
    text = (
        "【Hope Metrics】闲置告警任务失败\n"
        f"task={getattr(ti, 'task_id', '?')} run={context.get('run_id', '?')}"
    )
    try:
        send_feishu_text(text)
    except Exception:
        logger.exception("Feishu failure callback failed")


with DAG(
    dag_id="hope_device_alerts",
    description="Feishu alert when devices are stale (unused)",
    schedule="30 12 * * *",  # after hope_dbt_daily (12:00 UTC)
    start_date=datetime(2026, 8, 1),
    catchup=False,
    max_active_runs=1,
    tags=["hope", "alerts", "feishu"],
    default_args={
        "retries": 1,
        "on_failure_callback": _feishu_on_failure,
    },
) as dag:
    PythonOperator(
        task_id="check_stale_devices",
        python_callable=check_stale_devices,
    )
