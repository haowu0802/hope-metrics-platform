# ingest

`POST /v1/events` appends to `raw_device_usage_hour`.  
`GET /` shows `mart_device_daily_usage` with filters, daily trend, and device rank (UI: English default; `?lang=zh` for Chinese). Health: `GET /health`.

Dashboard query params (shareable):

```text
/?lang=zh&date_from=2026-07-28&date_to=2026-07-30&device_id=demo-site-a&device_id=demo-site-b
```

JSON: `GET /api/v1/daily-usage` accepts the same `date_from` / `date_to` / `device_id` filters and returns `summary`, `trend`, `rank`, `rows`.

## Setup

Repo-root `.env`:

```text
DATABASE_URL=postgresql://USER:PASSWORD@127.0.0.1:5432/hope_metrics
```

Schema + transforms (configure dbt first: see `dbt/README.md`):

```bash
# from repo root
psql "$DATABASE_URL" -f ingest/schema.sql
cd dbt
source .venv/bin/activate
dbt deps && dbt build
cd ..
```

Run:

```bash
cd ingest
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8080
```

## Smoke

```bash
curl -s -X POST http://127.0.0.1:8080/v1/events \
  -H "Content-Type: application/json" \
  -d '{"schema_version":"1","probe_version":"0.1.0","device_id":"test-device","window_start":"2026-07-27T14:00:00-04:00","window_end":"2026-07-27T15:00:00-04:00","active_minutes":12}'
```

JSON dump: `GET /api/v1/daily-usage`

Deploy notes: `docs/deploy-checklist.md`
