"""Маршруты API-шлюза для Mini App: выдача токена, bootstrap-данные и смена активного пространства."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import FileResponse

from ..common import internal_get, miniapp_context, miniapp_file, proxy_json, raise_proxy_error
from ..config import settings
from ..miniapp_auth import sign_miniapp_token
from ..proxy import forward
from ..security import require_internal_key

router = APIRouter()


@router.get("/miniapp/dashboard", dependencies=[Depends(require_internal_key)])
async def miniapp_dashboard(telegram_id: int = Query(...), workspace_id: int | None = Query(None), days: int = Query(30), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение данных дашборда Mini App."""
    params: dict[str, object] = {"telegram_id": telegram_id, "days": days}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.analytics_url}/miniapp/dashboard", x_api_key, params=params)


@router.get("/miniapp/timeseries", dependencies=[Depends(require_internal_key)])
async def miniapp_timeseries(telegram_id: int = Query(...), workspace_id: int | None = Query(None), date_from: date = Query(...), date_to: date = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует получение временного ряда для графика Mini App."""
    params: dict[str, object] = {"telegram_id": telegram_id, "date_from": date_from.isoformat(), "date_to": date_to.isoformat()}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.analytics_url}/miniapp/timeseries", x_api_key, params=params)


@router.get("/miniapp/app")
async def miniapp_app(token: str = Query(...)):
    """Открывает статический файл Mini App после проверки токена."""
    await miniapp_context(token)
    return FileResponse(miniapp_file())


@router.get("/miniapp/token", dependencies=[Depends(require_internal_key)])
async def miniapp_token(telegram_id: int = Query(...), workspace_id: int | None = Query(None), ttl_seconds: int = Query(43200, ge=300, le=172800)):
    """Выдаёт подписанный токен доступа для Mini App."""
    return {"token": sign_miniapp_token(telegram_id, settings.miniapp_signing_secret, workspace_id=workspace_id, ttl_seconds=ttl_seconds)}


@router.get("/miniapp/public/bootstrap")
async def miniapp_public_bootstrap(token: str = Query(...)):
    """Собирает стартовые данные Mini App для авторизованного пользователя."""
    telegram_id, workspace_id = await miniapp_context(token)
    x_api_key = settings.internal_api_key
    active = await internal_get(f"{settings.finance_url}/workspaces/active", x_api_key, {"telegram_id": telegram_id})
    effective_ws = int(active["id"]) if active else workspace_id
    workspaces = await internal_get(f"{settings.finance_url}/workspaces", x_api_key, {"telegram_id": telegram_id})
    today = date.today()
    year, month = today.year, today.month
    timeline_from = today - timedelta(days=29)
    dashboard = await internal_get(f"{settings.analytics_url}/miniapp/dashboard", x_api_key, {"telegram_id": telegram_id, "workspace_id": effective_ws, "days": 30})
    monthly = await internal_get(f"{settings.analytics_url}/reports/monthly", x_api_key, {"telegram_id": telegram_id, "workspace_id": effective_ws, "year": year, "month": month})
    timeline = await internal_get(f"{settings.analytics_url}/miniapp/timeseries", x_api_key, {"telegram_id": telegram_id, "workspace_id": effective_ws, "date_from": timeline_from.isoformat(), "date_to": today.isoformat()})
    limits = await internal_get(f"{settings.finance_url}/limits/overview", x_api_key, {"telegram_id": telegram_id, "workspace_id": effective_ws})
    analysis = await internal_get(f"{settings.analytics_url}/analysis/spending", x_api_key, {"telegram_id": telegram_id, "workspace_id": effective_ws, "year": year, "month": month})
    members = await internal_get(f"{settings.finance_url}/workspaces/{effective_ws}/members", x_api_key, {"telegram_id": telegram_id})
    return {
        "active_workspace": active,
        "workspaces": workspaces,
        "dashboard": dashboard,
        "monthly_report": {**monthly, "base_currency": active.get("base_currency", "RUB") if active else "RUB"},
        "timeline": timeline,
        "limits": limits,
        "analysis": analysis,
        "members": members,
    }


@router.post("/miniapp/public/workspaces/active")
async def miniapp_public_set_active_workspace(payload: dict, token: str = Query(...)):
    """Меняет активное пространство из публичного Mini App."""
    telegram_id, _ = await miniapp_context(token)
    workspace_id = int(payload.get("workspace_id"))
    response = await forward(
        "POST",
        f"{settings.finance_url}/workspaces/active",
        x_api_key=settings.internal_api_key,
        json={"telegram_id": telegram_id, "workspace_id": workspace_id},
    )
    if response.status_code >= 400:
        raise_proxy_error(response)
    return response.json()
