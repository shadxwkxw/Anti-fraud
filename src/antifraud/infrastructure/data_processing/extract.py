import argparse
import os
import shutil

from src.antifraud.config import config
from src.antifraud.infrastructure.storage.s3_io import s3_download, s3_upload


def extract_data(date, output_path):
    source_path = config["data"]["raw_path"]

    # Скачиваем сырой датасет из S3, если его нет локально
    if not os.path.exists(source_path):
        print(f"Source file {source_path} not found locally, downloading from S3...")
        s3_download(source_path, source_path)

    if os.path.abspath(source_path) == os.path.abspath(output_path):
        print(f"Source and destination are the same: {source_path}. Skipping copy.")
    else:
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        shutil.copy(source_path, output_path)

    # Загружаем результат в S3 для следующего шага
    s3_upload(output_path, output_path)
    print(f"Data for {date} extracted to {output_path}")


def main():
    """CLI entrypoint for extraction step."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    extract_data(args.date, args.output)


if __name__ == "__main__":
    main()
