-- Staleness for demo/alerts: same logic as mart_device_staleness, demo cohort only.
-- Full mart_device_staleness still lists every device (including smoke).

{% set stale_days = var('stale_device_days', 2) %}

with bounds as (
    select (timezone('Asia/Shanghai', now()))::date as today_cn
),

summary as (
    select
        device_id,
        last_seen_date,
        active_minutes_total,
        active_days,
        cpu_util_avg_pct,
        gpu_util_avg_pct
    from {{ ref('mart_device_summary_cn_demo') }}
)

select
    s.device_id,
    dim.display_name,
    dim.display_name_zh,
    dim.persona,
    s.last_seen_date,
    s.active_days,
    s.active_minutes_total,
    b.today_cn,
    greatest((b.today_cn - s.last_seen_date)::integer, 0) as days_since_seen,
    case
        when (b.today_cn - s.last_seen_date) >= {{ stale_days }} then true
        else false
    end as is_stale,
    (
        s.cpu_util_avg_pct is not null
        or s.gpu_util_avg_pct is not null
    ) as has_resource_metrics
from summary s
inner join {{ ref('dim_device') }} dim on dim.device_id = s.device_id
cross join bounds b
