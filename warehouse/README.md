# warehouse (legacy)

Publish path is [`dbt/`](../dbt/) (`dbt build`). SQL here is reference only.

| Object | Grain |
|---|---|
| `stg_device_usage_hour` | One row per `(device_id, window_start)` |
| `mart_device_daily_usage` | Device × US/Eastern day |
