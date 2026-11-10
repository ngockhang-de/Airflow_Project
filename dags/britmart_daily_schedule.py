import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.providers.standard.operators.python import PythonOperator
from airflow import DAG
from airflow.sdk import Param

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from pipeline import check_raw_files, clean_orders, build_city_summary, run_quality_check # noqa: E402


default_args = {'retries': 2,
                'retry_delay': timedelta(minutes=1),
                'start_date': datetime(2026, 1, 1)}


RUN_DATE = "{{ (params.run_date if params.run_date else ds_nodash).replace('-', '') }}"

with DAG(
    dag_id="britmart_daily_schedule",
    default_args=default_args,
    schedule="@daily",
    params={
        "run_date": Param(
            "",
            type="string",
            description="Day to process as YYYYMMDD (e.g. 20261105). Leave empty to use the logical date.",
        ),
    },
    catchup=False,
) as dag:

    check_raw_files_task = PythonOperator(
        task_id="check_raw_files",
        python_callable=check_raw_files,
        op_kwargs={
            "run_date": RUN_DATE
        }
    )

    clean = PythonOperator(
        task_id="clean_orders",
        python_callable=clean_orders,
        op_kwargs={
            "run_date": RUN_DATE
        },
    )

    build_summary = PythonOperator(
        task_id="build_city_summary",
        python_callable=build_city_summary,
        op_kwargs={
            "run_date": RUN_DATE
        },
    )

    quality_check = PythonOperator(
        task_id="run_quality_check",
        python_callable=run_quality_check,
        op_kwargs={
            "run_date": RUN_DATE
        },
    )

    check_raw_files_task >> clean >> build_summary >> quality_check
