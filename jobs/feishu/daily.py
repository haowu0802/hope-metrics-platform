"""Daily Hope Metrics Feishu digest with Metabase public dashboard link."""

from __future__ import annotations

import logging
from datetime import timedelta

from jobs.feishu.common import (
    cohort_counts,
    connect_fn,
    dashboard_footer_lines,
    database_url,
    fetch_freshness,
    freshness_line,
    now_cn_str,
    pct_delta,
    stale_device_days,
    today_cn,
)
from jobs.feishu.webhook import send_feishu_text

logger = logging.getLogger(__name__)


def send_daily_metabase_report() -> None:
    """Yesterday-focused demo KPIs + Metabase links → Feishu."""
    stale_days = stale_device_days()
    connect = connect_fn()

    with connect(database_url()) as conn:
        with conn.cursor() as cur:
            today = today_cn(cur)
            yday = today - timedelta(days=1)
            prev = today - timedelta(days=2)

            devices, with_resources = cohort_counts(cur)

            cur.execute(
                """
                select
                    coalesce(sum(active_minutes_total) filter (where usage_date = %s), 0)::bigint,
                    coalesce(max(active_devices) filter (where usage_date = %s), 0)::int,
                    coalesce(sum(active_minutes_total) filter (where usage_date = %s), 0)::bigint,
                    coalesce(
                        round(
                            avg(active_minutes_total) filter (
                                where usage_date >= %s - 7 and usage_date < %s
                            )::numeric,
                            0
                        ),
                        0
                    )::bigint,
                    coalesce(
                        round(
                            avg(cpu_util_avg_pct) filter (where usage_date = %s)::numeric,
                            1
                        ),
                        0
                    )
                from mart_fleet_daily_cn_demo
                """,
                (yday, yday, prev, today, today, yday),
            )
            (
                minutes_yday,
                active_devices_yday,
                minutes_prev,
                minutes_7d_avg,
                cpu_yday,
            ) = cur.fetchone()

            cur.execute(
                """
                select display_name_zh, active_minutes_day
                from mart_device_daily_usage_cn_demo
                where usage_date = %s
                order by active_minutes_day desc nulls last
                limit 3
                """,
                (yday,),
            )
            top = cur.fetchall()

            cur.execute(
                """
                select display_name_zh, round(cpu_util_avg_pct::numeric, 1)
                from mart_device_daily_usage_cn_demo
                where usage_date = %s
                  and cpu_util_avg_pct is not null
                order by cpu_util_avg_pct desc nulls last
                limit 2
                """,
                (yday,),
            )
            cpu_peak = cur.fetchall()

            cur.execute(
                """
                select
                    extract(
                        hour from (s.window_start at time zone 'Asia/Shanghai')
                    )::int as hour_cn,
                    sum(s.active_minutes)::bigint as mins
                from stg_device_usage_hour s
                inner join dim_device dim
                    on dim.device_id = s.device_id
                   and dim.include_in_demo
                where (s.window_start at time zone 'Asia/Shanghai')::date = %s
                group by 1
                order by mins desc nulls last
                limit 1
                """,
                (yday,),
            )
            peak_hour_row = cur.fetchone()

            cur.execute(
                """
                select display_name_zh, days_since_seen
                from mart_device_staleness_demo
                where days_since_seen = %s
                order by display_name_zh nulls last, device_id
                limit 5
                """,
                (stale_days,),
            )
            newly_stale = cur.fetchall()

            cur.execute(
                """
                select display_name_zh, days_since_seen
                from mart_device_staleness_demo
                where days_since_seen > %s
                order by days_since_seen desc, device_id
                limit 5
                """,
                (stale_days,),
            )
            long_stale = cur.fetchall()

            cur.execute(
                """
                with yday_usage as (
                    select device_id, active_minutes_day
                    from mart_device_daily_usage_cn_demo
                    where usage_date = %s
                )
                select s.display_name_zh, s.days_since_seen
                from mart_device_staleness_demo s
                left join yday_usage u on u.device_id = s.device_id
                where s.days_since_seen < %s
                  and coalesce(u.active_minutes_day, 0) = 0
                order by s.days_since_seen desc, s.device_id
                limit 5
                """,
                (yday, stale_days),
            )
            quiet = cur.fetchall()

            last_ingest_at, last_event_at, mart_through = fetch_freshness(cur)

    vs_prev = pct_delta(minutes_yday, minutes_prev)
    vs_7d = pct_delta(minutes_yday, minutes_7d_avg)

    lines = [
        "【Hope 每日捐赠电脑用量简报】",
        f"报告日（北京）：{yday.isoformat()} · 生成 {now_cn_str()}",
        "",
        (
            f"昨日活跃：{minutes_yday} 分钟"
            f"（较前日 {vs_prev} · 较近7日日均 {vs_7d}）"
        ),
        f"昨日有用量设备：{active_devices_yday}/{devices}（含资源指标机群 {with_resources} 台）",
        f"昨日机群平均CPU≈{cpu_yday}%",
        "",
        "昨日活跃 Top3：",
    ]
    if top:
        for name_zh, mins in top:
            lines.append(f"· {name_zh or '?'} — {mins} 分钟")
    else:
        lines.append("· （昨日无用量行）")

    if cpu_peak:
        lines.append("")
        lines.append("昨日 CPU 高峰：")
        for name_zh, cpu in cpu_peak:
            lines.append(f"· {name_zh or '?'} ≈ {cpu}%")

    if peak_hour_row:
        hour_cn, peak_mins = peak_hour_row
        lines.append("")
        lines.append(f"昨日高峰时段：{hour_cn:02d}:00–{hour_cn:02d}:59（约 {peak_mins} 分钟）")

    lines.append("")
    if newly_stale:
        lines.append(f"新闲置（刚好 {stale_days} 日）：{len(newly_stale)} 台")
        for name_zh, days in newly_stale:
            lines.append(f"· {name_zh or '?'} 闲置 {days} 天")
    else:
        lines.append(f"新闲置（刚好 {stale_days} 日）：无")

    if long_stale:
        lines.append(f"持续闲置（>{stale_days} 日）：{len(long_stale)} 台")
        for name_zh, days in long_stale:
            lines.append(f"· {name_zh or '?'} 闲置 {days} 天")

    if quiet:
        lines.append("昨日沉寂（尚未达闲置阈值）：")
        for name_zh, days in quiet:
            lines.append(f"· {name_zh or '?'}（距上次活跃 {days} 日）")

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
        "daily Feishu report mode=%s yday=%s minutes=%s active=%s/%s",
        mode,
        yday,
        minutes_yday,
        active_devices_yday,
        devices,
    )
