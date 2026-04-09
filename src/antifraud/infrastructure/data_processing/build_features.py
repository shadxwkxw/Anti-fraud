import argparse
import os

from src.antifraud.application.training.utils import load_and_preprocess_data
from src.antifraud.infrastructure.storage.s3_io import s3_download, s3_upload


def build_features(input_path, output_path):
    """
    Выполняет инженерию признаков.
    """
    # Скачиваем из S3, если нет локально
    if not os.path.exists(input_path):
        s3_download(input_path, input_path)

    print(f"Building features from {input_path}...")

    df = load_and_preprocess_data(input_path)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    df.to_parquet(output_path, index=False)

    # Загружаем результат в S3 для следующего шага
    s3_upload(output_path, output_path)
    print(f"Features saved to {output_path}")


def main():
    """CLI entrypoint for feature building."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    build_features(args.input, args.output)


if __name__ == "__main__":
    main()
