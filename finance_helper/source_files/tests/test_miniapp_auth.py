"""Тесты подписи и проверки токенов Mini App."""
# flake8: noqa: E402
# pyright: reportMissingImports=false

from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path, module_name: str):
    """Вспомогательная функция для загрузки модуля из указанного пути."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


gateway_auth = _load(ROOT / "services" / "api-gateway" / "app" / "miniapp_auth.py", "gateway_miniapp_auth")
bot_auth = _load(ROOT / "services" / "bot-service" / "app" / "miniapp_auth.py", "bot_miniapp_auth")


def test_miniapp_token_roundtrip_between_bot_and_gateway():
    """Проверяет полный цикл подписи и проверки токена Mini App между ботом и шлюзом."""
    token = bot_auth.sign_miniapp_token(telegram_id=123456, secret="secret123", workspace_id=99, ttl_seconds=3600)
    payload = gateway_auth.verify_miniapp_token(token, "secret123")
    assert payload["telegram_id"] == 123456
    assert payload["workspace_id"] == 99


def test_gateway_signed_token_verifies():
    """Проверяет, что токен, подписанный шлюзом, успешно проходит проверку."""
    token = gateway_auth.sign_miniapp_token(telegram_id=42, secret="another-secret", ttl_seconds=3600)
    payload = gateway_auth.verify_miniapp_token(token, "another-secret")
    assert payload["telegram_id"] == 42
