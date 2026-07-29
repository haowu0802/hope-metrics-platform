# warehouse

Apply in order:

```bat
psql %DATABASE_URL% -f warehouse/stg_device_usage_hour.sql
psql %DATABASE_URL% -f warehouse/mart_device_daily_usage.sql
```

| View | Role |
|---|---|
| `stg_device_usage_hour` | Dedupe by `(device_id, window_start)` |
| `mart_device_daily_usage` | Daily sum (US Eastern) |

```sql
SELECT * FROM mart_device_daily_usage ORDER BY usage_date, device_id;
```
