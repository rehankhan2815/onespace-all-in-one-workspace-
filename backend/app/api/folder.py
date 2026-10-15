from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.folder import Folder
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.folder import FolderCreate, FolderListResponse, FolderResponse, FolderUpdate

router = APIRouter(prefix="/workspaces/{workspace_id}/folders", tags=["folders"])


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


async def _get_folder_or_404(
    workspace_id: UUID,
    folder_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Folder:
    await _get_workspace_or_404(workspace_id, current_user, db)

    result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.workspace_id == workspace_id,
        )
    )
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )
    return folder


async def _validate_folder_parent(
    workspace_id: UUID,
    parent_id: UUID | None,
    current_folder_id: UUID | None,
    db: AsyncSession,
) -> None:
    """Validate that parent folder exists, belongs to the same workspace, and is not a descendant."""
    if parent_id is None:
        return

    result = await db.execute(
        select(Folder).where(
            Folder.id == parent_id,
            Folder.workspace_id == workspace_id,
        )
    )
    parent = result.scalar_one_or_none()
    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent folder not found in this workspace",
        )

    if current_folder_id is not None:
        # Check if moving folder into its own descendant
        current_id = parent_id
        while current_id is not None:
            if current_id == current_folder_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move folder into its own descendant",
                )
            parent_result = await db.execute(
                select(Folder.parent_id).where(Folder.id == current_id)
            )
            current_id = parent_result.scalar_one_or_none()


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    workspace_id: UUID,
    folder_in: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)
    await _validate_folder_parent(workspace_id, folder_in.parent_id, None, db)

    folder = Folder(
        workspace_id=workspace_id,
        parent_id=folder_in.parent_id,
        name=folder_in.name,
        description=folder_in.description,
    )
    db.add(folder)
    await db.commit()
    await db.refresh(folder)
    return FolderResponse.model_validate(folder)


@router.get("", response_model=FolderListResponse)
async def list_folders(
    workspace_id: UUID,
    parent_id: UUID | None = Query(None, description="Filter by parent folder (None for root)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)
    # Handle empty string as None for root folders
    if parent_id == "":
        parent_id = None

    stmt = select(Folder).where(
        Folder.workspace_id == workspace_id,
        Folder.parent_id == parent_id,
    ).order_by(Folder.name)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    folders = result.scalars().all()

    return FolderListResponse(
        items=[FolderResponse.model_validate(f) for f in folders],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    workspace_id: UUID,
    folder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folder = await _get_folder_or_404(workspace_id, folder_id, current_user, db)
    return FolderResponse.model_validate(folder)


@router.get("/{folder_id}/children", response_model=FolderListResponse)
async def list_child_folders(
    workspace_id: UUID,
    folder_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_folder_or_404(workspace_id, folder_id, current_user, db)

    stmt = select(Folder).where(
        Folder.workspace_id == workspace_id,
        Folder.parent_id == folder_id,
    ).order_by(Folder.name)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    folders = result.scalars().all()

    return FolderListResponse(
        items=[FolderResponse.model_validate(f) for f in folders],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{folder_id}/files", response_model=FolderListResponse)
async def list_folder_files(
    workspace_id: UUID,
    folder_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.file import File
    from app.schemas.file import FileListResponse, FileResponse

    await _get_folder_or_404(workspace_id, folder_id, current_user, db)

    stmt = select(File).where(
        File.workspace_id == workspace_id,
        File.folder_id == folder_id,
    ).order_by(File.upload_date.desc())

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(total_stmt)

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    files = result.scalars().all()

    return FileListResponse(
        items=[FileResponse.model_validate(f) for f in files],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    workspace_id: UUID,
    folder_id: UUID,
    folder_in: FolderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folder = await _get_folder_or_404(workspace_id, folder_id, current_user, db)

    update_data = folder_in.model_dump(exclude_unset=True)

    # Validate parent_id change
    if "parent_id" in update_data:
        await _validate_folder_parent(workspace_id, update_data["parent_id"], folder_id, db)

    for field, value in update_data.items():
        setattr(folder, field, value)

    await db.commit()
    await db.refresh(folder)
    return FolderResponse.model_validate(folder)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    workspace_id: UUID,
    folder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folder = await _get_folder_or_404(workspace_id, folder_id, current_user, db)

    # Cascade delete will handle children folders and files via ORM
    await db.delete(folder)
    await db.commit()
    return None
