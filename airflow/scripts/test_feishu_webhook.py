"""Send a one-off Feishu test message (uses FEISHU_WEBHOOK_URL + keyword)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dags"))

from hope_feishu import feishu_keyword, send_feishu_text  # noqa: E402

if __name__ == "__main__":
    mode = send_feishu_text(
        "【Hope Metrics】飞书 webhook 测试成功\n"
        f"keyword={feishu_keyword()}\n"
        "若看到此消息，Airflow 告警/简报通道可用。",
        require_url=True,
    )
    print("ok", mode)
