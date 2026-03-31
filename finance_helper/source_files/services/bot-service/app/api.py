"""Модуль сервисного слоя Telegram-бота Finance Helper."""
from __future__ import annotations

from datetime import date

import httpx

from .config import settings
from .miniapp_auth import sign_miniapp_token


def _headers() -> dict[str, str]:
    """Выполняет действие «headers» в рамках логики Finance Helper."""
    return {"X-API-Key": settings.internal_api_key}


async def upsert_user(telegram_id: int, username: str | None):
    """Выполняет действие «upsert user» в рамках логики Finance Helper."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{settings.gateway_url}/users/upsert",
            json={"telegram_id": telegram_id, "username": username},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


async def set_limit(telegram_id: int, daily_limit: float):
    """Выполняет действие «set limit» в рамках логики Finance Helper."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{settings.gateway_url}/users/setlimit",
            json={"telegram_id": telegram_id, "daily_limit": daily_limit},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


# ----------------------------
# Workspaces
# ----------------------------
async def list_workspaces(telegram_id: int):
    """Возвращает список сущностей для сценария «workspaces»."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{settings.gateway_url}/workspaces",
            params={"telegram_id": telegram_id},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


async def get_active_workspace(telegram_id: int):
    """Возвращает данные для сценария «active workspace»."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{settings.gateway_url}/workspaces/active",
            params={"telegram_id": telegram_id},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


