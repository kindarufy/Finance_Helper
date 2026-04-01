"""Настройки Telegram-бота: токен, адрес шлюза, секрет Mini App и каталог загрузок."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Настройки Telegram-бота, которые считываются из переменных окружения."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    gateway_url: str = Field(default="http://api-gateway:8000", validation_alias="GATEWAY_URL")
    internal_api_key: str = Field(default="change_me", validation_alias="INTERNAL_API_KEY")
    miniapp_public_url: str = Field(default="http://localhost:8000/miniapp/app", validation_alias="MINIAPP_PUBLIC_URL")
    miniapp_signing_secret: str = Field(default="change_me", validation_alias="MINIAPP_SIGNING_SECRET")
    upload_dir: str = Field(default="/tmp/finance_helper_uploads", validation_alias="UPLOAD_DIR")

settings = Settings()
