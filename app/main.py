from __future__ import annotations

import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .core.settings import get_settings
from .core.logging import setup_logging
from .database import get_engine
from .routers import tasks
from .deps import get_db
from .exceptions import conflict_handler, precondition_failed_handler, ConflictError, PreconditionFailed

settings = get_settings()
setup_logging(settings.debug)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Сервис управления задачами (CRUD) с UUID, статусами, валидацией переходов, "
        "ETag/версией и расширенной пагинацией."
    ),
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Исключения
app.add_exception_handler(ConflictError, conflict_handler)
app.add_exception_handler(PreconditionFailed, precondition_failed_handler)

# Роуты
app.include_router(tasks.router)


@app.get("/health", tags=["Health"], summary="Проверка работоспособности (пинг БД)")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:  # noqa: BLE001
        logging.exception("Health check failed: %s", e)
        return {"status": "degraded", "error": str(e)}


@app.get("/", include_in_schema=False)
def root():
    return {"message": "See /docs for OpenAPI"}
