-- Add v2 resource columns to existing Neon / Postgres (safe to re-run).

ALTER TABLE raw_device_usage_hour ADD COLUMN IF NOT EXISTS cpu_util_avg_pct real;
ALTER TABLE raw_device_usage_hour ADD COLUMN IF NOT EXISTS gpu_util_avg_pct real;
ALTER TABLE raw_device_usage_hour ADD COLUMN IF NOT EXISTS mem_util_avg_pct real;
ALTER TABLE raw_device_usage_hour ADD COLUMN IF NOT EXISTS disk_free_gb real;
