from __future__ import annotations

from enum import Enum


class TaskStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED},
    TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED},
    TaskStatus.COMPLETED: set(),
}
