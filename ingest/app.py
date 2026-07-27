"""POST /v1/events -> raw_device_usage_hour."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from db import insert_usage_hour

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="hope-metrics-ingest", version="0.1.0")


class UsageHourEvent(BaseModel):
    schema_version: str
    probe_version: str
    device_id: str
    window_start: str
    window_end: str
    active_minutes: int = Field(..., ge=0)

    @field_validator("schema_version", "probe_version", "device_id", "window_start", "window_end")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("must not be empty")
        return v


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/events", status_code=201)
def post_event(event: UsageHourEvent) -> dict[str, Any]:
    try:
        row_id = insert_usage_hour(event.model_dump())
    except Exception as exc:  # local: surface DB errors in 500 body
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"id": row_id, "status": "accepted"}
