import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.workspace import Workspace


class TestWorkspaceCreate:
    @pytest.mark.asyncio
    async def test_create_workspace_success(self, client: AsyncClient, auth_headers, db_session):
        response = await client.post(
            "/api/workspaces",
            json={"name": "New Workspace", "description": "A new workspace"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Workspace"
        assert data["description"] == "A new workspace"
        assert data["archived"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_workspace_minimal(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/workspaces",
            json={"name": "Minimal Workspace"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Workspace"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_workspace_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/api/workspaces",
            json={"name": "No Auth Workspace"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_workspace_validation_empty_name(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/workspaces",
            json={"name": "", "description": "test"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_workspace_validation_long_name(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/workspaces",
            json={"name": "x" * 201, "description": "test"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestWorkspaceList:
    @pytest.mark.asyncio
    async def test_list_workspaces_empty(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/workspaces", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_list_workspaces_with_data(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.get("/api/workspaces", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == test_workspace.name

    @pytest.mark.asyncio
    async def test_list_workspaces_pagination(self, client: AsyncClient, auth_headers, test_user, db_session):
        # Create multiple workspaces
        for i in range(5):
            ws = Workspace(owner_id=test_user.id, name=f"Workspace {i}")
            db_session.add(ws)
        await db_session.commit()

        response = await client.get("/api/workspaces?page=1&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5

        response = await client.get("/api/workspaces?page=2&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2

    @pytest.mark.asyncio
    async def test_list_workspaces_archived_filter(self, client: AsyncClient, auth_headers, test_user, db_session):
        ws1 = Workspace(owner_id=test_user.id, name="Active", archived=False)
        ws2 = Workspace(owner_id=test_user.id, name="Archived", archived=True)
        db_session.add_all([ws1, ws2])
        await db_session.commit()

        response = await client.get("/api/workspaces?archived=false", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Active"

        response = await client.get("/api/workspaces?archived=true", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Archived"

    @pytest.mark.asyncio
    async def test_list_workspaces_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.get("/api/workspaces", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should not see another user's workspace
        assert data["total"] == 0


class TestWorkspaceGet:
    @pytest.mark.asyncio
    async def test_get_workspace_success(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.get(f"/api/workspaces/{test_workspace.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_workspace.id)
        assert data["name"] == test_workspace.name
        assert data["description"] == test_workspace.description

    @pytest.mark.asyncio
    async def test_get_workspace_not_found(self, client: AsyncClient, auth_headers):
        import uuid
        response = await client.get(f"/api/workspaces/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_workspace_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.get(f"/api/workspaces/{another_user_workspace.id}", headers=auth_headers)
        assert response.status_code == 404


class TestWorkspaceUpdate:
    @pytest.mark.asyncio
    async def test_update_workspace_name(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == test_workspace.description

    @pytest.mark.asyncio
    async def test_update_workspace_description(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_workspace_archived(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}",
            json={"archived": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["archived"] is True

    @pytest.mark.asyncio
    async def test_update_workspace_partial(self, client: AsyncClient, auth_headers, test_workspace):
        # Only update name, description should remain
        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}",
            json={"name": "New Name Only"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name Only"
        assert data["description"] == test_workspace.description

    @pytest.mark.asyncio
    async def test_update_workspace_not_found(self, client: AsyncClient, auth_headers):
        import uuid
        response = await client.patch(
            f"/api/workspaces/{uuid.uuid4()}",
            json={"name": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_workspace_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.patch(
            f"/api/workspaces/{another_user_workspace.id}",
            json={"name": "Hacked"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_workspace_validation(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}",
            json={"name": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestWorkspaceArchive:
    @pytest.mark.asyncio
    async def test_archive_workspace(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/archive",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["archived"] is True

    @pytest.mark.asyncio
    async def test_archive_already_archived(self, client: AsyncClient, auth_headers, test_user, db_session):
        ws = Workspace(owner_id=test_user.id, name="Already Archived", archived=True)
        db_session.add(ws)
        await db_session.commit()

        response = await client.post(f"/api/workspaces/{ws.id}/archive", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["archived"] is True

    @pytest.mark.asyncio
    async def test_unarchive_workspace(self, client: AsyncClient, auth_headers, test_user, db_session):
        ws = Workspace(owner_id=test_user.id, name="To Unarchive", archived=True)
        db_session.add(ws)
        await db_session.commit()

        response = await client.post(f"/api/workspaces/{ws.id}/unarchive", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["archived"] is False

    @pytest.mark.asyncio
    async def test_archive_not_found(self, client: AsyncClient, auth_headers):
        import uuid
        response = await client.post(f"/api/workspaces/{uuid.uuid4()}/archive", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_archive_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.post(
            f"/api/workspaces/{another_user_workspace.id}/archive",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestWorkspaceDelete:
    @pytest.mark.asyncio
    async def test_delete_workspace(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.delete(f"/api/workspaces/{test_workspace.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        response = await client.get(f"/api/workspaces/{test_workspace.id}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_workspace_cascades(
        self, client: AsyncClient, auth_headers, test_user, db_session
    ):
        ws = Workspace(owner_id=test_user.id, name="To Delete")
        db_session.add(ws)
        await db_session.commit()

        # Add a task to the workspace
        from app.models.task import Task
        task = Task(workspace_id=ws.id, title="Task in workspace")
        db_session.add(task)
        await db_session.commit()

        response = await client.delete(f"/api/workspaces/{ws.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify workspace and task are gone
        from sqlalchemy import select
        result = await db_session.execute(select(Workspace).where(Workspace.id == ws.id))
        assert result.scalar_one_or_none() is None
        result = await db_session.execute(select(Task).where(Task.workspace_id == ws.id))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_delete_workspace_not_found(self, client: AsyncClient, auth_headers):
        import uuid
        response = await client.delete(f"/api/workspaces/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_workspace_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.delete(
            f"/api/workspaces/{another_user_workspace.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404