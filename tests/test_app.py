import threading
import urllib.error
import urllib.request
from collections.abc import Iterator

import pytest

import app


@pytest.fixture
def base_url(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    monkeypatch.setenv("SERVER_MESSAGE", "Первая <публикация>")
    server = app.create_server(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def test_home_shows_heading_and_escaped_message(base_url: str) -> None:
    status, body = get(f"{base_url}/")
    assert status == 200
    assert "<h1>Привет от Хекслета!</h1>" in body
    assert "Первая &lt;публикация&gt;" in body


def test_error_then_home_still_works(
    base_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[BaseException] = []
    monkeypatch.setattr(app.sentry_sdk, "capture_exception", captured.append)
    assert get(f"{base_url}/error") == (500, "Oops! Something went wrong!\n")
    assert len(captured) == 1
    assert get(f"{base_url}/")[0] == 200


def test_unknown_path(base_url: str) -> None:
    assert get(f"{base_url}/missing") == (404, "not found\n")


def test_request_is_logged(base_url: str, capsys: pytest.CaptureFixture[str]) -> None:
    get(f"{base_url}/missing")
    assert "GET /missing 404" in capsys.readouterr().out


def test_listens_on_all_interfaces() -> None:
    server = app.create_server(0)
    try:
        assert server.server_address[0] == "0.0.0.0"
    finally:
        server.server_close()
