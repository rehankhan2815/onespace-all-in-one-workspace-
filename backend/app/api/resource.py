from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.resource import Resource
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.resource import ResourceCreate, ResourceResponse, ResourceUpdate
from app.utils.activity import (
    log_resource_added,
    log_resource_deleted,
    log_resource_updated,
)

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
    await db.flush()
    await log_resource_added(db, workspace_id, resource.title)
    await db.commit()
    await db.refresh(resource)
    return ResourceResponse.model_validate(resource)


@router.get("", response_model=list[ResourceResponse])
async def list_resources(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)

    stmt = (
        select(Resource).where(Resource.workspace_id == workspace_id).order_by(Resource.updated_at.desc())
    )
    result = await db.execute(stmt)
    resources = result.scalars().all()

    return [ResourceResponse.model_validate(r) for r in resources]


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

    await log_resource_updated(db, workspace_id, resource.title)
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

    resource_title = resource.title
    await db.delete(resource)
    await log_resource_deleted(db, workspace_id, resource_title)
    await db.commit()
    return None
