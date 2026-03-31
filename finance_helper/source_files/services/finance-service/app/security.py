"""Модуль финансового сервиса Finance Helper."""
from fastapi import Header, HTTPException
from .config import settings

def require_internal_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    # простой ключ
    """Выполняет действие «require internal key» в рамках логики Finance Helper."""
    if settings.internal_api_key and x_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid X-API-Key")
