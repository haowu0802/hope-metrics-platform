"""Status-page copy: English default, Chinese optional (?lang=zh)."""

from __future__ import annotations

DEFAULT_LANG = "en"
SUPPORTED = frozenset({"en", "zh"})

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "html_lang": "en",
        "title": "Hope Metrics",
        "brand": "Hope Metrics",
        "lede": "Ingest status for donated-device active minutes. Charts live in Metabase; Airflow schedules dbt.",
        "status_kicker": "Live ingest",
        "empty_before": "No daily usage yet. Run the Windows probe against this ingest, or POST hour events to",
        "empty_after": ".",
        "devices": "Devices",
        "day_rows": "Day-rows",
        "total_minutes": "Active minutes",
        "dates": "Date span",
        "last_ingest": "Last ingest",
        "explore_kicker": "Explore",
        "lang_en": "EN",
        "lang_zh": "中文",
        "link_metabase": "Open Metabase",
        "link_airflow": "Open Airflow",
        "metabase_desc": "Fleet trends, device drill-down, idle alerts on marts.",
        "airflow_desc": "Daily dbt build and Feishu alerts.",
        "tools_unset": "Set METABASE_URL / AIRFLOW_URL on the app to show toolchain links.",
        "foot_api": "API",
    },
    "zh": {
        "html_lang": "zh-Hans",
        "title": "Hope Metrics",
        "brand": "Hope Metrics",
        "lede": "捐赠设备活跃分钟的接入状态。图表在 Metabase；Airflow 调度 dbt 与告警。",
        "status_kicker": "接入实况",
        "empty_before": "暂无日用量。请用 Windows probe 上报，或向",
        "empty_after": " 提交小时事件。",
        "devices": "设备数",
        "day_rows": "日行数",
        "total_minutes": "活跃分钟",
        "dates": "日期跨度",
        "last_ingest": "最近接入",
        "explore_kicker": "继续探索",
        "lang_en": "EN",
        "lang_zh": "中文",
        "link_metabase": "打开 Metabase",
        "link_airflow": "打开 Airflow",
        "metabase_desc": "机群趋势、单设备、闲置告警（mart）。",
        "airflow_desc": "每日 dbt 构建与飞书告警。",
        "tools_unset": "在应用上设置 METABASE_URL / AIRFLOW_URL 以显示工具链链接。",
        "foot_api": "接口",
    },
}


def resolve_lang(raw: str | None) -> str:
    if not raw:
        return DEFAULT_LANG
    key = raw.strip().lower().replace("_", "-")
    if key.startswith("zh"):
        return "zh"
    if key.startswith("en"):
        return "en"
    return DEFAULT_LANG


def messages_for(lang: str) -> dict[str, str]:
    return MESSAGES.get(lang, MESSAGES[DEFAULT_LANG])
