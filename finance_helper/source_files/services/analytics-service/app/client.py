"""HTTP-клиент сервиса аналитики для запросов к finance-service и отправки сообщений в Telegram."""
from __future__ import annotations

from datetime import date

import httpx

from .config import settings


def _headers() -> dict[str, str]:
    """Возвращает заголовки с внутренним API-ключом для межсервисных запросов."""
    return {"X-API-Key": settings.internal_api_key}


async def fetch_operations(
    telegram_id: int,
    workspace_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 5000,
    op_type: str | None = None,
    category_name: str | None = None,
    user_telegram_id: int | None = None,
    actor_telegram_id: int | None = None,
    search: str | None = None,
) -> list[dict]:
    """Постранично запрашивает операции из финансового сервиса с учётом переданных фильтров."""
    per_page = 200
    offset = 0
    result: list[dict] = []

    async with httpx.AsyncClient(timeout=20.0) as client:
        while len(result) < limit:
            take = min(per_page, limit - len(result))
            params: dict[str, object] = {"telegram_id": telegram_id, "limit": take, "offset": offset}
            if workspace_id is not None:
                params["workspace_id"] = workspace_id
            if date_from:
                params["date_from"] = date_from.isoformat()
            if date_to:
                params["date_to"] = date_to.isoformat()
            if op_type:
                params["op_type"] = op_type
            if category_name:
                params["category_name"] = category_name
            if user_telegram_id is not None:
                params["user_telegram_id"] = user_telegram_id
            if actor_telegram_id is not None:
                params["actor_telegram_id"] = actor_telegram_id
            if search:
                params["search"] = search

            r = await client.get(f"{settings.finance_url}/operations", params=params, headers=_headers())
            r.raise_for_status()
            payload = r.json()
            items = payload.get("items", [])
            result.extend(items)
            if len(items) < take:
                break
            offset += take
    return result


async def fetch_limit_overview(telegram_id: int, workspace_id: int | None = None, ref_date: date | None = None) -> list[dict]:
    """Запрашивает сводку по лимитам из финансового сервиса."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if ref_date is not None:
        params["ref_date"] = ref_date.isoformat()
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{settings.finance_url}/limits/overview", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


async def fetch_due_report_schedules(run_date: date, send_time: str) -> list[dict]:
    """Получает расписания отчётов, которые нужно отправить в указанное время."""
    params = {"run_date": run_date.isoformat(), "send_time": send_time}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{settings.finance_url}/report-schedules/due", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


async def send_telegram_message(chat_id: int, text: str) -> bool:
    """Отправляет текстовое сообщение пользователю через Bot API Telegram."""
    if not settings.bot_token:
        return False
    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(url, json={"chat_id": chat_id, "text": text})
        return r.status_code == 200
