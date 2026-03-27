import argparse
import os
import shutil


def extract_data(date, output_path):
    """
    В MVP просто копирует существующий файл, имитируя выгрузку за дату.
    В реальности здесь был бы SQL запрос к БД транзакций.
    """
    source_path = "data/raw/creditcard.csv"

    if not os.path.exists(source_path):
        print(f"Error: Source file {source_path} not found")
        return

    if os.path.abspath(source_path) == os.path.abspath(output_path):
        print(f"Source and destination are the same: {source_path}. Skipping copy.")
        return

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # В реальности мы бы фильтровали данные по дате
    shutil.copy(source_path, output_path)
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
