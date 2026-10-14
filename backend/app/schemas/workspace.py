import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    archived: Optional[bool] = None


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    items: list[WorkspaceResponse]
    total: int
    page: int
    page_size: int