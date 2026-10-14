from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate

router = APIRouter(prefix="/workspaces/{workspace_id}/tasks", tags=["tasks"])


async def _get_workspace_or_404(
    workspace_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Workspace:
    result = await db.execute(
        select(Workspace).where(
            Workspace.id == workspace_id,
            Workspace.owner_id == current_user.id,
        )
    )
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace


async def _get_task_or_404(
    workspace_id: UUID,
    task_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Task:
    await _get_workspace_or_404(workspace_id, current_user, db)

    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.workspace_id == workspace_id,
        )
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    workspace_id: UUID,
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)

    task = Task(
        workspace_id=workspace_id,
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        due_date=task_in.due_date,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    workspace_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)

    stmt = select(Task).where(Task.workspace_id == workspace_id)

    if status_filter:
        stmt = stmt.where(Task.status == status_filter)
    if priority:
        stmt = stmt.where(Task.priority == priority)

    stmt = stmt.order_by(Task.updated_at.desc())

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    workspace_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task_or_404(workspace_id, task_id, current_user, db)
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    workspace_id: UUID,
    task_id: UUID,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task_or_404(workspace_id, task_id, current_user, db)

    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    workspace_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task_or_404(workspace_id, task_id, current_user, db)

    await db.delete(task)
    await db.commit()
    return None