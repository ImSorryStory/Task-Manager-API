#!/usr/bin/env bash
set -e

# применяем миграции
alembic upgrade head

# запускаем приложение
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
