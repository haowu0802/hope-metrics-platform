with summary as (
    {{ mart_device_summary_sql('mart_device_daily_usage_cn_demo') }}
)

select
    s.*,
    dim.display_name,
    dim.display_name_zh,
    dim.persona,
    dim.site,
    (
        s.cpu_util_avg_pct is not null
        or s.gpu_util_avg_pct is not null
    ) as has_resource_metrics
from summary s
inner join {{ ref('dim_device') }} dim on dim.device_id = s.device_id
