import uvicorn

from src.antifraud.interfaces.online.main import app


def main():
    """CLI entrypoint for online service."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
