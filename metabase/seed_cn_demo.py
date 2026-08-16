"""Seed / repair CN stakeholder Metabase dashboard (demo cohort marts).

Keeps real probe devices; excludes smoke via *_cn_demo models.
Run after dbt build when marts or viz break:

  python metabase/seed_cn_demo.py

Reads admin from metabase/.fly-admin.txt (gitignored).
"""
from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://hope-metrics-metabase.fly.dev"
ADMIN = Path(__file__).with_name(".fly-admin.txt")
CTX = ssl.create_default_context()
DASHBOARD_ID = 3
DEFAULT_DEVICE = "AI实验室01"
PUBLIC_DEVICE_SLUG = "device"  # login dashboard filter slug; public handout URL omits ?device=

# Physical column -> Chinese axis / table header (demo marts on public dashboard).
FIELD_LABELS_ZH: dict[str, str] = {
    "device_id": "设备ID",
    "display_name": "设备名称(英文)",
    "display_name_zh": "设备名称",
    "persona": "角色",
    "site": "站点",
    "usage_date": "日期",
    "active_devices": "有用量设备数",
    "active_minutes_total": "活跃分钟合计",
    "active_minutes_avg_device": "设备日均活跃分钟",
    "active_minutes_day": "当日活跃分钟",
    "active_minutes_sum": "活跃分钟合计",
    "active_minutes_avg": "平均活跃分钟",
    "active_minutes_avg_day": "日均活跃分钟",
    "active_hour_slots": "有活跃小时数",
    "active_days": "活跃天数",
    "devices_ge_1h": "活跃≥1小时设备数",
    "utilization_pct": "利用率(%)",
    "utilization_pct_avg": "平均利用率(%)",
    "cpu_util_avg_pct": "平均CPU(%)",
    "gpu_util_avg_pct": "平均GPU(%)",
    "mem_util_avg_pct": "平均内存(%)",
    "disk_free_gb_avg": "平均剩余磁盘(GB)",
    "disk_free_gb_min": "最低剩余磁盘(GB)",
    "has_resource_metrics": "含资源指标",
    "hour_cn": "小时(北京时间)",
    "device_count": "设备数",
    "first_seen_date": "首次活跃日期",
    "last_seen_date": "最近活跃日期",
    "today_cn": "今日(北京)",
    "days_since_seen": "闲置天数",
    "is_stale": "是否闲置",
    "window_start": "窗口开始(UTC)",
    "window_end": "窗口结束(UTC)",
    "hour_start_cn": "小时(北京时间)",
    "active_minutes": "活跃分钟",
    "disk_free_gb": "剩余磁盘(GB)",
    "schema_version": "协议版本",
    "probe_version": "探针版本",
    "_loaded_at": "接入时间",
}

DEMO_LABEL_TABLES = (
    "mart_fleet_daily_cn_demo",
    "mart_device_daily_usage_cn_demo",
    "mart_device_hour_cn_demo",
    "mart_hour_of_day_cn_demo",
    "mart_device_summary_cn_demo",
    "mart_device_staleness_demo",
    "dim_device",
)

# logical name -> card intent
CARD_SPECS = [
    # --- near-real-time (hour grain over staging view) ---
    {
        "name": "近24小时机群每小时活跃分钟",
        "table": "mart_device_hour_cn_demo",
        "display": "bar",
        "dim": "hour_start_cn",
        "metric": "active_minutes",
        "agg": "sum",
        "temporal": True,
        "temporal_unit": "hour",
        "last_hours": 24,
    },
    {
        "name": "近24小时机群每小时平均CPU(%)",
        "table": "mart_device_hour_cn_demo",
        "display": "bar",
        "dim": "hour_start_cn",
        "metric": "cpu_util_avg_pct",
        "agg": "avg",
        "temporal": True,
        "temporal_unit": "hour",
        "last_hours": 24,
    },
    {
        "name": "近24小时单设备每小时活跃分钟",
        "table": "mart_device_hour_cn_demo",
        "display": "bar",
        "dim": "hour_start_cn",
        "metric": "active_minutes",
        "agg": "sum",
        "temporal": True,
        "temporal_unit": "hour",
        "last_hours": 24,
        "filter_device": True,
        "device_table": "mart_device_hour_cn_demo",
    },
    {
        "name": "近24小时单设备每小时CPU(%)",
        "table": "mart_device_hour_cn_demo",
        "display": "bar",
        "dim": "hour_start_cn",
        "metric": "cpu_util_avg_pct",
        "agg": "avg",
        "temporal": True,
        "temporal_unit": "hour",
        "last_hours": 24,
        "filter_device": True,
        "device_table": "mart_device_hour_cn_demo",
    },
    # --- daily trends ---
    {
        "name": "机群每日活跃分钟(北京时间)",
        "table": "mart_fleet_daily_cn_demo",
        "display": "line",
        "dim": "usage_date",
        "metric": "active_minutes_total",
        "temporal": True,
    },
    {
        "name": "机群每日平均CPU(%)",
        "table": "mart_fleet_daily_cn_demo",
        "display": "line",
        "dim": "usage_date",
        "metric": "cpu_util_avg_pct",
        "temporal": True,
    },
    {
        "name": "机群每日平均GPU(%)",
        "table": "mart_fleet_daily_cn_demo",
        "display": "line",
        "dim": "usage_date",
        "metric": "gpu_util_avg_pct",
        "temporal": True,
    },
    {
        "name": "单设备每日活跃分钟",
        "table": "mart_device_daily_usage_cn_demo",
        "display": "line",
        "dim": "usage_date",
        "metric": "active_minutes_day",
        "temporal": True,
        "filter_device": True,
        "device_table": "mart_device_daily_usage_cn_demo",
    },
    {
        "name": "单设备每日CPU(%)",
        "table": "mart_device_daily_usage_cn_demo",
        "display": "line",
        "dim": "usage_date",
        "metric": "cpu_util_avg_pct",
        "temporal": True,
        "filter_device": True,
        "device_table": "mart_device_daily_usage_cn_demo",
    },
    {
        "name": "单设备每日GPU(%)",
        "table": "mart_device_daily_usage_cn_demo",
        "display": "line",
        "dim": "usage_date",
        "metric": "gpu_util_avg_pct",
        "temporal": True,
        "filter_device": True,
        "device_table": "mart_device_daily_usage_cn_demo",
    },
    {
        "name": "按时段活跃分钟(北京时间)",
        "table": "mart_hour_of_day_cn_demo",
        "display": "bar",
        "dim": "hour_cn",
        "metric": "active_minutes_sum",
        "temporal": False,
    },
    {
        "name": "设备累计活跃分钟排行",
        "table": "mart_device_summary_cn_demo",
        "display": "row",
        "dim": "display_name_zh",
        "metric": "active_minutes_total",
        "temporal": False,
    },
    {
        "name": "闲置设备告警列表",
        "table": "mart_device_staleness_demo",
        "display": "table",
        "fields": [
            "device_id",
            "display_name_zh",
            "last_seen_date",
            "days_since_seen",
            "has_resource_metrics",
        ],
        "filter_stale": True,
    },
    {
        "name": "无资源指标的设备(仅活跃分钟)",
        "table": "mart_device_summary_cn_demo",
        "display": "table",
        "fields": [
            "device_id",
            "display_name_zh",
            "active_minutes_total",
            "has_resource_metrics",
        ],
        "filter_no_resources": True,
    },
]


def load_admin() -> tuple[str, str]:
    email = password = None
    for line in ADMIN.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line.startswith("METABASE_ADMIN_EMAIL="):
            email = line.split("=", 1)[1].strip()
        elif line.startswith("METABASE_ADMIN_PASSWORD="):
            password = line.split("=", 1)[1].strip()
    if not email or not password:
        raise SystemExit(f"missing admin in {ADMIN}")
    return email, password


def req(method: str, path: str, data=None, session: str | None = None):
    headers = {"Content-Type": "application/json"}
    if session:
        headers["X-Metabase-Session"] = session
    body = None if data is None else json.dumps(data).encode("utf-8")
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=180, context=CTX) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> {e.code} {e.read()[:800]}") from e


