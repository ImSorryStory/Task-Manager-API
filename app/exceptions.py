from __future__ import annotations

from fastapi import status
from fastapi.responses import JSONResponse

from .schemas import ErrorResponse


class ConflictError(Exception):
    """Бизнес-конфликт (например, недопустимый переход статуса)."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class PreconditionFailed(Exception):
    """Несовпадение ETag/версии (If-Match)."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def conflict_handler(_, exc: ConflictError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(detail=exc.message).model_dump(),
    )


def precondition_failed_handler(_, exc: PreconditionFailed):
    return JSONResponse(
        status_code=status.HTTP_412_PRECONDITION_FAILED,
        content=ErrorResponse(detail=exc.message).model_dump(),
    )
