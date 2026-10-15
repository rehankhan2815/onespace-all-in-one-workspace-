import uuid
from datetime import datetime

from pydantic import BaseModel


class FileResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    folder_id: uuid.UUID | None
    filename: str
    size: int
    upload_date: datetime

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    items: list[FileResponse]
    total: int
    page: int
    page_size: int


class FileUploadResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    folder_id: uuid.UUID | None
    filename: str
    size: int
    upload_date: datetime

    class Config:
        from_attributes = True
