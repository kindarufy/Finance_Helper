"""Модуль маршрутов API-шлюза Finance Helper."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Header, Query

from ..common import proxy_json
from ..config import settings
from ..security import require_internal_key

router = APIRouter()


@router.get("/reports/summary", dependencies=[Depends(require_internal_key)])
async def report_summary(telegram_id: int = Query(...), workspace_id: int | None = Query(None), date_from: date | None = Query(None), date_to: date | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «report summary» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if date_from:
        params["date_from"] = date_from.isoformat()
    if date_to:
        params["date_to"] = date_to.isoformat()
    return await proxy_json("GET", f"{settings.analytics_url}/reports/summary", x_api_key, params=params)


@router.get("/reports/monthly", dependencies=[Depends(require_internal_key)])
async def report_monthly(telegram_id: int = Query(...), workspace_id: int | None = Query(None), year: int = Query(...), month: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «report monthly» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id, "year": year, "month": month}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.analytics_url}/reports/monthly", x_api_key, params=params)


@router.get("/analysis/spending", dependencies=[Depends(require_internal_key)])
async def analysis_spending(telegram_id: int = Query(...), workspace_id: int | None = Query(None), year: int = Query(...), month: int = Query(...), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «analysis spending» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id, "year": year, "month": month}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("GET", f"{settings.analytics_url}/analysis/spending", x_api_key, params=params)


@router.post("/notify/daily", dependencies=[Depends(require_internal_key)])
async def notify_daily(telegram_id: int = Query(...), workspace_id: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «notify daily» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    return await proxy_json("POST", f"{settings.analytics_url}/notify/daily", x_api_key, params=params)


@router.post("/notify/monthly", dependencies=[Depends(require_internal_key)])
async def notify_monthly(telegram_id: int = Query(...), workspace_id: int | None = Query(None), year: int | None = Query(None), month: int | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «notify monthly» в рамках логики Finance Helper."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if year is not None:
        params["year"] = year
    if month is not None:
        params["month"] = month
    return await proxy_json("POST", f"{settings.analytics_url}/notify/monthly", x_api_key, params=params)


@router.post("/notify/monthly/run-due", dependencies=[Depends(require_internal_key)])
async def notify_monthly_run_due(run_date: date | None = Query(None), send_time: str | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Выполняет действие «notify monthly run due» в рамках логики Finance Helper."""
    params: dict[str, object] = {}
    if run_date is not None:
        params["run_date"] = run_date.isoformat()
    if send_time is not None:
        params["send_time"] = send_time
    return await proxy_json("POST", f"{settings.analytics_url}/notify/monthly/run-due", x_api_key, params=params)
