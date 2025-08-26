from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, func, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base
from .domain.enums import TaskStatus


class GUIDString(String):
    """Храним UUID как строку (36) — переносимо между БД."""
    def __init__(self, *args, **kwargs):
        super().__init__(length=36, *args, **kwargs)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(GUIDString, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=TaskStatus.CREATED.value, index=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    # Версионирование для ETag/оптимистичной блокировки
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("ix_tasks_status_title", "status", "title"),
    )
