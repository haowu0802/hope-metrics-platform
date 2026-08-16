# Deploy

Do not commit secrets. Put `DATABASE_URL` in platform secrets / local `.env` only.

## Pieces

1. Managed Postgres — `ingest/schema.sql` for raw; stg/mart via `dbt build` (scheduled on Fly Airflow)
2. Ingest app — `ingest/` → `hope-metrics`
3. Airflow (+ dbt in image) — `airflow/` → `hope-metrics-airflow` (**deploy on every DAG/dbt change**)
4. Metabase — `metabase/` → `hope-metrics-metabase` (add Hope Neon in Admin → Databases; re-run `metabase/seed_cn_demo.py` after new marts)
5. Optional custom domain later

## First deploy / update

**Transforms** (from a machine with `~/.dbt/profiles.yml` pointing at the same DB):

```bash
cd dbt
source .venv/bin/activate
dbt deps
dbt build
```

**Airflow** (default — embeds latest `dbt/` + DAGs; do not use local Compose for demos):

```bash
bash airflow/deploy.sh
```

**App** from `ingest/`:

```bash
fly deploy --ha=false
fly scale count 1 -y
```

(`--ha=false` avoids a second standby machine.) Windows hosts may use `deploy.ps1`; commands above are the source of truth.

Set `DATABASE_URL` as a platform secret before the first app deploy.

Check:

- `GET /health` -> `{"status":"ok"}`
- `GET /` shows mart rows
- `POST /v1/events` then refresh `/`

## URLs

- Local: http://127.0.0.1:8080/
- Current public: https://hope-metrics.fly.dev/
- Airflow: https://hope-metrics-airflow.fly.dev/
- Metabase: https://hope-metrics-metabase.fly.dev/

Optional ingest dashboard links (Fly secrets on `hope-metrics`):

```bash
fly secrets set AIRFLOW_URL=https://hope-metrics-airflow.fly.dev/ \
  METABASE_URL=https://hope-metrics-metabase.fly.dev/ \
  -a hope-metrics
```
