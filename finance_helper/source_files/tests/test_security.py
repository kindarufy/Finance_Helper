"""Тесты проверки внутреннего API-ключа на защищённых эндпоинтах."""
import os

import httpx
import pytest

BASE_URL = os.getenv("TEST_GATEWAY_URL", "http://127.0.0.1:8000").rstrip("/")


def test_protected_endpoint_without_api_key():
    """Проверяет, что защищённый эндпоинт недоступен без API-ключа."""
    try:
        response = httpx.get(
            f"{BASE_URL}/operations",
            params={"telegram_id": 1},
            timeout=5,
            trust_env=False,
        )
    except httpx.ConnectError:
        pytest.skip("Gateway is not running in this test environment")
    assert response.status_code == 401


def test_protected_endpoint_with_wrong_api_key():
    """Проверяет, что защищённый эндпоинт недоступен с неверным API-ключом."""
    try:
        response = httpx.get(
            f"{BASE_URL}/operations",
            params={"telegram_id": 1},
            headers={"X-API-Key": "wrong_key"},
            timeout=5,
            trust_env=False,
        )
    except httpx.ConnectError:
        pytest.skip("Gateway is not running in this test environment")
    assert response.status_code == 401
