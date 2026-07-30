# ingest

`POST /v1/events` appends to `raw_device_usage_hour`.  
`GET /` shows `mart_device_daily_usage`. Health: `GET /health`.

## Setup

Repo-root `.env`:

```text
DATABASE_URL=postgresql://USER:PASSWORD@127.0.0.1:5432/hope_metrics
```

Apply SQL:

```bat
psql %DATABASE_URL% -f ingest/schema.sql
psql %DATABASE_URL% -f warehouse/stg_device_usage_hour.sql
psql %DATABASE_URL% -f warehouse/mart_device_daily_usage.sql
```

Run:

```bat
cd ingest
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8080
```

## Smoke

```bat
curl -s -X POST http://127.0.0.1:8080/v1/events -H "Content-Type: application/json" -d "{\"schema_version\":\"1\",\"probe_version\":\"0.1.0\",\"device_id\":\"test-device\",\"window_start\":\"2026-07-27T14:00:00-04:00\",\"window_end\":\"2026-07-27T15:00:00-04:00\",\"active_minutes\":12}"
```

JSON dump: `GET /api/v1/daily-usage`

Deploy notes: `docs/deploy-checklist.md`
