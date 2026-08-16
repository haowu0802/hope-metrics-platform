-- Device freshness for unused-machine alerts (China calendar).

{% set stale_days = var('stale_device_days', 2) %}

with bounds as (
    select (timezone('Asia/Shanghai', now()))::date as today_cn
),

summary as (
    select
        device_id,
        last_seen_date,
        active_minutes_total,
        active_days
    from {{ ref('mart_device_summary_cn') }}
)

select
    s.device_id,
    s.last_seen_date,
    s.active_days,
    s.active_minutes_total,
    b.today_cn,
    greatest((b.today_cn - s.last_seen_date)::integer, 0) as days_since_seen,
    case
        when (b.today_cn - s.last_seen_date) >= {{ stale_days }} then true
        else false
    end as is_stale
from summary s
cross join bounds b
