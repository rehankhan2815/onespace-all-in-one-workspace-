from app.api.auth import router as auth_router
from app.api.note import router as note_router
from app.api.resource import router as resource_router
from app.api.task import router as task_router
from app.api.workspace import router as workspace_router

__all__ = [
    "auth_router",
    "workspace_router",
    "task_router",
    "note_router",
    "resource_router",
]