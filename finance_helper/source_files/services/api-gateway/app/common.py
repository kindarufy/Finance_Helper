"""Модуль API-шлюза Finance Helper."""
from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from .config import settings
from .miniapp_auth import verify_miniapp_token
from .proxy import forward


def raise_proxy_error(response):
    """Выполняет действие «raise proxy error» в рамках логики Finance Helper."""
    raise HTTPException(status_code=response.status_code, detail=response.text)


async def proxy_json(method: str, url: str, x_api_key: str, *, params: dict | None = None, json: dict | None = None):
    """Выполняет действие «proxy json» в рамках логики Finance Helper."""
    response = await forward(method, url, x_api_key=x_api_key, params=params, json=json)
    if response.status_code >= 400:
        raise_proxy_error(response)
    return response.json()


async def internal_get(url: str, x_api_key: str, params: dict | None = None):
    """Выполняет действие «internal get» в рамках логики Finance Helper."""
    return await proxy_json("GET", url, x_api_key, params=params)


def miniapp_file() -> Path:
    """Выполняет действие «miniapp file» в рамках логики Finance Helper."""
    return Path(__file__).resolve().parent / "static" / "miniapp" / "index.html"


async def miniapp_context(token: str) -> tuple[int, int | None]:
    """Выполняет действие «miniapp context» в рамках логики Finance Helper."""
    try:
        payload = verify_miniapp_token(token, settings.miniapp_signing_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return int(payload["telegram_id"]), payload.get("workspace_id")
