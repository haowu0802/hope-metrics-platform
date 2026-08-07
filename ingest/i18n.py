"""Dashboard copy: English default, Chinese optional (?lang=zh)."""

from __future__ import annotations

DEFAULT_LANG = "en"
SUPPORTED = frozenset({"en", "zh"})

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "html_lang": "en",
        "title": "Hope Metrics",
        "note_active": "Active minutes = keyboard/mouse activity (idle cutoff 10 minutes).",
        "note_grain": "Grain: one row per device per US/Eastern calendar day.",
        "note_pilot": "Pilot / demo telemetry — not beneficiary or child-level impact data.",
        "note_smoke": "Rows may include smoke-test device ids until replaced by real probes.",
        "empty_before": "No daily usage yet. Run the Windows probe against this ingest, or POST hour events to",
        "empty_after": ".",
        "empty_filtered": "No rows match these filters. Clear filters or widen the date range.",
        "devices": "Devices",
        "day_rows": "Day-rows",
        "total_minutes": "Active minutes (sum)",
        "dates": "Dates",
        "meta": "Newest days first. Source view:",
        "col_device": "device_id",
        "col_date": "usage_date",
        "col_minutes": "active_minutes_day",
        "col_rank_minutes": "active_minutes_sum",
        "lang_en": "EN",
        "lang_zh": "中文",
        "filters": "Filters",
        "date_from": "From",
        "date_to": "To",
        "device": "Device",
        "all_devices": "All devices",
        "device_hint": "Leave device blank for all; multi-select with Ctrl/Cmd.",
        "apply": "Apply",
        "clear": "Clear",
        "trend_title": "Daily active minutes (sum)",
        "rank_title": "Devices by active minutes",
        "detail_title": "Day-level detail",
        "chart_label": "active_minutes_day",
    },
    "zh": {
        "html_lang": "zh-Hans",
        "title": "Hope Metrics",
        "note_active": "活跃分钟 = 键鼠活动（空闲阈值 10 分钟）。",
        "note_grain": "粒度：每台设备 × 每个美东日历日一行。",
        "note_pilot": "试点 / 演示遥测 — 不是受益人或儿童级 Impact 数据。",
        "note_smoke": "表中可能含冒烟测试设备 ID，正式装机后会被替换。",
        "empty_before": "暂无日用量。请用 Windows probe 上报，或向",
        "empty_after": " 提交小时事件。",
        "empty_filtered": "当前筛选无数据。请清空筛选或扩大日期范围。",
        "devices": "设备数",
        "day_rows": "日行数",
        "total_minutes": "活跃分钟合计",
        "dates": "日期范围",
        "meta": "按日从新到旧。来源视图：",
        "col_device": "device_id",
        "col_date": "usage_date",
        "col_minutes": "active_minutes_day",
        "col_rank_minutes": "active_minutes_sum",
        "lang_en": "EN",
        "lang_zh": "中文",
        "filters": "筛选",
        "date_from": "起",
        "date_to": "止",
        "device": "设备",
        "all_devices": "全部设备",
        "device_hint": "不选设备即全部；多选请按住 Ctrl/Cmd。",
        "apply": "应用",
        "clear": "清空",
        "trend_title": "日活跃分钟合计",
        "rank_title": "设备活跃分钟排行",
        "detail_title": "日明细",
        "chart_label": "active_minutes_day",
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
