"""Учебное приложение курса «Деплой на PaaS»."""

import asyncio
import html
import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

import db

HEADING = "Привет от Хекслета!"
ERROR_TEXT = "Oops! Something went wrong!"

# Без SENTRY_DSN SDK ничего не отправляет. Интеграции FastAPI и Starlette
# подключаются сами, когда эти пакеты установлены.
sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # С DATABASE_URL приложение сначала применяет миграции, и только потом
    # uvicorn начинает принимать запросы. Без неё оно работает без базы.
    url = os.environ.get("DATABASE_URL")
    if url:
        engine = db.create_db_engine(url)
        await asyncio.to_thread(db.migrate, engine)
        app.state.engine = engine
    yield


# Страницы документации FastAPI не входят в контракт: путь /docs отвечает 404.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


def env(name: str, fallback: str) -> str:
    value = os.environ.get(name)
    return value if value else fallback


@app.middleware("http")
async def log_request(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # Стандартный журнал uvicorn выключен флагом --no-access-log,
    # строку на каждый запрос печатаем сами.
    response = await call_next(request)
    target = request.url.path
    if request.url.query:
        target = f"{target}?{request.url.query}"
    print(f"{request.method} {target} {response.status_code}", flush=True)
    return response


def failure() -> Response:
    return PlainTextResponse(f"{ERROR_TEXT}\n", status_code=500)


# Обычная функция вместо async: запрос к базе синхронный, и FastAPI выполняет
# такой обработчик в отдельном потоке.
@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> Response:
    message = html.escape(env("SERVER_MESSAGE", "Hello, PaaS!"))
    visits = ""
    # Без базы движка нет, и главная страница выходит без счётчика посещений.
    engine = getattr(request.app.state, "engine", None)
    if engine is not None:
        try:
            visits = f"<p>Посещений: {db.count_visit(engine)}</p>"
        except SQLAlchemyError as exc:
            # Сбой базы обрабатывается как ошибка /error: событие в Sentry и ответ 500.
            sentry_sdk.capture_exception(exc)
            return failure()
    return HTMLResponse(f"<h1>{HEADING}</h1><p>{message}</p>{visits}\n")


@app.get("/error", response_class=PlainTextResponse)
async def error() -> Response:
    try:
        raise RuntimeError(ERROR_TEXT)
    except RuntimeError as exc:
        sentry_sdk.capture_exception(exc)
    return failure()


@app.exception_handler(404)
async def not_found(_request: Request, _exc: HTTPException) -> Response:
    return PlainTextResponse("not found\n", status_code=404)
