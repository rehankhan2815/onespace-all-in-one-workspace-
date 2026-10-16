from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi import File as FastAPIFile
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.file import File
from app.models.folder import Folder
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.file import FileListResponse, FileResponse, FileUploadResponse
from app.utils.activity import log_file_deleted, log_file_uploaded
from app.utils.file_storage import (
    delete_storage_file,
    generate_storage_name,
    get_storage_path,
    sanitize_filename,
    save_upload_file,
    validate_upload_size,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/files", tags=["files"])


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


async def _get_file_or_404(
    workspace_id: UUID,
    file_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> File:
    await _get_workspace_or_404(workspace_id, current_user, db)

    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.workspace_id == workspace_id,
        )
    )
    file = result.scalar_one_or_none()
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return file


async def _validate_folder_belongs_to_workspace(
    workspace_id: UUID,
    folder_id: UUID | None,
    db: AsyncSession,
) -> None:
    """Validate that folder exists and belongs to the workspace."""
    if folder_id is None:
        return

    result = await db.execute(
        select(Folder).where(
            Folder.id == folder_id,
            Folder.workspace_id == workspace_id,
        )
    )
    folder = result.scalar_one_or_none()
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Folder not found in this workspace",
        )


@router.post("", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    workspace_id: UUID,
    file: UploadFile = FastAPIFile(...),
    folder_id: UUID | None = Query(None, description="Optional folder ID to place file in"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)
    await _validate_folder_belongs_to_workspace(workspace_id, folder_id, db)

    # Read file content to validate size
    content = await file.read()
    try:
        validate_upload_size(len(content))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Sanitize filename
    safe_filename = sanitize_filename(file.filename or "unnamed")
    storage_name = generate_storage_name(safe_filename)

    # Save file to storage
    from io import BytesIO
    file_size = save_upload_file(BytesIO(content), storage_name)

    # Create file record
    file_record = File(
        workspace_id=workspace_id,
        folder_id=folder_id,
        filename=safe_filename,
        size=file_size,
        storage_path=storage_name,
    )
    db.add(file_record)
    await db.flush()
    await log_file_uploaded(db, workspace_id, file_record.filename)
    await db.commit()
    await db.refresh(file_record)

    return FileUploadResponse.model_validate(file_record)


@router.get("", response_model=FileListResponse)
async def list_files(
    workspace_id: UUID,
    folder_id: UUID | None = Query(None, description="Filter by folder (None for root files)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_workspace_or_404(workspace_id, current_user, db)
    # Handle empty string as None for root files
    if folder_id == "":
        folder_id = None
    await _validate_folder_belongs_to_workspace(workspace_id, folder_id, db)

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


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    workspace_id: UUID,
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file = await _get_file_or_404(workspace_id, file_id, current_user, db)
    return FileResponse.model_validate(file)


@router.get("/{file_id}/download")
async def download_file(
    workspace_id: UUID,
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file = await _get_file_or_404(workspace_id, file_id, current_user, db)

    storage_path = get_storage_path(file.storage_path)

    if not storage_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage",
        )

    return FastAPIFileResponse(
        path=storage_path,
        filename=file.filename,
        media_type="application/octet-stream",
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    workspace_id: UUID,
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file = await _get_file_or_404(workspace_id, file_id, current_user, db)

    file_filename = file.filename
    # Delete physical file from storage
    delete_storage_file(file.storage_path)

    # Delete database record
    await db.delete(file)
    await log_file_deleted(db, workspace_id, file_filename)
    await db.commit()
    return None
