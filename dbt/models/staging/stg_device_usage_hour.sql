-- Latest row per (device_id, window_start).

select distinct on (device_id, window_start)
    id,
    schema_version,
    probe_version,
    device_id,
    window_start,
    window_end,
    active_minutes,
    cpu_util_avg_pct,
    gpu_util_avg_pct,
    mem_util_avg_pct,
    disk_free_gb,
    payload,
    _loaded_at
from {{ source('hope', 'raw_device_usage_hour') }}
order by
    device_id,
    window_start,
    _loaded_at desc,
    id desc
