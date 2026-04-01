"""Проверка внутреннего X-API-Key для служебных запросов к финансовому сервису."""
from fastapi import Header, HTTPException
from .config import settings

def require_internal_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    # Проверяем внутренний ключ для служебных запросов
    """Проверяет внутренний API-ключ в заголовке X-API-Key."""
    if settings.internal_api_key and x_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Invalid X-API-Key")
