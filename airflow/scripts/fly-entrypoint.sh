#!/usr/bin/env bash
set -euo pipefail

# Write dbt profiles from Hope DATABASE_URL (Fly secret).
python3 - <<'PY'
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

url = os.environ.get("DATABASE_URL", "").strip()
if not url:
    raise SystemExit("DATABASE_URL is required for dbt profiles")

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
(profiles / "profiles.yml").write_text(
    f"""hope_metrics:
  target: prod
  outputs:
    prod:
      type: postgres
      host: "{host}"
      user: "{user}"
      password: "{password}"
      port: {port}
      dbname: "{dbname}"
      schema: public
      threads: 2
      sslmode: "{sslmode}"
""",
    encoding="utf-8",
)
print("Wrote", profiles / "profiles.yml")
PY

airflow db migrate

airflow users create \
  --username "${AIRFLOW_ADMIN_USER:-admin}" \
  --password "${AIRFLOW_ADMIN_PASSWORD:-admin}" \
  --firstname Hope \
  --lastname Admin \
  --role Admin \
  --email admin@example.com \
  || true

# LocalExecutor: tasks run in scheduler process.
airflow scheduler &
exec airflow webserver --port "${PORT:-8080}"
