import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=10000)
    status: Optional[str] = Field("To Do", pattern="^(To Do|In Progress|Done)$")
    priority: Optional[str] = Field("Medium", pattern="^(High|Medium|Low)$")
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = Field(None, max_length=10000)
    status: Optional[str] = Field(None, pattern="^(To Do|In Progress|Done)$")
    priority: Optional[str] = Field(None, pattern="^(High|Medium|Low)$")
    due_date: Optional[date] = None


class TaskResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int