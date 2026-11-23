"""Подключение к PostgreSQL, миграции и счётчик посещений главной страницы."""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

# Один запрос и создаёт строку счётчика, и увеличивает её, поэтому
# одновременные запросы не теряют посещения.
COUNT_VISIT = text(
    "INSERT INTO page_visits (path, total) VALUES ('/', 1) "
    "ON CONFLICT (path) DO UPDATE SET total = page_visits.total + 1 "
    "RETURNING total"
)


# Alembic пишет в лог, какие миграции применены при запуске.
alembic_log = logging.getLogger("alembic")
alembic_log.setLevel(logging.INFO)
alembic_log.addHandler(logging.StreamHandler())


def sqlalchemy_url(url: str) -> str:
    """Адрес postgresql://… из DATABASE_URL с драйвером psycopg для SQLAlchemy."""
    scheme, rest = url.split("://", 1)
    if scheme not in ("postgres", "postgresql"):
        raise ValueError(f"DATABASE_URL: неизвестная схема {scheme}")
    return f"postgresql+psycopg://{rest}"


def create_db_engine(url: str) -> Engine:
    return create_engine(sqlalchemy_url(url))


def migrate(engine: Engine) -> None:
    """Применяет новые миграции из alembic/versions, блокировку берёт env.py."""
    config = Config(toml_file=Path(__file__).with_name("pyproject.toml"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def count_visit(engine: Engine) -> int:
    """Увеличивает счётчик главной страницы и возвращает новое значение."""
    with engine.begin() as connection:
        return connection.execute(COUNT_VISIT).scalar_one()
