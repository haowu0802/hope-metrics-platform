# Device event contract

Used by the Windows probe, simulator, and server ingest.

## Event `device_usage_hour`

### Schema version `2` (current)

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | string | yes | `"2"` |
| `probe_version` | string | yes | Probe/sim semver |
| `device_id` | string | yes | Windows MachineGuid (lowercase) or `sim-*` |
| `window_start` | string (RFC3339) | yes | Hour start, inclusive |
| `window_end` | string (RFC3339) | yes | Hour end, exclusive (`[start, end)`) |
| `active_minutes` | integer | yes | In-use minutes in the window (`0`–`60`) |
| `cpu_util_avg_pct` | number | yes | Mean CPU utilization % over samples in the hour (`0`–`100`) |
| `gpu_util_avg_pct` | number \| null | yes | Mean GPU utilization %, or `null` if no discrete GPU / unsupported |
| `mem_util_avg_pct` | number | yes | Mean RAM used % (`0`–`100`) |
| `disk_free_gb` | number | yes | Free space on system volume at hour close (GiB) |

Example:

```json
{
  "schema_version": "2",
  "probe_version": "0.2.0",
  "device_id": "b4b8a740-ae48-4171-b90b-10631222a612",
  "window_start": "2026-07-27T14:00:00+08:00",
  "window_end": "2026-07-27T15:00:00+08:00",
  "active_minutes": 37,
  "cpu_util_avg_pct": 42.5,
  "gpu_util_avg_pct": 68.0,
  "mem_util_avg_pct": 71.2,
  "disk_free_gb": 128.4
}
```

### Schema version `1` (accepted)

Same identity fields + `active_minutes` only. Resource fields are stored as SQL `NULL`. Prefer v2 for new emitters.

## How the probe counts activity (unchanged)

- About once a minute, read Windows last-input time (`GetLastInputInfo`).
- If last input was within the idle threshold, that clock minute counts as active.
- Default idle threshold: 10 minutes (600 seconds).
- Does not record what was typed or clicked.

## How the probe samples resources (v2)

- Same cadence as activity (~1/min).
- CPU: system utilization via `GetSystemTimes` deltas.
- Memory: `GlobalMemoryStatusEx` used %.
- Disk: free GiB on the system drive (`GetDiskFreeSpaceExW`).
- GPU: optional; omitted (`null`) when no readable adapter counter (common on donated PCs without NVIDIA NVML). Simulator may still emit GPU for demo fleets.

Hour event fields are the mean of samples in that hour (disk uses the last sample in the hour).

## How events leave the machine

1. Write each closed hour to a JSON file under the local `pending` directory.
2. If `ingest-url` is set, POST them to `/v1/events`.
3. After HTTP 2xx, delete the local file.

Rows land in Postgres `raw_device_usage_hour` (append only).
