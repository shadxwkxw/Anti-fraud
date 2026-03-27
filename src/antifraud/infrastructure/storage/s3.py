import os

import boto3

from src.antifraud.config import config


def get_s3_client():
    """Создает S3 клиент, используя параметры из конфига или переменных окружения."""
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", config["s3"]["region"]),
        endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL"),
    )


def upload_model(local_path, s3_key=None):
    """Выгружает обученную модель в S3 бакет."""
    s3 = get_s3_client()
    bucket = config["s3"]["bucket"]

    if s3_key is None:
        s3_key = os.path.basename(local_path)

    try:
        s3.upload_file(local_path, bucket, s3_key)
        print(f"Model {local_path} uploaded to S3: {bucket}/{s3_key}")
    except Exception as e:
        print(f"Failed to upload model to S3: {e}")


def download_model(s3_key, local_path):
    """Загружает модель из S3 бакета для инференса."""
    s3 = get_s3_client()
    bucket = config["s3"]["bucket"]

    output_dir = os.path.dirname(local_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        s3.download_file(bucket, s3_key, local_path)
        print(f"Model {s3_key} downloaded from S3 to {local_path}")
    except Exception as e:
        print(f"Failed to download model from S3: {e}")
