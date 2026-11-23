"""Тесты с базой идут, когда задан TEST_DATABASE_URL.

Например postgresql://postgres@localhost:5432/paas_test. База очищается.
"""

import os
from concurrent.futures import ProcessPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

import app as app_module
import db

URL = os.environ.get("TEST_DATABASE_URL", "")

pytestmark = pytest.mark.skipif(not URL, reason="TEST_DATABASE_URL не задан")


@pytest.fixture
def engine() -> Engine:
    engine = db.create_db_engine(URL)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS page_visits, alembic_version"))
    return engine


def start_instance(_: int) -> None:
    db.migrate(db.create_db_engine(URL))


def test_concurrent_migrations_apply_once(engine: Engine) -> None:
    # Экземпляры приложения это отдельные процессы. Потоки не подходят:
    # контекст Alembic общий на процесс.
    with ProcessPoolExecutor(max_workers=5) as pool:
        list(pool.map(start_instance, range(5)))

    with engine.connect() as connection:
        versions = connection.execute(text("SELECT version_num FROM alembic_version"))
        assert versions.scalars().all() == ["4cbeeae9b768"]


def test_home_counts_visits(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("SERVER_MESSAGE", "Первая публикация")
    # Контекстный менеджер запускает lifespan, то есть миграции.
    with TestClient(app_module.app) as client:
        for visit in (1, 2):
            assert client.get("/").text == (
                "<h1>Привет от Хекслета!</h1><p>Первая публикация</p>"
                f"<p>Посещений: {visit}</p>\n"
            )


def test_render_url_gets_psycopg_driver() -> None:
    assert (
        db.sqlalchemy_url("postgresql://paas_user@dpg-example-a/paas_demo")
        == "postgresql+psycopg://paas_user@dpg-example-a/paas_demo"
    )
