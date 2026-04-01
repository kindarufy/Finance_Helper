"""Настройки API-шлюза: адреса сервисов, внутренний ключ и секрет подписи Mini App."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Настройки API-шлюза, которые считываются из переменных окружения."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    internal_api_key: str = Field(default="change_me", validation_alias="INTERNAL_API_KEY")
    finance_url: str = Field(default="http://finance-service:8001", validation_alias="FINANCE_URL")
    analytics_url: str = Field(default="http://analytics-service:8002", validation_alias="ANALYTICS_URL")
    miniapp_signing_secret: str = Field(default="change_me", validation_alias="MINIAPP_SIGNING_SECRET")

settings = Settings()
