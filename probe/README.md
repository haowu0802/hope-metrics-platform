# hope-probe (Windows)

Go agent for donated PCs. Counts active-use minutes per clock hour, writes local JSON, and POSTs to ingest when a URL is set.

`device_id` is always Windows `MachineGuid`.

Details: `../docs/device-event-contract.md`

## Build

```bat
cd probe
go mod tidy
go build -o hope-probe.exe ./cmd/hope-probe
```

## Run

```bat
hope-probe.exe --out-dir C:\hope-probe\out --ingest-url http://127.0.0.1:8080/v1/events
hope-probe.exe --debug --out-dir .\out --sample-every 10s
```

| Flag / env | Meaning |
|---|---|
| `--debug` | Verbose console logs |
| `--out-dir` / `HOPE_OUT_DIR` | Pending dir (default `out`) |
| `--ingest-url` / `HOPE_INGEST_URL` | POST URL; empty = local only |
| `--idle-seconds` / `HOPE_IDLE_SECONDS` | Default 600 (10 minutes) |
| `--tz` / `HOPE_TZ` | Default `Local` |
| `--sample-every` | Default `1m` |

## Behavior

1. Read `MachineGuid`.
2. Sample last-input about once a minute.
3. On the hour, write `out/pending/*.json`.
4. Upload pending files when URL is set; delete after HTTP 2xx.
