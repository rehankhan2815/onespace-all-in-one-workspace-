import uuid
from datetime import datetime

from pydantic import BaseModel


class ActivityResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    type: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True
