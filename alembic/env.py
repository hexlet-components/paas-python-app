"""Окружение Alembic: подключение к базе и блокировка на время миграций."""

import os

from alembic import context
from sqlalchemy import Connection, text

from db import create_db_engine

# Alembic сам базу не блокирует. Транзакционная advisory-блокировка с
# постоянным ключом не даёт двум экземплярам приложения применять миграции
# одновременно: второй ждёт, пока первый закончит, и затем видит, что новых
# миграций нет. PostgreSQL снимает блокировку в конце транзакции.
MIGRATION_LOCK_KEY = 7_200_202_611


def run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        connection.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": MIGRATION_LOCK_KEY}
        )
        context.run_migrations()


# Приложение передаёт своё подключение, команда alembic в терминале
# подключается по DATABASE_URL.
connection = context.config.attributes.get("connection")
if connection is not None:
    run_migrations(connection)
else:
    with create_db_engine(os.environ["DATABASE_URL"]).connect() as connection:
        run_migrations(connection)
