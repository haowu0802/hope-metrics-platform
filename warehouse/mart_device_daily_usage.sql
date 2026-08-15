-- Legacy reference only. Publish via dbt/models/marts/mart_device_daily_usage.sql

CREATE OR REPLACE VIEW mart_device_daily_usage AS
SELECT
    device_id,
    (window_start AT TIME ZONE 'America/New_York')::date AS usage_date,
    SUM(active_minutes)::integer AS active_minutes_day
FROM stg_device_usage_hour
GROUP BY
    device_id,
    (window_start AT TIME ZONE 'America/New_York')::date;
