# Airflow — schedule dbt + alerts (Fly by default)

**Default workflow:** change DAGs or `dbt/` → deploy to Fly. Do not rely on local Compose for the product demo.

UI: https://hope-metrics-airflow.fly.dev/

## Layout

| Path | Role |
|---|---|
| `dags/hope_dbt_daily.py` | Daily `dbt build`; optional Feishu on failure |
| `dags/hope_device_alerts.py` | Unused-device Feishu alert |
| `dags/hope_daily_feishu_report.py` | Daily Feishu digest + Metabase public link |
| `dags/hope_weekly_feishu_report.py` | Weekly Feishu digest (prev Mon–Sun CN) |
| `dags/hope_monthly_feishu_report.py` | Monthly Feishu digest (prev CN month) |
| `dags/hope_report_common.py` | Shared digest helpers (URL sanitize, freshness) |
| `dags/hope_feishu.py` | Shared Feishu webhook helper |
| `FEISHU.md` | Webhook + keyword (`hope`) setup |
| `README_DAGS.md` | When to add more DAGs |
| `Dockerfile.fly` / `fly.toml` / `deploy.sh` | **Primary** always-on deploy |
| `docker-compose.yml` | Optional laptop-only; not used for demos |

## Deploy (default)

From **repo root** (image embeds `airflow/dags` + `dbt/`):

```bash
bash airflow/deploy.sh
# Windows-friendly equivalent:
# fly deploy . -c airflow/fly.toml --dockerfile airflow/Dockerfile.fly --ha=false
```

After deploy: confirm both `hope_dbt_daily` and `hope_device_alerts` appear; unpause if needed; Trigger once.

### Secrets (once)

```bash
fly secrets set -a hope-metrics-airflow \
  DATABASE_URL='postgresql://...@.../neondb?sslmode=require' \
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN='postgresql+psycopg2://...@.../airflow?sslmode=require' \
  AIRFLOW__CORE__FERNET_KEY='...' \
  AIRFLOW_ADMIN_USER='admin' \
  AIRFLOW_ADMIN_PASSWORD='...'
# optional: see airflow/FEISHU.md
# FEISHU_WEBHOOK_URL='...'  STALE_DEVICE_DAYS='2'
```

`DATABASE_URL` = Hope metrics DB (same as ingest).  
`AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` = Airflow metadata DB (separate Neon database).

## Notes

- Fly keeps `min_machines_running = 1` so the daily schedule is not lost to auto-stop.
- Image is ~2GB RAM class; adjust `fly.toml` if OOM.
- Alerts use the **demo cohort** (real probes + sim personas; smoke IDs excluded). Core marts still store every `device_id`.

## Local Compose (optional only)

Not part of the default path. If you must run Compose: `cd airflow && docker compose up -d --build` → http://127.0.0.1:8081. Prefer Fly for anything you will show stakeholders.
