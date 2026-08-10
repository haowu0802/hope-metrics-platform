# Deploy

Do not commit secrets. Put `DATABASE_URL` in platform secrets / local `.env` only.

## Pieces

1. Managed Postgres - same `ingest/schema.sql` + `warehouse/*.sql` as local
2. App from `ingest/` (`Dockerfile`, `fly.toml`) - `POST /v1/events`, `GET /`, `GET /health`
3. Optional custom domain later

## First deploy / update

From `ingest/`:

```bash
fly deploy --ha=false
fly scale count 1 -y
```

(`--ha=false` avoids a second standby machine; not configurable in fly.toml.)

There is also `deploy.ps1` for Windows hosts; the commands above are the source of truth.

Set `DATABASE_URL` as a platform secret before the first deploy.

Check:

- `GET /health` -> `{"status":"ok"}`
- `GET /` shows mart rows
- `POST /v1/events` then refresh `/`

## URLs

- Local: http://127.0.0.1:8080/
- Current public: https://hope-metrics.fly.dev/
