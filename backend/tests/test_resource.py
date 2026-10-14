import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.resource import Resource
from app.models.workspace import Workspace


@pytest_asyncio.fixture
async def test_resource(db_session, test_workspace):
    resource = Resource(
        workspace_id=test_workspace.id,
        title="Test Resource",
        url="https://example.com/resource",
        description="A test resource",
    )
    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)
    return resource


@pytest_asyncio.fixture
async def another_user_resource(db_session, another_user_workspace):
    resource = Resource(
        workspace_id=another_user_workspace.id,
        title="Another User's Resource",
        url="https://private.example.com",
        description="Private resource",
    )
    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)
    return resource


class TestResourceCreate:
    @pytest.mark.asyncio
    async def test_create_resource_success(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/resources",
            json={
                "title": "New Resource",
                "url": "https://example.com/new-resource",
                "description": "A new resource",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Resource"
        assert data["url"] == "https://example.com/new-resource"
        assert data["description"] == "A new resource"
        assert data["workspace_id"] == str(test_workspace.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_resource_minimal(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/resources",
            json={"title": "Minimal Resource", "url": "https://minimal.example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Resource"
        assert data["url"] == "https://minimal.example.com/"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_resource_requires_auth(self, client: AsyncClient, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/resources",
            json={"title": "No Auth", "url": "https://example.com"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_resource_invalid_workspace(self, client: AsyncClient, auth_headers):
        import uuid
        response = await client.post(
            f"/api/workspaces/{uuid.uuid4()}/resources",
            json={"title": "Resource", "url": "https://example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_resource_cross_user_workspace(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.post(
            f"/api/workspaces/{another_user_workspace.id}/resources",
            json={"title": "Resource", "url": "https://example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_resource_validation_invalid_url(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/resources",
            json={"title": "Resource", "url": "not-a-url"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_resource_validation_ftp_url(self, client: AsyncClient, auth_headers, test_workspace):
        # Only http and https should be allowed
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/resources",
            json={"title": "Resource", "url": "ftp://example.com/file"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_resource_validation_empty_title(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/resources",
            json={"title": "", "url": "https://example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestResourceList:
    @pytest.mark.asyncio
    async def test_list_resources_empty(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/resources",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_resources_with_data(self, client: AsyncClient, auth_headers, test_resource):
        response = await client.get(
            f"/api/workspaces/{test_resource.workspace_id}/resources",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["title"] == test_resource.title

    @pytest.mark.asyncio
    async def test_list_resources_pagination(self, client: AsyncClient, auth_headers, test_workspace, db_session):
        for i in range(5):
            db_session.add(Resource(
                workspace_id=test_workspace.id,
                title=f"Resource {i}",
                url=f"https://example.com/{i}"
            ))
        await db_session.commit()

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/resources?page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_list_resources_ordering(self, client: AsyncClient, auth_headers, test_workspace, db_session):
        import asyncio
        for i in range(3):
            db_session.add(Resource(
                workspace_id=test_workspace.id,
                title=f"Resource {i}",
                url=f"https://example.com/{i}"
            ))
            await db_session.commit()
            await asyncio.sleep(0.01)

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/resources",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["items"][0]["title"] == "Resource 2"


class TestResourceGet:
    @pytest.mark.asyncio
    async def test_get_resource_success(self, client: AsyncClient, auth_headers, test_resource):
        response = await client.get(
            f"/api/workspaces/{test_resource.workspace_id}/resources/{test_resource.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_resource.id)
        assert data["title"] == test_resource.title
        assert data["url"] == test_resource.url
        assert data["description"] == test_resource.description

    @pytest.mark.asyncio
    async def test_get_resource_not_found(self, client: AsyncClient, auth_headers, test_workspace):
        import uuid
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/resources/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_resource_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_resource
    ):
        response = await client.get(
            f"/api/workspaces/{another_user_resource.workspace_id}/resources/{another_user_resource.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestResourceUpdate:
    @pytest.mark.asyncio
    async def test_update_resource_title(self, client: AsyncClient, auth_headers, test_resource):
        response = await client.patch(
            f"/api/workspaces/{test_resource.workspace_id}/resources/{test_resource.id}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["url"] == test_resource.url

    @pytest.mark.asyncio
    async def test_update_resource_url(self, client: AsyncClient, auth_headers, test_resource):
        response = await client.patch(
            f"/api/workspaces/{test_resource.workspace_id}/resources/{test_resource.id}",
            json={"url": "https://updated.example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://updated.example.com/"

    @pytest.mark.asyncio
    async def test_update_resource_description(self, client: AsyncClient, auth_headers, test_resource):
        response = await client.patch(
            f"/api/workspaces/{test_resource.workspace_id}/resources/{test_resource.id}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_resource_partial(self, client: AsyncClient, auth_headers, test_resource):
        original_url = test_resource.url
        response = await client.patch(
            f"/api/workspaces/{test_resource.workspace_id}/resources/{test_resource.id}",
            json={"title": "New Title Only"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title Only"
        assert data["url"] == original_url

    @pytest.mark.asyncio
    async def test_update_resource_not_found(self, client: AsyncClient, auth_headers, test_workspace):
        import uuid
        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}/resources/{uuid.uuid4()}",
            json={"title": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_resource_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_resource
    ):
        response = await client.patch(
            f"/api/workspaces/{another_user_resource.workspace_id}/resources/{another_user_resource.id}",
            json={"title": "Hacked"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_resource_validation_invalid_url(self, client: AsyncClient, auth_headers, test_resource):
        response = await client.patch(
            f"/api/workspaces/{test_resource.workspace_id}/resources/{test_resource.id}",
            json={"url": "not-a-url"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestResourceDelete:
    @pytest.mark.asyncio
    async def test_delete_resource(self, client: AsyncClient, auth_headers, test_resource):
        response = await client.delete(
            f"/api/workspaces/{test_resource.workspace_id}/resources/{test_resource.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's gone
        response = await client.get(
            f"/api/workspaces/{test_resource.workspace_id}/resources/{test_resource.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_resource_not_found(self, client: AsyncClient, auth_headers, test_workspace):
        import uuid
        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/resources/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_resource_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_resource
    ):
        response = await client.delete(
            f"/api/workspaces/{another_user_resource.workspace_id}/resources/{another_user_resource.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404