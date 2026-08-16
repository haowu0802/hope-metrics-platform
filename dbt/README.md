# Hope Metrics dbt project

Transforms (`stg` / `mart`). Ingest owns `raw_*`.

## Layout

| Path | Role |
|---|---|
| `dbt_project.yml` | Project and default materializations |
| `profiles.example.yml` | Copy to `~/.dbt/profiles.yml` |
| `packages.yml` | `dbt_utils` |
| `models/staging/` | Sources + dedupe |
| `models/marts/` | Daily usage grain |
| `requirements.txt` | `dbt-postgres` |

## Setup

```bash
cd dbt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p ~/.dbt
cp profiles.example.yml ~/.dbt/profiles.yml   # edit YOUR_*
dbt debug
dbt deps
dbt build
```

Models: `stg_device_usage_hour`; ET marts + `_cn` twins (`Asia/Shanghai`); `dim_device` + `*_cn_demo` stakeholder views (smoke hidden; **real probes kept**); `mart_device_staleness` (all) / `_demo` (alerts).

Seed: `seeds/device_registry.csv` — labels only; never deletes warehouse rows.

Tests cover unique grains, `not_null`, and non-negative minutes.

After model changes used by Airflow, **deploy Fly Airflow** so the image picks up `dbt/` (`bash airflow/deploy.sh`).
