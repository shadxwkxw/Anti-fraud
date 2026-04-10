# Anti-Fraud ML System

Система автоматического обнаружения мошеннических транзакций, развёрнутая на Kubernetes (k3s).

Два контура:
- **Batch**: ежедневный скоринг транзакций и еженедельное переобучение модели через Airflow DAGs;
- **Online**: REST API для скоринга транзакций в реальном времени.

Все промежуточные артефакты между тасками передаются через S3 (MinIO), результаты скоринга сохраняются в PostgreSQL.

## Архитектура

Код организован по **Clean Architecture**:

| Слой | Путь | Ответственность |
|------|------|-----------------|
| Domain | `src/antifraud/domain/` | Сущности (`Transaction`, `Prediction`), бизнес-логика предсказания |
| Application | `src/antifraud/application/` | Use cases: batch-скоринг, обучение, оценка, регистрация модели |
| Infrastructure | `src/antifraud/infrastructure/` | Адаптеры: PostgreSQL, S3 (MinIO), ETL-пайплайн |
| Interfaces | `src/antifraud/interfaces/` | Точки входа: Online API (FastAPI), Batch (Airflow DAGs) |

## Инфраструктура (Kubernetes)

Все компоненты работают в namespace `antifraud-system` на k3s-кластере:

| Компонент | Тип | Назначение |
|-----------|-----|------------|
| `antifraud-online` | Deployment + HPA | FastAPI-сервис для real-time предсказаний |
| `antifraud-db` | StatefulSet (PG16) | PostgreSQL для данных приложения (таблица `predictions`) |
| `minio` | Deployment | S3-совместимое хранилище (модели, датасеты, артефакты) |
| `airflow-scheduler` | Deployment | Планировщик Airflow — запуск DAG-тасков |
| `airflow-webserver` | Deployment | Web UI Airflow (порт 8080) |
| `airflow-db` | StatefulSet (PG16) | PostgreSQL для метаданных Airflow |

Секреты хранятся в **GitHub Secrets** и прокидываются через CI → `kubectl create secret` → k8s Secret → `env_from` в подах.

## Batch-пайплайны (Airflow)

### `fraud_batch_pipeline` — ежедневный скоринг (`@daily`)

```
extract_data → validate_data → build_features → predict → save_results
```

| Таск | Что делает | Input | Output |
|------|-----------|-------|--------|
| `extract_data` | Извлекает сырой датасет из S3 | S3: `creditcard.csv` | S3: `transactions_{ds}.csv` |
| `validate_data` | Проверяет наличие колонок, null-значения | S3: `transactions_{ds}.csv` | pass/fail |
| `build_features` | Feature engineering, сохраняет parquet | S3: `transactions_{ds}.csv` | S3: `features_{ds}.parquet` |
| `predict` | Инференс: RandomForest + threshold (0.32) | S3: features + model + scaler | S3: `predictions_{ds}.csv` |
| `save_results` | Идемпотентная запись в PostgreSQL | S3: `predictions_{ds}.csv` | Postgres: `predictions` |

Идемпотентность: `DELETE FROM predictions WHERE execution_date = '{ds}'` перед `INSERT`.

### `fraud_training_pipeline` — переобучение модели (`@weekly`)

```
prepare_training_data → train_model → evaluate_model → register_model
```

| Таск | Что делает |
|------|-----------|
| `prepare_training_data` | Train/test split из сырых данных |
| `train_model` | Обучение RandomForest, сохранение `model.joblib` |
| `evaluate_model` | Оценка: precision, recall, PR-AUC |
| `register_model` | Регистрация модели в S3 |

Связь: training pipeline кладёт `model.joblib` в S3, batch pipeline при каждом запуске скачивает свежую модель.

### Передача артефактов между тасками

Каждый таск — отдельный Pod (`KubernetesPodOperator`). Поды эфемерные, общей файловой системы нет. Промежуточные файлы передаются через **S3 (MinIO)**:

```
extract → S3 → validate → S3 → build_features → S3 → predict → S3 → save_results → PostgreSQL
```

## Структура репозитория

