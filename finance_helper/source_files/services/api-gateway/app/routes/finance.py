"""Маршруты API-шлюза для работы с пользователями, пространствами, категориями, операциями и лимитами."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Header, Query

from ..common import proxy_json
from ..config import settings
from ..security import require_internal_key

router = APIRouter()


@router.post("/users/upsert", dependencies=[Depends(require_internal_key)])
async def users_upsert(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует создание или обновление пользователя."""
    return await proxy_json("POST", f"{settings.finance_url}/users/upsert", x_api_key, json=payload)


@router.post("/users/setlimit", dependencies=[Depends(require_internal_key)])
async def users_setlimit(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует установку дневного лимита пользователя."""
    return await proxy_json("POST", f"{settings.finance_url}/users/setlimit", x_api_key, json=payload)


@router.get("/workspaces", dependencies=[Depends(require_internal_key)])
async def workspaces(telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение списка пространств пользователя."""
    return await proxy_json("GET", f"{settings.finance_url}/workspaces", x_api_key, params={"telegram_id": telegram_id})


@router.get("/workspaces/active", dependencies=[Depends(require_internal_key)])
async def get_active_workspace(telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение активного пространства пользователя."""
    return await proxy_json("GET", f"{settings.finance_url}/workspaces/active", x_api_key, params={"telegram_id": telegram_id})


@router.post("/workspaces/active", dependencies=[Depends(require_internal_key)])
async def set_active_workspace(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует смену активного пространства пользователя."""
    return await proxy_json("POST", f"{settings.finance_url}/workspaces/active", x_api_key, json=payload)


@router.post("/workspaces", dependencies=[Depends(require_internal_key)])
async def create_workspace(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует создание нового пространства."""
    return await proxy_json("POST", f"{settings.finance_url}/workspaces", x_api_key, json=payload)


@router.get("/workspaces/{workspace_id}/members", dependencies=[Depends(require_internal_key)])
async def workspace_members(workspace_id: int, telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение участников пространства."""
    return await proxy_json("GET", f"{settings.finance_url}/workspaces/{workspace_id}/members", x_api_key, params={"telegram_id": telegram_id})


@router.post("/workspaces/{workspace_id}/members", dependencies=[Depends(require_internal_key)])
async def add_workspace_member(workspace_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует добавление участника в пространство."""
    return await proxy_json("POST", f"{settings.finance_url}/workspaces/{workspace_id}/members", x_api_key, json=payload)


@router.patch("/workspaces/{workspace_id}/members/{member_telegram_id}", dependencies=[Depends(require_internal_key)])
async def update_workspace_member(workspace_id: int, member_telegram_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Обновляет участника пространства."""
    return await proxy_json("PATCH", f"{settings.finance_url}/workspaces/{workspace_id}/members/{member_telegram_id}", x_api_key, json=payload)


@router.delete("/workspaces/{workspace_id}/members/{member_telegram_id}", dependencies=[Depends(require_internal_key)])
async def delete_workspace_member(workspace_id: int, member_telegram_id: int, telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Удаляет участника пространства."""
    return await proxy_json("DELETE", f"{settings.finance_url}/workspaces/{workspace_id}/members/{member_telegram_id}", x_api_key, params={"telegram_id": telegram_id})


@router.get("/categories", dependencies=[Depends(require_internal_key)])
async def categories(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    category_type: str | None = Query(None),
    include_archived: bool = Query(False),
    x_api_key: str = Header(alias="X-API-Key"),
):
    """Проксирует получение категорий пространства."""
    params: dict[str, object] = {"telegram_id": telegram_id, "include_archived": include_archived}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if category_type is not None:
        params["category_type"] = category_type
    return await proxy_json("GET", f"{settings.finance_url}/categories", x_api_key, params=params)


@router.post("/categories", dependencies=[Depends(require_internal_key)])
async def create_category(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует создание категории."""
    return await proxy_json("POST", f"{settings.finance_url}/categories", x_api_key, json=payload)


@router.patch("/categories/{category_id}", dependencies=[Depends(require_internal_key)])
async def update_category(category_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует обновление категории."""
    return await proxy_json("PATCH", f"{settings.finance_url}/categories/{category_id}", x_api_key, json=payload)


@router.get("/categories/{category_id}/aliases", dependencies=[Depends(require_internal_key)])
async def category_aliases(category_id: int, telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение ключевых слов категории."""
    return await proxy_json("GET", f"{settings.finance_url}/categories/{category_id}/aliases", x_api_key, params={"telegram_id": telegram_id})


@router.post("/categories/{category_id}/aliases", dependencies=[Depends(require_internal_key)])
async def create_alias(category_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует добавление ключевого слова категории."""
    return await proxy_json("POST", f"{settings.finance_url}/categories/{category_id}/aliases", x_api_key, json=payload)


@router.delete("/aliases/{alias_id}", dependencies=[Depends(require_internal_key)])
async def delete_alias(alias_id: int, telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует удаление ключевого слова категории."""
    return await proxy_json("DELETE", f"{settings.finance_url}/aliases/{alias_id}", x_api_key, params={"telegram_id": telegram_id})


@router.post("/categories/match", dependencies=[Depends(require_internal_key)])
async def match_category(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует подбор категории по тексту операции."""
    return await proxy_json("POST", f"{settings.finance_url}/categories/match", x_api_key, json=payload)


@router.post("/operations", dependencies=[Depends(require_internal_key)])
async def operations_create(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует создание операции."""
    return await proxy_json("POST", f"{settings.finance_url}/operations", x_api_key, json=payload)


@router.get("/operations", dependencies=[Depends(require_internal_key)])
async def operations_list(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    op_type: str | None = Query(None),
    category_id: int | None = Query(None),
    category_name: str | None = Query(None),
    user_telegram_id: int | None = Query(None),
    actor_telegram_id: int | None = Query(None),
    search: str | None = Query(None),
    x_api_key: str = Header(alias="X-API-Key"),
):
    """Проксирует получение списка операций с фильтрами и пагинацией."""
    params: dict[str, object] = {"telegram_id": telegram_id, "limit": limit, "offset": offset}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if date_from:
        params["date_from"] = date_from.isoformat()
    if date_to:
        params["date_to"] = date_to.isoformat()
    if op_type:
        params["op_type"] = op_type
    if category_id is not None:
        params["category_id"] = category_id
    if category_name:
        params["category_name"] = category_name
    if user_telegram_id is not None:
        params["user_telegram_id"] = user_telegram_id
    if actor_telegram_id is not None:
        params["actor_telegram_id"] = actor_telegram_id
    if search:
        params["search"] = search
    return await proxy_json("GET", f"{settings.finance_url}/operations", x_api_key, params=params)


@router.patch("/operations/{op_id}", dependencies=[Depends(require_internal_key)])
async def operations_update(op_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует обновление операции."""
    return await proxy_json("PATCH", f"{settings.finance_url}/operations/{op_id}", x_api_key, json=payload)


@router.delete("/operations/{op_id}", dependencies=[Depends(require_internal_key)])
async def operations_delete(op_id: int, telegram_id: int = Query(...), workspace_id: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует удаление операции."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("DELETE", f"{settings.finance_url}/operations/{op_id}", x_api_key, params=params)


@router.get("/limits", dependencies=[Depends(require_internal_key)])
async def limits(telegram_id: int = Query(...), workspace_id: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение списка лимитов."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.finance_url}/limits", x_api_key, params=params)


@router.get("/limits/overview", dependencies=[Depends(require_internal_key)])
async def limits_overview(telegram_id: int = Query(...), workspace_id: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение сводки по лимитам."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.finance_url}/limits/overview", x_api_key, params=params)


@router.post("/limits", dependencies=[Depends(require_internal_key)])
async def create_limit(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует создание бюджетного лимита."""
    return await proxy_json("POST", f"{settings.finance_url}/limits", x_api_key, json=payload)


@router.get("/report-schedules", dependencies=[Depends(require_internal_key)])
async def report_schedules(telegram_id: int = Query(...), workspace_id: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение расписаний отчётов."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.finance_url}/report-schedules", x_api_key, params=params)


@router.post("/report-schedules", dependencies=[Depends(require_internal_key)])
async def create_report_schedule(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует создание расписания отчёта."""
    return await proxy_json("POST", f"{settings.finance_url}/report-schedules", x_api_key, json=payload)


@router.get("/report-schedules/due", dependencies=[Depends(require_internal_key)])
async def due_report_schedules(run_date: date = Query(...), send_time: str = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение расписаний отчётов, готовых к отправке."""
    return await proxy_json("GET", f"{settings.finance_url}/report-schedules/due", x_api_key, params={"run_date": run_date.isoformat(), "send_time": send_time})


@router.post("/receipts", dependencies=[Depends(require_internal_key)])
async def create_receipt(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует создание записи о загруженном чеке."""
    return await proxy_json("POST", f"{settings.finance_url}/receipts", x_api_key, json=payload)


@router.post("/receipts/{receipt_id}/parse", dependencies=[Depends(require_internal_key)])
async def parse_receipt(receipt_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует сохранение результата распознавания чека."""
    return await proxy_json("POST", f"{settings.finance_url}/receipts/{receipt_id}/parse", x_api_key, json=payload)


@router.post("/receipts/{receipt_id}/confirm", dependencies=[Depends(require_internal_key)])
async def confirm_receipt(receipt_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует подтверждение чека и создание операции."""
    return await proxy_json("POST", f"{settings.finance_url}/receipts/{receipt_id}/confirm", x_api_key, json=payload)


@router.post("/statement-imports", dependencies=[Depends(require_internal_key)])
async def create_statement_import(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует создание записи импорта банковской выписки."""
    return await proxy_json("POST", f"{settings.finance_url}/statement-imports", x_api_key, json=payload)


@router.post("/statement-imports/{import_id}/complete", dependencies=[Depends(require_internal_key)])
async def complete_statement_import(import_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует завершение импорта банковской выписки."""
    return await proxy_json("POST", f"{settings.finance_url}/statement-imports/{import_id}/complete", x_api_key, json=payload)
