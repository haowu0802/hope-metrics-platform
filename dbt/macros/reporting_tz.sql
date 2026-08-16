{# Device × calendar day in a reporting timezone. #}
{% macro mart_device_daily_usage_sql(tz) %}
with daily as (
    select
        device_id,
        (window_start at time zone '{{ tz }}')::date as usage_date,
        sum(active_minutes)::integer as active_minutes_day,
        count(*) filter (where active_minutes > 0)::integer as active_hour_slots,
        round(avg(cpu_util_avg_pct)::numeric, 1) as cpu_util_avg_pct,
        round(avg(gpu_util_avg_pct)::numeric, 1) as gpu_util_avg_pct,
        round(avg(mem_util_avg_pct)::numeric, 1) as mem_util_avg_pct,
        round(min(disk_free_gb)::numeric, 1) as disk_free_gb_min
    from {{ ref('stg_device_usage_hour') }}
    group by
        device_id,
        (window_start at time zone '{{ tz }}')::date
)

select
    device_id,
    usage_date,
    active_minutes_day,
    active_hour_slots,
    round((100.0 * active_minutes_day / 1440.0)::numeric, 1) as utilization_pct,
    cpu_util_avg_pct,
    gpu_util_avg_pct,
    mem_util_avg_pct,
    disk_free_gb_min
from daily
{% endmacro %}


{# Hour-of-day pattern in a reporting timezone. #}
{% macro mart_hour_of_day_sql(tz, hour_col) %}
select
    extract(hour from (window_start at time zone '{{ tz }}'))::integer as {{ hour_col }},
    sum(active_minutes)::integer as active_minutes_sum,
    count(distinct device_id)::integer as device_count,
    round(avg(active_minutes)::numeric, 1) as active_minutes_avg,
    round(avg(cpu_util_avg_pct)::numeric, 1) as cpu_util_avg_pct,
    round(avg(gpu_util_avg_pct)::numeric, 1) as gpu_util_avg_pct,
    round(avg(mem_util_avg_pct)::numeric, 1) as mem_util_avg_pct
from {{ ref('stg_device_usage_hour') }}
group by
    extract(hour from (window_start at time zone '{{ tz }}'))
{% endmacro %}


{# Fleet rollup from a device-day mart. #}
{% macro mart_fleet_daily_sql(device_daily_ref) %}
select
    usage_date,
    count(distinct device_id)::integer as active_devices,
    sum(active_minutes_day)::integer as active_minutes_total,
    round(avg(active_minutes_day)::numeric, 1) as active_minutes_avg_device,
    count(*) filter (where active_minutes_day >= 60)::integer as devices_ge_1h,
    round(avg(utilization_pct)::numeric, 1) as utilization_pct_avg,
    round(avg(cpu_util_avg_pct)::numeric, 1) as cpu_util_avg_pct,
    round(avg(gpu_util_avg_pct)::numeric, 1) as gpu_util_avg_pct,
    round(avg(mem_util_avg_pct)::numeric, 1) as mem_util_avg_pct,
    round(avg(disk_free_gb_min)::numeric, 1) as disk_free_gb_avg
from {{ ref(device_daily_ref) }}
group by usage_date
{% endmacro %}


{# Lifetime rollup from a device-day mart. #}
{% macro mart_device_summary_sql(device_daily_ref) %}
select
    device_id,
    min(usage_date) as first_seen_date,
    max(usage_date) as last_seen_date,
    count(*)::integer as active_days,
    sum(active_minutes_day)::integer as active_minutes_total,
    round(avg(active_minutes_day)::numeric, 1) as active_minutes_avg_day,
    round(avg(utilization_pct)::numeric, 1) as utilization_pct_avg,
    round(avg(cpu_util_avg_pct)::numeric, 1) as cpu_util_avg_pct,
    round(avg(gpu_util_avg_pct)::numeric, 1) as gpu_util_avg_pct,
    round(avg(mem_util_avg_pct)::numeric, 1) as mem_util_avg_pct,
    round(min(disk_free_gb_min)::numeric, 1) as disk_free_gb_min
from {{ ref(device_daily_ref) }}
group by device_id
{% endmacro %}
