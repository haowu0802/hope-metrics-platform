"""Run hope_daily_feishu_report locally (needs DATABASE_URL + FEISHU_WEBHOOK_URL)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Allow importing the DAG module without a local Airflow install.
sys.modules.setdefault("airflow", MagicMock())
sys.modules.setdefault("airflow.operators.python", MagicMock())

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "airflow" / "dags"))

# Load .env from repo root if present (do not print secrets).
env_path = ROOT / ".env"
if env_path.is_file():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in __import__("os").environ:
            __import__("os").environ[key] = val

from hope_daily_feishu_report import send_daily_metabase_report  # noqa: E402

if __name__ == "__main__":
    send_daily_metabase_report()
    print("ok sent daily report")
