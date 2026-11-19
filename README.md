<div align="center">

<a href="https://hexlet.io/?utm_source=github&utm_medium=link&utm_campaign=paas-python-app">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Hexlet/brand-assets/master/images/svg/hexlet_wordmark_white_rus.svg">
        <img src="https://raw.githubusercontent.com/Hexlet/brand-assets/master/images/svg/hexlet_wordmark_primary_rus.svg" alt="Хекслет" height="64">
    </picture>
</a>

# Python-приложение для курса «Деплой на PaaS»

[![CI](https://github.com/hexlet-components/paas-python-app/actions/workflows/main.yml/badge.svg)](https://github.com/hexlet-components/paas-python-app/actions/workflows/main.yml)
[![Check](https://github.com/hexlet-components/paas-python-app/actions/workflows/check.yml/badge.svg)](https://github.com/hexlet-components/paas-python-app/actions/workflows/check.yml)

</div>

Компонент создаёт и поддерживает команда [Хекслета](https://hexlet.io/?utm_source=github&utm_medium=link&utm_campaign=paas-python-app), образовательного проекта.

Учебное приложение курса [«Деплой на PaaS»](https://ru.hexlet.io/courses/paas-deploy) для тех, кто проходит курс на Python. Студент делает fork, публикует приложение на Render и учится на нём конфигурации, обновлениям и диагностике. Такие же приложения есть для других стеков курса, у всех одинаковое поведение по HTTP. Изменение маршрутов, ответов или формата лога ломает шаги курса, поэтому такие правки сначала сверяются с уроками.

## Поведение

| Запрос | Ответ |
| --- | --- |
| `GET /` | `200`, заголовок «Привет от Хекслета!» и значение `SERVER_MESSAGE` |
| `GET /error` | `500`, событие уходит в Sentry, процесс продолжает работать |
| другой путь | `404` |

Приложение написано на [FastAPI](https://fastapi.tiangolo.com/) и работает под сервером [uvicorn](https://uvicorn.dev/). Оно слушает `0.0.0.0` на порту из `PORT` (по умолчанию `3000`) и печатает строку `GET / 200` на каждый запрос, стандартный access log uvicorn выключен флагом `--no-access-log`. Sentry SDK с интеграцией FastAPI включается переменной `SENTRY_DSN`, без неё события не отправляются.

## Публикация на Render

| Поле | Значение |
| --- | --- |
| Language | Python |
| Build Command | `pip install uv && uv sync --frozen --no-dev` |
| Start Command | `uv run --no-sync uvicorn app:app --host 0.0.0.0 --port $PORT --no-access-log` |
| Environment | `PORT=3000`, `SERVER_MESSAGE`, по желанию `SENTRY_DSN` |

Версию Python задаёт файл `.python-version`.

## Запуск

```sh
mise run setup
mise run test
PORT=3000 SERVER_MESSAGE="Первая публикация" mise run start
```

`make build` и `make start` повторяют Build Command и Start Command из таблицы выше, `start` перед запуском сам выполняет `build`. Эти две цели работают без mise, нужен только рантайм стека.

`make <задача>` вызывает ту же задачу mise.

## Проверки

`mise run check` гоняет тот же набор, что CI: ruff, ty, OSV-Scanner, разметку, опечатки, ссылки, workflows и секреты.
