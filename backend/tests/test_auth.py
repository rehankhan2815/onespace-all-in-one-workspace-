from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.models.user import User


class TestPasswordHashing:
    def test_hash_password_returns_hash(self):
        password = "testpass"
        hashed = hash_password(password)
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_password_correct(self):
        password = "testpass"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "testpass"
        hashed = hash_password(password)
        assert verify_password("wrongpass", hashed) is False


class TestJWT:
    def test_create_access_token(self):
        token = create_access_token(data={"sub": "user-id"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_valid(self):
        token = create_access_token(data={"sub": "user-id"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-id"
        assert "exp" in payload

    def test_decode_token_invalid(self):
        payload = decode_token("invalid.token.string")
        assert payload is None

    def test_decode_token_expired(self):
        token = create_access_token(data={"sub": "user-id"}, expires_delta=timedelta(seconds=-1))
        payload = decode_token(token)
        assert payload is None


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "New User",
                "email": "new@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New User"
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_register_password_hashed(self, client: AsyncClient, db_session):
        await client.post(
            "/api/auth/register",
            json={
                "name": "New User",
                "email": "hashed@example.com",
                "password": "password123",
            },
        )
        # Check password is hashed in database
        from sqlalchemy import select
        result = await db_session.execute(select(User).where(User.email == "hashed@example.com"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.password_hash != "password123"
        assert verify_password("password123", user.password_hash)

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "Another User",
                "email": test_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_email_normalization(self, client: AsyncClient, db_session):
        await client.post(
            "/api/auth/register",
            json={
                "name": "User",
                "email": "UPPER@EXAMPLE.COM",
                "password": "password123",
            },
        )
        from sqlalchemy import select
        result = await db_session.execute(select(User).where(User.email == "upper@example.com"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "upper@example.com"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "User",
                "email": "invalid-email",
                "password": "password123",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={
                "name": "User",
                "email": "user@example.com",
                "password": "123",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={"name": "User"},
        )
        assert response.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 30 * 60

        # Verify token is valid
        payload = decode_token(data["access_token"])
        assert payload is not None
        assert payload["sub"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_login_incorrect_password(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_unknown_email(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "unknown@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_email_normalization(self, client: AsyncClient, test_user: User):
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email.upper(),
                "password": "password123",
            },
        )
        assert response.status_code == 200


class TestCurrentUser:
    @pytest.mark.asyncio
    async def test_me_with_valid_token(self, client: AsyncClient, test_user: User):
        token = create_access_token(data={"sub": str(test_user.id)})
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["name"] == test_user.name
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_me_without_token(self, client: AsyncClient):
        response = await client.get("/api/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_me_with_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.string"},
        )
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_me_with_malformed_token(self, client: AsyncClient):
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_expired_token(self, client: AsyncClient, test_user: User):
        token = create_access_token(data={"sub": str(test_user.id)}, expires_delta=timedelta(seconds=-1))
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_me_with_nonexistent_user(self, client: AsyncClient):
        import uuid
        token = create_access_token(data={"sub": str(uuid.uuid4())})
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_me_with_invalid_uuid_in_token(self, client: AsyncClient):
        token = create_access_token(data={"sub": "not-a-uuid"})
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert "Invalid token payload" in response.json()["detail"]
