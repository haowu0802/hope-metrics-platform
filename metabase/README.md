# Metabase — read-only BI on marts

Metabase does **not** replace dbt. Stakeholder demo uses **`*_cn_demo`** marts (Asia/Shanghai): **real probe devices kept**; smoke/`demo-site` hidden via `device_registry`. Core `*_cn` marts still hold every `device_id`.

## China demo (primary)

Use the **login** dashboard for demos.

| | URL |
|---|---|
| **Login (preferred)** | https://hope-metrics-metabase.fly.dev/dashboard/3 |
| Public preview (no login) | https://hope-metrics-metabase.fly.dev/public/dashboard/df568889-d528-46f4-a9c7-115e4c36b93c |
| Collection | `Hope 演示(北京时间)` |

Admin creds: gitignored `metabase/.fly-admin.txt`.

### Near-real-time (hour)

Top of dashboard **今日实时**: `mart_device_hour_cn_demo` (dbt **view** over staging). Updates as ingest lands — no wait for the daily mart rebuild. Cards show last 24 hours (fleet + selected device).

Daily charts below remain the trusted trend / Feishu layer.

1. Section **单设备**
2. Filter **设备** is a dropdown of **中文名** (e.g. `AI实验室01`, `探针机甲`) — Metabase filters on `display_name_zh`
3. Default `AI实验室01`
4. Bottom table lists devices with activity only (null CPU/GPU)

Labels live in `dbt/seeds/device_registry.csv` → `dim_device.display_name_zh`.
`seed_cn_demo.py` also sets **Chinese `display_name`** on all demo-mart columns (axes / table headers on the public dashboard).

**Why not remap id→label in the widget?** On Metabase 0.50, dashboard `string/=` filters still display the raw value even when you pass `[device_id, 中文名]` pairs. Filtering by the Chinese column itself is the reliable way to show labels.

### After dbt / label changes

```bash
python metabase/seed_cn_demo.py
```

### What the public link is for

Share-only preview without an account. Prefer the login URL when presenting. Do **not** put `?device=` on the public handout link (pick the device inside the dashboard). Login deep-link example: `?device=AI实验室01`.

## Older US-Eastern dashboard

https://hope-metrics-metabase.fly.dev/dashboard/2 — comparison only; prefer China demo above.

## Local / Fly deploy

```bash
cd metabase && docker compose up -d
# or
bash metabase/deploy.sh
```

App: https://hope-metrics-metabase.fly.dev/
