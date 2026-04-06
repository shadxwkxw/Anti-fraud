FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AIRFLOW_HOME=/opt/airflow

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

RUN uv pip install apache-airflow-providers-cncf-kubernetes asyncpg

COPY src/ src/
COPY configs/ configs/

RUN mkdir -p ${AIRFLOW_HOME}/dags
RUN cp src/antifraud/interfaces/batch/dags/*.py ${AIRFLOW_HOME}/dags/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

EXPOSE 8080

CMD ["airflow", "webserver"]
