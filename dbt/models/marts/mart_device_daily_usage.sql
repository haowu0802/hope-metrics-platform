-- Device × US/Eastern day.

select
    device_id,
    (window_start at time zone 'America/New_York')::date as usage_date,
    sum(active_minutes)::integer as active_minutes_day
from {{ ref('stg_device_usage_hour') }}
group by
    device_id,
    (window_start at time zone 'America/New_York')::date
