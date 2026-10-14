from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.resource import Resource
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.resource import ResourceCreate, ResourceListResponse, ResourceResponse, ResourceUpdate

router = APIRouter(prefix="/workspaces/{workspace_id}/resources", tags=["resources"])


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


async def _get_resource_or_404(
    workspace_id: UUID,
    resource_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Resource:
    await _get_workspace_or_404(workspace_id, current_user, db)

    result = await db.execute(
        select(Resource).where(
            Resource.id == resource_id,
            Resource.workspace_id == workspace_id,
        )
    )
    resource = result.scalar_one_or_none()
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    return resource


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    workspace_id: UUID,
    resource_in: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)

    resource = Resource(
        workspace_id=workspace_id,
        title=resource_in.title,
        url=str(resource_in.url),
        description=resource_in.description,
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return ResourceResponse.model_validate(resource)


@router.get("", response_model=ResourceListResponse)
async def list_resources(
    workspace_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)

    stmt = (
        select(Resource).where(Resource.workspace_id == workspace_id).order_by(Resource.updated_at.desc())
    )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    resources = result.scalars().all()

    return ResourceListResponse(
        items=[ResourceResponse.model_validate(r) for r in resources],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    workspace_id: UUID,
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resource = await _get_resource_or_404(workspace_id, resource_id, current_user, db)
    return ResourceResponse.model_validate(resource)


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    workspace_id: UUID,
    resource_id: UUID,
    resource_in: ResourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resource = await _get_resource_or_404(workspace_id, resource_id, current_user, db)

    update_data = resource_in.model_dump(exclude_unset=True)
    if "url" in update_data and update_data["url"] is not None:
        update_data["url"] = str(update_data["url"])
    for field, value in update_data.items():
        setattr(resource, field, value)

    await db.commit()
    await db.refresh(resource)
    return ResourceResponse.model_validate(resource)


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    workspace_id: UUID,
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resource = await _get_resource_or_404(workspace_id, resource_id, current_user, db)

    await db.delete(resource)
    await db.commit()
    return None