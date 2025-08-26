# Task Manager API — FastAPI, SQLAlchemy, Alembic, pytest

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](#)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-AE2D2A.svg)](#)
[![Alembic](https://img.shields.io/badge/Alembic-migrations-4B8869.svg)](#)
[![Tests](https://img.shields.io/badge/tests-pytest%20%2B%20coverage-6C63FF.svg)](#)
[![CI](https://img.shields.io/badge/GitHub_Actions-ready-2088FF.svg)](#)

Сервис управления задачами на **FastAPI** с:
- CRUD API и UUID-идентификаторами
- **Единым Enum статусов** и **правилами переходов** с кодом **409 Conflict**
- **ETag/версирование** и заголовком **If-Match** с кодом **412 Precondition Failed**
- Расширенной пагинацией (`items` + `meta{total,offset,limit}`)
- Alembic-миграциями, Docker/Compose, health-check, CORS, структурированным логированием
- Контуром качества: `black`, `ruff`, `mypy`, `pytest`, GitHub Actions

---

## Содержание
- [Архитектура и структура](#архитектура-и-структура)
- [Доменные правила](#доменные-правила)
- [API: эндпоинты и примеры](#api-эндпоинты-и-примеры)
- [Ошибка и коды статусов](#ошибка-и-коды-статусов)
- [Быстрый старт](#быстрый-старт)
- [Конфигурация и окружение](#конфигурация-и-окружение)
- [Миграции БД](#миграции-бд)
- [Качество кода и CI](#качество-кода-и-ci)
- [Тестирование](#тестирование)
- [Наброски дорожной карты](#наброски-дорожной-карты)
- [FAQ / Траблшутинг](#faq--траблшутинг)

---

## Архитектура и структура

Лёгкая слойность: **schemas** (валидация/контракты), **models** (ORM), **crud** (бизнес-логика), **routers** (HTTP), **core** (настройки/логирование).

```
.
├── app   
│   ├── core   
│   │   ├── logging.py             # структура логов   
│   │   └── settings.py            # конфигурация (pydantic-settings)   
│   ├── database.py                # engine/session (SQLite/Postgres)   
│   ├── domain   
│   │   └── enums.py               # TaskStatus + правила переходов   
│   ├── exceptions.py              # Conflict(409), PreconditionFailed(412)   
│   ├── main.py                    # FastAPI app, CORS, health, routers   
│   ├── models.py                  # ORM-модели (timestamps, version)   
│   ├── routers   
│   │   └── tasks.py               # HTTP-роуты /tasks   
│   ├── crud.py                    # бизнес-операции и валидация переходов   
│   ├── deps.py                    # зависимости (DB session)   
│   └── schemas.py                 # Pydantic-схемы + пагинация/ошибки   
├── alembic                        # миграции   
│   ├── env.py   
│   └── versions/0001_create_tasks.py   
├── docs/adr/0001-status-and-etag.md   
├── tests/test_tasks.py   
├── entrypoint.sh   
├── docker-compose.yml   
├── Dockerfile   
├── pyproject.toml                 # black/ruff/mypy   
├── .pre-commit-config.yaml   
├── .github/workflows/ci.yml   
├── requirements.txt   
└── README.md   
```

### Диаграмма состояний (Mermaid)
```mermaid
stateDiagram-v2
    [*] --> created
    created --> in_progress
    created --> completed
    in_progress --> completed
    completed --> [*]
```

---

## Доменные правила

### Статусы задач
- `created`
- `in_progress`
- `completed`

### Допустимые переходы
- `created → in_progress | completed`
- `in_progress → completed`
- `completed → (нет переходов)`

Нарушение даёт **409 Conflict** с сообщением `Transition <old> → <new> is not allowed`.

### Конкурентные обновления (ETag/If-Match)
- Каждая задача имеет поле `version: int`.
- `GET /tasks/{id}` возвращает заголовок `ETag: <version>`.
- `PATCH /tasks/{id}` может (и рекомендуется) присылать `If-Match: <version>` — при несовпадении возвращается **412 Precondition Failed**.

---

## API: эндпоинты и примеры

### Базовые URL
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`
- OpenAPI JSON: `GET /openapi.json`

### Схемы данных

**TaskOut**
```json
{
  "id": "c8ab0d0b-4b0a-4f2a-bd8a-6c0d1b6b7a77",
  "title": "Написать тесты",
  "description": "Покрыть CRUD",
  "status": "in_progress",
  "created_at": "2025-08-26T10:00:00",
  "updated_at": "2025-08-26T10:05:00",
  "version": 2
}
```

**TaskListOut**
```json
{
  "items": [ /* массив TaskOut */ ],
  "meta": { "total": 42, "offset": 0, "limit": 20 }
}
```

### Эндпоинты

| Метод | Путь           | Описание                                   | Код(ы) |
|------:|----------------|--------------------------------------------|--------|
| POST  | `/tasks/`      | Создать задачу                             | 201, 422 |
| GET   | `/tasks/{id}`  | Получить задачу + заголовок `ETag`         | 200, 404 |
| GET   | `/tasks/`      | Список задач с `meta{total,offset,limit}`  | 200 |
| PATCH | `/tasks/{id}`  | Частичное обновление; `If-Match` поддержка | 200, 404, 409, 412, 422 |
| DELETE| `/tasks/{id}`  | Удалить задачу                             | 204, 404 |
| GET   | `/health`      | Пинг БД                                    | 200 |

### Примеры запросов (cURL)

**Создать**
```bash
curl -X POST http://localhost:8000/tasks/ \
  -H 'Content-Type: application/json' \
  -d '{"title":"Написать тесты","description":"Покрыть CRUD","status":"created"}'
```

**Получить + ETag**
```bash
curl -i http://localhost:8000/tasks/<id>
# ...
# ETag: 1
```

**PATCH с If-Match (успех)**
```bash
ETAG=$(curl -sI http://localhost:8000/tasks/<id> | awk '/ETag/ {print $2}' | tr -d '\r')
curl -X PATCH http://localhost:8000/tasks/<id> \
  -H "Content-Type: application/json" \
  -H "If-Match: $ETAG" \
  -d '{"status":"in_progress"}'
```

**PATCH с неверной версией (412)**
```bash
curl -X PATCH http://localhost:8000/tasks/<id> \
  -H "Content-Type: application/json" \
  -H "If-Match: 999" \
  -d '{"title":"Новый заголовок"}'
```

**Удалить**
```bash
curl -X DELETE http://localhost:8001/tasks/<id> -i
```

---

## Ошибка и коды статусов

Стандартная форма ошибки:
```json
{ "detail": "Человеко-читаемое сообщение" }
```

- **409 Conflict** — нарушение бизнес-правил (например, недопустимый переход статуса).
- **412 Precondition Failed** — несовпадение версии (`If-Match` ↔ `ETag`).
- **404 Not Found** — задача не найдена.
- **422 Unprocessable Entity** — ошибки валидации (Pydantic).

---

## Быстрый старт

### Вариант A — Локально (SQLite по умолчанию)
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head                                   # применить миграции
uvicorn app.main:app --reload
# Откройте http://127.0.0.1:8001/docs
```

### Вариант B — Docker Compose (Postgres)
```bash
docker compose up --build
# API: http://localhost:8001/docs
```
В этом режиме приложение использует `DATABASE_URL=postgresql+psycopg://task:task@db:5432/taskdb`.

---

## Конфигурация и окружение

Конфигурация через `pydantic-settings` (`app/core/settings.py`). По умолчанию читается из `.env` (опционально).

| Переменная         | По умолчанию          | Описание |
|-------------------:|-----------------------|----------|
| `DATABASE_URL`     | `sqlite:///./app.db`  | Строка подключения SQLAlchemy. Для Postgres используйте `postgresql+psycopg://user:pass@host:5432/db` |
| `DEBUG`            | `false`               | Уровень логирования/диагностики |
| CORS-параметры     | `*`                   | Настроены максимально либерально. Для продакшна сузьте списки |

---

## Миграции БД

Система миграций — **Alembic**. Стартовая миграция уже присутствует.

**Применить все миграции:**
```bash
alembic upgrade head
```

**Сгенерировать новую миграцию (после изменения моделей):**
```bash
alembic revision --autogenerate -m "describe changes"
alembic upgrade head
```

---

## Качество кода и CI

- **Форматирование** — `black`
- **Линтинг** — `ruff` (исправления `--fix` поддерживаются)
- **Типы** — `mypy`
- **CI** — GitHub Actions (`.github/workflows/ci.yml`):
  - установка зависимостей
  - ruff + black --check + mypy
  - pytest с покрытием

**Pre-commit хуки:**
```bash
pip install pre-commit && pre-commit install
pre-commit run --all-files
```

---

## Тестирование

Запуск тестов:
```bash
pytest -q
pytest --cov=app --cov-report=term-missing
```

Что покрыто тестами:
- Доступность OpenAPI
- Health-check
- Создание/чтение и ETag
- Пагинация с метаданными
- Недопустимые переходы статусов → 409
- ETag/If-Match (успех + 412)
- Удаление и 404
- Валидация входных данных (422)

---

## Наброски дорожной карты

- Фильтры/сортировки в списке задач (`status`, `created_at`, `updated_at`)
- Поиск по ключевым словам, полнотекстовый индекс
- Soft-delete (поле `deleted_at`) и аудит
- Роли/права доступа и аутентификация (OAuth2/JWT)
- Rate limiting (например, SlowAPI/Redis)
- Метрики Prometheus и трейсинг OpenTelemetry
- Версионирование API (`/v1`), E2E тесты, нагрузочное тестирование

---

## FAQ / Траблшутинг

**Ошибка подключения к БД в Docker**  
Проверьте, что сервис `db` в `docker-compose.yml` в состоянии `healthy`. Перезапустите: `docker compose restart db`.

**`alembic` не видит модели**  
Убедитесь, что в `alembic/env.py` импортируется пакет `app` и модуль `app.models` (для автогенерации).

**Windows: проблемы с виртуальным окружением**  
Запускайте терминал PowerShell от имени администратора и активируйте окружение: `.venv\\Scripts\\Activate.ps1`.

---