async def set_active_workspace(telegram_id: int, workspace_id: int):
    """Выполняет действие «set active workspace» в рамках логики Finance Helper."""
    payload = {"telegram_id": telegram_id, "workspace_id": workspace_id}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{settings.gateway_url}/workspaces/active", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def create_workspace(
    telegram_id: int,
    name: str,
    workspace_type: str = "shared",
    base_currency: str = "RUB",
):
    """Создаёт сущность для сценария «workspace»."""
    payload = {
        "telegram_id": telegram_id,
        "name": name,
        "type": workspace_type,
        "base_currency": base_currency,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{settings.gateway_url}/workspaces", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def list_workspace_members(telegram_id: int, workspace_id: int):
    """Возвращает список сущностей для сценария «workspace members»."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{settings.gateway_url}/workspaces/{workspace_id}/members",
            params={"telegram_id": telegram_id},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


async def add_workspace_member(
    telegram_id: int,
    workspace_id: int,
    member_identifier: str,
    role: str = "editor",
):
    """Выполняет действие «add workspace member» в рамках логики Finance Helper."""
    payload = {
        "telegram_id": telegram_id,
        "member_identifier": member_identifier,
        "role": role,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{settings.gateway_url}/workspaces/{workspace_id}/members",
            json=payload,
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


async def update_workspace_member_role(telegram_id: int, workspace_id: int, member_telegram_id: int, role: str):
    """Обновляет данные в сценарии «workspace member role»."""
    payload = {"telegram_id": telegram_id, "role": role}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.patch(
            f"{settings.gateway_url}/workspaces/{workspace_id}/members/{member_telegram_id}",
            json=payload,
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


async def remove_workspace_member(telegram_id: int, workspace_id: int, member_telegram_id: int):
    """Удаляет сущность в сценарии «workspace member»."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.delete(
            f"{settings.gateway_url}/workspaces/{workspace_id}/members/{member_telegram_id}",
            params={"telegram_id": telegram_id},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


# ----------------------------
# Operations
# ----------------------------
async def create_operation(
    telegram_id: int,
    op_type: str,
    amount: float,
    category: str | None,
    comment: str | None,
    source: str | None,
    occurred_at: date | None,
    currency: str = "RUB",
    workspace_id: int | None = None,
    merchant: str | None = None,
    external_ref: str | None = None,
    is_imported: bool = False,
    receipt_upload_id: int | None = None,
    statement_import_id: int | None = None,
):
    """Создаёт сущность для сценария «operation»."""
    payload = {
        "telegram_id": telegram_id,
        "workspace_id": workspace_id,
        "type": op_type,
        "amount": amount,
        "currency": currency,
        "category": category,
        "comment": comment,
        "source": source,
        "merchant": merchant,
        "external_ref": external_ref,
        "is_imported": is_imported,
        "receipt_upload_id": receipt_upload_id,
        "statement_import_id": statement_import_id,
        "occurred_at": occurred_at.isoformat() if occurred_at else None,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{settings.gateway_url}/operations", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def list_operations_page(
    telegram_id: int,
    limit: int = 100,
    offset: int = 0,
    date_from: date | None = None,
    date_to: date | None = None,
    op_type: str | None = None,
    category_name: str | None = None,
    search: str | None = None,
    workspace_id: int | None = None,
    user_telegram_id: int | None = None,
):
    """Возвращает список сущностей для сценария «operations page»."""
    params: dict[str, object] = {"telegram_id": telegram_id, "limit": limit, "offset": offset}
    if date_from:
        params["date_from"] = date_from.isoformat()
    if date_to:
        params["date_to"] = date_to.isoformat()
    if op_type:
        params["op_type"] = op_type
    if category_name:
        params["category_name"] = category_name
    if search:
        params["search"] = search
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if user_telegram_id is not None:
        params["user_telegram_id"] = user_telegram_id

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{settings.gateway_url}/operations", params=params, headers=_headers())
        r.raise_for_status()
        return r.json().get("items", [])


async def list_operations(telegram_id: int, limit: int = 10, workspace_id: int | None = None):
    """Возвращает список сущностей для сценария «operations»."""
    return await list_operations_page(telegram_id=telegram_id, limit=limit, offset=0, workspace_id=workspace_id)


async def delete_operation(telegram_id: int, op_id: int, workspace_id: int | None = None):
    """Удаляет сущность в сценарии «operation»."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.delete(f"{settings.gateway_url}/operations/{op_id}", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


async def edit_operation(
    telegram_id: int,
    op_id: int,
    amount: float | None = None,
    comment: str | None = None,
    category: str | None = None,
    occurred_at: date | None = None,
    currency: str | None = None,
    workspace_id: int | None = None,
):
    """Выполняет действие «edit operation» в рамках логики Finance Helper."""
    payload: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        payload["workspace_id"] = workspace_id
    if amount is not None:
        payload["amount"] = amount
    if comment is not None:
        payload["comment"] = comment
    if category is not None:
        payload["category"] = category
    if occurred_at is not None:
        payload["occurred_at"] = occurred_at.isoformat()
    if currency is not None:
        payload["currency"] = currency
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.patch(f"{settings.gateway_url}/operations/{op_id}", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


# ----------------------------
# Categories
# ----------------------------
async def list_categories(
    telegram_id: int,
    category_type: str | None = None,
    include_archived: bool = False,
    workspace_id: int | None = None,
):
    """Возвращает список сущностей для сценария «categories»."""
    params: dict[str, object] = {"telegram_id": telegram_id, "include_archived": include_archived}
    if category_type:
        params["category_type"] = category_type
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{settings.gateway_url}/categories", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


async def create_category(
    telegram_id: int,
    name: str,
    category_type: str,
    emoji: str | None = None,
    workspace_id: int | None = None,
):
    """Создаёт сущность для сценария «category»."""
    payload: dict[str, object] = {"telegram_id": telegram_id, "name": name, "type": category_type, "emoji": emoji}
    if workspace_id is not None:
        payload["workspace_id"] = workspace_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{settings.gateway_url}/categories", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def update_category(
    telegram_id: int,
    category_id: int,
    name: str | None = None,
    emoji: str | None = None,
    is_archived: bool | None = None,
):
    """Обновляет данные в сценарии «category»."""
    payload: dict[str, object] = {"telegram_id": telegram_id}
    if name is not None:
        payload["name"] = name
    if emoji is not None:
        payload["emoji"] = emoji
    if is_archived is not None:
        payload["is_archived"] = is_archived
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.patch(f"{settings.gateway_url}/categories/{category_id}", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def list_aliases(telegram_id: int, category_id: int):
    """Возвращает список сущностей для сценария «aliases»."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{settings.gateway_url}/categories/{category_id}/aliases",
            params={"telegram_id": telegram_id},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


async def create_alias(telegram_id: int, category_id: int, alias: str):
    """Создаёт сущность для сценария «alias»."""
    payload = {"telegram_id": telegram_id, "alias": alias}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{settings.gateway_url}/categories/{category_id}/aliases", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def delete_alias(telegram_id: int, alias_id: int):
    """Удаляет сущность в сценарии «alias»."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.delete(f"{settings.gateway_url}/aliases/{alias_id}", params={"telegram_id": telegram_id}, headers=_headers())
        r.raise_for_status()
        return r.json()


async def match_category(telegram_id: int, text: str, op_type: str, workspace_id: int | None = None):
    """Выполняет действие «match category» в рамках логики Finance Helper."""
    payload = {"telegram_id": telegram_id, "workspace_id": workspace_id, "text": text, "type": op_type}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{settings.gateway_url}/categories/match", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


# ----------------------------
# Reports / analysis / exports / mini app
# ----------------------------
async def report_summary(telegram_id: int, date_from: str, date_to: str):
    """Выполняет действие «report summary» в рамках логики Finance Helper."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{settings.gateway_url}/reports/summary",
            params={"telegram_id": telegram_id, "date_from": date_from, "date_to": date_to},
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()


async def monthly_report(telegram_id: int, year: int, month: int, workspace_id: int | None = None):
    """Выполняет действие «monthly report» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id, "year": year, "month": month}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{settings.gateway_url}/reports/monthly", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


async def spending_analysis(telegram_id: int, year: int, month: int, workspace_id: int | None = None):
    """Выполняет действие «spending analysis» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id, "year": year, "month": month}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{settings.gateway_url}/analysis/spending", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


