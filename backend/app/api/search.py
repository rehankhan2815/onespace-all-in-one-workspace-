from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.file import File
from app.models.note import Note
from app.models.resource import Resource
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.search import (
    SearchFileResult,
    SearchNoteResult,
    SearchResourceResult,
    SearchResponse,
    SearchTaskResult,
)

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["search"])


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


@router.get("/search/", response_model=SearchResponse)
async def search_workspace(
    workspace_id: UUID,
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search across tasks, notes, resources, and files in a workspace."""
    await _get_workspace_or_404(workspace_id, current_user, db)

    query = q.strip()
    if not query:
        return SearchResponse(tasks=[], notes=[], resources=[], files=[])

    search_term = f"%{query.lower()}%"

    # Search tasks
    tasks_stmt = select(Task).where(
        Task.workspace_id == workspace_id,
        or_(
            Task.title.ilike(search_term),
            Task.description.ilike(search_term),
            Task.status.ilike(search_term),
            Task.priority.ilike(search_term),
        )
    ).order_by(Task.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)

    tasks_result = await db.execute(tasks_stmt)
    tasks = tasks_result.scalars().all()

    # Search notes
    notes_stmt = select(Note).where(
        Note.workspace_id == workspace_id,
        or_(
            Note.title.ilike(search_term),
            Note.body.ilike(search_term),
        )
    ).order_by(Note.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)

    notes_result = await db.execute(notes_stmt)
    notes = notes_result.scalars().all()

    # Search resources
    resources_stmt = select(Resource).where(
        Resource.workspace_id == workspace_id,
        or_(
            Resource.title.ilike(search_term),
            Resource.description.ilike(search_term),
            Resource.url.ilike(search_term),
        )
    ).order_by(Resource.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)

    resources_result = await db.execute(resources_stmt)
    resources = resources_result.scalars().all()

    # Search files
    files_stmt = select(File).where(
        File.workspace_id == workspace_id,
        File.filename.ilike(search_term),
    ).order_by(File.upload_date.desc()).offset((page - 1) * page_size).limit(page_size)

    files_result = await db.execute(files_stmt)
    files = files_result.scalars().all()

    return SearchResponse(
        tasks=[SearchTaskResult.model_validate(t) for t in tasks],
        notes=[SearchNoteResult.model_validate(n) for n in notes],
        resources=[SearchResourceResult.model_validate(r) for r in resources],
        files=[SearchFileResult.model_validate(f) for f in files],
    )
