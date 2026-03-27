import argparse
import os

from src.antifraud.application.batch_predict import run_batch


def main():
    """CLI entrypoint for batch service."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="data/raw/creditcard.csv")
    parser.add_argument("output", nargs="?", default="artifacts/batch_predictions.csv")
    args = parser.parse_args()

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    run_batch(args.input, args.output)
    print("Batch inference finished via service entrypoint")


if __name__ == "__main__":
    main()
