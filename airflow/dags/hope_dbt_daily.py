"""Daily dbt build for Hope Metrics transforms."""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

logger = logging.getLogger(__name__)


def _feishu_on_failure(context) -> None:
    url = os.environ.get("FEISHU_WEBHOOK_URL", "").strip()
    if not url:
        return
    ti = context.get("task_instance")
    dag = context.get("dag")
    text = (
        f"Hope Metrics Airflow failure\n"
        f"dag={getattr(dag, 'dag_id', '?')} "
        f"task={getattr(ti, 'task_id', '?')} "
        f"run={context.get('run_id', '?')}"
    )
    body = json.dumps({"msg_type": "text", "content": {"text": text}}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception:
        logger.exception("Feishu webhook failed")


with DAG(
    dag_id="hope_dbt_daily",
    description="dbt build (stg/mart + tests)",
    schedule="0 12 * * *",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["hope", "dbt"],
    default_args={
        "retries": 1,
        "on_failure_callback": _feishu_on_failure,
    },
) as dag:
    BashOperator(
        task_id="dbt_build",
        bash_command="cd /opt/hope/dbt && dbt build",
    )
