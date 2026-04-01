"""Маршруты API-шлюза для выгрузки операций в CSV и XLSX."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import Response

from ..common import raise_proxy_error
from ..config import settings
from ..proxy import forward
from ..security import require_internal_key

router = APIRouter()


def _build_export_params(telegram_id: int, workspace_id: int | None, date_from: date | None, date_to: date | None, op_type: str | None) -> dict[str, object]:
    """Собирает параметры запроса для выгрузки операций."""
    params: dict[str, object] = {"telegram_id": telegram_id}
    if workspace_id is not None:
        params["workspace_id"] = workspace_id
    if date_from:
        params["date_from"] = date_from.isoformat()
    if date_to:
        params["date_to"] = date_to.isoformat()
    if op_type:
        params["op_type"] = op_type
    return params


@router.get("/exports/csv", dependencies=[Depends(require_internal_key)])
async def export_csv(telegram_id: int = Query(...), workspace_id: int | None = Query(None), date_from: date | None = Query(None), date_to: date | None = Query(None), op_type: str | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует выгрузку операций в CSV."""
    response = await forward("GET", f"{settings.analytics_url}/exports/csv", x_api_key=x_api_key, params=_build_export_params(telegram_id, workspace_id, date_from, date_to, op_type))
    if response.status_code >= 400:
        raise_proxy_error(response)
    return Response(content=response.content, media_type=response.headers.get("content-type"), headers={"Content-Disposition": response.headers.get("content-disposition", "attachment; filename=finance_export.csv")})


@router.get("/exports/xlsx", dependencies=[Depends(require_internal_key)])
async def export_xlsx(telegram_id: int = Query(...), workspace_id: int | None = Query(None), date_from: date | None = Query(None), date_to: date | None = Query(None), op_type: str | None = Query(None), x_api_key: str = Header(alias="X-API-Key")):
    """Проксирует выгрузку операций в XLSX."""
    response = await forward("GET", f"{settings.analytics_url}/exports/xlsx", x_api_key=x_api_key, params=_build_export_params(telegram_id, workspace_id, date_from, date_to, op_type))
    if response.status_code >= 400:
        raise_proxy_error(response)
    return Response(content=response.content, media_type=response.headers.get("content-type"), headers={"Content-Disposition": response.headers.get("content-disposition", "attachment; filename=finance_export.xlsx")})
