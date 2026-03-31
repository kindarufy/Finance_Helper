"""Модуль сервисного слоя Telegram-бота Finance Helper."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


def _b64url_encode(data: bytes) -> str:
    """Выполняет действие «b64url encode» в рамках логики Finance Helper."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def sign_miniapp_token(telegram_id: int, secret: str, workspace_id: int | None = None, ttl_seconds: int = 3600 * 12) -> str:
    """Выполняет действие «sign miniapp token» в рамках логики Finance Helper."""
    payload: dict[str, Any] = {"telegram_id": int(telegram_id), "exp": int(time.time()) + int(ttl_seconds)}
    if workspace_id is not None:
        payload["workspace_id"] = int(workspace_id)
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()
    return f"{_b64url_encode(raw)}.{_b64url_encode(sig)}"
