-- Stakeholder demo grain: core CN daily mart minus smoke/noise only.
-- Real probe UUIDs remain. Full mart_device_daily_usage_cn is unchanged.

select
    d.device_id,
    dim.display_name,
    dim.display_name_zh,
    dim.persona,
    dim.site,
    d.usage_date,
    d.active_minutes_day,
    d.active_hour_slots,
    d.utilization_pct,
    d.cpu_util_avg_pct,
    d.gpu_util_avg_pct,
    d.mem_util_avg_pct,
    d.disk_free_gb_min,
    (
        d.cpu_util_avg_pct is not null
        or d.gpu_util_avg_pct is not null
        or d.mem_util_avg_pct is not null
    ) as has_resource_metrics
from {{ ref('mart_device_daily_usage_cn') }} d
inner join {{ ref('dim_device') }} dim
    on dim.device_id = d.device_id
    and dim.include_in_demo
