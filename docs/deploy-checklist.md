# Deploy

Do not commit secrets. Put `DATABASE_URL` in platform secrets / local `.env` only.

## Pieces

1. Managed Postgres — `ingest/schema.sql` for raw; stg/mart via `dbt build` (GitHub Actions daily)
2. Ingest app — `ingest/` → `hope-metrics`
3. GitHub Actions — `.github/workflows/dbt-daily.yml` (dbt + Feishu alerts/digests)
4. Metabase — `metabase/` → `hope-metrics-metabase` (add Hope Neon in Admin → Databases; re-run `metabase/seed_cn_demo.py` after new marts)
5. Optional custom domain later

Fly Airflow (`hope-metrics-airflow`) is retired. Do not redeploy it.

## First deploy / update

**dbt + Feishu** (production schedule — GitHub Actions):

- Repo **Settings → Secrets → Actions**: `DATABASE_URL` (required), `FEISHU_WEBHOOK_URL` (delivery), `FEISHU_KEYWORD` (optional, default `hope`)
- Workflow: `.github/workflows/dbt-daily.yml` (`0 12 * * *` UTC)
- After model or digest changes: push to default branch; or run workflow manually
- Details: `jobs/feishu/README.md`

Local one-off:

```bash
cd dbt
source .venv/bin/activate
export DATABASE_URL='...'
python scripts/write_profiles_from_env.py
dbt deps && dbt build
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
- Metabase: https://hope-metrics-metabase.fly.dev/
- Actions: https://github.com/haowu0802/hope-metrics-platform/actions

Optional ingest dashboard links (Fly secrets on `hope-metrics`):

```bash
fly secrets set METABASE_URL=https://hope-metrics-metabase.fly.dev/ -a hope-metrics
fly secrets unset AIRFLOW_URL -a hope-metrics
```