async def export_file(
    telegram_id: int,
    fmt: str,
    date_from: date | None = None,
    date_to: date | None = None,
    op_type: str | None = None,
    workspace_id: int | None = None,
) -> tuple[bytes, str, str]:
    """Выполняет действие «export file» в рамках логики Finance Helper."""
    endpoint = "/exports/csv" if fmt == "csv" else "/exports/xlsx"
    params: dict[str, object] = {"telegram_id": telegram_id}
    if date_from is not None:
        params["date_from"] = date_from.isoformat()
    if date_to is not None:
        params["date_to"] = date_to.isoformat()
    if op_type is not None:
        params["op_type"] = op_type
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{settings.gateway_url}{endpoint}", params=params, headers=_headers())
        r.raise_for_status()
        filename = "finance_export.csv" if fmt == "csv" else "finance_export.xlsx"
        cd = r.headers.get("content-disposition") or ""
        if "filename=" in cd:
            filename = cd.split("filename=", 1)[1].strip().strip('"')
        return r.content, filename, r.headers.get("content-type", "application/octet-stream")


async def build_miniapp_url(telegram_id: int, workspace_id: int | None = None) -> str:
    # local generation keeps bot-service independent from an extra gateway request
    """Собирает итоговую структуру или текст для сценария «miniapp url»."""
    token = sign_miniapp_token(
        telegram_id=telegram_id,
        secret=settings.miniapp_signing_secret,
        workspace_id=workspace_id,
    )
    separator = '&' if '?' in settings.miniapp_public_url else '?'
    return f"{settings.miniapp_public_url}{separator}token={token}"