```text
Anti-fraud/
├── .github/workflows/
│   ├── ci.yml                            # CI: lint, typecheck, tests (coverage >= 80%)
│   ├── deploy.yml                        # CD: сборка образов и деплой на k8s
│   ├── release-images.yml                # Публикация образов в GHCR
│   └── rollback.yml                      # Откат на предыдущую версию
│
├── configs/
│   └── config.yaml                       # Единый конфиг: модель, фичи, пороги, БД, S3
│
├── deploy/k8s/
│   ├── base/                             # Kubernetes-манифесты (Kustomize)
│   │   ├── namespace.yaml                # namespace: antifraud-system
│   │   ├── configmap.yaml                # ConfigMap: CONFIG_PATH, AWS_S3_ENDPOINT_URL
│   │   ├── secret.yaml                   # Secret-шаблон (значения из CI)
│   │   ├── antifraud-db.yaml             # StatefulSet PostgreSQL (данные приложения)
│   │   ├── airflow-db.yaml               # StatefulSet PostgreSQL (метаданные Airflow)
│   │   ├── airflow-scheduler.yaml        # Deployment Airflow Scheduler
│   │   ├── airflow-webserver.yaml        # Deployment Airflow Webserver
│   │   ├── airflow-dags-configmap.yaml   # ConfigMap с DAG-файлами
│   │   ├── airflow-configmap.yaml        # Airflow environment config
│   │   ├── airflow-secrets.yaml          # Airflow DB credentials
│   │   ├── airflow-rbac.yaml             # RBAC для KubernetesPodOperator
│   │   ├── airflow-logs-pvc.yaml         # PVC для Airflow-логов
│   │   ├── minio-deployment.yaml         # Deployment MinIO
│   │   ├── minio-service.yaml            # Service MinIO
│   │   ├── minio-pvc.yaml               # PVC для MinIO-данных
│   │   ├── online-deployment.yaml        # Deployment online API
│   │   ├── online-service.yaml           # Service online API
│   │   ├── online-hpa.yaml              # HorizontalPodAutoscaler
│   │   ├── ingress.yaml                  # Ingress (Traefik)
│   │   ├── batch-cronjob.yaml            # CronJob (legacy, заменён на Airflow)
│   │   ├── antifraud-data-pvc.yaml       # PVC для данных
│   │   └── kustomization.yaml            # Kustomize: список ресурсов + image overrides
│   └── overlays/production/              # Production-патчи
│
├── services/                             # Entrypoints (по одному Dockerfile)
│   ├── batch/
│   │   ├── Dockerfile                    # Образ для batch-инференса и обучения
│   │   └── main.py                       # CLI: загрузка модели из S3, batch-скоринг
│   └── online/
│       ├── Dockerfile                    # Образ для REST API
│       └── main.py                       # Запуск uvicorn
│
├── airflow/
│   └── Dockerfile                        # Образ Airflow (DAGs вшиты в image)
│
├── src/antifraud/                        # Основной код (Clean Architecture)
│   ├── config.py                         # Загрузка YAML + .env, подстановка ${VAR:-default}
│   │
│   ├── domain/
│   │   ├── models.py                     # Сущности: Transaction, Prediction, StoredPrediction
│   │   └── predictor.py                  # Загрузка модели, препроцессинг, инференс
│   │
│   ├── application/
│   │   ├── batch_predict.py              # Пакетный скоринг: S3 → модель → predict → S3
│   │   └── training/
│   │       ├── train_random_forest_model.py  # RandomForest (production)
│   │       ├── train_gradient_boosting_model.py
│   │       ├── train_baseline.py             # Logistic Regression (baseline)
│   │       ├── evaluate_model.py             # PR-AUC, precision, recall
│   │       ├── register_model.py             # Upload модели в S3
│   │       └── utils.py                      # load_and_preprocess_data, feature engineering
│   │
│   ├── infrastructure/
│   │   ├── data_processing/
│   │   │   ├── extract.py                # Извлечение данных из S3
│   │   │   ├── validate.py               # Валидация входных данных
│   │   │   ├── build_features.py         # Feature engineering для batch
│   │   │   └── make_splits.py            # Train/test split
│   │   └── storage/
│   │       ├── postgres.py               # get_connection(), init_db(), save_batch_predictions()
│   │       ├── s3.py                     # get_s3_client(), upload_model(), download_model()
│   │       ├── s3_io.py                  # s3_download(), s3_upload() — передача артефактов между тасками
│   │       ├── save_predictions.py       # CLI: S3 → Postgres (идемпотентно)
│   │       └── create_database.py        # Инициализация таблицы predictions
│   │
│   └── interfaces/
│       ├── online/
│       │   ├── main.py                   # Создание FastAPI-приложения
│       │   ├── routes.py                 # /, /health, /predict, /model/info
│       │   └── schemas.py               # Pydantic-схемы запросов и ответов
│       └── batch/dags/
│           ├── batch_prediction_dag.py   # DAG скоринга (@daily)
│           └── fraud_training_dag.py     # DAG обучения (@weekly)
│
├── tests/unit/                           # Unit-тесты (pytest, coverage >= 80%)
│   ├── application/
│   │   ├── test_batch_predict.py
│   │   └── training/
│   │       ├── test_evaluate_model.py
│   │       ├── test_register_model.py
│   │       └── test_utils.py
│   ├── domain/
│   │   └── test_predictor.py
│   ├── infrastructure/
│   │   ├── test_config.py
│   │   ├── data_processing/
│   │   │   ├── test_extract.py
│   │   │   └── test_validate.py
│   │   └── storage/
│   │       ├── test_postgres.py
│   │       ├── test_s3.py
│   │       └── test_save_predictions.py
│   └── interfaces/online/
│       ├── test_routes.py
│       └── test_schemas.py
│
├── .env.example                          # Шаблон переменных окружения
├── docker-compose.yml                    # Dev-окружение
├── docker-compose.prod.yml               # Prod-окружение (GHCR-образы)
├── Makefile                              # build, lint, test, check, up, down, clean
├── pyproject.toml                        # Зависимости + настройки линтеров
├── uv.lock                               # Lockfile зависимостей
└── ML_system_design_doc.md               # Дизайн-документ ML-системы
```

