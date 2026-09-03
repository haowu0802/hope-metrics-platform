# Hope Metrics Platform

Measures donated-device active use for a GenAI education pilot.

## Repo layout

- `probe/` — Windows agent (active minutes per hour)
- `ingest/` — HTTP ingest + status page (links to Metabase)
- `warehouse/` — legacy SQL (reference only)
- `dbt/` — stg/mart transforms and tests
- `jobs/feishu/` — Feishu alerts/digests on GitHub Actions (with daily `dbt build`)
- `metabase/` — BI on marts (local Compose or Fly `hope-metrics-metabase`)

See `docs/device-event-contract.md`, `docs/grains.md`, `docs/deploy-checklist.md`.

## Run ingest + status page locally

Needs `DATABASE_URL` in a repo-root `.env`, and schema/views applied (see `ingest/README.md`).

```bash
cd ingest
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8080
```

Open http://127.0.0.1:8080/

Public demo: https://hope-metrics.fly.dev/
