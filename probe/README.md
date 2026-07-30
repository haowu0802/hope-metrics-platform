# hope-probe (Windows)

Counts active-use minutes per clock hour, writes local JSON, POSTs to ingest when a URL is set.

`device_id` = Windows `MachineGuid`. Contract: `../docs/device-event-contract.md`

## Build

Edit `configs/probe.build.env`, then:

```powershell
cd probe
.\build.ps1
```

Produces `hope-probe.exe` with that ingest URL baked in. Override at runtime with `--ingest-url` or `HOPE_INGEST_URL`.

## Run

```bat
hope-probe.exe
hope-probe.exe --debug --out-dir .\out --sample-every 10s
hope-probe.exe --ingest-url http://127.0.0.1:8080/v1/events
```

| Flag / env | Meaning |
|---|---|
| `--debug` | Verbose logs |
| `--out-dir` / `HOPE_OUT_DIR` | Pending dir |
| `--ingest-url` / `HOPE_INGEST_URL` | Override baked URL |
| `--idle-seconds` / `HOPE_IDLE_SECONDS` | Default 600 |
| `--tz` / `HOPE_TZ` | Default `Local` |
| `--sample-every` | Default `1m` |

Priority: flag > env > `configs/probe.build.env`.
