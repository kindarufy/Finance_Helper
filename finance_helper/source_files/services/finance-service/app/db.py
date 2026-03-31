"""Модуль финансового сервиса Finance Helper."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    """Класс «Base» описывает состояние или структуру данных данного модуля."""
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Возвращает данные для сценария «db»."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
