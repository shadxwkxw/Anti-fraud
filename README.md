# Anti-Fraud ML System

MVP-система автоматического обнаружения мошеннических транзакций из двух сервисов:
- `batch` контур: еженедельное переобучение модели и пакетный скоринг через Airflow + Docker;
- `online` контур: API для скоринга транзакций в режиме реального времени.

Проект реализует pipeline: `ingest → feature engineering → train → evaluate → register → predict`.

## Архитектура

Код организован по Clean Architecture:
- `src/antifraud/domain` — сущности, value objects, логика предсказания.
- `src/antifraud/application` — use cases (обучение, оценка, регистрация модели, batch-скоринг).
- `src/antifraud/infrastructure` — адаптеры хранилищ, обработки данных и фичеризации.
- `src/antifraud/interfaces/online` — online API.
- `src/antifraud/interfaces/batch` — запуск batch-обработки и интеграция с Airflow.
- `services/batch` и `services/online` — отдельные deployable entrypoints.

## Структура репозитория

```text
antifraud/
│
├── .github/workflows/
│   └── ci.yml                        # CI/CD: lint, test, build, deploy
│
├── configs/
│   └── config.yaml                   # Единый конфиг: модель, фичи, пороги, БД, S3
│
├── data/                             # Данные (не в git, монтируются в контейнеры)
│   ├── raw/                          # Исходные CSV-файлы транзакций
│   ├── processed/                    # Parquet-файлы после feature engineering
│   ├── splits/                       # Train/test выборки
│   └── output/                       # Результаты batch-скоринга
│
├── models/                           # Сериализованные модели (joblib)
│   ├── random_forest/                # Prod-модель: model.joblib + scaler.joblib
│   ├── gradient_boosting/            # Альтернативная модель
│   └── baseline/                     # Baseline (Logistic Regression)
│
├── services/                         # Deployable entrypoints (по одному Dockerfile)
│   ├── batch/
│   │   ├── Dockerfile                # Образ для batch-инференса и обучения
│   │   └── main.py                   # CLI: запуск пакетного скоринга
│   └── online/
│       ├── Dockerfile                # Образ для REST API
│       └── main.py                   # Запуск uvicorn-сервера
│
├── src/antifraud/                    # Основной код (Clean Architecture)
│   ├── config.py                     # Загрузка YAML-конфига + .env через dotenv
│   │
│   ├── domain/                       # Доменный слой (бизнес-логика)
│   │   ├── models.py                 # Сущности: Transaction, Prediction
│   │   └── predictor.py              # Предсказание: загрузка модели, препроцессинг, инференс
│   │
│   ├── application/                  # Слой use cases
│   │   ├── batch_predict.py          # Пакетный скоринг: загрузка данных → инференс → сохранение
│   │   └── training/                 # Обучение моделей
│   │       ├── train_random_forest_model.py   # Random Forest (prod)
│   │       ├── train_gradient_boosting_model.py # Gradient Boosting
│   │       ├── train_baseline.py     # Logistic Regression (baseline)
│   │       ├── evaluate_model.py     # Оценка: classification_report, PR-AUC
│   │       ├── register_model.py     # Регистрация модели как production
│   │       └── utils.py              # Общее: загрузка данных, feature engineering, splits
│   │
│   ├── infrastructure/               # Адаптеры к внешним системам
│   │   ├── data_processing/          # ETL-пайплайн
│   │   │   ├── extract.py            # Извлечение данных (MVP: копирование CSV)
│   │   │   ├── build_features.py     # Feature engineering для batch
│   │   │   ├── validate.py           # Валидация входных данных
│   │   │   └── make_splits.py        # Разбиение на train/test
│   │   └── storage/                  # Хранилища
│   │       ├── postgres.py           # Подключение к PostgreSQL, запись предсказаний
│   │       ├── create_database.py    # Инициализация таблицы predictions
│   │       ├── save_predictions.py   # CLI для сохранения результатов в БД
│   │       └── s3.py                 # Загрузка моделей в S3
│   │
│   └── interfaces/                   # Точки входа
│       ├── online/                   # REST API (FastAPI)
│       │   ├── main.py               # Создание FastAPI-приложения
│       │   ├── routes.py             # Маршруты: /, /health, /model/info, /predict
│       │   └── schemas.py            # Pydantic-схемы запросов и ответов
│       └── batch/                    # Airflow DAGs
│           └── dags/
│               ├── fraud_training_dag.py     # DAG обучения (@weekly)
│               └── batch_prediction_dag.py   # DAG скоринга (@daily)
│
├── tests/                            # Тесты (pytest)
│   └── unit/
│       ├── application/
│       │   └── test_batch_predict.py  # Тесты batch-инференса
│       ├── domain/
│       │   └── test_predictor.py      # Тесты предсказания
│       └── infrastructure/
│           └── test_config.py         # Тесты загрузки конфига
│
├── .env.example                      # Шаблон переменных окружения
├── .flake8                           # Конфигурация flake8
├── docker-compose.yml                # Dev-окружение: API + Airflow + PostgreSQL + MinIO
├── docker-compose.prod.yml           # Prod-окружение с GHCR-образами + MinIO
├── Makefile                          # Команды: build, lint, test, up, down, clean
├── pyproject.toml                    # Зависимости, настройки линтеров и mypy
├── uv.lock                          # Lockfile зависимостей
├── requirements.txt                  # Fallback для pip install
├── ML_system_design_doc.md           # Дизайн-документ ML-системы
└── README.md
```

