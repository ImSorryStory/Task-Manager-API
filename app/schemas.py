from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .domain.enums import TaskStatus


class ErrorResponse(BaseModel):
    detail: str


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Название")
    description: Optional[str] = Field(None, max_length=2000, description="Описание")


class TaskCreate(TaskBase):
    status: TaskStatus = Field(default=TaskStatus.CREATED, description="Начальный статус")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None

    model_config = ConfigDict(extra="forbid")


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus
    created_at: str
    updated_at: str
    version: int


class PaginationMeta(BaseModel):
    total: int
    offset: int
    limit: int


class TaskListOut(BaseModel):
    items: list[TaskOut]
    meta: PaginationMeta
