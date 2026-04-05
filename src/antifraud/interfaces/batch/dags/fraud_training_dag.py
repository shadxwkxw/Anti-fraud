from datetime import datetime, timedelta

from docker.types import Mount

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

# Absolute path to project root on the host machine
PROJECT_ROOT = "/Users/maksim/Anti-fraud"

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
    MODEL_PATH = f"models/random_forest/model_{EXECUTION_DATE}.joblib"

    # Shared mounts for all tasks
    shared_mounts = [
        Mount(source=f"{PROJECT_ROOT}/data", target="/app/data", type="bind"),
        Mount(source=f"{PROJECT_ROOT}/models", target="/app/models", type="bind"),
        Mount(source=f"{PROJECT_ROOT}/configs", target="/app/configs", type="bind"),
        Mount(source=f"{PROJECT_ROOT}/src", target="/app/src", type="bind"),
        Mount(source=f"{PROJECT_ROOT}/.env", target="/app/.env", type="bind", read_only=True),
    ]

    # 1. Prepare data for training
    prepare_data = DockerOperator(
        task_id="prepare_training_data",
        image="antifraud-batch:latest",
        command=f"python src/antifraud/infrastructure/data_processing/make_splits.py \
            --output {TRAIN_DATA_PATH}",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    # 2. Train model
    train = DockerOperator(
        task_id="train_model",
        image="antifraud-batch:latest",
        command=f"python src/antifraud/application/training/train_random_forest_model.py \
            --input {TRAIN_DATA_PATH} --output {MODEL_PATH}",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    # 3. Evaluate model
    evaluate = DockerOperator(
        task_id="evaluate_model",
        image="antifraud-batch:latest",
        command=f"python src/antifraud/application/training/evaluate_model.py \
            --model {MODEL_PATH}",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    # 4. Register model (MLflow / registry)
    register = DockerOperator(
        task_id="register_model",
        image="antifraud-batch:latest",
        command=f"python src/antifraud/application/training/register_model.py \
            --model {MODEL_PATH}",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    prepare_data.set_downstream(train)
    train.set_downstream(evaluate)
    evaluate.set_downstream(register)
