# Grains

Published by [`dbt/`](../dbt/). `warehouse/` SQL is legacy reference only.

## `raw_device_usage_hour`

One row = one probe report for one device time window.

- Full hour: `[window_start, window_end)`.
- Clean shutdown may send a partial window (`window_end` not on the hour).
- Append-only; re-sends add another row.

## `stg_device_usage_hour`

One row = one `(device_id, window_start)` after dedupe.

- Keep latest `_loaded_at`, then highest `id`.
- Marts read this view, not raw.

## Reporting timezones

| Suffix | Timezone | Use |
|---|---|---|
| _(none)_ / `_et` | `America/New_York` | US / internal |
| `_cn` | `Asia/Shanghai` | **China demo / stakeholders** |

Twin marts share the same metrics; only calendar day and hour-of-day differ.

## Device-day / fleet / hour / summary

- `mart_device_daily_usage` / `_cn` — device × local day (+ CPU/GPU/mem/disk)
- `mart_fleet_daily` / `_cn` — fleet KPIs per local day
- `mart_hour_of_day` (`hour_et`) / `_cn` (`hour_cn`) — hour-of-day patterns
- `mart_device_summary` / `_cn` — lifetime rollup per device

## `mart_device_staleness`

One row per device (from China summary): `days_since_seen`, `is_stale` (default ≥ 2 China calendar days). Used by Airflow `hope_device_alerts`.
