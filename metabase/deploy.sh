#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/metabase"

fly volumes list -a hope-metrics-metabase 2>/dev/null | grep -q metabase_data \
  || fly volumes create metabase_data --size 1 --region sin -a hope-metrics-metabase -y

fly deploy . -c fly.toml --ha=false
fly scale count 1 -a hope-metrics-metabase -y || true
echo "UI: https://hope-metrics-metabase.fly.dev/"
