import argparse
import os
import shutil


def register_model(model_path):
    """
    Регистрация модели как основной (PROD).
    В MVP просто копирует файл в папку models/random_forest/.
    """
    prod_dir = "models/random_forest"
    os.makedirs(prod_dir, exist_ok=True)

    prod_path = os.path.join(prod_dir, "model.joblib")

    shutil.copy(model_path, prod_path)
    print(f"Model {model_path} registered as production model at {prod_path}")


def main():
    """CLI entrypoint for production model registration."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    register_model(args.model)


if __name__ == "__main__":
    main()
