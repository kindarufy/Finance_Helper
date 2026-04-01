"""Низкоуровневое проксирование HTTP-запросов из API-шлюза во внутренние сервисы."""
from __future__ import annotations
import httpx

async def forward(method: str, url: str, x_api_key: str, params=None, json=None) -> httpx.Response:
    """Выполняет HTTP-запрос во внутренний сервис и возвращает ответ без дополнительной обработки."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.request(method, url, params=params, json=json, headers={"X-API-Key": x_api_key})
