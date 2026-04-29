"""Скрипт для быстрого наполнения системы демонстрационными данными через API-шлюз."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:8000").rstrip("/")
API_KEY = os.getenv("INTERNAL_API_KEY", "change_me")
TELEGRAM_ID = int(os.getenv("DEMO_TELEGRAM_ID", "123456789"))
USERNAME = os.getenv("DEMO_TELEGRAM_USERNAME", "demo_user")


def request(method: str, path: str, payload: dict | None = None, params: dict | None = None):
    """Выполняет HTTP-запрос к API-шлюзу и возвращает JSON-ответ."""
    url = f"{GATEWAY_URL}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = None
    headers = {"X-API-Key": API_KEY}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {detail}") from exc


def main() -> int:
    """Создаёт демо-пользователя, категории, операции и лимиты для быстрого запуска проекта."""
    print("[seed-demo] upserting demo user")
    request("POST", "/users/upsert", {"telegram_id": TELEGRAM_ID, "username": USERNAME})
    active = request("GET", "/workspaces/active", params={"telegram_id": TELEGRAM_ID})
    workspace_id = active["id"]

    # Создаём базовые категории для демо-пользователя
    for category in [
        {"name": "Еда", "type": "expense", "emoji": "🍔"},
        {"name": "Транспорт", "type": "expense", "emoji": "🚇"},
        {"name": "Подписки", "type": "expense", "emoji": "💳"},
        {"name": "Зарплата", "type": "income", "emoji": "💰"},
    ]:
        try:
            request("POST", "/categories", {"telegram_id": TELEGRAM_ID, "workspace_id": workspace_id, **category})
        except RuntimeError:
            pass

    today = date.today()
    operations = [
        {"type": "income", "amount": 120000, "currency": "RUB", "category": "Зарплата", "comment": "основной доход", "occurred_at": today.replace(day=1).isoformat()},
        {"type": "expense", "amount": 320, "currency": "RUB", "category": "Еда", "comment": "кофе", "occurred_at": today.isoformat()},
        {"type": "expense", "amount": 1490, "currency": "RUB", "category": "Подписки", "comment": "music streaming", "occurred_at": (today - timedelta(days=2)).isoformat()},
        {"type": "expense", "amount": 780, "currency": "RUB", "category": "Транспорт", "comment": "такси", "occurred_at": (today - timedelta(days=1)).isoformat()},
    ]
    for op in operations:
        request("POST", "/operations", {"telegram_id": TELEGRAM_ID, "workspace_id": workspace_id, **op})

    print("[seed-demo] setting budget limits")
    request("POST", "/users/setlimit", {"telegram_id": TELEGRAM_ID, "daily_limit": 3000})
    request(
        "POST",
        "/budgets/limits",
        {
            "telegram_id": TELEGRAM_ID,
            "workspace_id": workspace_id,
            "period": "monthly",
            "amount": 60000,
            "currency": "RUB",
        },
    )

    print(f"[seed-demo] done for telegram_id={TELEGRAM_ID}, workspace_id={workspace_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
