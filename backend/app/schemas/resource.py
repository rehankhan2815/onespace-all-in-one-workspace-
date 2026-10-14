import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    url: HttpUrl
    description: Optional[str] = Field(None, max_length=10000)


class ResourceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    url: Optional[HttpUrl] = None
    description: Optional[str] = Field(None, max_length=10000)


class ResourceResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    url: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResourceListResponse(BaseModel):
    items: list[ResourceResponse]
    total: int
    page: int
    page_size: int