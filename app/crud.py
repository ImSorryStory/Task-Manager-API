from __future__ import annotations

from typing import Iterable, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .domain.enums import TaskStatus, ALLOWED_TRANSITIONS
from . import models, schemas
from .exceptions import ConflictError


def _validate_transition(old: str, new: str) -> None:
    if old == new:
        return
    try:
        old_e = TaskStatus(old)
        new_e = TaskStatus(new)
    except ValueError:
        raise ConflictError("Unknown status transition")
    if new_e not in ALLOWED_TRANSITIONS[old_e]:
        raise ConflictError(f"Transition {old} → {new} is not allowed")


def create_task(db: Session, task_in: schemas.TaskCreate) -> models.Task:
    task = models.Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status.value,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: str) -> models.Task | None:
    return db.get(models.Task, task_id)


def list_tasks(db: Session, offset: int = 0, limit: int = 100) -> Tuple[Iterable[models.Task], int]:
    total = db.execute(select(func.count(models.Task.id))).scalar_one()
    items = (
        db.query(models.Task)
        .order_by(models.Task.title.asc())
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 1000))
        .all()
    )
    return items, total


def update_task(db: Session, task: models.Task, patch: schemas.TaskUpdate) -> models.Task:
    if patch.title is not None:
        task.title = patch.title
    if patch.description is not None:
        task.description = patch.description
    if patch.status is not None:
        _validate_transition(task.status, patch.status.value)
        task.status = patch.status.value

    # оптимистичное версионирование
    task.version += 1
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.commit()