## Локальный запуск

1. Подготовить окружение:
   - скопировать `.env.example` в `.env`;
   - заполнить переменные под локальную среду;
   - сгенерировать Fernet-ключ для Airflow: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
2. Синхронизировать зависимости:
   - `uv sync --frozen --dev`
3. Собрать и запустить сервисы:
   - `make up`
4. Запуск online API вручную:
   - `uv run python services/online/main.py`
5. Запуск batch-скоринга вручную:
   - `uv run python services/batch/main.py <input_csv> <output_csv>`

Доступные команды:

```bash
make up        # сборка и запуск сервисов (docker-compose)
make down      # остановка сервисов
make lint      # запуск линтеров (flake8, isort, black, pylint, mypy)
make format    # автоформатирование кода
make typecheck # статический анализ типов
make test      # запуск тестов (pytest)
make check     # все quality gates разом
make clean     # полная очистка (volumes, cache, orphan-контейнеры)
make cov       # coverage тесты
```

## API online-сервиса (MVP)

- `GET /` — информация о сервисе.
- `GET /health` — healthcheck.
- `POST /predict` — скоринг транзакции, возвращает вероятность фрода и флаг `is_fraud`.
- `GET /model/info` — метаинформация о загруженной модели: тип, порог классификации, путь до артефакта.

## Качество кода

Проект использует единый стек линтеров, запускаемых через `make lint` / `make check`:

| Инструмент   | Версия   | Роль                                      |
|--------------|----------|-------------------------------------------|
| `flake8`     | ≥ 7.3    | Проверка стиля (PEP 8) и синтаксических ошибок |
| `isort`      | ≥ 6.1    | Сортировка импортов (профиль `black`)     |
| `black`      | ≥ 25.1   | Автоформатирование (`line-length = 100`)  |
| `pylint`     | ≥ 4.0    | Статический анализ качества кода          |
| `mypy`       | ≥ 1.18   | Проверка аннотаций типов (`python 3.11`)  |
| `pytest-cov` | ≥ 7.1    | Формирование отчета о покрытии тестами    |

Конфигурация всех инструментов хранится в `pyproject.toml`. В CI все проверки выполняются через `make check` и блокируют сборку образов при падении.

## Воспроизводимость

- Конфигурация централизована в `src/antifraud/config.py` и `configs/config.yaml`.
- Все env-переменные описаны в `.env.example`.
- Зависимости фиксируются через `pyproject.toml` и `uv.lock`.
- Результаты batch-скоринга сохраняются в PostgreSQL (`predictions`) и в `artifacts/batch_predictions.csv`.
- Модели сериализуются в `models/` и версионируются в S3-совместимом хранилище MinIO (бакет `antifraud-models`).
- MinIO web-консоль доступна на `http://localhost:9001` (креды в `.env`).

## Deploy и rollback

- Сборка происходит в CI после прохождения quality gates (lint, typecheck, tests).
- Публикуются 3 образа: `antifraud-online:<tag>`, `antifraud-batch:<tag>`, `antifraud-airflow:<tag>`.
- CD запускается в push-модели: CI обновляет удалённый сервер по SSH, применяя `docker-compose.prod.yml`.
- Rollback: переключение на предыдущий стабильный тег всех трёх сервисов.

## SLA и ограничения MVP

- Время отклика online API — не более N секунд на транзакцию.
- Целевые метрики модели: Recall ≥ 80%, Precision ≥ 40%, основная метрика — PR-AUC.
- Порог классификации настраивается через `configs/config.yaml` (`model.threshold`).
- Еженедельный цикл переобучения запускается по расписанию через Airflow DAG `fraud_training_pipeline`.

## Документация

- Основной ML-документ: `ML_system_design_doc.md`
