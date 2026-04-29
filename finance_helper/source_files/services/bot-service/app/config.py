"""Настройки Telegram-бота: токен, адрес шлюза, секрет Mini App и каталог загрузок."""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Настройки Telegram-бота, которые считываются из переменных окружения."""
    model_config = SettingsConfigDict(env_file=(ROOT_ENV, ".env"), extra="ignore")

    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    gateway_url: str = Field(default="http://127.0.0.1:8000", validation_alias="GATEWAY_URL")
    internal_api_key: str = Field(default="change_me", validation_alias="INTERNAL_API_KEY")
    miniapp_public_url: str = Field(default="", validation_alias="MINIAPP_PUBLIC_URL")
    miniapp_signing_secret: str = Field(default="change_me", validation_alias="MINIAPP_SIGNING_SECRET")
    upload_dir: str = Field(default="/data/finance_helper_uploads", validation_alias="UPLOAD_DIR")


settings = Settings()
