# Device event contract (v1)

Used by the Windows probe and server ingest.

## Event `device_usage_hour` (`schema_version` = `1`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | string | yes | `"1"` |
| `probe_version` | string | yes | Probe semver, e.g. `0.1.0` |
| `device_id` | string | yes | Windows MachineGuid (lowercase) |
| `window_start` | string (RFC3339) | yes | Hour start, inclusive |
| `window_end` | string (RFC3339) | yes | Hour end, exclusive (`[start, end)`) |
| `active_minutes` | integer | yes | In-use minutes in the window |

Example:

```json
{
  "schema_version": "1",
  "probe_version": "0.1.0",
  "device_id": "b4b8a740-ae48-4171-b90b-10631222a612",
  "window_start": "2026-07-27T14:00:00+08:00",
  "window_end": "2026-07-27T15:00:00+08:00",
  "active_minutes": 37
}
```

## How the probe counts activity

- About once a minute, read Windows last-input time (`GetLastInputInfo`).
- If last input was within the idle threshold, that clock minute counts as active.
- Default idle threshold: 10 minutes (600 seconds).
- Does not record what was typed or clicked.
- Does not compute daily/weekly totals (server does that from raw hour rows).
- v1 has no GPU metrics.

## How events leave the machine

1. Write each closed hour to a JSON file under the local `pending` directory.
2. If `ingest-url` is set, POST those files.
3. After HTTP 2xx, delete the local file.

`--debug` only adds console logs; same write/upload behavior.
