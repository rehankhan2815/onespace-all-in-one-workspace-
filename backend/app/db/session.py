from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


_engine = None
_async_session_maker = None


def get_engine():
    global _engine
    if _engine is None:
        url = settings.database_url
        # For SQLite, use aiosqlite driver
        if url.startswith("sqlite"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://")
        _engine = create_async_engine(url, echo=False, pool_pre_ping=True)
    return _engine


def get_async_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_maker


async def get_db() -> AsyncSession:
    async with get_async_session_maker()() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
