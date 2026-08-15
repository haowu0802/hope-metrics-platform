-- Legacy reference only. Publish via dbt/models/staging/stg_device_usage_hour.sql

CREATE OR REPLACE VIEW stg_device_usage_hour AS
SELECT DISTINCT ON (device_id, window_start)
    id,
    schema_version,
    probe_version,
    device_id,
    window_start,
    window_end,
    active_minutes,
    payload,
    _loaded_at
FROM raw_device_usage_hour
ORDER BY
    device_id,
    window_start,
    _loaded_at DESC,
    id DESC;
