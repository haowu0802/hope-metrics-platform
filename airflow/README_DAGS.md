# Airflow DAGs in this repo

## `hope_dbt_daily`

Runs `dbt build` once per day. Keep this as the **only** transform DAG unless builds become heavy enough to split (e.g. staging vs marts) or you need different cadences.

## `hope_device_alerts`

Unused-device Feishu alert (`mart_device_staleness_demo`). Smoke excluded; real probes kept. Keyword **`hope`** required on the bot.

| Env | Meaning |
|---|---|
| `DATABASE_URL` | Hope Neon (already required for dbt) |
| `FEISHU_WEBHOOK_URL` | Group bot webhook (Fly secret) |
| `FEISHU_KEYWORD` | Default `hope` |
| `STALE_DEVICE_DAYS` | Default `2` China calendar days without activity |

Schedule: `30 12 * * *` UTC (after `hope_dbt_daily` at 12:00).

## Digests → Feishu

| DAG | Window | Schedule (UTC) |
|---|---|---|
| `hope_daily_feishu_report` | Yesterday (CN) | `45 12 * * *` |
| `hope_weekly_feishu_report` | Prev Mon–Sun (CN) | `0 13 * * 1` |
| `hope_monthly_feishu_report` | Prev calendar month (CN) | `15 13 1 * *` |

Public Metabase link has **no** device filter. Details: `FEISHU.md`.

Deploy DAGs by **Fly** (`bash airflow/deploy.sh` / `fly deploy` from repo root); do not use local Compose for demos.

## When to add more DAGs

Add another DAG when the **trigger or owner differs**, not when you want “more Airflow on the resume”:

1. **Alerts / SLAs** — different schedule, must not block dbt.
2. **Digests** (daily / weekly / monthly) — stakeholder push, separate from pager alerts.
3. **Ingest / probe health** — e.g. “no raw rows in 6h” (ops), independent of mart rebuild.
4. **Backfills / one-shots** — manual DAG with `schedule=None`.
5. **Heavy ML / batch** — only if runtime or deps would starve `dbt build`.

Do **not** split one `dbt build` into many DAGs just for show; interview story is clearer as: *schedule transforms* + *alert on unused devices* + *Feishu digests*.
