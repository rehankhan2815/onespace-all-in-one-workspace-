import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    archived: bool | None = None


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True