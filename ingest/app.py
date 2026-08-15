"""Ingest API and dashboard."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from db import (
    fetch_daily_trend,
    fetch_daily_usage,
    fetch_device_rank,
    insert_usage_hour,
    list_device_ids,
    summarize_daily_usage,
)
from filters import build_query, normalize_device_ids, parse_iso_date
from i18n import messages_for, resolve_lang

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
def dashboard(
    request: Request,
    lang: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    device_id: Annotated[list[str] | None, Query()] = None,
) -> HTMLResponse:
    locale = resolve_lang(lang)
    df = parse_iso_date(date_from)
    dt = parse_iso_date(date_to)
    if df and dt and df > dt:
        df, dt = dt, df
    devices = normalize_device_ids(device_id)
    filters_active = bool(df or dt or devices)

    try:
        device_options = list_device_ids()
        rows = fetch_daily_usage(date_from=df, date_to=dt, device_ids=devices or None)
        summary = summarize_daily_usage(rows)
        trend = fetch_daily_trend(date_from=df, date_to=dt, device_ids=devices or None)
        rank = fetch_device_rank(date_from=df, date_to=dt, device_ids=devices or None)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    date_from_s = df.isoformat() if df else ""
    date_to_s = dt.isoformat() if dt else ""
    lang_en_href = "/" + build_query(
        lang="en",
        date_from=date_from_s or None,
        date_to=date_to_s or None,
        device_id=devices,
    )
    lang_zh_href = "/" + build_query(
        lang="zh",
        date_from=date_from_s or None,
        date_to=date_to_s or None,
        device_id=devices,
    )
    clear_href = "/" + build_query(lang=locale if locale != "en" else None)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "rows": rows,
            "summary": summary,
            "trend": trend,
            "rank": rank,
            "lang": locale,
            "t": messages_for(locale),
            "device_options": device_options,
            "selected_devices": devices,
            "date_from": date_from_s,
            "date_to": date_to_s,
            "filters_active": filters_active,
            "lang_en_href": lang_en_href,
            "lang_zh_href": lang_zh_href,
            "clear_href": clear_href,
            "airflow_url": os.environ.get("AIRFLOW_URL", "").strip() or None,
            "metabase_url": os.environ.get("METABASE_URL", "").strip() or None,
        },
    )


@app.get("/api/v1/daily-usage")
def api_daily_usage(
    date_from: str | None = None,
    date_to: str | None = None,
    device_id: Annotated[list[str] | None, Query()] = None,
) -> dict[str, Any]:
    df = parse_iso_date(date_from)
    dt = parse_iso_date(date_to)
    if df and dt and df > dt:
        df, dt = dt, df
    devices = normalize_device_ids(device_id)
    try:
        rows = fetch_daily_usage(date_from=df, date_to=dt, device_ids=devices or None)
        summary = summarize_daily_usage(rows)
        trend = fetch_daily_trend(date_from=df, date_to=dt, device_ids=devices or None)
        rank = fetch_device_rank(date_from=df, date_to=dt, device_ids=devices or None)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "filters": {
            "date_from": df.isoformat() if df else None,
            "date_to": dt.isoformat() if dt else None,
            "device_id": devices,
        },
        "summary": summary,
        "trend": trend,
        "rank": rank,
        "rows": rows,
    }


@app.post("/v1/events", status_code=201)
def post_event(event: UsageHourEvent) -> dict[str, Any]:
    try:
        row_id = insert_usage_hour(event.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"id": row_id, "status": "accepted"}
