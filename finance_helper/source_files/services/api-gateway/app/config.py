"""Настройки API-шлюза: адреса сервисов, внутренний ключ и секрет подписи Mini App."""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Настройки API-шлюза, которые считываются из переменных окружения."""
    model_config = SettingsConfigDict(env_file=(ROOT_ENV, ".env"), extra="ignore")

    internal_api_key: str = Field(default="change_me", validation_alias="INTERNAL_API_KEY")
    finance_url: str = Field(default="http://127.0.0.1:8001", validation_alias="FINANCE_URL")
    analytics_url: str = Field(default="http://127.0.0.1:8002", validation_alias="ANALYTICS_URL")
    miniapp_signing_secret: str = Field(default="change_me", validation_alias="MINIAPP_SIGNING_SECRET")


settings = Settings()
