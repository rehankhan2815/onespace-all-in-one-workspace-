from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
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

    app.include_router(auth_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok", "service": "onespace-api"}

    return app


app = create_app()
