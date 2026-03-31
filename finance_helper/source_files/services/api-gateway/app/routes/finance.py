"""Модуль маршрутов API-шлюза Finance Helper."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Header, Query

from ..common import proxy_json
from ..config import settings
from ..security import require_internal_key

router = APIRouter()


@router.post("/users/upsert", dependencies=[Depends(require_internal_key)])
async def users_upsert(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «users upsert» в рамках логики Finance Helper."""
    return await proxy_json("POST", f"{settings.finance_url}/users/upsert", x_api_key, json=payload)


@router.post("/users/setlimit", dependencies=[Depends(require_internal_key)])
async def users_setlimit(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «users setlimit» в рамках логики Finance Helper."""
    return await proxy_json("POST", f"{settings.finance_url}/users/setlimit", x_api_key, json=payload)


@router.get("/workspaces", dependencies=[Depends(require_internal_key)])
async def workspaces(telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «workspaces» в рамках логики Finance Helper."""
    return await proxy_json("GET", f"{settings.finance_url}/workspaces", x_api_key, params={"telegram_id": telegram_id})


@router.get("/workspaces/active", dependencies=[Depends(require_internal_key)])
async def get_active_workspace(telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Возвращает данные для сценария «active workspace»."""
    return await proxy_json("GET", f"{settings.finance_url}/workspaces/active", x_api_key, params={"telegram_id": telegram_id})


@router.post("/workspaces/active", dependencies=[Depends(require_internal_key)])
async def set_active_workspace(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «set active workspace» в рамках логики Finance Helper."""
    return await proxy_json("POST", f"{settings.finance_url}/workspaces/active", x_api_key, json=payload)


@router.post("/workspaces", dependencies=[Depends(require_internal_key)])
async def create_workspace(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Создаёт сущность для сценария «workspace»."""
    return await proxy_json("POST", f"{settings.finance_url}/workspaces", x_api_key, json=payload)


@router.get("/workspaces/{workspace_id}/members", dependencies=[Depends(require_internal_key)])
async def workspace_members(workspace_id: int, telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «workspace members» в рамках логики Finance Helper."""
    return await proxy_json("GET", f"{settings.finance_url}/workspaces/{workspace_id}/members", x_api_key, params={"telegram_id": telegram_id})


@router.post("/workspaces/{workspace_id}/members", dependencies=[Depends(require_internal_key)])
async def add_workspace_member(workspace_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «add workspace member» в рамках логики Finance Helper."""
    return await proxy_json("POST", f"{settings.finance_url}/workspaces/{workspace_id}/members", x_api_key, json=payload)


@router.patch("/workspaces/{workspace_id}/members/{member_telegram_id}", dependencies=[Depends(require_internal_key)])
async def update_workspace_member(workspace_id: int, member_telegram_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Обновляет данные в сценарии «workspace member»."""
    return await proxy_json("PATCH", f"{settings.finance_url}/workspaces/{workspace_id}/members/{member_telegram_id}", x_api_key, json=payload)


@router.delete("/workspaces/{workspace_id}/members/{member_telegram_id}", dependencies=[Depends(require_internal_key)])
async def delete_workspace_member(workspace_id: int, member_telegram_id: int, telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Удаляет сущность в сценарии «workspace member»."""
    return await proxy_json("DELETE", f"{settings.finance_url}/workspaces/{workspace_id}/members/{member_telegram_id}", x_api_key, params={"telegram_id": telegram_id})


@router.get("/categories", dependencies=[Depends(require_internal_key)])
async def categories(
    telegram_id: int = Query(...),
    workspace_id: int | None = Query(None),
    category_type: str | None = Query(None),
    include_archived: bool = Query(False),
    x_api_key: str = Header(alias="X-API-Key"),
):
    """Выполняет действие «categories» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id, "include_archived": include_archived}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if category_type is not None:
        params["category_type"] = category_type
    return await proxy_json("GET", f"{settings.finance_url}/categories", x_api_key, params=params)


@router.post("/categories", dependencies=[Depends(require_internal_key)])
async def create_category(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Создаёт сущность для сценария «category»."""
    return await proxy_json("POST", f"{settings.finance_url}/categories", x_api_key, json=payload)


@router.patch("/categories/{category_id}", dependencies=[Depends(require_internal_key)])
async def update_category(category_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Обновляет данные в сценарии «category»."""
    return await proxy_json("PATCH", f"{settings.finance_url}/categories/{category_id}", x_api_key, json=payload)


@router.get("/categories/{category_id}/aliases", dependencies=[Depends(require_internal_key)])
async def category_aliases(category_id: int, telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «category aliases» в рамках логики Finance Helper."""
    return await proxy_json("GET", f"{settings.finance_url}/categories/{category_id}/aliases", x_api_key, params={"telegram_id": telegram_id})


@router.post("/categories/{category_id}/aliases", dependencies=[Depends(require_internal_key)])
async def create_alias(category_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Создаёт сущность для сценария «alias»."""
    return await proxy_json("POST", f"{settings.finance_url}/categories/{category_id}/aliases", x_api_key, json=payload)


@router.delete("/aliases/{alias_id}", dependencies=[Depends(require_internal_key)])
async def delete_alias(alias_id: int, telegram_id: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Удаляет сущность в сценарии «alias»."""
    return await proxy_json("DELETE", f"{settings.finance_url}/aliases/{alias_id}", x_api_key, params={"telegram_id": telegram_id})


@router.post("/categories/match", dependencies=[Depends(require_internal_key)])
async def match_category(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «match category» в рамках логики Finance Helper."""
    return await proxy_json("POST", f"{settings.finance_url}/categories/match", x_api_key, json=payload)


@router.post("/operations", dependencies=[Depends(require_internal_key)])
async def operations_create(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «operations create» в рамках логики Finance Helper."""
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
    """Выполняет действие «operations list» в рамках логики Finance Helper."""
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
    """Выполняет действие «operations update» в рамках логики Finance Helper."""
    return await proxy_json("PATCH", f"{settings.finance_url}/operations/{op_id}", x_api_key, json=payload)


@router.delete("/operations/{op_id}", dependencies=[Depends(require_internal_key)])
async def operations_delete(op_id: int, telegram_id: int = Query(...), workspace_id: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «operations delete» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("DELETE", f"{settings.finance_url}/operations/{op_id}", x_api_key, params=params)


@router.get("/limits", dependencies=[Depends(require_internal_key)])
async def limits(telegram_id: int = Query(...), workspace_id: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «limits» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.finance_url}/limits", x_api_key, params=params)


@router.get("/limits/overview", dependencies=[Depends(require_internal_key)])
async def limits_overview(telegram_id: int = Query(...), workspace_id: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «limits overview» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.finance_url}/limits/overview", x_api_key, params=params)


@router.post("/limits", dependencies=[Depends(require_internal_key)])
async def create_limit(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Создаёт сущность для сценария «limit»."""
    return await proxy_json("POST", f"{settings.finance_url}/limits", x_api_key, json=payload)


@router.get("/report-schedules", dependencies=[Depends(require_internal_key)])
async def report_schedules(telegram_id: int = Query(...), workspace_id: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «report schedules» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.finance_url}/report-schedules", x_api_key, params=params)


@router.post("/report-schedules", dependencies=[Depends(require_internal_key)])
async def create_report_schedule(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Создаёт сущность для сценария «report schedule»."""
    return await proxy_json("POST", f"{settings.finance_url}/report-schedules", x_api_key, json=payload)


@router.get("/report-schedules/due", dependencies=[Depends(require_internal_key)])
async def due_report_schedules(run_date: date = Query(...), send_time: str = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «due report schedules» в рамках логики Finance Helper."""
    return await proxy_json("GET", f"{settings.finance_url}/report-schedules/due", x_api_key, params={"run_date": run_date.isoformat(), "send_time": send_time})


@router.post("/receipts", dependencies=[Depends(require_internal_key)])
async def create_receipt(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Создаёт сущность для сценария «receipt»."""
    return await proxy_json("POST", f"{settings.finance_url}/receipts", x_api_key, json=payload)


@router.post("/receipts/{receipt_id}/parse", dependencies=[Depends(require_internal_key)])
async def parse_receipt(receipt_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Разбирает входные данные для сценария «receipt»."""
    return await proxy_json("POST", f"{settings.finance_url}/receipts/{receipt_id}/parse", x_api_key, json=payload)


@router.post("/receipts/{receipt_id}/confirm", dependencies=[Depends(require_internal_key)])
async def confirm_receipt(receipt_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «confirm receipt» в рамках логики Finance Helper."""
    return await proxy_json("POST", f"{settings.finance_url}/receipts/{receipt_id}/confirm", x_api_key, json=payload)


@router.post("/statement-imports", dependencies=[Depends(require_internal_key)])
async def create_statement_import(payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Создаёт сущность для сценария «statement import»."""
    return await proxy_json("POST", f"{settings.finance_url}/statement-imports", x_api_key, json=payload)


@router.post("/statement-imports/{import_id}/complete", dependencies=[Depends(require_internal_key)])
async def complete_statement_import(import_id: int, payload: dict, x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «complete statement import» в рамках логики Finance Helper."""
    return await proxy_json("POST", f"{settings.finance_url}/statement-imports/{import_id}/complete", x_api_key, json=payload)
