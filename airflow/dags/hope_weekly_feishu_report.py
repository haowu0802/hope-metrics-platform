"""Weekly Hope Metrics Feishu digest (previous Mon–Sun, Asia/Shanghai)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.python import PythonOperator

from hope_feishu import send_feishu_text
from hope_report_common import (
    cohort_counts,
    connect_fn,
    dashboard_footer_lines,
    database_url,
    fetch_freshness,
    freshness_line,
    now_cn_str,
    pct_delta,
    stale_device_days,
    stale_snapshot,
    today_cn,
)

logger = logging.getLogger(__name__)


def _prev_week_bounds(today):
    """Previous complete Mon–Sun in Beijing calendar."""
    week_end = today - timedelta(days=today.weekday() + 1)  # last Sunday
    week_start = week_end - timedelta(days=6)
    return week_start, week_end


def send_weekly_feishu_report() -> None:
    stale_days = stale_device_days()
    connect = connect_fn()

    with connect(database_url()) as conn:
        with conn.cursor() as cur:
            today = today_cn(cur)
            start, end = _prev_week_bounds(today)
            prior_end = start - timedelta(days=1)
            prior_start = prior_end - timedelta(days=6)

            devices, with_resources = cohort_counts(cur)

            cur.execute(
                """
                select
                    coalesce(sum(active_minutes_total), 0)::bigint,
                    coalesce(round(avg(active_minutes_total)::numeric, 0), 0)::bigint,
                    coalesce(round(avg(active_devices)::numeric, 1), 0),
                    coalesce(round(avg(cpu_util_avg_pct)::numeric, 1), 0),
                    count(*)::int
                from mart_fleet_daily_cn_demo
                where usage_date between %s and %s
                """,
                (start, end),
            )
            minutes, avg_daily, avg_devices, avg_cpu, day_rows = cur.fetchone()

            cur.execute(
                """
                select coalesce(sum(active_minutes_total), 0)::bigint
                from mart_fleet_daily_cn_demo
                where usage_date between %s and %s
                """,
                (prior_start, prior_end),
            )
            minutes_prior = cur.fetchone()[0]

            cur.execute(
                """
                select usage_date, active_minutes_total, active_devices
                from mart_fleet_daily_cn_demo
                where usage_date between %s and %s
                order by active_minutes_total desc nulls last
                limit 1
                """,
                (start, end),
            )
            peak_day = cur.fetchone()

            cur.execute(
                """
                select usage_date, active_minutes_total
                from mart_fleet_daily_cn_demo
                where usage_date between %s and %s
                order by active_minutes_total asc nulls last
                limit 1
                """,
                (start, end),
            )
            quiet_day = cur.fetchone()

            cur.execute(
                """
                select count(distinct device_id)::int
                from mart_device_daily_usage_cn_demo
                where usage_date between %s and %s
                  and active_minutes_day > 0
                """,
                (start, end),
            )
            devices_active = cur.fetchone()[0]

            cur.execute(
                """
                select display_name_zh, sum(active_minutes_day)::bigint as mins
                from mart_device_daily_usage_cn_demo
                where usage_date between %s and %s
                group by display_name_zh
                order by mins desc nulls last
                limit 5
                """,
                (start, end),
            )
            top = cur.fetchall()

            cur.execute(
                """
                select display_name_zh,
                       round(avg(cpu_util_avg_pct)::numeric, 1) as cpu
                from mart_device_daily_usage_cn_demo
                where usage_date between %s and %s
                  and cpu_util_avg_pct is not null
                group by display_name_zh
                order by cpu desc nulls last
                limit 3
                """,
                (start, end),
            )
            cpu_top = cur.fetchall()

            stale = stale_snapshot(cur, stale_days)
            last_ingest_at, last_event_at, mart_through = fetch_freshness(cur)

    vs_prior = pct_delta(minutes, minutes_prior)
    lines = [
        "【Hope 每周捐赠电脑用量简报】",
        f"报告周（北京）：{start.isoformat()} ~ {end.isoformat()} · 生成 {now_cn_str()}",
        "",
        f"本周活跃合计：{minutes} 分钟（较上周 {vs_prior}）",
        f"日均活跃：{avg_daily} 分钟 · 日均有用量设备≈{avg_devices}",
        f"本周曾活跃设备：{devices_active}/{devices}（含资源指标机群 {with_resources} 台）",
        f"本周机群平均CPU≈{avg_cpu}% · 有数据日数 {day_rows}/7",
    ]

    if peak_day:
        d, m, n = peak_day
        lines.append(f"最忙日：{d} — {m} 分钟（{n} 台有用量）")
    if quiet_day:
        d, m = quiet_day
        lines.append(f"最闲日：{d} — {m} 分钟")

    lines.extend(["", "本周活跃 Top5："])
    if top:
        for name_zh, mins in top:
            lines.append(f"· {name_zh or '?'} — {mins} 分钟")
    else:
        lines.append("· （本周无用量）")

    if cpu_top:
        lines.append("")
        lines.append("本周平均 CPU Top3：")
        for name_zh, cpu in cpu_top:
            lines.append(f"· {name_zh or '?'} ≈ {cpu}%")

    lines.append("")
    if stale:
        lines.append(f"当前闲置（≥{stale_days} 日）：{len(stale)} 台")
        for name_zh, days in stale:
            lines.append(f"· {name_zh or '?'} 闲置 {days} 天")
    else:
        lines.append(f"当前闲置（≥{stale_days} 日）：无")

    lines.extend(
        [
            "",
            freshness_line(last_ingest_at, last_event_at, mart_through),
            "",
            *dashboard_footer_lines(),
        ]
    )

    mode = send_feishu_text("\n".join(lines))
    logger.info(
        "weekly Feishu report mode=%s period=%s..%s minutes=%s",
        mode,
        start,
        end,
        minutes,
    )


def _feishu_on_failure(context) -> None:
    ti = context.get("task_instance")
    text = (
        "【Hope Metrics】每周飞书简报任务失败\n"
        f"task={getattr(ti, 'task_id', '?')} run={context.get('run_id', '?')}"
    )
    try:
        send_feishu_text(text)
    except Exception:
        logger.exception("Feishu failure callback failed")


with DAG(
    dag_id="hope_weekly_feishu_report",
    description="Weekly Feishu digest (prev Mon–Sun CN) + Metabase links",
    schedule="0 13 * * 1",  # Monday after daily dbt/alerts
    start_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    tags=["hope", "feishu", "metabase", "report", "weekly"],
    default_args={
        "retries": 1,
        "on_failure_callback": _feishu_on_failure,
    },
) as dag:
    PythonOperator(
        task_id="send_weekly_feishu_report",
        python_callable=send_weekly_feishu_report,
    )
