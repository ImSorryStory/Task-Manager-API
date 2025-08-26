from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, Header, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..deps import get_db
from ..exceptions import PreconditionFailed

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "/",
    response_model=schemas.TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать задачу",
    responses={409: {"model": schemas.ErrorResponse}},
)
def create_task(task_in: schemas.TaskCreate, db: Session = Depends(get_db)):
    task = crud.create_task(db, task_in)
    return task


@router.get(
    "/{task_id}",
    response_model=schemas.TaskOut,
    summary="Получить задачу по UUID",
    responses={404: {"model": schemas.ErrorResponse}},
)
def get_task(
    response: Response,
    task_id: str = Path(..., description="UUID задачи"),
    db: Session = Depends(get_db),
):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    response.headers["ETag"] = str(task.version)
    return task


@router.get(
    "/",
    response_model=schemas.TaskListOut,
    summary="Список задач (с пагинацией и метаданными)",
)
def list_tasks(
    offset: int = Query(0, ge=0, description="Смещение"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит"),
    db: Session = Depends(get_db),
):
    items, total = crud.list_tasks(db, offset=offset, limit=limit)
    return schemas.TaskListOut(items=list(items), meta=schemas.PaginationMeta(total=total, offset=offset, limit=limit))


@router.patch(
    "/{task_id}",
    response_model=schemas.TaskOut,
    summary="Частичное обновление (ETag/If-Match поддерживается)",
    responses={
        404: {"model": schemas.ErrorResponse},
        409: {"model": schemas.ErrorResponse},
        412: {"model": schemas.ErrorResponse},
    },
)
def update_task(
    response: Response,
    task_id: str,
    patch: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    if_match: Optional[str] = Header(None, convert_underscores=False),
):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if if_match is not None:
        try:
            expected = int(if_match.strip('"')) if if_match.startswith('"') else int(if_match)
        except ValueError:
            raise PreconditionFailed("If-Match must be an integer version")
        if expected != task.version:
            raise PreconditionFailed("ETag version does not match (If-Match failed)")

    task = crud.update_task(db, task, patch)
    response.headers["ETag"] = str(task.version)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу",
    responses={404: {"model": schemas.ErrorResponse}},
)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    crud.delete_task(db, task)
    return None
