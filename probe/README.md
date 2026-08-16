# hope-probe (Windows)

Counts active-use minutes per clock hour, samples CPU/mem/disk/GPU when available, writes local JSON, POSTs to ingest when a URL is set.

GPU (`gpu_util_avg_pct`) on Windows, in order:

1. **NVML** (`nvml.dll` from the NVIDIA driver)
2. **PDH** `\GPU Engine(*)\Utilization Percentage` (WDDM; NVIDIA/AMD/Intel)
3. **`nvidia-smi`** CLI fallback

If none work (no GPU / no counters), the field stays JSON `null` — not `0`.

This component **runs and builds on Windows only** (OS APIs). Platform docs elsewhere default to macOS/Linux shells.

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
