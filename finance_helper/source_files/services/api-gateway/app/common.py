"""Общие вспомогательные функции API-шлюза: проксирование, ошибки и контекст Mini App."""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from .config import settings
from .miniapp_auth import verify_miniapp_token
from .proxy import forward


def raise_proxy_error(response):
    """Преобразует ошибку внутреннего сервиса в HTTP-ошибку шлюза."""
    raise HTTPException(status_code=response.status_code, detail=response.text)


async def proxy_json(method: str, url: str, x_api_key: str, *, params: dict | None = None, json: dict | None = None):
    """Проксирует JSON-запрос во внутренний сервис и возвращает разобранный ответ."""
    response = await forward(method, url, x_api_key=x_api_key, params=params, json=json)
    if response.status_code >= 400:
        raise_proxy_error(response)
    return response.json()


async def internal_get(url: str, x_api_key: str, params: dict | None = None):
    """Выполняет внутренний GET-запрос через общую функцию проксирования."""
    return await proxy_json("GET", url, x_api_key, params=params)


def miniapp_file() -> Path:
    """Возвращает путь к статическому файлу Mini App."""
    return Path(__file__).resolve().parent / "static" / "miniapp" / "index.html"


async def miniapp_context(token: str) -> tuple[int, int | None]:
    """Проверяет токен Mini App и извлекает telegram_id и workspace_id."""
    try:
        payload = verify_miniapp_token(token, settings.miniapp_signing_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return int(payload["telegram_id"]), payload.get("workspace_id")
