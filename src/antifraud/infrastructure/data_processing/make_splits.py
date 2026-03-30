import argparse
import os

from sklearn.model_selection import train_test_split

from src.antifraud.application.training.utils import load_and_preprocess_data
from src.antifraud.config import config


def make_splits(input_path, train_output, test_output):
    """
    Загружает данные, применяет предобработку и делит их на обучающую и тестовую выборки.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file {input_path} not found")

    print(f"Loading and preprocessing data from {input_path}...")
    df = load_and_preprocess_data(input_path)

    # Сортировка по времени
    df = df.sort_values("Time")

    # Train / test split
    print("Splitting data...")
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["Class"])

    os.makedirs(os.path.dirname(train_output), exist_ok=True)
    os.makedirs(os.path.dirname(test_output), exist_ok=True)

    train_df.to_parquet(train_output, index=False)
    test_df.to_parquet(test_output, index=False)

    print(f"Train shape: {train_df.shape} saved to {train_output}")
    print(f"Test shape: {test_df.shape} saved to {test_output}")


def main():
    """CLI entrypoint for train/test split generation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=config["data"]["raw_path"])
    parser.add_argument("--output", help="Path to train output", required=False)
    parser.add_argument("--test-output", default="data/splits/test.parquet")
    args = parser.parse_args()

    train_output_path = args.output or "data/splits/train.parquet"
    make_splits(args.input, train_output_path, args.test_output)


if __name__ == "__main__":
    main()