async def notify_daily(telegram_id: int):
    """Выполняет действие «notify daily» в рамках логики Finance Helper."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{settings.gateway_url}/notify/daily", params={"telegram_id": telegram_id}, headers=_headers())
        r.raise_for_status()
        return r.json()


async def notify_monthly(telegram_id: int, year: int | None = None, month: int | None = None, workspace_id: int | None = None):
    """Выполняет действие «notify monthly» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if year is not None:
        params["year"] = year
    if month is not None:
        params["month"] = month
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(f"{settings.gateway_url}/notify/monthly", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


# ----------------------------
# Limits / budgets / schedules
# ----------------------------
async def list_limits(telegram_id: int, workspace_id: int | None = None):
    """Возвращает список сущностей для сценария «limits»."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{settings.gateway_url}/limits", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


async def limits_overview(telegram_id: int, workspace_id: int | None = None, ref_date: date | None = None):
    """Выполняет действие «limits overview» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if ref_date is not None:
        params["ref_date"] = ref_date.isoformat()
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{settings.gateway_url}/limits/overview", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


async def create_budget_limit(
    telegram_id: int,
    scope: str,
    period: str,
    amount: float,
    currency: str = "RUB",
    workspace_id: int | None = None,
    user_telegram_id: int | None = None,
    category_id: int | None = None,
):
    """Создаёт сущность для сценария «budget limit»."""
    payload: dict[str, object] = {
        "telegram_id": telegram_id,
        "scope": scope,
        "period": period,
        "amount": amount,
        "currency": currency,
        "notify_at_50": True,
        "notify_at_80": True,
        "notify_at_100": True,
    }
    if workspace_id is not None:
        payload["workspace_id"] = workspace_id
    if user_telegram_id is not None:
        payload["user_telegram_id"] = user_telegram_id
    if category_id is not None:
        payload["category_id"] = category_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{settings.gateway_url}/limits", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def list_report_schedules(telegram_id: int, workspace_id: int | None = None):
    """Возвращает список сущностей для сценария «report schedules»."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{settings.gateway_url}/report-schedules", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


async def upsert_report_schedule(
    telegram_id: int,
    day_of_month: int,
    send_time: str,
    timezone: str = "Europe/Moscow",
    enabled: bool = True,
    workspace_id: int | None = None,
    user_telegram_id: int | None = None,
):
    """Выполняет действие «upsert report schedule» в рамках логики Finance Helper."""
    payload: dict[str, object] = {
        "telegram_id": telegram_id,
        "frequency": "monthly",
        "day_of_month": day_of_month,
        "send_time": send_time,
        "timezone": timezone,
        "enabled": enabled,
    }
    if workspace_id is not None:
        payload["workspace_id"] = workspace_id
    if user_telegram_id is not None:
        payload["user_telegram_id"] = user_telegram_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{settings.gateway_url}/report-schedules", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


# ----------------------------
# Receipts / statement imports
# ----------------------------
async def create_receipt_upload(telegram_id: int, original_filename: str | None = None, telegram_file_id: str | None = None, storage_path: str | None = None, workspace_id: int | None = None):
    """Создаёт сущность для сценария «receipt upload»."""
    payload = {"telegram_id": telegram_id, "workspace_id": workspace_id, "original_filename": original_filename, "telegram_file_id": telegram_file_id, "storage_path": storage_path}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(f"{settings.gateway_url}/receipts", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def parse_receipt_upload(receipt_id: int, telegram_id: int, parsed_total: float | None = None, parsed_currency: str | None = None, parsed_merchant: str | None = None, parsed_date: date | None = None, raw_text: str | None = None, error_message: str | None = None, status: str = "parsed"):
    """Разбирает входные данные для сценария «receipt upload»."""
    payload = {
        "telegram_id": telegram_id,
        "parsed_total": parsed_total,
        "parsed_currency": parsed_currency,
        "parsed_merchant": parsed_merchant,
        "parsed_date": parsed_date.isoformat() if parsed_date else None,
        "raw_text": raw_text,
        "error_message": error_message,
        "status": status,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(f"{settings.gateway_url}/receipts/{receipt_id}/parse", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def confirm_receipt_upload(receipt_id: int, telegram_id: int, category: str | None = None, comment: str | None = None, currency: str | None = None, amount: float | None = None, occurred_at: date | None = None):
    """Выполняет действие «confirm receipt upload» в рамках логики Finance Helper."""
    payload = {
        "telegram_id": telegram_id,
        "category": category,
        "comment": comment,
        "currency": currency,
        "amount": amount,
        "occurred_at": occurred_at.isoformat() if occurred_at else None,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(f"{settings.gateway_url}/receipts/{receipt_id}/confirm", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def create_statement_import_record(telegram_id: int, original_filename: str | None = None, file_type: str | None = None, summary_text: str | None = None, workspace_id: int | None = None):
    """Создаёт сущность для сценария «statement import record»."""
    payload = {"telegram_id": telegram_id, "workspace_id": workspace_id, "original_filename": original_filename, "file_type": file_type, "summary_text": summary_text}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(f"{settings.gateway_url}/statement-imports", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()


async def complete_statement_import(import_id: int, telegram_id: int, imported_rows: int, skipped_rows: int, summary_text: str | None = None, error_message: str | None = None, status: str = "confirmed"):
    """Выполняет действие «complete statement import» в рамках логики Finance Helper."""
    payload = {
        "telegram_id": telegram_id,
        "imported_rows": imported_rows,
        "skipped_rows": skipped_rows,
        "summary_text": summary_text,
        "error_message": error_message,
        "status": status,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(f"{settings.gateway_url}/statement-imports/{import_id}/complete", json=payload, headers=_headers())
        r.raise_for_status()
        return r.json()
