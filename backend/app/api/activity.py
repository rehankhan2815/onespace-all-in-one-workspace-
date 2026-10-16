from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.activity import Activity
from app.models.file import File
from app.models.note import Note
from app.models.resource import Resource
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.activity import ActivityResponse
from app.schemas.dashboard import DashboardSummaryResponse

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["activity", "dashboard"])


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


@router.get("/activity/", response_model=list[ActivityResponse])
async def list_activity(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List activity for a workspace, newest first."""
    await _get_workspace_or_404(workspace_id, current_user, db)

    stmt = (
        select(Activity)
        .where(Activity.workspace_id == workspace_id)
        .order_by(Activity.timestamp.desc())
    )
    result = await db.execute(stmt)
    activities = result.scalars().all()

    return [ActivityResponse.model_validate(a) for a in activities]


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary counts for the dashboard."""
    await _get_workspace_or_404(workspace_id, current_user, db)

    # Count tasks
    total_tasks_stmt = select(func.count()).select_from(
        select(Task).where(Task.workspace_id == workspace_id).subquery()
    )
    total_tasks = await db.scalar(total_tasks_stmt)

    completed_tasks_stmt = select(func.count()).select_from(
        select(Task).where(
            Task.workspace_id == workspace_id,
            Task.status == "Done"
        ).subquery()
    )
    completed_tasks = await db.scalar(completed_tasks_stmt)

    pending_tasks = total_tasks - completed_tasks

    # Count notes
    total_notes_stmt = select(func.count()).select_from(
        select(Note).where(Note.workspace_id == workspace_id).subquery()
    )
    total_notes = await db.scalar(total_notes_stmt)

    # Count resources
    total_resources_stmt = select(func.count()).select_from(
        select(Resource).where(Resource.workspace_id == workspace_id).subquery()
    )
    total_resources = await db.scalar(total_resources_stmt)

    # Count files
    total_files_stmt = select(func.count()).select_from(
        select(File).where(File.workspace_id == workspace_id).subquery()
    )
    total_files = await db.scalar(total_files_stmt)

    return DashboardSummaryResponse(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        total_notes=total_notes,
        total_resources=total_resources,
        total_files=total_files,
    )
