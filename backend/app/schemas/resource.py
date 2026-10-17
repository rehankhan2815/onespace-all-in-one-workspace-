import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    url: HttpUrl
    description: str | None = Field(None, max_length=10000)


class ResourceUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    url: HttpUrl | None = None
    description: str | None = Field(None, max_length=10000)


class ResourceResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    url: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True