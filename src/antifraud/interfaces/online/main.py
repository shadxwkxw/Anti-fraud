from fastapi import FastAPI

from src.antifraud.interfaces.online.routes import router

app = FastAPI(
    title="Fraud Detection API",
    description=(
        "REST-сервис для обнаружения мошеннических транзакций по кредитным картам.\n\n"
        "**Основные возможности:**\n"
        "- Скоринг одиночных и батчевых транзакций в реальном времени\n"
        "- Мониторинг состояния модели и базы данных\n\n"
        "Модель: Random Forest, обученная на Credit Card Fraud Detection dataset."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "predictions",
            "description": "Скоринг транзакций",
        },
        {
            "name": "model",
            "description": "Информация о загруженной ML-модели",
        },
        {
            "name": "system",
            "description": "Мониторинг и healthcheck",
        },
    ],
)

app.include_router(router)
