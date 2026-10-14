from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceListResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspace = Workspace(
        owner_id=current_user.id,
        name=workspace_in.name,
        description=workspace_in.description,
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return WorkspaceResponse.model_validate(workspace)


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    archived: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Workspace).where(
        Workspace.owner_id == current_user.id,
        Workspace.archived == archived,
    ).order_by(Workspace.updated_at.desc())

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    workspaces = result.scalars().all()

    return WorkspaceListResponse(
        items=[WorkspaceResponse.model_validate(w) for w in workspaces],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    return WorkspaceResponse.model_validate(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    workspace_in: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    update_data = workspace_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)

    await db.commit()
    await db.refresh(workspace)
    return WorkspaceResponse.model_validate(workspace)


@router.post("/{workspace_id}/archive", response_model=WorkspaceResponse)
async def archive_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    workspace.archived = True
    await db.commit()
    await db.refresh(workspace)
    return WorkspaceResponse.model_validate(workspace)


@router.post("/{workspace_id}/unarchive", response_model=WorkspaceResponse)
async def unarchive_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    workspace.archived = False
    await db.commit()
    await db.refresh(workspace)
    return WorkspaceResponse.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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

    await db.delete(workspace)
    await db.commit()
    return None