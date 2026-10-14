from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.note import router as note_router
from app.api.resource import router as resource_router
from app.api.task import router as task_router
from app.api.workspace import router as workspace_router
from app.core.config import settings
from app.db.session import close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title="OneSpace API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix="/api")
    app.include_router(workspace_router, prefix="/api")
    app.include_router(task_router, prefix="/api")
    app.include_router(note_router, prefix="/api")
    app.include_router(resource_router, prefix="/api")

    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok", "service": "onespace-api"}

    return app


app = create_app()
