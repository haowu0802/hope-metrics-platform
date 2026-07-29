# Grains

## `raw_device_usage_hour`

One row = one probe report for one device time window.

- Full hour: `[window_start, window_end)`.
- Clean shutdown may send a partial window (`window_end` not on the hour).
- Append-only; re-sends add another row.

## `stg_device_usage_hour`

One row = one `(device_id, window_start)` after dedupe.

- Keep latest `_loaded_at`, then highest `id`.
- Marts read this view, not raw.

## `mart_device_daily_usage`

One row = one device on one US Eastern day (`America/New_York`).

- `active_minutes_day` = sum of staging `active_minutes` for that date.
- If the kept staging row is partial, those minutes still count.
