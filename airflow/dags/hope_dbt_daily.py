"""Daily dbt build for Hope Metrics transforms."""

from __future__ import annotations

import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

from hope_feishu import send_feishu_text

logger = logging.getLogger(__name__)


def _feishu_on_failure(context) -> None:
    ti = context.get("task_instance")
    dag = context.get("dag")
    text = (
        "【Hope Metrics】dbt 日批失败\n"
        f"dag={getattr(dag, 'dag_id', '?')} "
        f"task={getattr(ti, 'task_id', '?')} "
        f"run={context.get('run_id', '?')}"
    )
    try:
        send_feishu_text(text)
    except Exception:
        logger.exception("Feishu webhook failed")


with DAG(
    dag_id="hope_dbt_daily",
    description="dbt build (stg/mart + tests)",
    schedule="0 12 * * *",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    max_active_runs=1,
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
