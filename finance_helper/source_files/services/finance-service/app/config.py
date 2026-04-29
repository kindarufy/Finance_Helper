"""Настройки финансового сервиса: внутренний ключ и параметры подключения к PostgreSQL."""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Настройки финансового сервиса, которые считываются из переменных окружения."""
    model_config = SettingsConfigDict(env_file=(ROOT_ENV, ".env"), extra="ignore")

    internal_api_key: str = Field(default="change_me", validation_alias="INTERNAL_API_KEY")

    postgres_host: str = Field(default="127.0.0.1", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="finance_db", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="finance_user", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="finance_pass", validation_alias="POSTGRES_PASSWORD")

    @property
    def database_url(self) -> str:
        """Собирает строку подключения SQLAlchemy к PostgreSQL из настроек сервиса."""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
