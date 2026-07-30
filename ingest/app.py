"""Ingest API and dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from db import fetch_daily_usage, insert_usage_hour

_root = Path(__file__).resolve().parent.parent
load_dotenv(_root / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="hope-metrics-ingest", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


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


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    try:
        rows = fetch_daily_usage()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"rows": rows, "row_count": len(rows)},
    )


@app.get("/api/v1/daily-usage")
def api_daily_usage() -> dict[str, Any]:
    try:
        rows = fetch_daily_usage()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"rows": rows, "count": len(rows)}


@app.post("/v1/events", status_code=201)
def post_event(event: UsageHourEvent) -> dict[str, Any]:
    try:
        row_id = insert_usage_hour(event.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"id": row_id, "status": "accepted"}
