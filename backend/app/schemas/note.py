import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    body: str = Field(default="")


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    body: Optional[str] = None


class NoteResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    body: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int
    page: int
    page_size: int