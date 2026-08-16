"""Monthly Hope Metrics Feishu digest (previous Beijing calendar month)."""

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


def _prev_month_bounds(today):
    first_this = today.replace(day=1)
    month_end = first_this - timedelta(days=1)
    month_start = month_end.replace(day=1)
    return month_start, month_end


def _prior_month_bounds(month_start):
    prior_end = month_start - timedelta(days=1)
    prior_start = prior_end.replace(day=1)
    return prior_start, prior_end


def send_monthly_feishu_report() -> None:
    stale_days = stale_device_days()
    connect = connect_fn()

    with connect(database_url()) as conn:
        with conn.cursor() as cur:
            today = today_cn(cur)
            start, end = _prev_month_bounds(today)
            prior_start, prior_end = _prior_month_bounds(start)
            days_in_month = (end - start).days + 1

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
                select display_name_zh,
                       sum(active_minutes_day)::bigint as mins,
                       count(*) filter (where active_minutes_day > 0)::int as active_days
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
                select coalesce(site, '未标注') as site,
                       sum(active_minutes_day)::bigint as mins
                from mart_device_daily_usage_cn_demo
                where usage_date between %s and %s
                group by 1
                order by mins desc nulls last
                limit 5
                """,
                (start, end),
            )
            by_site = cur.fetchall()

            cur.execute(
                """
                select coalesce(persona, '未标注') as persona,
                       sum(active_minutes_day)::bigint as mins
                from mart_device_daily_usage_cn_demo
                where usage_date between %s and %s
                group by 1
                order by mins desc nulls last
                limit 5
                """,
                (start, end),
            )
            by_persona = cur.fetchall()

            cur.execute(
                """
                select display_name_zh,
                       round(avg(cpu_util_avg_pct)::numeric, 1) as cpu,
                       round(avg(gpu_util_avg_pct)::numeric, 1) as gpu
                from mart_device_daily_usage_cn_demo
                where usage_date between %s and %s
                  and (cpu_util_avg_pct is not null or gpu_util_avg_pct is not null)
                group by display_name_zh
                order by cpu desc nulls last
                limit 3
                """,
                (start, end),
            )
            resource_top = cur.fetchall()

            stale = stale_snapshot(cur, stale_days)
            last_ingest_at, last_event_at, mart_through = fetch_freshness(cur)

    vs_prior = pct_delta(minutes, minutes_prior)
    lines = [
        "【Hope 每月捐赠电脑用量简报】",
        (
            f"报告月（北京）：{start.isoformat()} ~ {end.isoformat()}"
            f"（{days_in_month} 天）· 生成 {now_cn_str()}"
        ),
        "",
        f"本月活跃合计：{minutes} 分钟（较上月 {vs_prior}）",
        f"日均活跃：{avg_daily} 分钟 · 日均有用量设备≈{avg_devices}",
        f"本月曾活跃设备：{devices_active}/{devices}（含资源指标机群 {with_resources} 台）",
        f"本月机群平均CPU≈{avg_cpu}% · 有数据日数 {day_rows}/{days_in_month}",
    ]

    if peak_day:
        d, m, n = peak_day
        lines.append(f"最忙日：{d} — {m} 分钟（{n} 台有用量）")

    lines.extend(["", "本月活跃 Top5："])
    if top:
        for name_zh, mins, active_days in top:
            lines.append(f"· {name_zh or '?'} — {mins} 分钟（活跃 {active_days} 天）")
    else:
        lines.append("· （本月无用量）")

    if by_site:
        lines.append("")
        lines.append("按站点：")
        for site, mins in by_site:
            lines.append(f"· {site} — {mins} 分钟")

    if by_persona:
        lines.append("")
        lines.append("按角色：")
        for persona, mins in by_persona:
            lines.append(f"· {persona} — {mins} 分钟")

    if resource_top:
        lines.append("")
        lines.append("本月平均资源 Top3：")
        for name_zh, cpu, gpu in resource_top:
            gpu_s = f" · GPU≈{gpu}%" if gpu is not None else ""
            lines.append(f"· {name_zh or '?'} CPU≈{cpu}%{gpu_s}")

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
        "monthly Feishu report mode=%s period=%s..%s minutes=%s",
        mode,
        start,
        end,
        minutes,
    )


def _feishu_on_failure(context) -> None:
    ti = context.get("task_instance")
    text = (
        "【Hope Metrics】每月飞书简报任务失败\n"
        f"task={getattr(ti, 'task_id', '?')} run={context.get('run_id', '?')}"
    )
    try:
        send_feishu_text(text)
    except Exception:
        logger.exception("Feishu failure callback failed")


with DAG(
    dag_id="hope_monthly_feishu_report",
    description="Monthly Feishu digest (prev CN calendar month) + Metabase links",
    schedule="15 13 1 * *",  # 1st of month after daily pipeline
    start_date=datetime(2026, 8, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    tags=["hope", "feishu", "metabase", "report", "monthly"],
    default_args={
        "retries": 1,
        "on_failure_callback": _feishu_on_failure,
    },
) as dag:
    PythonOperator(
        task_id="send_monthly_feishu_report",
        python_callable=send_monthly_feishu_report,
    )
