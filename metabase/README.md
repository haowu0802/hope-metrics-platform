# Metabase — read-only BI on marts

Metabase is the analysis UI. It does **not** replace dbt. Connect it to Hope Postgres and query `mart_device_daily_usage` (and related views).

## Local

```bash
cd metabase
docker compose up -d
```

Open http://127.0.0.1:3000 — complete setup wizard — Add database → Postgres using the same host/db as ingest (`DATABASE_URL` fields). Point questions at `mart_device_daily_usage`.

## Fly

```bash
fly apps create hope-metrics-metabase   # once
bash metabase/deploy.sh
```

UI: https://hope-metrics-metabase.fly.dev/

App state uses a Fly volume (H2 file). After first login, add the Hope Neon database in **Admin → Databases** (same credentials as ingest; read-only role preferred later).

## Suggested first questions

- Daily active minutes by day (sum of `active_minutes_day`)
- Active minutes by `device_id` (table or bar)
