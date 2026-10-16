import os
import sys
import tempfile
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db
from app.main import create_app
from app.models.user import User
from app.models.workspace import Workspace


@pytest.fixture(autouse=True)
def _isolate_test_upload_dir(tmp_path):
    from app.core.config import settings

    original = settings.upload_dir
    settings.upload_dir = tmp_path / "uploads"
    yield
    settings.upload_dir = original


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    # Use a temporary file for SQLite to avoid in-memory isolation issues
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", poolclass=NullPool)
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest_asyncio.fixture(scope="function")
async def db_connection(db_engine):
    """Provide a transactional connection for the test."""
    async with db_engine.connect() as conn:
        trans = await conn.begin()
        yield conn
        await trans.rollback()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_connection) -> AsyncGenerator[AsyncSession, None]:
    """Create a session bound to the test connection."""
    async_session = async_sessionmaker(db_connection, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_connection) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client using the test connection."""
    async_session = async_sessionmaker(db_connection, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with async_session() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session) -> User:
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=hash_password("password123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def another_user(db_session) -> User:
    user = User(
        name="Another User",
        email="another@example.com",
        password_hash="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_workspace(db_session, test_user) -> Workspace:
    workspace = Workspace(
        owner_id=test_user.id,
        name="Test Workspace",
        description="A test workspace",
    )
    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)
    return workspace


@pytest_asyncio.fixture(scope="function")
async def another_user_workspace(db_session, another_user) -> Workspace:
    workspace = Workspace(
        owner_id=another_user.id,
        name="Another User's Workspace",
    )
    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)
    return workspace


@pytest_asyncio.fixture(scope="function")
def auth_headers(test_user) -> dict:
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
def another_user_auth_headers(another_user) -> dict:
    token = create_access_token(data={"sub": str(another_user.id)})
    return {"Authorization": f"Bearer {token}"}