## Online API

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/` | GET | Информация о сервисе |
| `/health` | GET | Healthcheck |
| `/predict` | POST | Скоринг транзакции (вероятность фрода + `is_fraud`) |
| `/model/info` | GET | Метаинформация о модели: тип, порог, путь |

## Локальный запуск

```bash
# 1. Подготовить окружение
cp .env.example .env
# Заполнить переменные в .env

# 2. Установить зависимости
uv sync --frozen --dev

# 3. Запустить сервисы (Docker Compose)
make up

# 4. Или запустить отдельно
uv run python services/online/main.py        # Online API на :8000
uv run python services/batch/main.py         # Batch-скоринг
```

## Команды (Makefile)

```bash
make check     # Все quality gates: lint + typecheck + tests (coverage >= 80%)
make lint      # flake8, isort, black, pylint
make format    # Автоформатирование (isort + black)
make typecheck # mypy
make test      # pytest
make test-cov  # pytest + coverage (fail-under=80)
make up        # Сборка и запуск (docker-compose)
make down      # Остановка
make clean     # Полная очистка (volumes, cache)
```

## CI/CD

| Workflow | Триггер | Что делает |
|----------|---------|-----------|
| `ci.yml` | push/PR на любую ветку | flake8, isort, black, pylint, mypy, pytest (coverage >= 80%) |
| `deploy.yml` | push в main | Сборка образов, деплой на k8s через SSH |
| `release-images.yml` | release | Публикация образов в GHCR |
| `rollback.yml` | manual | Откат на предыдущий стабильный тег |

Образы: `ghcr.io/shadxwkxw/antifraud-online`, `ghcr.io/shadxwkxw/antifraud-batch`, `ghcr.io/shadxwkxw/antifraud-airflow`.

## Качество кода

| Инструмент | Роль |
|------------|------|
| `flake8` | PEP 8, синтаксические ошибки |
| `isort` | Сортировка импортов (профиль `black`) |
| `black` | Автоформатирование (`line-length = 100`) |
| `pylint` | Статический анализ качества |
| `mypy` | Проверка аннотаций типов (Python 3.11) |
| `pytest-cov` | Покрытие тестами (порог 80%, текущее ~93%) |

## Конфигурация

Централизована в `configs/config.yaml` с подстановкой переменных окружения:

```yaml
postgres:
  host: ${POSTGRES_HOST:-localhost}
  port: ${POSTGRES_PORT:-5432}
  database: ${POSTGRES_DB:-antifraud}
  sslmode: ${POSTGRES_SSLMODE:-disable}

model:
  type: random_forest
  threshold: 0.32

s3:
  bucket: antifraud-models
```

Env-переменные прокидываются: GitHub Secrets → CI → k8s Secret → `env_from` в Pod → `os.environ` → `config.py` подставляет через regex.

## Метрики модели

- **Primary metric**: PR-AUC
- **Target Recall**: >= 80%
- **Target Precision**: >= 40%
- **Threshold**: 0.32 (настраивается в `config.yaml`)
