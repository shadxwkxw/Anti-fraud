FROM python:3.11-slim

# Отключаем лишнее
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/

# Системные зависимости (нужны для numpy, scipy, sklearn и postgres)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости
RUN uv sync --frozen --no-dev

# Копируем код, конфиги и модели
COPY src/ src/
COPY services/batch/ services/batch/
COPY configs/ configs/
COPY models/ models/

# Настраиваем пути для доступа к установленному окружению
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Команда по умолчанию (может быть переопределена в Airflow)
CMD ["python", "services/batch/main.py"]
