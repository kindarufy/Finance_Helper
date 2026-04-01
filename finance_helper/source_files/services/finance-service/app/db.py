"""Подключение SQLAlchemy к базе данных и выдача сессии для обработчиков финансового сервиса."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    """Базовый класс SQLAlchemy для всех ORM-моделей финансового сервиса."""
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Открывает сессию базы данных и закрывает её после завершения запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
