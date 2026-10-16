import uuid
from datetime import datetime

from pydantic import BaseModel


class SearchTaskResult(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    description: str | None
    status: str
    priority: str
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchNoteResult(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    body: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchResourceResult(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    url: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchFileResult(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    folder_id: uuid.UUID | None
    filename: str
    size: int
    upload_date: datetime

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    tasks: list[SearchTaskResult]
    notes: list[SearchNoteResult]
    resources: list[SearchResourceResult]
    files: list[SearchFileResult]
