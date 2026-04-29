"""Настройки сервиса аналитики: адрес финансового сервиса, внутренний API-ключ и токен бота."""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Настройки сервиса аналитики, которые считываются из переменных окружения."""
    model_config = SettingsConfigDict(env_file=(ROOT_ENV, ".env"), extra="ignore")

    internal_api_key: str = Field(default="change_me", validation_alias="INTERNAL_API_KEY")
    finance_url: str = Field(default="http://127.0.0.1:8001", validation_alias="FINANCE_URL")
    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")


settings = Settings()
