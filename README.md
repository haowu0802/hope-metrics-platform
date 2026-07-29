# Hope Metrics Platform

A data platform that turns education GenAI pilot operations into measurable metrics.

## What's in this repo

- `probe/`: Windows agent that measures active use
- `probe/`: Windows agent (active-use minutes per hour)
- `ingest/`: HTTP API that writes probe events into Postgres
- `warehouse/`: staging dedupe + daily usage views

Contract: `docs/device-event-contract.md`  
Grains: `docs/grains.md`
