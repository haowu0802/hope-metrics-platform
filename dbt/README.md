# Hope Metrics dbt project

Transforms live here (`raw` stays owned by ingest).

## Layout

| Path | Role |
|---|---|
| `dbt_project.yml` | Project name, profile name, paths, default materializations |
| `packages.yml` | Optional community packages (empty for now) |
| `models/staging/` | Clean/dedupe models (later) |
| `models/marts/` | Business grains (later) |
| `requirements.txt` | `dbt-postgres` for local installs |

Connection (`profiles`) is a separate step — see `profiles.example.yml` when you get there.

## Install

```bash
cd dbt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Do not run `dbt run` until models exist. Use `dbt debug` only after local profiles are configured.
