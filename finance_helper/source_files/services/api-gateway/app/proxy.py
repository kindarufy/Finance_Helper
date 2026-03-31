"""Модуль API-шлюза Finance Helper."""
from __future__ import annotations
import httpx

async def forward(method: str, url: str, x_api_key: str, params=None, json=None) -> httpx.Response:
    """Выполняет действие «forward» в рамках логики Finance Helper."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await client.request(method, url, params=params, json=json, headers={"X-API-Key": x_api_key})
