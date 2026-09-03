"""CLI: python -m jobs.feishu <command>

Commands: ping | alerts | daily | weekly | monthly | fail
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = val


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    _load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(prog="python -m jobs.feishu")
    parser.add_argument(
        "command",
        choices=["ping", "alerts", "daily", "weekly", "monthly", "fail"],
    )
    parser.add_argument("--subject", default="", help="for fail: Feishu failure line")
    args = parser.parse_args(argv)

    if args.command == "ping":
        from jobs.feishu.webhook import feishu_keyword, send_feishu_text

        mode = send_feishu_text(
            "【Hope Metrics】飞书 webhook 测试成功\n"
            f"keyword={feishu_keyword()}\n"
            "若看到此消息，GitHub Actions 告警/简报通道可用。",
            require_url=True,
        )
        print("ok", mode)
        return 0

    if args.command == "fail":
        from jobs.feishu.webhook import send_feishu_text

        subject = args.subject.strip() or "【Hope Metrics】任务失败 (GitHub Actions)"
        send_feishu_text(subject)
        return 0

    if args.command == "alerts":
        from jobs.feishu.alerts import check_stale_devices

        check_stale_devices()
        print("ok alerts")
        return 0

    if args.command == "daily":
        from jobs.feishu.daily import send_daily_metabase_report

        send_daily_metabase_report()
        print("ok daily")
        return 0

    if args.command == "weekly":
        from jobs.feishu.weekly import send_weekly_feishu_report

        send_weekly_feishu_report()
        print("ok weekly")
        return 0

    from jobs.feishu.monthly import send_monthly_feishu_report

    send_monthly_feishu_report()
    print("ok monthly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
