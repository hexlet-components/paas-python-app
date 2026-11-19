"""Учебное приложение курса «Деплой на PaaS»."""

import html
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import sentry_sdk

HEADING = "Привет от Хекслета!"


def env(name: str, fallback: str) -> str:
    value = os.environ.get(name)
    return value if value else fallback


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        status = 200
        content_type = "text/plain; charset=utf-8"
        if self.path == "/":
            content_type = "text/html; charset=utf-8"
            message = html.escape(env("SERVER_MESSAGE", "Hello, PaaS!"))
            body = f"<h1>{HEADING}</h1><p>{message}</p>"
        elif self.path == "/error":
            status = 500
            body = "Oops! Something went wrong!"
            try:
                raise RuntimeError(body)
            except RuntimeError as error:
                sentry_sdk.capture_exception(error)
        else:
            status = 404
            body = "not found"
        payload = f"{body}\n".encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        print(f"{self.command} {self.path} {status}", flush=True)

    def log_message(self, format: str, *args: object) -> None:
        # Строку на каждый запрос печатает do_GET, стандартный журнал не нужен.
        pass


def create_server(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)


def main() -> None:
    # Без SENTRY_DSN SDK ничего не отправляет.
    sentry_sdk.init(dsn=os.environ.get("SENTRY_DSN"))
    port = int(env("PORT", "3000"))
    server = create_server(port)
    print(f"Listening on http://0.0.0.0:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
