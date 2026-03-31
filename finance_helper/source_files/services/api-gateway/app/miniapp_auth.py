"""Модуль API-шлюза Finance Helper."""
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


def _b64url_decode(data: str) -> bytes:
    """Выполняет действие «b64url decode» в рамках логики Finance Helper."""
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def sign_miniapp_token(telegram_id: int, secret: str, workspace_id: int | None = None, ttl_seconds: int = 3600 * 12) -> str:
    """Выполняет действие «sign miniapp token» в рамках логики Finance Helper."""
    payload: dict[str, Any] = {"telegram_id": int(telegram_id), "exp": int(time.time()) + int(ttl_seconds)}
    if workspace_id is not None:
        payload["workspace_id"] = int(workspace_id)
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()
    return f"{_b64url_encode(raw)}.{_b64url_encode(sig)}"


def verify_miniapp_token(token: str, secret: str) -> dict[str, Any]:
    """Выполняет действие «verify miniapp token» в рамках логики Finance Helper."""
    try:
        payload_part, sig_part = token.split('.', 1)
        raw = _b64url_decode(payload_part)
        provided_sig = _b64url_decode(sig_part)
    except Exception as exc:
        raise ValueError('invalid_token') from exc

    expected_sig = hmac.new(secret.encode('utf-8'), raw, hashlib.sha256).digest()
    if not hmac.compare_digest(provided_sig, expected_sig):
        raise ValueError('bad_signature')

    payload = json.loads(raw.decode('utf-8'))
    if int(payload.get('exp', 0)) < int(time.time()):
        raise ValueError('token_expired')
    if 'telegram_id' not in payload:
        raise ValueError('missing_telegram_id')
    return payload
