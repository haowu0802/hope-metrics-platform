"""Run weekly/monthly Feishu reports locally (DATABASE_URL + FEISHU_WEBHOOK_URL)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.modules.setdefault("airflow", MagicMock())
sys.modules.setdefault("airflow.operators.python", MagicMock())

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "airflow" / "dags"))

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

parser = argparse.ArgumentParser()
parser.add_argument("cadence", choices=["daily", "weekly", "monthly"])
args = parser.parse_args()

if args.cadence == "daily":
    from hope_daily_feishu_report import send_daily_metabase_report as fn
elif args.cadence == "weekly":
    from hope_weekly_feishu_report import send_weekly_feishu_report as fn
else:
    from hope_monthly_feishu_report import send_monthly_feishu_report as fn

fn()
print(f"ok sent {args.cadence} report")
