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

Models: `stg_device_usage_hour` (dedupe by device + hour), `mart_device_daily_usage` (device × US/Eastern day).
Tests cover unique grains, `not_null`, and non-negative minutes.
