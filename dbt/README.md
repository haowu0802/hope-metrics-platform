# Hope Metrics dbt project

Transforms live here (`raw` stays owned by ingest).

## Layout

| Path | Role |
|---|---|
| `dbt_project.yml` | Project name, profile name, paths, default materializations |
| `profiles.example.yml` | Template for `~/.dbt/profiles.yml` (no secrets in git) |
| `packages.yml` | Optional community packages (empty for now) |
| `models/staging/` | Sources + clean/dedupe models |
| `models/marts/` | Business grains (later) |
| `requirements.txt` | `dbt-postgres` for local installs |

Declared source (step 3): `source('hope', 'raw_device_usage_hour')` → table `public.raw_device_usage_hour`.


## Install

```bash
cd dbt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Connect + verify

1. Copy the example profile and fill in the **same Postgres** ingest uses:

```bash
mkdir -p ~/.dbt
cp profiles.example.yml ~/.dbt/profiles.yml
# edit ~/.dbt/profiles.yml — replace YOUR_*
```

2. From `dbt/` with the venv active:

```bash
dbt debug
```

Success: `Connection test: OK` / `All checks passed!`

Do not set `DBT_PROFILES_DIR` to this repo folder — use the default `~/.dbt`.  
Do not run `dbt run` until staging/mart models exist (next steps).
