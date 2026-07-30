# Deploy

Do not commit secrets. Put `DATABASE_URL` in platform secrets / local `.env` only.

## Pieces

1. Managed Postgres - same `ingest/schema.sql` + `warehouse/*.sql` as local
2. App from `ingest/` (`Dockerfile`, `fly.toml`) - `POST /v1/events`, `GET /`, `GET /health`
3. Optional custom domain later

## First deploy

```text
# in ingest/
# set DATABASE_URL as a secret on the host
# fly deploy   (or your host's equivalent)
```

Check:

- `GET /health` -> `{"status":"ok"}`
- `GET /` shows mart rows
- `POST /v1/events` then refresh `/`

## URLs

- Local: http://127.0.0.1:8080/
- Current public: https://hope-metrics.fly.dev/
