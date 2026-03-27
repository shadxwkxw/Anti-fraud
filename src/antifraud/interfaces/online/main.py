from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.antifraud.interfaces.online.routes import router

app = FastAPI(
    title="Fraud Detection API",
    version="1.0",
)

app.include_router(router)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)
