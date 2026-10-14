from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.note import Note
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.note import NoteCreate, NoteListResponse, NoteResponse, NoteUpdate

router = APIRouter(prefix="/workspaces/{workspace_id}/notes", tags=["notes"])


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


async def _get_note_or_404(
    workspace_id: UUID,
    note_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Note:
    await _get_workspace_or_404(workspace_id, current_user, db)

    result = await db.execute(
        select(Note).where(
            Note.id == note_id,
            Note.workspace_id == workspace_id,
        )
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found",
        )
    return note


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    workspace_id: UUID,
    note_in: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)

    note = Note(
        workspace_id=workspace_id,
        title=note_in.title,
        body=note_in.body,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.get("", response_model=NoteListResponse)
async def list_notes(
    workspace_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)

    stmt = select(Note).where(Note.workspace_id == workspace_id).order_by(Note.updated_at.desc())

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    notes = result.scalars().all()

    return NoteListResponse(
        items=[NoteResponse.model_validate(n) for n in notes],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    workspace_id: UUID,
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await _get_note_or_404(workspace_id, note_id, current_user, db)
    return NoteResponse.model_validate(note)


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    workspace_id: UUID,
    note_id: UUID,
    note_in: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await _get_note_or_404(workspace_id, note_id, current_user, db)

    update_data = note_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    workspace_id: UUID,
    note_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    note = await _get_note_or_404(workspace_id, note_id, current_user, db)

    await db.delete(note)
    await db.commit()
    return None