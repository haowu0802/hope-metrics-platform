"""Write ~/.dbt/profiles.yml from DATABASE_URL (CI / local)."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 1

    raw = urlparse(url)
    if raw.scheme not in ("postgres", "postgresql"):
        print("DATABASE_URL must be postgres/postgresql", file=sys.stderr)
        return 1

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

    profiles_dir = Path(os.environ.get("DBT_PROFILES_DIR", Path.home() / ".dbt"))
    profiles_dir.mkdir(parents=True, exist_ok=True)

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
    out = profiles_dir / "profiles.yml"
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
