-- Hour-of-day for demo cohort only (real probes + sim personas; no smoke).

select
    extract(hour from (s.window_start at time zone 'Asia/Shanghai'))::integer as hour_cn,
    sum(s.active_minutes)::integer as active_minutes_sum,
    count(distinct s.device_id)::integer as device_count,
    round(avg(s.active_minutes)::numeric, 1) as active_minutes_avg,
    round(avg(s.cpu_util_avg_pct)::numeric, 1) as cpu_util_avg_pct,
    round(avg(s.gpu_util_avg_pct)::numeric, 1) as gpu_util_avg_pct,
    round(avg(s.mem_util_avg_pct)::numeric, 1) as mem_util_avg_pct
from {{ ref('stg_device_usage_hour') }} s
inner join {{ ref('dim_device') }} dim
    on dim.device_id = s.device_id
    and dim.include_in_demo
group by
    extract(hour from (s.window_start at time zone 'Asia/Shanghai'))
