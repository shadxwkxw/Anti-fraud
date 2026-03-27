from datetime import datetime, timedelta

from docker.types import Mount

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

# Absolute path to project root on the host machine
PROJECT_ROOT = "/Users/maksim/Anti-fraud"

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
    tags=["fraud", "batch", "ml"],
) as dag:

    # Параметры (динамические)
    EXECUTION_DATE = "{{ ds }}"
    INPUT_PATH = f"data/raw/transactions_{EXECUTION_DATE}.csv"
    FEATURES_PATH = f"data/processed/features_{EXECUTION_DATE}.parquet"
    PREDICTIONS_PATH = f"data/output/predictions_{EXECUTION_DATE}.csv"

    # Shared mounts for all tasks
    shared_mounts = [
        Mount(source=f"{PROJECT_ROOT}/data", target="/app/data", type="bind"),
        Mount(source=f"{PROJECT_ROOT}/models", target="/app/models", type="bind"),
        Mount(source=f"{PROJECT_ROOT}/configs", target="/app/configs", type="bind"),
        Mount(source=f"{PROJECT_ROOT}/src", target="/app/src", type="bind"),
    ]

    # 0. Create database if not exists
    create_database = DockerOperator(
        task_id="create_fraud_database",
        image="antifraud-batch:latest",
        command="python src/antifraud/infrastructure/storage/create_database.py",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    # 1. Extract / Prepare data
    extract = DockerOperator(
        task_id="extract_data",
        image="antifraud-batch:latest",
        command=f"python src/antifraud/infrastructure/data_processing/extract.py \
            --date {EXECUTION_DATE} --output {INPUT_PATH}",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    # 2. Validate data
    validate = DockerOperator(
        task_id="validate_data",
        image="antifraud-batch:latest",
        command=f"python src/antifraud/infrastructure/data_processing/validate.py \
            --input {INPUT_PATH}",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    # 3. Feature engineering
    features = DockerOperator(
        task_id="build_features",
        image="antifraud-batch:latest",
        command=f"python src/antifraud/infrastructure/data_processing/build_features.py \
            --input {INPUT_PATH} --output {FEATURES_PATH}",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    # 4. Run batch inference
    predict = DockerOperator(
        task_id="predict",
        image="antifraud-batch:latest",
        command=f"python src/antifraud/application/batch_predict.py \
            --input {FEATURES_PATH} --output {PREDICTIONS_PATH}",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    # 5. Save / publish results
    save = DockerOperator(
        task_id="save_results",
        image="antifraud-batch:latest",
        command=f"python src/antifraud/infrastructure/storage/save_predictions.py \
            --input {PREDICTIONS_PATH}",
        docker_url="unix://var/run/docker.sock",
        network_mode="antifraud-network",
        auto_remove="success",
        mount_tmp_dir=False,
        mounts=shared_mounts,
    )

    # Dependencies
    create_database.set_downstream(extract)
    extract.set_downstream(validate)
    validate.set_downstream(features)
    features.set_downstream(predict)
    predict.set_downstream(save)
