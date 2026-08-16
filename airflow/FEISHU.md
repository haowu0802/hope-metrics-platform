# Feishu / Lark alerts + Metabase digests

Airflow posts to a **group custom bot** webhook:

| DAG | What |
|---|---|
| `hope_device_alerts` | Unused-device alert (`mart_device_staleness_demo`) |
| `hope_daily_feishu_report` | Daily digest (昨日 KPIs / Top3 / CPU / 闲置 / 新鲜度) |
| `hope_weekly_feishu_report` | Weekly digest (上周 Mon–Sun 合计 / Top5 / 忙闲日) |
| `hope_monthly_feishu_report` | Monthly digest (上月合计 / Top5 / 站点·角色 / 资源) |
| `hope_dbt_daily` / alert failures | Failure pings |

All digests append **public** + login Metabase links. Public URL has **no** `device` query param.

## Keyword

If the bot requires a keyword (this project: **`hope`**), every message must include it.
`hope_feishu.send_feishu_text` appends `#hope` automatically when missing.

Env override: `FEISHU_KEYWORD=hope`

## One-time setup

```bash
fly secrets set \
  FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN' \
  FEISHU_KEYWORD='hope' \
  -a hope-metrics-airflow
```

Optional:

```bash
fly secrets set STALE_DEVICE_DAYS=2 \
  METABASE_DEMO_URL='https://hope-metrics-metabase.fly.dev/dashboard/3' \
  METABASE_PUBLIC_URL='https://hope-metrics-metabase.fly.dev/public/dashboard/df568889-d528-46f4-a9c7-115e4c36b93c' \
  -a hope-metrics-airflow
```

Then **deploy** and Trigger the digest DAGs you want to smoke-test.

## Local test

```powershell
# webhook smoke
$env:FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/...'
$env:FEISHU_KEYWORD='hope'
python airflow/scripts/test_feishu_webhook.py

# digests (needs DATABASE_URL in env or repo .env)
python airflow/scripts/test_feishu_report.py daily
python airflow/scripts/test_feishu_report.py weekly
python airflow/scripts/test_feishu_report.py monthly
```

Shared helpers live in `dags/hope_report_common.py` (URL sanitization strips any `?device=` from `METABASE_PUBLIC_URL`).

## Schedule (UTC)

| DAG | Cron |
|---|---|
| `hope_dbt_daily` | `0 12 * * *` |
| `hope_device_alerts` | `30 12 * * *` |
| `hope_daily_feishu_report` | `45 12 * * *` |
| `hope_weekly_feishu_report` | `0 13 * * 1` (Monday) |
| `hope_monthly_feishu_report` | `15 13 1 * *` (1st) |

Do **not** commit webhook URLs. Fly secrets / local `.env` only.
