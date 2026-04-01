"""FastAPI-приложение API-шлюза, которое объединяет маршруты финансов, аналитики, экспорта и Mini App."""
from fastapi import FastAPI

from .routes.analytics import router as analytics_router
from .routes.exports import router as exports_router
from .routes.finance import router as finance_router
from .routes.miniapp import router as miniapp_router

app = FastAPI(title="API Gateway", version="0.8-release-refactor")


@app.get("/health")
def health():
    """Возвращает ответ для проверки, что API-шлюз работает."""
    return {"status": "ok"}


app.include_router(finance_router)
app.include_router(analytics_router)
app.include_router(exports_router)
app.include_router(miniapp_router)
