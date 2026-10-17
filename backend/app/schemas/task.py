import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = Field(None, max_length=10000)
    status: str | None = Field("To Do", pattern="^(To Do|In Progress|Done)$")
    priority: str | None = Field("Medium", pattern="^(High|Medium|Low)$")
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = Field(None, max_length=10000)
    status: str | None = Field(None, pattern="^(To Do|In Progress|Done)$")
    priority: str | None = Field(None, pattern="^(High|Medium|Low)$")
    due_date: date | None = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    description: str | None
    status: str
    priority: str
    due_date: date | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True