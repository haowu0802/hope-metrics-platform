# Feishu jobs (GitHub Actions)

Idle-device alerts and daily / weekly / monthly digests. Replaces Fly Airflow.

## Schedule

One workflow: `.github/workflows/dbt-daily.yml`

1. `dbt build` at `0 12 * * *` UTC
2. On success: stale-device alert + daily digest
3. Monday UTC: also weekly digest (prev Mon–Sun, Beijing calendar)
4. 1st of month UTC: also monthly digest (prev Beijing calendar month)

Manual: **Actions → dbt daily → Run workflow** (optional weekly/monthly checkboxes).

## Secrets

Repo → **Settings → Secrets and variables → Actions**:

| Secret | Required |
|---|---|
| `DATABASE_URL` | Yes (Hope Neon, same as ingest) |
| `FEISHU_WEBHOOK_URL` | Yes for delivery (omit = log only) |
| `FEISHU_KEYWORD` | No (default `hope`) |

Optional env (workflow `env:` or secrets): `STALE_DEVICE_DAYS` (default `2`), `METABASE_DEMO_URL`, `METABASE_PUBLIC_URL`.

## Local

```powershell
$env:DATABASE_URL='postgresql://...'
$env:FEISHU_WEBHOOK_URL='https://open.feishu.cn/open-apis/bot/v2/hook/...'
$env:FEISHU_KEYWORD='hope'
pip install -r jobs/feishu/requirements.txt
python -m jobs.feishu ping
python -m jobs.feishu alerts
python -m jobs.feishu daily
python -m jobs.feishu weekly
python -m jobs.feishu monthly
```

Repo-root `.env` is loaded if present. Do not commit webhook URLs.

Keyword **`hope`** must appear in every bot message; `jobs.feishu.webhook` appends `#hope` when missing.
