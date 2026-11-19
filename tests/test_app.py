import pytest
from fastapi.testclient import TestClient

import app as app_module


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SERVER_MESSAGE", "Первая <публикация>")
    return TestClient(app_module.app)


def test_home_shows_heading_and_escaped_message(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.text == (
        "<h1>Привет от Хекслета!</h1><p>Первая &lt;публикация&gt;</p>\n"
    )


@pytest.mark.parametrize("value", [None, ""])
def test_home_falls_back_to_default_message(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv("SERVER_MESSAGE")
    else:
        monkeypatch.setenv("SERVER_MESSAGE", value)
    assert "<p>Hello, PaaS!</p>" in client.get("/").text


def test_error_goes_to_sentry_and_app_keeps_working(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[BaseException] = []
    monkeypatch.setattr(app_module.sentry_sdk, "capture_exception", captured.append)
    response = client.get("/error")
    assert response.status_code == 500
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "Oops! Something went wrong!\n"
    assert [str(error) for error in captured] == ["Oops! Something went wrong!"]
    assert client.get("/").status_code == 200


@pytest.mark.parametrize("path", ["/missing", "/docs", "/openapi.json"])
def test_unknown_path(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 404
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.text == "not found\n"


def test_request_is_logged(
    client: TestClient, capsys: pytest.CaptureFixture[str]
) -> None:
    client.get("/")
    client.get("/error")
    client.get("/missing")
    assert capsys.readouterr().out.splitlines() == [
        "GET / 200",
        "GET /error 500",
        "GET /missing 404",
    ]
