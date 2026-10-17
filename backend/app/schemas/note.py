import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    body: str = Field(default="")


class NoteUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    body: str | None = None


class NoteResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    body: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True