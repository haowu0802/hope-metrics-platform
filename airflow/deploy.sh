#!/usr/bin/env bash
# Deploy Airflow (+ embedded dbt) to Fly. Run from repo root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

fly deploy . \
  -c airflow/fly.toml \
  --dockerfile airflow/Dockerfile.fly \
  --ha=false

fly scale count 1 -a hope-metrics-airflow -y || true
echo "UI: https://hope-metrics-airflow.fly.dev/"
