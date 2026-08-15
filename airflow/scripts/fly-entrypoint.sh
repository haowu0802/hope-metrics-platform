#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required for dbt profiles" >&2
  exit 1
fi
if [[ -z "${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN:-}" ]]; then
  echo "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN is required (Airflow metadata Postgres)" >&2
  exit 1
fi
if [[ -z "${AIRFLOW_ADMIN_PASSWORD:-}" ]]; then
  echo "AIRFLOW_ADMIN_PASSWORD is required (no default on Fly)" >&2
  exit 1
fi

# Write dbt profiles from Hope DATABASE_URL (Fly secret).
python3 - <<'PY'
import json
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

url = os.environ["DATABASE_URL"].strip()
raw = urlparse(url)
if raw.scheme not in ("postgres", "postgresql"):
    raise SystemExit("DATABASE_URL must be postgres/postgresql")

host = raw.hostname or ""
port = raw.port or 5432
user = unquote(raw.username or "")
password = unquote(raw.password or "")
dbname = (raw.path or "/").lstrip("/") or "neondb"
query = raw.query or ""
sslmode = "require"
m = re.search(r"(?:^|&)sslmode=([^&]+)", query)
if m:
    sslmode = m.group(1)

profiles = Path.home() / ".dbt"
profiles.mkdir(parents=True, exist_ok=True)
doc = {
    "hope_metrics": {
        "target": "prod",
        "outputs": {
            "prod": {
                "type": "postgres",
                "host": host,
                "user": user,
                "password": password,
                "port": port,
                "dbname": dbname,
                "schema": "public",
                "threads": 2,
                "sslmode": sslmode,
            }
        },
    }
}
# PyYAML may be absent; emit minimal YAML with json-escaped strings via block scalars.
def ystr(s: str) -> str:
    return json.dumps(s)

text = f"""hope_metrics:
  target: prod
  outputs:
    prod:
      type: postgres
      host: {ystr(host)}
      user: {ystr(user)}
      password: {ystr(password)}
      port: {port}
      dbname: {ystr(dbname)}
      schema: public
      threads: 2
      sslmode: {ystr(sslmode)}
"""
(profiles / "profiles.yml").write_text(text, encoding="utf-8")
print("Wrote", profiles / "profiles.yml")
PY

airflow db migrate

airflow users create \
  --username "${AIRFLOW_ADMIN_USER:-admin}" \
  --password "${AIRFLOW_ADMIN_PASSWORD}" \
  --firstname Hope \
  --lastname Admin \
  --role Admin \
  --email admin@example.com \
  || true

airflow scheduler &
SCHED_PID=$!

cleanup() {
  kill "$SCHED_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Fail the container if scheduler exits early.
(
  while kill -0 "$SCHED_PID" 2>/dev/null; do sleep 5; done
  echo "airflow scheduler exited" >&2
  kill -TERM $$ 2>/dev/null || true
) &

exec airflow webserver --port "${PORT:-8080}"
