# Airflow — schedule dbt build

Runs `dbt build` daily. Local Compose for laptop demos; Fly for always-on scheduling against Neon.

## Layout

| Path | Role |
|---|---|
| `dags/hope_dbt_daily.py` | Daily `dbt build`; optional Feishu on failure |
| `docker-compose.yml` | Local webserver + scheduler + metadata Postgres |
| `Dockerfile` | Local image + `dbt-postgres` |
| `Dockerfile.fly` | Fly image: Airflow + dbt project + `dbt deps` |
| `fly.toml` / `deploy.sh` | App `hope-metrics-airflow` |
| `scripts/fly-entrypoint.sh` | Write dbt profiles from `DATABASE_URL`, migrate, run scheduler+web |

## Local Compose

Prerequisites: Docker; host `dbt deps` once; `%USERPROFILE%\.dbt\profiles.yml` or `~/.dbt/profiles.yml`.

```bash
cd airflow
cp .env.example .env
# set AIRFLOW__CORE__FERNET_KEY
docker compose up -d --build
```

UI: http://127.0.0.1:8081 — `admin` / `admin`.

## Fly (always-on)

dbt is **not** a separate app. It ships inside the Airflow image and runs when the DAG fires.

1. On Neon, create a second database for Airflow metadata (e.g. `airflow`).
2. Create app and secrets (once):

```bash
fly apps create hope-metrics-airflow -o personal   # if needed
fly secrets set -a hope-metrics-airflow \
  DATABASE_URL='postgresql://...@.../neondb?sslmode=require' \
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN='postgresql+psycopg2://...@.../airflow?sslmode=require' \
  AIRFLOW__CORE__FERNET_KEY='...' \
  AIRFLOW_ADMIN_USER='admin' \
  AIRFLOW_ADMIN_PASSWORD='...'
# optional: FEISHU_WEBHOOK_URL='...'
```

`DATABASE_URL` = Hope metrics DB (same as ingest).  
`AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` = Airflow metadata DB (not the metrics DB).

3. Deploy from **repo root** (build context must include `dbt/`):

```bash
bash airflow/deploy.sh
# or: fly deploy . -c airflow/fly.toml --ha=false
```

UI: https://hope-metrics-airflow.fly.dev/

Unpause `hope_dbt_daily`, then Trigger once to verify.

## Notes

- Fly keeps `min_machines_running = 1` so the daily schedule is not lost to auto-stop.
- Image is ~2GB RAM class; adjust `fly.toml` if OOM.
- Local Compose metadata Postgres is separate from Neon.
