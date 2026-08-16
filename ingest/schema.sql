-- Hourly probe events. Append only.

CREATE TABLE IF NOT EXISTS raw_device_usage_hour (
    id              bigserial PRIMARY KEY,
    schema_version  text        NOT NULL,
    probe_version   text        NOT NULL,
    device_id       text        NOT NULL,
    window_start    timestamptz NOT NULL,
    window_end      timestamptz NOT NULL,
    active_minutes  integer     NOT NULL,
    cpu_util_avg_pct real,
    gpu_util_avg_pct real,
    mem_util_avg_pct real,
    disk_free_gb     real,
    payload         jsonb       NOT NULL,
    _loaded_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT raw_device_usage_hour_active_minutes_nonneg
        CHECK (active_minutes >= 0),
    CONSTRAINT raw_device_usage_hour_cpu_pct_range
        CHECK (cpu_util_avg_pct IS NULL OR (cpu_util_avg_pct >= 0 AND cpu_util_avg_pct <= 100)),
    CONSTRAINT raw_device_usage_hour_gpu_pct_range
        CHECK (gpu_util_avg_pct IS NULL OR (gpu_util_avg_pct >= 0 AND gpu_util_avg_pct <= 100)),
    CONSTRAINT raw_device_usage_hour_mem_pct_range
        CHECK (mem_util_avg_pct IS NULL OR (mem_util_avg_pct >= 0 AND mem_util_avg_pct <= 100)),
    CONSTRAINT raw_device_usage_hour_disk_nonneg
        CHECK (disk_free_gb IS NULL OR disk_free_gb >= 0)
);

CREATE INDEX IF NOT EXISTS idx_raw_device_usage_hour_device_window
    ON raw_device_usage_hour (device_id, window_start);

-- Idempotent upgrade from v1 table shape.
ALTER TABLE raw_device_usage_hour ADD COLUMN IF NOT EXISTS cpu_util_avg_pct real;
ALTER TABLE raw_device_usage_hour ADD COLUMN IF NOT EXISTS gpu_util_avg_pct real;
ALTER TABLE raw_device_usage_hour ADD COLUMN IF NOT EXISTS mem_util_avg_pct real;
ALTER TABLE raw_device_usage_hour ADD COLUMN IF NOT EXISTS disk_free_gb real;
