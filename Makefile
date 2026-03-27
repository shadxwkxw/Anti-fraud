
.PHONY: all build build-batch lint lint-check format typecheck test check up down clean

all: build

build: build-batch
	docker-compose build

build-batch:
	docker build -t antifraud-batch:latest -f services/batch/Dockerfile .

lint:
	uv run flake8 src tests services
	uv run isort src tests services airflow
	uv run black src tests services airflow
	uv run pylint src tests services

lint-check:
	uv run flake8 src tests services
	uv run isort --check-only src tests services airflow
	uv run black --check src tests services airflow
	uv run pylint src tests services

format:
	uv run isort src tests services airflow
	uv run black src tests services airflow

typecheck:
	uv run mypy src

test:
	uv run pytest -q

check: lint-check typecheck test

up: build
	docker-compose up -d

down:
	docker-compose down

clean:
	docker-compose down --volumes --remove-orphans
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache
