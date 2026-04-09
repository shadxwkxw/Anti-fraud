"""Утилиты для загрузки/выгрузки промежуточных артефактов через S3 (MinIO)."""

import os

from src.antifraud.infrastructure.storage.s3 import get_s3_client
from src.antifraud.config import config

BUCKET = config["s3"]["bucket"]


def s3_download(s3_key: str, local_path: str) -> str:
    """Скачивает файл из S3 в локальный путь."""
    output_dir = os.path.dirname(local_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    s3 = get_s3_client()
    s3.download_file(BUCKET, s3_key, local_path)
    print(f"Downloaded s3://{BUCKET}/{s3_key} -> {local_path}")
    return local_path


def s3_upload(local_path: str, s3_key: str) -> str:
    """Загружает локальный файл в S3."""
    s3 = get_s3_client()
    s3.upload_file(local_path, BUCKET, s3_key)
    print(f"Uploaded {local_path} -> s3://{BUCKET}/{s3_key}")
    return s3_key
