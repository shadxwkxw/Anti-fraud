import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from src.antifraud.config import config

DB_HOST = config["postgres"]["host"]
DB_PORT = config["postgres"]["port"]
DB_USER = config["postgres"]["user"]
DB_PASSWORD = config["postgres"]["password"]
DB_NAME = config["postgres"]["database"]


def create_database_if_not_exists():
    """Create the application database if it does not exist yet."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres",
            sslmode=config["postgres"].get("sslmode", "require"),
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()

        if not exists:
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")

        cur.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"Error: Unable to connect to the database or create it. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    create_database_if_not_exists()
