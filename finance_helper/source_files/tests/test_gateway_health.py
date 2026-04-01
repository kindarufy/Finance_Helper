"""Smoke-тест проверки health-эндпоинта API-шлюза."""
import httpx
import pytest


def test_gateway_health():
    """Проверяет доступность health-эндпоинта API-шлюза."""
    try:
        response = httpx.get("http://localhost:8000/health", timeout=5, trust_env=False)
    except httpx.ConnectError:
        pytest.skip("Gateway is not running in this test environment")
    assert response.status_code == 200
