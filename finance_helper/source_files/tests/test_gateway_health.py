"""Smoke-тест проверки health-эндпоинта API-шлюза."""
import os

import httpx
import pytest

BASE_URL = os.getenv("TEST_GATEWAY_URL", "http://127.0.0.1:8000").rstrip("/")


def test_gateway_health():
    """Проверяет доступность health-эндпоинта API-шлюза."""
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=5, trust_env=False)
    except httpx.ConnectError:
        pytest.skip("Gateway is not running in this test environment")
    assert response.status_code == 200
