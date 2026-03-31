"""Модуль автоматических тестов проекта Finance Helper."""
import httpx
import pytest


def test_gateway_health():
    """Проверяет сценарий «gateway health»."""
    try:
        response = httpx.get("http://localhost:8000/health", timeout=5, trust_env=False)
    except httpx.ConnectError:
        pytest.skip("Gateway is not running in this test environment")
    assert response.status_code == 200
