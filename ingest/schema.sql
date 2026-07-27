-- Hourly probe events. Append only.

CREATE TABLE IF NOT EXISTS raw_device_usage_hour (
    id              bigserial PRIMARY KEY,
    schema_version  text        NOT NULL,
    probe_version   text        NOT NULL,
    device_id       text        NOT NULL,
    window_start    timestamptz NOT NULL,
    window_end      timestamptz NOT NULL,
    active_minutes  integer     NOT NULL,
    payload         jsonb       NOT NULL,
    _loaded_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT raw_device_usage_hour_active_minutes_nonneg
        CHECK (active_minutes >= 0)
);

CREATE INDEX IF NOT EXISTS idx_raw_device_usage_hour_device_window
    ON raw_device_usage_hour (device_id, window_start);
