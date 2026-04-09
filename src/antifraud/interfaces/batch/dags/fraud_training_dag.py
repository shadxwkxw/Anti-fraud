from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

NAMESPACE = "antifraud-system"
BATCH_IMAGE = "ghcr.io/shadxwkxw/antifraud-batch:latest"
IMAGE_PULL_SECRETS = [k8s.V1LocalObjectReference("ghcr-pull-secret")]

ENV_FROM = [
    {"configMapRef": {"name": "antifraud-config"}},
    {"secretRef": {"name": "antifraud-secrets"}},
]

DEFAULT_ARGS = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="fraud_training_pipeline",
    default_args=DEFAULT_ARGS,
    description="Fraud model training pipeline",
    schedule="@weekly",
    catchup=False,
    max_active_runs=1,
    tags=["fraud", "training", "ml"],
) as dag:

    EXECUTION_DATE = "{{ ds }}"
    TRAIN_DATA_PATH = f"data/processed/train_{EXECUTION_DATE}.parquet"
    MODEL_PATH = "data/models/random_forest/model.joblib"

    prepare_data = KubernetesPodOperator(
        task_id="prepare_training_data",
        namespace=NAMESPACE,
        image=BATCH_IMAGE,
        cmds=["python"],
        arguments=[
            "src/antifraud/infrastructure/data_processing/make_splits.py",
            "--output", TRAIN_DATA_PATH,
        ],
        env_from=ENV_FROM,
        image_pull_secrets=IMAGE_PULL_SECRETS,
        service_account_name="airflow",
        is_delete_operator_pod=True,
        get_logs=True,
    )

    train = KubernetesPodOperator(
        task_id="train_model",
        namespace=NAMESPACE,
        image=BATCH_IMAGE,
        cmds=["python"],
        arguments=[
            "src/antifraud/application/training/train_random_forest_model.py",
            "--input", TRAIN_DATA_PATH,
            "--output", MODEL_PATH,
        ],
        env_from=ENV_FROM,
        image_pull_secrets=IMAGE_PULL_SECRETS,
        service_account_name="airflow",
        is_delete_operator_pod=True,
        get_logs=True,
    )

    evaluate = KubernetesPodOperator(
        task_id="evaluate_model",
        namespace=NAMESPACE,
        image=BATCH_IMAGE,
        cmds=["python"],
        arguments=[
            "src/antifraud/application/training/evaluate_model.py",
            "--model", MODEL_PATH,
        ],
        env_from=ENV_FROM,
        image_pull_secrets=IMAGE_PULL_SECRETS,
        service_account_name="airflow",
        is_delete_operator_pod=True,
        get_logs=True,
    )

    register = KubernetesPodOperator(
        task_id="register_model",
        namespace=NAMESPACE,
        image=BATCH_IMAGE,
        cmds=["python"],
        arguments=[
            "src/antifraud/application/training/register_model.py",
            "--model", MODEL_PATH,
        ],
        env_from=ENV_FROM,
        image_pull_secrets=IMAGE_PULL_SECRETS,
        service_account_name="airflow",
        is_delete_operator_pod=True,
        get_logs=True,
    )

    prepare_data >> train >> evaluate >> register
