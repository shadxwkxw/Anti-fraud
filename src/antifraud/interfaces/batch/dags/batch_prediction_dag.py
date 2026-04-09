from datetime import datetime, timedelta

from kubernetes.client import models as k8s

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

NAMESPACE = "antifraud-system"
BATCH_IMAGE = "ghcr.io/shadxwkxw/antifraud-batch:latest"
IMAGE_PULL_SECRETS = [k8s.V1LocalObjectReference("ghcr-pull-secret")]

ENV_FROM = [
    {"configMapRef": {"name": "antifraud-config"}},
    {"secretRef": {"name": "antifraud-secrets"}},
]

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="fraud_batch_pipeline",
    default_args=DEFAULT_ARGS,
    description="Fraud batch scoring pipeline",
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["fraud", "batch", "ml"],
) as dag:

    EXECUTION_DATE = "{{ ds }}"
    INPUT_PATH = f"data/raw/transactions_{EXECUTION_DATE}.csv"
    FEATURES_PATH = f"data/processed/features_{EXECUTION_DATE}.parquet"
    PREDICTIONS_PATH = f"data/output/predictions_{EXECUTION_DATE}.csv"

    extract = KubernetesPodOperator(
        task_id="extract_data",
        namespace=NAMESPACE,
        image=BATCH_IMAGE,
        cmds=["python"],
        arguments=[
            "src/antifraud/infrastructure/data_processing/extract.py",
            "--date",
            EXECUTION_DATE,
            "--output",
            INPUT_PATH,
        ],
        env_from=ENV_FROM,
        image_pull_secrets=IMAGE_PULL_SECRETS,
        service_account_name="airflow",
        is_delete_operator_pod=True,
        get_logs=True,
    )

    validate = KubernetesPodOperator(
        task_id="validate_data",
        namespace=NAMESPACE,
        image=BATCH_IMAGE,
        cmds=["python"],
        arguments=[
            "src/antifraud/infrastructure/data_processing/validate.py",
            "--input",
            INPUT_PATH,
        ],
        env_from=ENV_FROM,
        image_pull_secrets=IMAGE_PULL_SECRETS,
        service_account_name="airflow",
        is_delete_operator_pod=True,
        get_logs=True,
    )

    features = KubernetesPodOperator(
        task_id="build_features",
        namespace=NAMESPACE,
        image=BATCH_IMAGE,
        cmds=["python"],
        arguments=[
            "src/antifraud/infrastructure/data_processing/build_features.py",
            "--input",
            INPUT_PATH,
            "--output",
            FEATURES_PATH,
        ],
        env_from=ENV_FROM,
        image_pull_secrets=IMAGE_PULL_SECRETS,
        service_account_name="airflow",
        is_delete_operator_pod=True,
        get_logs=True,
    )

    predict = KubernetesPodOperator(
        task_id="predict",
        namespace=NAMESPACE,
        image=BATCH_IMAGE,
        cmds=["python"],
        arguments=[
            "src/antifraud/application/batch_predict.py",
            "--input",
            FEATURES_PATH,
            "--output",
            PREDICTIONS_PATH,
        ],
        env_from=ENV_FROM,
        image_pull_secrets=IMAGE_PULL_SECRETS,
        service_account_name="airflow",
        is_delete_operator_pod=True,
        get_logs=True,
    )

    save = KubernetesPodOperator(
        task_id="save_results",
        namespace=NAMESPACE,
        image=BATCH_IMAGE,
        cmds=["python"],
        arguments=[
            "src/antifraud/infrastructure/storage/save_predictions.py",
            "--input",
            PREDICTIONS_PATH,
        ],
        env_from=ENV_FROM,
        image_pull_secrets=IMAGE_PULL_SECRETS,
        service_account_name="airflow",
        is_delete_operator_pod=True,
        get_logs=True,
    )

    extract.set_downstream(validate)
    validate.set_downstream(features)
    features.set_downstream(predict)
    predict.set_downstream(save)
