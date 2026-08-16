-- Near-real-time device-hour grain for stakeholder demo.
-- View over staging: refreshes as soon as ingest lands (no daily-mart lag).

select
    s.device_id,
    dim.display_name,
    dim.display_name_zh,
    dim.persona,
    dim.site,
    s.window_start,
    (s.window_start at time zone 'Asia/Shanghai') as hour_start_cn,
    s.window_end,
    s.active_minutes,
    s.cpu_util_avg_pct,
    s.gpu_util_avg_pct,
    s.mem_util_avg_pct,
    s.disk_free_gb,
    s.schema_version,
    s.probe_version,
    s._loaded_at,
    (
        s.cpu_util_avg_pct is not null
        or s.gpu_util_avg_pct is not null
        or s.mem_util_avg_pct is not null
    ) as has_resource_metrics
from {{ ref('stg_device_usage_hour') }} s
inner join {{ ref('dim_device') }} dim
    on dim.device_id = s.device_id
    and dim.include_in_demo
