"""Учебное приложение курса «Деплой на PaaS»."""

import html
import os
from collections.abc import Awaitable, Callable

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from starlette.exceptions import HTTPException

HEADING = "Привет от Хекслета!"

# Без SENTRY_DSN SDK ничего не отправляет. Интеграции FastAPI и Starlette
# подключаются сами, когда эти пакеты установлены.
sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"))

# Страницы документации FastAPI не входят в контракт: путь /docs отвечает 404.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


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


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    message = html.escape(env("SERVER_MESSAGE", "Hello, PaaS!"))
    return f"<h1>{HEADING}</h1><p>{message}</p>\n"


@app.get("/error", response_class=PlainTextResponse)
async def error() -> Response:
    body = "Oops! Something went wrong!"
    try:
        raise RuntimeError(body)
    except RuntimeError as exc:
        sentry_sdk.capture_exception(exc)
    return PlainTextResponse(f"{body}\n", status_code=500)


@app.exception_handler(404)
async def not_found(_request: Request, _exc: HTTPException) -> Response:
    return PlainTextResponse("not found\n", status_code=404)
