import argparse
import os

from src.antifraud.application.training.utils import load_and_preprocess_data


def build_features(input_path, output_path):
    """
    Выполняет инженерию признаков.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file {input_path} not found")

    print(f"Building features from {input_path}...")

    # Используем общую логику предобработки из utils.py
    df = load_and_preprocess_data(input_path)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Сохраняем в parquet (требует pyarrow)
    df.to_parquet(output_path, index=False)
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