def main() -> None:
    email, password = load_admin()
    session = req("POST", "/api/session", {"username": email, "password": password})["id"]

    dbs = req("GET", "/api/database", session=session)
    db_list = dbs if isinstance(dbs, list) else (dbs or {}).get("data") or []
    db = next((d for d in db_list if d.get("id") == 2 or "neon" in (d.get("name") or "").lower() or "hope" in (d.get("name") or "").lower()), None)
    if not db and db_list:
        db = db_list[0]
    if not db:
        raise SystemExit("no Metabase database configured")
    db_id = db["id"]
    print("database", db_id, db.get("name"))

    req("POST", f"/api/database/{db_id}/sync_schema", session=session)
    time.sleep(12)

    def load_tables() -> dict:
        tables = req("GET", f"/api/database/{db_id}/metadata", session=session).get("tables") or []
        return {t["name"]: t for t in tables if not t.get("name", "").startswith("pg_")}

    by_name = load_tables()
    needed = {s["table"] for s in CARD_SPECS} | {"dim_device", "mart_device_hour_cn_demo"}
    missing = sorted(needed - set(by_name))
    if missing:
        print("resync for missing", missing)
        req("POST", f"/api/database/{db_id}/sync_schema", session=session)
        time.sleep(20)
        by_name = load_tables()
        missing = sorted(needed - set(by_name))
        if missing:
            raise SystemExit(f"missing tables after sync: {missing}")

    def field_map(table_name: str) -> dict[str, dict]:
        t = by_name.get(table_name)
        if not t:
            raise SystemExit(f"missing table {table_name} — run dbt build first")
        meta = req("GET", f"/api/table/{t['id']}/query_metadata", session=session)
        return {f["name"]: f for f in meta.get("fields") or []}

    def field_ids(table_name: str) -> dict[str, int]:
        return {n: f["id"] for n, f in field_map(table_name).items()}

    def label_demo_fields() -> None:
        """Chinese display names for all demo-mart columns used on the public dashboard."""
        for table_name in DEMO_LABEL_TABLES:
            fmap = field_map(table_name)
            for col, zh in FIELD_LABELS_ZH.items():
                if col not in fmap:
                    continue
                fid = fmap[col]["id"]
                payload: dict = {
                    "display_name": zh,
                    "visibility_type": "normal",
                }
                if col == "device_id":
                    try:
                        req("DELETE", f"/api/field/{fid}/dimension", session=session)
                    except RuntimeError:
                        pass
                    payload.update(
                        {
                            "semantic_type": "type/Category",
                            "fk_target_field_id": None,
                            "has_field_values": "list",
                        }
                    )
                elif col == "display_name_zh":
                    payload["semantic_type"] = "type/Name"
                req("PUT", f"/api/field/{fid}", payload, session=session)
            print("labeled", table_name, "fields", sum(1 for c in FIELD_LABELS_ZH if c in fmap))

    # Hide non-demo noise tables in browse? keep core; prefer demo in dashboard only.
    collection = None
    for c in req("GET", "/api/collection", session=session) or []:
        if c.get("name") == "Hope 演示(北京时间)":
            collection = c
            break
    if not collection:
        collection = req(
            "POST",
            "/api/collection",
            {"name": "Hope 演示(北京时间)", "color": "#509EE3"},
            session=session,
        )
    coll_id = collection["id"]

    label_demo_fields()
    # Device filter targets differ for hour vs daily cards (different tables / field ids).
    zh_field_by_table = {
        "mart_device_daily_usage_cn_demo": field_ids("mart_device_daily_usage_cn_demo")[
            "display_name_zh"
        ],
        "mart_device_hour_cn_demo": field_ids("mart_device_hour_cn_demo")["display_name_zh"],
    }

    existing_cards = {
        c["name"]: c
        for c in (req("GET", "/api/card", session=session) or [])
        if c.get("collection_id") == coll_id or c.get("name") in {s["name"] for s in CARD_SPECS}
    }

    def column_settings_zh(names: list[str]) -> dict:
        """Force Chinese titles even if metadata cache is stale."""
        out: dict = {}
        for n in names:
            zh = FIELD_LABELS_ZH.get(n)
            if not zh:
                continue
            out[json.dumps(["name", n])] = {"column_title": zh}
        return out

    card_ids: dict[str, int] = {}
    for spec in CARD_SPECS:
        fmap = field_ids(spec["table"])
        table_id = by_name[spec["table"]]["id"]
        if spec["display"] == "table":
            cols = [n for n in spec["fields"] if n in fmap]
            field_id_list = [fmap[n] for n in cols]
            query = {
                "source-table": table_id,
                "fields": [["field", fid, None] for fid in field_id_list],
            }
            if spec.get("filter_stale") and "is_stale" in fmap:
                query["filter"] = ["=", ["field", fmap["is_stale"], None], True]
            if spec.get("filter_no_resources") and "has_resource_metrics" in fmap:
                query["filter"] = ["=", ["field", fmap["has_resource_metrics"], None], False]
            viz = {
                "table.columns": [{"name": n, "enabled": True} for n in cols],
                "column_settings": column_settings_zh(cols),
            }
        elif spec.get("agg"):
            dim_id = fmap[spec["dim"]]
            metric_id = fmap[spec["metric"]]
            unit = spec.get("temporal_unit", "day")
            dim_opts = {"temporal-unit": unit} if spec.get("temporal") else None
            dim_ref = ["field", dim_id, dim_opts]
            agg_op = spec["agg"]
            query = {
                "source-table": table_id,
                "aggregation": [[agg_op, ["field", metric_id, None]]],
                "breakout": [dim_ref],
                "order-by": [["asc", dim_ref]],
            }
            if spec.get("last_hours"):
                query["filter"] = [
                    "time-interval",
                    ["field", dim_id, {"base-type": "type/DateTime"}],
                    -int(spec["last_hours"]),
                    "hour",
                ]
            metric_viz_name = agg_op  # Metabase names agg columns "sum" / "avg"
            viz = {
                "graph.dimensions": [spec["dim"]],
                "graph.metrics": [metric_viz_name],
                "graph.x_axis.title_text": FIELD_LABELS_ZH.get(spec["dim"], spec["dim"]),
                "graph.y_axis.title_text": FIELD_LABELS_ZH.get(spec["metric"], spec["metric"]),
                "column_settings": column_settings_zh([spec["dim"], spec["metric"]]),
            }
        else:
            dim_id = fmap[spec["dim"]]
            metric_id = fmap[spec["metric"]]
            dim_ref = (
                ["field", dim_id, {"temporal-unit": "day"}]
                if spec.get("temporal")
                else ["field", dim_id, None]
            )
            query = {
                "source-table": table_id,
                "fields": [dim_ref, ["field", metric_id, None]],
                "order-by": [["asc", dim_ref]],
            }
            viz = {
                "graph.dimensions": [spec["dim"]],
                "graph.metrics": [spec["metric"]],
                "graph.x_axis.title_text": FIELD_LABELS_ZH.get(spec["dim"], spec["dim"]),
                "graph.y_axis.title_text": FIELD_LABELS_ZH.get(spec["metric"], spec["metric"]),
                "column_settings": column_settings_zh([spec["dim"], spec["metric"]]),
            }

        payload = {
            "name": spec["name"],
            "display": spec["display"],
            "dataset_query": {"type": "query", "database": db_id, "query": query},
            "visualization_settings": viz,
            "collection_id": coll_id,
        }
        old = existing_cards.get(spec["name"])
        if old:
            updated = req("PUT", f"/api/card/{old['id']}", payload, session=session)
            card_ids[spec["name"]] = updated["id"]
            print("updated card", updated["id"], spec["name"])
        else:
            created = req("POST", "/api/card", payload, session=session)
            card_ids[spec["name"]] = created["id"]
            print("created card", created["id"], spec["name"])

    def heading(text: str, row: int, dash_id: int) -> dict:
        return {
            "id": dash_id,
            "card_id": None,
            "card": {
                "name": None,
                "display": "heading",
                "visualization_settings": {},
                "dataset_query": {},
                "archived": False,
            },
            "visualization_settings": {
                "text": text,
                "virtual_card": {
                    "name": None,
                    "display": "heading",
                    "visualization_settings": {},
                    "archived": False,
                    "dataset_query": {},
                },
            },
            "parameter_mappings": [],
            "col": 0,
            "row": row,
            "size_x": 18,
            "size_y": 1,
        }

    # Layout: live hour section on top, then daily trends (18-col grid).
    layout = [
        ("近24小时机群每小时活跃分钟", 1, 0, 9, 7),
        ("近24小时机群每小时平均CPU(%)", 1, 9, 9, 7),
        ("近24小时单设备每小时活跃分钟", 8, 0, 9, 7),
        ("近24小时单设备每小时CPU(%)", 8, 9, 9, 7),
        ("机群每日活跃分钟(北京时间)", 17, 0, 18, 7),
        ("机群每日平均CPU(%)", 24, 0, 9, 7),
        ("机群每日平均GPU(%)", 24, 9, 9, 7),
        ("单设备每日活跃分钟", 33, 0, 18, 8),
        ("单设备每日CPU(%)", 41, 0, 9, 7),
        ("单设备每日GPU(%)", 41, 9, 9, 7),
        ("按时段活跃分钟(北京时间)", 48, 0, 18, 7),
        ("设备累计活跃分钟排行", 55, 0, 9, 8),
        ("闲置设备告警列表", 55, 9, 9, 8),
        ("无资源指标的设备(仅活跃分钟)", 63, 0, 18, 6),
    ]

    dashcards = [
        heading(
            "## 今日实时（小时级 · 接入即可见，无需等日报）",
            0,
            -1,
        ),
        heading(
            "## 历史趋势（日）· 单设备下拉为中文名，默认 AI实验室01",
            16,
            -2,
        ),
        heading(
            "## 单设备日趋势（无 CPU/GPU 见底部表）",
            32,
            -3,
        ),
    ]

    next_id = -4
    for name, row, col, sx, sy in layout:
        cid = card_ids[name]
        mappings = []
        spec = next(s for s in CARD_SPECS if s["name"] == name)
        if spec.get("filter_device"):
            zh_fid = zh_field_by_table[spec.get("device_table", spec["table"])]
            mappings = [
                {
                    "parameter_id": "device_cn",
                    "card_id": cid,
                    "target": ["dimension", ["field", zh_fid, None]],
                }
            ]
        dashcards.append(
            {
                "id": next_id,
                "card_id": cid,
                "card": {"id": cid},
                "parameter_mappings": mappings,
                "visualization_settings": {},
                "col": col,
                "row": row,
                "size_x": sx,
                "size_y": sy,
            }
        )
        next_id -= 1

    # Plain Chinese labels as the filter values (reliable dropdown text in Metabase 0.50).
    labels_q = req(
        "POST",
        "/api/dataset",
        {
            "database": db_id,
            "type": "native",
            "native": {
                "query": """
                    select display_name_zh
                    from dim_device
                    where include_in_demo
                    order by display_name_zh
                """
            },
        },
        session=session,
    )
    device_labels = [
        r[0] for r in ((labels_q or {}).get("data") or {}).get("rows") or []
    ]

    parameters = [
        {
            "id": "device_cn",
            "name": "设备",
            "slug": PUBLIC_DEVICE_SLUG,
            "type": "string/=",
            "sectionId": "string",
            "isMultiSelect": False,
            "default": DEFAULT_DEVICE,
            "values_query_type": "list",
            "values_source_type": "static-list",
            "values_source_config": {"values": device_labels},
        }
    ]

    dash = req("GET", f"/api/dashboard/{DASHBOARD_ID}", session=session)
    # Replace dashcards: Metabase accepts PUT with new negative ids
    updated = req(
        "PUT",
        f"/api/dashboard/{DASHBOARD_ID}",
        {
            "name": "Hope 中国演示(北京时间)",
            "description": (
                "Stakeholder demo: real probes kept; smoke hidden via *_cn_demo. "
                "Login preferred; public link is preview-only."
            ),
            "parameters": parameters,
            "dashcards": dashcards,
            "width": dash.get("width") or "full",
            "collection_id": coll_id,
        },
        session=session,
    )
    print("dashboard", DASHBOARD_ID, "cards", len(updated.get("dashcards") or []))
    print("OK", f"{BASE}/dashboard/{DASHBOARD_ID}")


if __name__ == "__main__":
    main()
